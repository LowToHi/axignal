from __future__ import annotations

import json
import os
import socket
from datetime import UTC, datetime

from axignal_api.retention_config import RetentionSettings
from axignal_api.retention_repository import RetentionRepository


def run_once(*, now: datetime | None = None) -> dict[str, object]:
    settings = RetentionSettings.from_env()
    settings.require_purge_worker()
    assert settings.database_url is not None
    repository = RetentionRepository(settings.database_url)
    current = now or datetime.now(UTC)
    worker_id = f"retention-{socket.gethostname()}-{os.getpid()}"
    queued = repository.queue_due(now=current)
    claim = repository.claim(
        worker_id=worker_id,
        lease_seconds=settings.purge_lease_seconds,
        now=current,
    )
    if claim is None:
        return {
            "schema": "axignal.retention-worker-run.v0.1",
            "status": "IDLE",
            "queued": queued,
            "purged": 0,
        }

    tombstone = repository.purge(
        deletion_id=claim["deletion_id"],
        worker_id=worker_id,
        now=current,
    )
    return {
        "schema": "axignal.retention-worker-run.v0.1",
        "status": "PURGED",
        "queued": queued,
        "purged": 1,
        "deletion_id": str(tombstone["deletion_id"]),
        "verification_digest": tombstone["verification_digest"],
    }


def main() -> int:
    print(json.dumps(run_once(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
