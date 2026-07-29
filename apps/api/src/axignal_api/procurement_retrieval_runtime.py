from __future__ import annotations

import argparse
import logging
import time

from axignal_api.connectors.ted_xml import TEDXMLConnector, TEDXMLRetrievalError
from axignal_api.procurement_persistent_types import (
    ProcurementPersistencePolicyError,
    sanitise_retrieved_lifecycle,
)
from axignal_api.procurement_queue import (
    ProcurementRetrievalJob,
    ProcurementRetrievalOutboxPublisher,
    ValkeyProcurementRetrievalQueue,
)
from axignal_api.procurement_repository import (
    ProcurementIntegrityError,
    ProcurementRetrievalRepository,
)
from axignal_api.settings import Settings

LOGGER = logging.getLogger("axignal.ted-retrieval-worker")


class ProcurementRetrievalRuntime:
    def __init__(
        self,
        *,
        repository: ProcurementRetrievalRepository,
        queue: ValkeyProcurementRetrievalQueue,
        connector: TEDXMLConnector,
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

    def process(self, job: ProcurementRetrievalJob) -> None:
        run = self.repository.load_run(job)
        if run is None:
            LOGGER.warning("Ignoring absent TED ResearchRun %s", job.research_run_id)
            return
        if run["state"] in {"COMPLETED", "HANDOFF_PENDING", "ADMISSION_REVIEWING"}:
            LOGGER.info("TED ResearchRun %s is already durable", job.research_run_id)
            return
        source = self.repository.load_source()
        if source is None:
            self.repository.fail(job, ProcurementIntegrityError("TED source is absent"))
            return
        try:
            self.repository.transition(job, "RETRIEVING")
            retrieved = tuple(self.connector.fetch(item) for item in job.publication_numbers)
            self.repository.transition(job, "DOCUMENT_PARSING")
            lifecycle = sanitise_retrieved_lifecycle(retrieved)
            self.repository.transition(job, "EVIDENCE_BINDING")
            result = self.repository.persist_lifecycle(
                job=job,
                lifecycle=lifecycle,
                source=source,
            )
            LOGGER.info(
                "TED ResearchRun %s produced handoff %s with %s non-personal claims",
                job.research_run_id,
                result.admission_handoff_id,
                len(result.candidate_claim_ids),
            )
        except (
            TEDXMLRetrievalError,
            ProcurementPersistencePolicyError,
            ProcurementIntegrityError,
            LookupError,
            RuntimeError,
            ValueError,
        ) as exc:
            LOGGER.exception("TED retrieval failed closed for %s", job.research_run_id)
            self.repository.fail(job, exc)


def build_runtime(
    settings: Settings,
) -> tuple[ProcurementRetrievalOutboxPublisher, ProcurementRetrievalRuntime]:
    settings.require_ted_retrieval_runtime()
    assert settings.ted_worker_database_url is not None
    assert settings.valkey_url is not None
    repository = ProcurementRetrievalRepository(settings.ted_worker_database_url)
    queue = ValkeyProcurementRetrievalQueue(
        settings.valkey_url,
        queue_key=settings.ted_retrieval_queue_key,
    )
    connector = TEDXMLConnector(
        live_enabled=settings.ted_live_sources_enabled,
        fixture_manifest_path=settings.ted_fixture_manifest_path,
    )
    return ProcurementRetrievalOutboxPublisher(repository, queue), ProcurementRetrievalRuntime(
        repository=repository,
        queue=queue,
        connector=connector,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="AXIGNAL isolated TED retrieval runtime")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--poll-seconds", type=float, default=2.0)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    publisher, runtime = build_runtime(Settings.from_env())
    if args.once:
        publisher.publish_pending(limit=20)
        runtime.run_once(timeout_seconds=1)
        return 0
    while True:
        publisher.publish_pending(limit=20)
        runtime.run_once(timeout_seconds=max(1, int(args.poll_seconds)))
        time.sleep(max(0.1, args.poll_seconds))


if __name__ == "__main__":
    raise SystemExit(main())
