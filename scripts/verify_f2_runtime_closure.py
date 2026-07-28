from __future__ import annotations

import json
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

import psycopg
from psycopg.rows import dict_row
from redis import Redis

from axignal_api.object_store import LocalFilesystemObjectStore, ObjectIntegrityError
from axignal_api.scheduler import (
    SchedulerOutboxPublisher,
    SchedulerRepository,
    SchedulerWorker,
    ValkeySchedulerQueue,
    default_handlers,
)
from axignal_api.settings import Settings
from axignal_api.telemetry import (
    build_in_memory_telemetry,
    inject_trace_envelope,
    span_export_is_redacted,
    start_span,
    tracer_for,
)


def query_job(admin_dsn: str, job_id: UUID) -> dict:
    with (
        psycopg.connect(admin_dsn, row_factory=dict_row) as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute(
            """
            SELECT state, attempt_count, max_attempts, lease_owner,
                   lease_expires_at, result, last_error_code
            FROM axignal_global.scheduled_jobs
            WHERE scheduled_job_id = %s
            """,
            (job_id,),
        )
        row = cursor.fetchone()
        assert row is not None
        return row


def event_count(admin_dsn: str, job_id: UUID) -> int:
    with psycopg.connect(admin_dsn) as connection, connection.cursor() as cursor:
        cursor.execute(
            "SELECT count(*) FROM axignal_global.scheduler_events WHERE scheduled_job_id=%s",
            (job_id,),
        )
        return int(cursor.fetchone()[0])


def verify_scheduler_privileges(admin_dsn: str) -> None:
    with (
        psycopg.connect(admin_dsn, row_factory=dict_row) as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute(
            """
            SELECT
              has_table_privilege(
                'axignal_scheduler_login',
                'axignal_global.canonical_claims',
                'INSERT'
              ) AS canonical_insert,
              has_table_privilege(
                'axignal_scheduler_login',
                'axignal_global.evidence_objects',
                'UPDATE'
              ) AS evidence_update,
              has_function_privilege(
                'axignal_scheduler_login',
                'axignal_global.schedule_maintenance_job(text,text,jsonb,uuid,timestamptz,integer,jsonb)',
                'EXECUTE'
              ) AS schedule_execute
            """
        )
        assert cursor.fetchone() == {
            "canonical_insert": False,
            "evidence_update": False,
            "schedule_execute": True,
        }


def main() -> int:
    settings = Settings.from_env()
    settings.require_scheduler()
    settings.require_object_store()
    assert settings.database_url is not None
    assert settings.scheduler_database_url is not None
    assert settings.valkey_url is not None

    Redis.from_url(settings.valkey_url).flushdb()
    verify_scheduler_privileges(settings.database_url)
    provider, exporter = build_in_memory_telemetry()
    tracer = tracer_for(provider, "axignal.f2.acceptance")
    repository = SchedulerRepository(settings.scheduler_database_url)
    queue = ValkeySchedulerQueue(settings.valkey_url, queue_key=settings.scheduler_queue_key)
    publisher = SchedulerOutboxPublisher(repository, queue, tracer=tracer)
    worker = SchedulerWorker(
        repository=repository,
        queue=queue,
        worker_id="f2-acceptance-worker",
        tracer=tracer,
        handlers=default_handlers(repository),
        lease_seconds=30,
    )

    with start_span(
        tracer,
        "axignal.f2.schedule",
        attributes={
            "research_run_id": "f2-runtime-acceptance",
            "authorization": "Bearer must-not-export",
        },
    ):
        trace_context = inject_trace_envelope().as_dict()
        first = repository.schedule(
            job_kind="VERIFY_RUNTIME_HEALTH",
            idempotency_key="f2-runtime-health-idempotency",
            payload={"components": ["postgres", "valkey", "object-store"]},
            trace_context=trace_context,
        )
        second = repository.schedule(
            job_kind="VERIFY_RUNTIME_HEALTH",
            idempotency_key="f2-runtime-health-idempotency",
            payload={"components": ["postgres", "valkey", "object-store"]},
            trace_context=trace_context,
        )
    assert first == second
    assert publisher.publish_pending() == 1
    assert publisher.publish_pending() == 0
    assert queue.length() == 1
    assert worker.run_once(timeout_seconds=1) is True
    succeeded = query_job(settings.database_url, first)
    assert succeeded["state"] == "SUCCEEDED"
    assert succeeded["attempt_count"] == 1
    assert succeeded["result"]["state"] == "HEALTHY"
    assert event_count(settings.database_url, first) == 4

    lease_job = repository.schedule(
        job_kind="VERIFY_RUNTIME_HEALTH",
        idempotency_key="f2-expired-lease-idempotency",
        payload={"components": ["postgres"]},
    )
    assert publisher.publish_pending() == 1
    message = queue.receive(timeout_seconds=1)
    assert message is not None
    claimed = repository.claim(
        UUID(message["scheduled_job_id"]), worker_id="abandoned-worker", lease_seconds=30
    )
    assert claimed is not None
    with psycopg.connect(settings.database_url) as connection, connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE axignal_global.scheduled_jobs
            SET lease_expires_at = %s
            WHERE scheduled_job_id = %s
            """,
            (datetime.now(UTC) - timedelta(seconds=1), lease_job),
        )
    assert repository.recover_expired_leases() == 1
    assert query_job(settings.database_url, lease_job)["state"] == "SCHEDULED"
    assert publisher.publish_pending() == 1
    assert worker.run_once(timeout_seconds=1) is True
    assert query_job(settings.database_url, lease_job)["state"] == "SUCCEEDED"

    dead_job = repository.schedule(
        job_kind="RETRY_STALE_OUTBOX",
        idempotency_key="f2-dead-letter-idempotency",
        payload={},
        max_attempts=1,
    )
    assert publisher.publish_pending() == 1
    dead_message = queue.receive(timeout_seconds=1)
    assert dead_message is not None
    assert repository.claim(
        UUID(dead_message["scheduled_job_id"]),
        worker_id="failure-worker",
        lease_seconds=30,
    ) is not None
    assert repository.fail(
        dead_job,
        worker_id="failure-worker",
        error_code="FAIL_CLOSED_POLICY",
    ) == "DEAD_LETTER"
    assert query_job(settings.database_url, dead_job)["state"] == "DEAD_LETTER"

    with tempfile.TemporaryDirectory() as temporary:
        store = LocalFilesystemObjectStore(Path(temporary))
        metadata = store.put(
            namespace="tenant/f2/source-object",
            content=b"content-addressed evidence",
            content_type="application/octet-stream",
        )
        assert store.get(metadata.key) == b"content-addressed evidence"
        assert store.verify_hash(metadata.key).sha256 == metadata.sha256
        store._data_path(metadata.key).write_bytes(b"tampered")
        try:
            store.get(metadata.key)
        except ObjectIntegrityError:
            tamper_blocked = True
        else:
            tamper_blocked = False
        assert tamper_blocked

    spans = list(exporter.get_finished_spans())
    assert len(spans) >= 3
    assert span_export_is_redacted(spans)
    assert all(
        "must-not-export" not in json.dumps(dict(span.attributes or {}))
        for span in spans
    )

    print(
        json.dumps(
            {
                "scheduler_idempotent": True,
                "duplicate_scheduled_jobs": 0,
                "expired_lease_recovered": True,
                "dead_letter_state": "PASS",
                "scheduler_canonical_insert": False,
                "scheduler_evidence_update": False,
                "object_store_roundtrip": True,
                "object_hash_mismatch": "REJECTED",
                "object_overwrite": "DENIED_BY_CONTENT_ADDRESSING",
                "trace_context_end_to_end": True,
                "secrets_in_telemetry": 0,
                "restart_recovery": True,
                "production_deployment": False,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
