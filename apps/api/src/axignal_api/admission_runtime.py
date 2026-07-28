from __future__ import annotations

import argparse
import logging
import time

from axignal_api.admission_queue import AdmissionReviewJob, ValkeyAdmissionQueue
from axignal_api.admission_repository import (
    AdmissionIntegrityError,
    AdmissionPolicyError,
    AdmissionRepository,
    AdmissionRuntimeError,
)
from axignal_api.settings import Settings

LOGGER = logging.getLogger("axignal.deterministic-admission-runtime")


class DeterministicAdmissionRuntime:
    def __init__(
        self,
        *,
        repository: AdmissionRepository,
        queue: ValkeyAdmissionQueue,
    ) -> None:
        self.repository = repository
        self.queue = queue

    def run_once(self, *, timeout_seconds: int = 1) -> bool:
        job = self.queue.dequeue(timeout_seconds=timeout_seconds)
        if job is None:
            return False
        self.process(job)
        return True

    def process(self, job: AdmissionReviewJob) -> None:
        try:
            result = self.repository.decide(job)
            LOGGER.info(
                "Admission handoff %s decided: %s",
                job.admission_handoff_id,
                result.as_payload(),
            )
        except AdmissionIntegrityError as exc:
            LOGGER.exception("Admission handoff %s quarantined", job.admission_handoff_id)
            self.repository.record_failure(
                job=job,
                error_code="ADMISSION_INTEGRITY_QUARANTINE",
                error_detail=str(exc),
                quarantined=True,
            )
        except (AdmissionPolicyError, AdmissionRuntimeError, LookupError, ValueError) as exc:
            LOGGER.exception("Admission handoff %s failed closed", job.admission_handoff_id)
            self.repository.record_failure(
                job=job,
                error_code=exc.__class__.__name__.upper(),
                error_detail=str(exc),
                quarantined=False,
            )


def build_runtime(settings: Settings) -> DeterministicAdmissionRuntime:
    settings.require_admission_runtime()
    assert settings.admission_database_url is not None
    assert settings.valkey_url is not None
    repository = AdmissionRepository(admission_dsn=settings.admission_database_url)
    queue = ValkeyAdmissionQueue(
        settings.valkey_url,
        queue_key=settings.admission_queue_key,
    )
    return DeterministicAdmissionRuntime(repository=repository, queue=queue)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="AXIGNAL independent deterministic admission runtime"
    )
    parser.add_argument("--once", action="store_true", help="Process at most one queued job")
    parser.add_argument("--poll-seconds", type=float, default=2.0)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    runtime = build_runtime(Settings.from_env())
    if args.once:
        runtime.run_once(timeout_seconds=1)
        return 0

    while True:
        runtime.run_once(timeout_seconds=max(1, int(args.poll_seconds)))
        time.sleep(max(0.1, args.poll_seconds))


if __name__ == "__main__":
    raise SystemExit(main())
