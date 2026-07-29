from __future__ import annotations

import argparse
import logging
import time

from axignal_api.connectors.ted_xml import TEDXMLConnector, TEDXMLRetrievalError
from axignal_api.procurement_persistent_types import ProcurementPersistencePolicyError
from axignal_api.procurement_queue import (
    ProcurementAdmissionJob,
    ProcurementAdmissionOutboxPublisher,
    ValkeyProcurementAdmissionQueue,
)
from axignal_api.procurement_repository import (
    ProcurementAdmissionRepository,
    ProcurementIntegrityError,
)
from axignal_api.settings import Settings

LOGGER = logging.getLogger("axignal.ted-admission-runtime")


class ProcurementAdmissionRuntime:
    def __init__(
        self,
        *,
        repository: ProcurementAdmissionRepository,
        queue: ValkeyProcurementAdmissionQueue,
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

    def process(self, job: ProcurementAdmissionJob) -> None:
        try:
            result = self.repository.decide(job=job, connector=self.connector)
            LOGGER.info(
                "TED handoff %s decided with %s canonical claims",
                job.admission_handoff_id,
                len(result.canonical_claim_ids),
            )
        except (
            TEDXMLRetrievalError,
            ProcurementPersistencePolicyError,
            ProcurementIntegrityError,
            LookupError,
            RuntimeError,
            ValueError,
        ) as exc:
            LOGGER.exception("TED admission failed closed for %s", job.admission_handoff_id)
            self.repository.fail(job, exc)


def build_runtime(
    settings: Settings,
) -> tuple[ProcurementAdmissionOutboxPublisher, ProcurementAdmissionRuntime]:
    settings.require_ted_admission_runtime()
    assert settings.ted_admission_database_url is not None
    assert settings.valkey_url is not None
    repository = ProcurementAdmissionRepository(settings.ted_admission_database_url)
    queue = ValkeyProcurementAdmissionQueue(
        settings.valkey_url,
        queue_key=settings.ted_admission_queue_key,
    )
    connector = TEDXMLConnector(
        live_enabled=settings.ted_live_sources_enabled,
        fixture_manifest_path=settings.ted_fixture_manifest_path,
    )
    return ProcurementAdmissionOutboxPublisher(repository, queue), ProcurementAdmissionRuntime(
        repository=repository,
        queue=queue,
        connector=connector,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="AXIGNAL isolated TED admission runtime")
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
