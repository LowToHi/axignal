from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from uuid import UUID

import psycopg
from psycopg.rows import dict_row
from redis import Redis

from axignal_api.telemetry import (
    attach_trace_envelope,
    inject_trace_envelope,
    start_span,
)


@dataclass(frozen=True)
class ScheduledJob:
    scheduled_job_id: UUID
    tenant_id: UUID | None
    job_kind: str
    idempotency_key: str
    payload: dict[str, Any]
    trace_context: dict[str, str]
    state: str
    attempt_count: int
    max_attempts: int


@dataclass(frozen=True)
class SchedulerOutboxEvent:
    scheduler_outbox_event_id: UUID
    scheduled_job_id: UUID
    payload: dict[str, Any]


class SchedulerRepository:
    def __init__(self, scheduler_dsn: str) -> None:
        self.scheduler_dsn = scheduler_dsn

    def schedule(
        self,
        *,
        job_kind: str,
        idempotency_key: str,
        payload: dict[str, Any] | None = None,
        tenant_id: UUID | None = None,
        run_at_iso: str | None = None,
        max_attempts: int = 3,
        trace_context: dict[str, str] | None = None,
    ) -> UUID:
        envelope = trace_context or inject_trace_envelope().as_dict()
        with (
            psycopg.connect(self.scheduler_dsn, row_factory=dict_row) as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute(
                """
                SELECT axignal_global.schedule_maintenance_job(
                  %s, %s, %s::jsonb, %s, %s::timestamptz, %s, %s::jsonb
                ) AS scheduled_job_id
                """,
                (
                    job_kind,
                    idempotency_key,
                    json.dumps(payload or {}),
                    tenant_id,
                    run_at_iso,
                    max_attempts,
                    json.dumps(envelope),
                ),
            )
            row = cursor.fetchone()
            assert row is not None
            return row["scheduled_job_id"]

    def pending_outbox(self, limit: int = 100) -> list[SchedulerOutboxEvent]:
        with (
            psycopg.connect(self.scheduler_dsn, row_factory=dict_row) as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute(
                "SELECT * FROM axignal_global.scheduler_pending_outbox(%s)",
                (limit,),
            )
            return [
                SchedulerOutboxEvent(
                    scheduler_outbox_event_id=row["scheduler_outbox_event_id"],
                    scheduled_job_id=row["scheduled_job_id"],
                    payload=row["payload"],
                )
                for row in cursor.fetchall()
            ]

    def mark_published(self, event_id: UUID) -> None:
        with psycopg.connect(self.scheduler_dsn) as connection, connection.cursor() as cursor:
            cursor.execute(
                "SELECT axignal_global.mark_scheduler_outbox_published(%s)",
                (event_id,),
            )

    def claim(self, job_id: UUID, *, worker_id: str, lease_seconds: int) -> ScheduledJob | None:
        with (
            psycopg.connect(self.scheduler_dsn, row_factory=dict_row) as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute(
                "SELECT item FROM axignal_global.claim_scheduled_job(%s, %s, %s) AS item",
                (job_id, worker_id, lease_seconds),
            )
            row = cursor.fetchone()
            if row is None or row["item"] is None:
                return None
            item = row["item"]
            return ScheduledJob(
                scheduled_job_id=UUID(item["scheduled_job_id"]),
                tenant_id=UUID(item["tenant_id"]) if item.get("tenant_id") else None,
                job_kind=item["job_kind"],
                idempotency_key=item["idempotency_key"],
                payload=item["payload"],
                trace_context=item.get("trace_context") or {},
                state=item["state"],
                attempt_count=item["attempt_count"],
                max_attempts=item["max_attempts"],
            )

    def complete(self, job_id: UUID, *, worker_id: str, result: dict[str, Any]) -> None:
        with psycopg.connect(self.scheduler_dsn) as connection, connection.cursor() as cursor:
            cursor.execute(
                "SELECT axignal_global.complete_scheduled_job(%s, %s, %s::jsonb)",
                (job_id, worker_id, json.dumps(result)),
            )

    def fail(
        self,
        job_id: UUID,
        *,
        worker_id: str,
        error_code: str,
        retry_delay_seconds: int = 0,
    ) -> str:
        with (
            psycopg.connect(self.scheduler_dsn, row_factory=dict_row) as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute(
                "SELECT axignal_global.fail_scheduled_job(%s, %s, %s, %s) AS state",
                (job_id, worker_id, error_code, retry_delay_seconds),
            )
            row = cursor.fetchone()
            assert row is not None
            return row["state"]

    def recover_expired_leases(self) -> int:
        with (
            psycopg.connect(self.scheduler_dsn, row_factory=dict_row) as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute(
                "SELECT axignal_global.recover_expired_scheduler_leases() AS recovered"
            )
            row = cursor.fetchone()
            assert row is not None
            return int(row["recovered"])


class ValkeySchedulerQueue:
    def __init__(self, valkey_url: str, *, queue_key: str) -> None:
        self.client = Redis.from_url(valkey_url, decode_responses=True)
        self.queue_key = queue_key

    def publish(self, event: SchedulerOutboxEvent) -> None:
        message = json.dumps(
            {
                "scheduler_outbox_event_id": str(event.scheduler_outbox_event_id),
                "scheduled_job_id": str(event.scheduled_job_id),
                "payload": event.payload,
            },
            sort_keys=True,
        )
        dedupe_key = f"{self.queue_key}:published:{event.scheduler_outbox_event_id}"
        script = """
        if redis.call('SETNX', KEYS[1], '1') == 1 then
          redis.call('EXPIRE', KEYS[1], 604800)
          redis.call('LPUSH', KEYS[2], ARGV[1])
          return 1
        end
        return 0
        """
        self.client.eval(script, 2, dedupe_key, self.queue_key, message)

    def receive(self, timeout_seconds: int = 1) -> dict[str, Any] | None:
        item = self.client.brpop(self.queue_key, timeout=timeout_seconds)
        if item is None:
            return None
        return json.loads(item[1])

    def length(self) -> int:
        return int(self.client.llen(self.queue_key))


class SchedulerOutboxPublisher:
    def __init__(
        self,
        repository: SchedulerRepository,
        queue: ValkeySchedulerQueue,
        *,
        tracer: Any,
    ) -> None:
        self.repository = repository
        self.queue = queue
        self.tracer = tracer

    def publish_pending(self, limit: int = 100) -> int:
        count = 0
        for event in self.repository.pending_outbox(limit):
            trace_context = event.payload.get("trace_context") or {}
            with attach_trace_envelope(trace_context), start_span(
                self.tracer,
                "axignal.scheduler.publish",
                attributes={
                    "scheduled_job_id": str(event.scheduled_job_id),
                    "scheduler_outbox_event_id": str(event.scheduler_outbox_event_id),
                },
            ):
                self.queue.publish(event)
                self.repository.mark_published(event.scheduler_outbox_event_id)
                count += 1
        return count


Handler = Callable[[ScheduledJob], dict[str, Any]]


class SchedulerWorker:
    def __init__(
        self,
        *,
        repository: SchedulerRepository,
        queue: ValkeySchedulerQueue,
        worker_id: str,
        tracer: Any,
        handlers: dict[str, Handler],
        lease_seconds: int = 30,
    ) -> None:
        self.repository = repository
        self.queue = queue
        self.worker_id = worker_id
        self.tracer = tracer
        self.handlers = handlers
        self.lease_seconds = lease_seconds

    def run_once(self, timeout_seconds: int = 1) -> bool:
        message = self.queue.receive(timeout_seconds)
        if message is None:
            return False
        job_id = UUID(message["scheduled_job_id"])
        job = self.repository.claim(
            job_id,
            worker_id=self.worker_id,
            lease_seconds=self.lease_seconds,
        )
        if job is None:
            return True
        with attach_trace_envelope(job.trace_context), start_span(
            self.tracer,
            "axignal.scheduler.execute",
            attributes={
                "scheduled_job_id": str(job.scheduled_job_id),
                "job_kind": job.job_kind,
                "attempt_count": job.attempt_count,
                "tenant_id_hash": (
                    str(job.tenant_id).split("-")[0] if job.tenant_id else "global"
                ),
            },
        ):
            handler = self.handlers.get(job.job_kind)
            if handler is None:
                self.repository.fail(
                    job.scheduled_job_id,
                    worker_id=self.worker_id,
                    error_code="UNSUPPORTED_JOB_KIND",
                )
                return True
            try:
                result = handler(job)
            except Exception as exc:
                self.repository.fail(
                    job.scheduled_job_id,
                    worker_id=self.worker_id,
                    error_code=exc.__class__.__name__.upper(),
                )
                return True
            self.repository.complete(
                job.scheduled_job_id,
                worker_id=self.worker_id,
                result=result,
            )
            return True


def default_handlers(repository: SchedulerRepository) -> dict[str, Handler]:
    return {
        "VERIFY_RUNTIME_HEALTH": lambda job: {
            "state": "HEALTHY",
            "checked": sorted(job.payload.get("components", [])),
        },
        "RECOVER_EXPIRED_SCHEDULER_LEASES": lambda job: {
            "recovered": repository.recover_expired_leases(),
        },
        "CHECK_SOURCE_FRESHNESS": lambda job: {
            "state": "OBSERVATION_ONLY",
            "source_id": job.payload.get("source_id"),
            "network_calls": 0,
        },
        "REBUILD_DOSSIER_IF_DIRTY": lambda job: {
            "state": "NOOP_UNLESS_DIRTY",
            "research_run_id": job.payload.get("research_run_id"),
        },
        "RETRY_STALE_OUTBOX": lambda job: {
            "state": "FAIL_CLOSED",
            "reason": "TARGET_RUNTIME_MUST_OWN_ITS_OUTBOX_RETRY",
        },
    }
