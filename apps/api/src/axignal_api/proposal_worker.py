from __future__ import annotations

import argparse
import json
import logging
import time
from pathlib import Path

from axignal_api.deepseek_proposals import (
    DEEPSEEK_CHECKPOINT,
    DeepSeekV4FlashProposalAdapter,
)
from axignal_api.document_proposals import (
    DocumentPipelineError,
    DocumentSecurityError,
    FrozenProposalAdapter,
    InstitutionalDocument,
    LocalDocumentProposalPipeline,
    OpenAICompatibleLocalModelAdapter,
    ProposalBatch,
)
from axignal_api.proposal_queue import (
    DocumentProposalJob,
    ValkeyDocumentProposalQueue,
)
from axignal_api.proposal_repository import (
    DOCUMENT_ID,
    PIPELINE_VERSION,
    SOURCE_ID,
    DocumentProposalRepository,
)
from axignal_api.runtime_invariants import require_runtime_value
from axignal_api.settings import Settings

LOGGER = logging.getLogger("axignal.document-proposal-worker")


class PersistentDocumentProposalWorker:
    def __init__(
        self,
        *,
        repository: DocumentProposalRepository,
        queue: ValkeyDocumentProposalQueue,
        document: InstitutionalDocument,
        pipeline: LocalDocumentProposalPipeline,
    ) -> None:
        self.repository = repository
        self.queue = queue
        self.document = document
        self.pipeline = pipeline

    def run_once(self, *, timeout_seconds: int = 1) -> bool:
        job = self.queue.dequeue(timeout_seconds=timeout_seconds)
        if job is None:
            return False
        self.process(job)
        return True

    def process(self, job: DocumentProposalJob) -> None:
        run = self.repository.get_run_for_worker(
            tenant_id=job.tenant_id,
            run_id=job.research_run_id,
        )
        if run is None:
            LOGGER.warning(
                "Ignoring missing tenant-scoped document ResearchRun %s",
                job.research_run_id,
            )
            return
        if run["state"] == "COMPLETED_PROVISIONAL":
            LOGGER.info("Document ResearchRun %s is already complete", job.research_run_id)
            return
        if run.get("job_kind") != "DOCUMENT_PROPOSAL":
            self._fail(job, "JOB_KIND_MISMATCH", "ResearchRun is not a document proposal run")
            return
        if job.source_id != SOURCE_ID or job.document_id != DOCUMENT_ID:
            self._fail(job, "DOCUMENT_NOT_ROUTED", "No admitted document route matches this job")
            return
        if job.pipeline_version != PIPELINE_VERSION:
            self._fail(
                job,
                "PIPELINE_VERSION_MISMATCH",
                "Document proposal pipeline version differs",
            )
            return
        if self.document.document_id != job.document_id:
            self._fail(job, "DOCUMENT_FIXTURE_MISMATCH", "Configured document identity differs")
            return

        source = self.repository.get_source(job.source_id)
        if source is None:
            self._fail(job, "SOURCE_NOT_REGISTERED", "Document source is absent from registry")
            return
        source_error = self._source_block_reason(source)
        if source_error:
            self._fail(job, "SOURCE_NOT_ADMITTED", source_error)
            return

        try:
            self.repository.transition_run(
                tenant_id=job.tenant_id,
                run_id=job.research_run_id,
                state="RETRIEVING",
            )
            self.repository.transition_run(
                tenant_id=job.tenant_id,
                run_id=job.research_run_id,
                state="DOCUMENT_PARSING",
            )
            self.repository.transition_run(
                tenant_id=job.tenant_id,
                run_id=job.research_run_id,
                state="SECURITY_SCANNING",
            )
            self.repository.transition_run(
                tenant_id=job.tenant_id,
                run_id=job.research_run_id,
                state="PROPOSING",
            )
            result = self.pipeline.execute(
                document=self.document,
                opportunity_id=run["opportunity_id"],
                research_question=run["question"],
            )
            self.repository.transition_run(
                tenant_id=job.tenant_id,
                run_id=job.research_run_id,
                state="EVIDENCE_BINDING",
            )
            self.repository.transition_run(
                tenant_id=job.tenant_id,
                run_id=job.research_run_id,
                state="HANDOFF_PENDING",
            )
            self.repository.persist_result(
                tenant_id=job.tenant_id,
                run_id=job.research_run_id,
                source=source,
                result=result,
            )
        except DocumentSecurityError as exc:
            LOGGER.exception("Document ResearchRun %s quarantined", job.research_run_id)
            self.repository.record_failure(
                job=job,
                error_code="DOCUMENT_SECURITY_QUARANTINE",
                error_detail=str(exc),
                quarantined=True,
            )
        except (DocumentPipelineError, LookupError, RuntimeError, ValueError) as exc:
            LOGGER.exception("Document ResearchRun %s failed closed", job.research_run_id)
            self.repository.record_failure(
                job=job,
                error_code=exc.__class__.__name__.upper(),
                error_detail=str(exc),
                quarantined=False,
            )

    def _fail(self, job: DocumentProposalJob, error_code: str, detail: str) -> None:
        self.repository.record_failure(
            job=job,
            error_code=error_code,
            error_detail=detail,
            quarantined=False,
        )

    @staticmethod
    def _source_block_reason(source: dict[str, object]) -> str | None:
        if source.get("admission_state") != "ADMITTED":
            return "Document source admission state is not ADMITTED"
        if bool(source.get("kill_switch")):
            return "Document source kill switch is enabled"
        if source.get("rights_status") != "COMMERCIAL_REUSE_WITH_ATTRIBUTION":
            return "Document source rights do not permit commercial reuse"
        if source.get("license_id") != "CC-BY-4.0":
            return "Document source license is not the admitted fixture license"
        if not bool(source.get("commercial_use")) or not bool(source.get("redistribution")):
            return "Document source reuse permissions are incomplete"
        return None


