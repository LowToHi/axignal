from __future__ import annotations

import argparse
import logging
import time

from axignal_api.admission import (
    build_world_bank_inflation_artifacts,
    evaluate_observed_fact,
)
from axignal_api.connectors.world_bank import (
    SOURCE_ID,
    SourceRetrievalError,
    WorldBankConnector,
)
from axignal_api.queue import OutboxPublisher, ResearchJob, ValkeyResearchQueue
from axignal_api.repository import ResearchRepository
from axignal_api.settings import Settings

LOGGER = logging.getLogger("axignal.research-worker")


class ResearchWorker:
    def __init__(
        self,
        *,
        repository: ResearchRepository,
        queue: ValkeyResearchQueue,
        connector: WorldBankConnector,
    ) -> None:
        self.repository = repository
        self.queue = queue
        self.connector = connector

    def run_once(self, *, timeout_seconds: int = 1) -> bool:
        job = self.queue.dequeue(timeout_seconds=timeout_seconds)
        if job is None:
            return False
        self.process(job)
        return True

    def process(self, job: ResearchJob) -> None:
        run = self.repository.get_run_for_worker(
            tenant_id=job.tenant_id,
            run_id=job.research_run_id,
        )
        if run is None:
            LOGGER.warning(
                "Ignoring job for missing tenant-scoped ResearchRun %s",
                job.research_run_id,
            )
            return
        if run["state"] == "COMPLETED":
            LOGGER.info(
                "ResearchRun %s is already complete; duplicate delivery ignored",
                job.research_run_id,
            )
            return
        if job.source_id != SOURCE_ID:
            self.repository.fail_run(
                tenant_id=job.tenant_id,
                run_id=job.research_run_id,
                error_code="SOURCE_NOT_ROUTED",
                error_detail=f"No admitted worker route exists for source {job.source_id}",
            )
            return

        source = self.repository.get_source(job.source_id)
        if source is None:
            self.repository.fail_run(
                tenant_id=job.tenant_id,
                run_id=job.research_run_id,
                error_code="SOURCE_NOT_REGISTERED",
                error_detail="The source registry contains no matching source",
            )
            return
        source_error = self._source_block_reason(source)
        if source_error:
            self.repository.fail_run(
                tenant_id=job.tenant_id,
                run_id=job.research_run_id,
                error_code="SOURCE_NOT_ADMITTED",
                error_detail=source_error,
            )
            return

        try:
            self.repository.transition_run(
                tenant_id=job.tenant_id,
                run_id=job.research_run_id,
                state="RETRIEVING",
            )
            observation = self.connector.fetch_latest_inflation()
            self.repository.transition_run(
                tenant_id=job.tenant_id,
                run_id=job.research_run_id,
                state="PROPOSING",
            )
            evidence, candidate = build_world_bank_inflation_artifacts(
                opportunity_id=run["opportunity_id"],
                period=observation.period,
                value=observation.value,
                source_content_hash=observation.content_hash,
            )
            self.repository.transition_run(
                tenant_id=job.tenant_id,
                run_id=job.research_run_id,
                state="ADMISSION_PENDING",
            )
            decision = evaluate_observed_fact(
                source=source,
                evidence=evidence,
                candidate=candidate,
            )
            self.repository.complete_world_bank_run(
                tenant_id=job.tenant_id,
                run_id=job.research_run_id,
                source=source,
                observation=observation,
                evidence=evidence,
                candidate=candidate,
                decision=decision,
            )
        except (SourceRetrievalError, LookupError, RuntimeError, ValueError) as exc:
            LOGGER.exception("ResearchRun %s failed closed", job.research_run_id)
            self.repository.fail_run(
                tenant_id=job.tenant_id,
                run_id=job.research_run_id,
                error_code=exc.__class__.__name__.upper(),
                error_detail=str(exc),
            )

    @staticmethod
    def _source_block_reason(source: dict[str, object]) -> str | None:
        if source.get("admission_state") != "ADMITTED":
            return "Source admission state is not ADMITTED"
        if bool(source.get("kill_switch")):
            return "Source kill switch is enabled"
        if source.get("rights_status") != "COMMERCIAL_REUSE_WITH_ATTRIBUTION":
            return "Source rights do not permit commercial reuse with attribution"
        if not bool(source.get("commercial_use")) or not bool(source.get("redistribution")):
            return "Source commercial-use or redistribution permission is absent"
        return None


def build_runtime(settings: Settings) -> tuple[OutboxPublisher, ResearchWorker]:
    settings.require_persistent_research()
    assert settings.database_url is not None
    assert settings.valkey_url is not None
    repository = ResearchRepository(settings.database_url)
    queue = ValkeyResearchQueue(settings.valkey_url, queue_key=settings.queue_key)
    connector = WorldBankConnector(
        live_enabled=settings.live_sources_enabled,
        fixture_path=settings.world_bank_fixture_path,
    )
    return OutboxPublisher(repository, queue), ResearchWorker(
        repository=repository,
        queue=queue,
        connector=connector,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="AXIGNAL persistent Research Worker")
    parser.add_argument("--once", action="store_true", help="Publish and process at most one job")
    parser.add_argument("--poll-seconds", type=float, default=2.0)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    publisher, worker = build_runtime(Settings.from_env())

    if args.once:
        publisher.publish_pending(limit=20)
        worker.run_once(timeout_seconds=1)
        publisher.publish_pending(limit=20)
        return 0

    while True:
        publisher.publish_pending(limit=20)
        worker.run_once(timeout_seconds=max(1, int(args.poll_seconds)))
        time.sleep(max(0.1, args.poll_seconds))


if __name__ == "__main__":
    raise SystemExit(main())