def _load_json(path: Path) -> dict[str, object]:
    decoded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(decoded, dict):
        raise RuntimeError(f"Fixture {path} must contain a JSON object")
    return decoded


def build_runtime(settings: Settings) -> PersistentDocumentProposalWorker:
    settings.require_document_proposal_worker()
    proposal_database_url = require_runtime_value(
        settings.proposal_database_url,
        name="AXIGNAL_PROPOSAL_DATABASE_URL",
    )
    valkey_url = require_runtime_value(
        settings.valkey_url,
        name="AXIGNAL_VALKEY_URL",
    )
    document_fixture_path = require_runtime_value(
        settings.document_fixture_path,
        name="AXIGNAL_DOCUMENT_FIXTURE_PATH",
    )

    repository = DocumentProposalRepository(proposal_dsn=proposal_database_url)
    queue = ValkeyDocumentProposalQueue(
        valkey_url,
        queue_key=settings.proposal_queue_key,
    )
    document = InstitutionalDocument.model_validate(_load_json(document_fixture_path))

    if settings.deepseek_proposal_enabled:
        deepseek_api_key = require_runtime_value(
            settings.deepseek_api_key,
            name="AXIGNAL_DEEPSEEK_API_KEY",
        )
        gateway = DeepSeekV4FlashProposalAdapter(
            api_key=deepseek_api_key,
            base_url=settings.deepseek_base_url,
            model=settings.deepseek_model,
            checkpoint=DEEPSEEK_CHECKPOINT,
            max_output_tokens=settings.deepseek_max_output_tokens,
            timeout_seconds=settings.deepseek_timeout_seconds,
        )
    elif settings.local_model_base_url:
        if not settings.local_model_name:
            raise RuntimeError("AXIGNAL_LOCAL_MODEL_NAME is required with local model endpoint")
        gateway = OpenAICompatibleLocalModelAdapter(
            base_url=settings.local_model_base_url,
            model=settings.local_model_name,
            api_key=settings.local_model_api_key or "local-only",
        )
    else:
        proposal_fixture_path = require_runtime_value(
            settings.document_proposal_fixture_path,
            name="AXIGNAL_DOCUMENT_PROPOSAL_FIXTURE_PATH",
        )
        proposal = ProposalBatch.model_validate(_load_json(proposal_fixture_path))
        gateway = FrozenProposalAdapter(proposal)

    worker = PersistentDocumentProposalWorker(
        repository=repository,
        queue=queue,
        document=document,
        pipeline=LocalDocumentProposalPipeline(model_gateway=gateway),
    )
    return worker


def main() -> int:
    parser = argparse.ArgumentParser(description="AXIGNAL proposal-only document worker")
    parser.add_argument("--once", action="store_true", help="Process at most one queued job")
    parser.add_argument("--poll-seconds", type=float, default=2.0)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    worker = build_runtime(Settings.from_env())
    if args.once:
        worker.run_once(timeout_seconds=1)
        return 0

    while True:
        worker.run_once(timeout_seconds=max(1, int(args.poll_seconds)))
        time.sleep(max(0.1, args.poll_seconds))


if __name__ == "__main__":
    raise SystemExit(main())
