from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from redis import Redis
from redis.exceptions import RedisError

from axignal_api.repository import OutboxEvent, ResearchRepository


@dataclass(frozen=True)
class ResearchJob:
    tenant_id: UUID
    research_run_id: UUID
    source_id: str

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> ResearchJob:
        if payload.get("schema_version") != 1:
            raise ValueError("Unsupported research job schema version")
        return cls(
            tenant_id=UUID(str(payload["tenant_id"])),
            research_run_id=UUID(str(payload["research_run_id"])),
            source_id=str(payload["source_id"]),
        )

    def as_payload(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "tenant_id": str(self.tenant_id),
            "research_run_id": str(self.research_run_id),
            "source_id": self.source_id,
        }


class ValkeyResearchQueue:
    def __init__(self, url: str, *, queue_key: str) -> None:
        self.client = Redis.from_url(url, decode_responses=True)
        self.queue_key = queue_key
        self.event_stream_key = "axignal:events:v1"
        self.lease_key = f"{queue_key}:inflight"

    def enqueue(self, job: ResearchJob) -> None:
        self.client.rpush(
            self.queue_key,
            json.dumps(job.as_payload(), sort_keys=True, separators=(",", ":")),
        )

    def publish_event(self, event: OutboxEvent) -> None:
        self.client.xadd(
            self.event_stream_key,
            {
                "event_type": event.event_type,
                "aggregate_id": str(event.aggregate_id),
                "payload": json.dumps(event.payload, sort_keys=True, separators=(",", ":")),
            },
            maxlen=10_000,
            approximate=True,
        )

    def dequeue(self, *, timeout_seconds: int = 1) -> ResearchJob | None:
        result = self.client.blpop(self.queue_key, timeout=timeout_seconds)
        if result is None:
            return None
        _, encoded = result
        payload = json.loads(encoded)
        if not isinstance(payload, dict):
            raise ValueError("Research queue payload must be an object")
        return ResearchJob.from_payload(payload)

    def claim(
        self,
        *,
        timeout_seconds: int = 1,
        worker_id: str,
        lease_seconds: int,
    ) -> ResearchJob | None:
        """Atomically take one job and register a renewable lease for it.

        The job remains in the lease hash until the worker completes it, fails
        it or the lease expires; ``recover_expired_leases`` re-enqueues jobs
        whose lease lapsed without a terminal transition (worker crash).
        """
        job = self.dequeue(timeout_seconds=timeout_seconds)
        if job is None:
            return None
        payload = json.dumps(job.as_payload(), sort_keys=True, separators=(",", ":"))
        lease = json.dumps(
            {
                "worker_id": worker_id,
                "lease_expires_at": time.time() + lease_seconds,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        self.client.hset(self.lease_key, payload, lease)
        self.client.expire(self.lease_key, max(lease_seconds * 3, 60))
        return job

    def renew_lease(
        self,
        job: ResearchJob,
        *,
        worker_id: str,
        lease_seconds: int,
    ) -> bool:
        """Heartbeat: extend the lease only while this worker still owns it."""
        payload = json.dumps(job.as_payload(), sort_keys=True, separators=(",", ":"))
        current = self.client.hget(self.lease_key, payload)
        if current is None:
            return False
        try:
            holder = json.loads(current)
        except ValueError:
            return False
        if holder.get("worker_id") != worker_id:
            return False
        renewed = json.dumps(
            {
                "worker_id": worker_id,
                "lease_expires_at": time.time() + lease_seconds,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        self.client.hset(self.lease_key, payload, renewed)
        self.client.expire(self.lease_key, max(lease_seconds * 3, 60))
        return True

    def release(self, job: ResearchJob, *, worker_id: str) -> bool:
        """Terminal release: drop the lease without re-enqueueing."""
        payload = json.dumps(job.as_payload(), sort_keys=True, separators=(",", ":"))
        current = self.client.hget(self.lease_key, payload)
        if current is None:
            return False
        try:
            holder = json.loads(current)
        except ValueError:
            holder = {}
        if holder.get("worker_id") != worker_id:
            return False
        return bool(self.client.hdel(self.lease_key, payload))

    def recover_expired_leases(self) -> int:
        """Re-enqueue jobs whose lease expired without a terminal transition.

        Returns the number of jobs recovered. Idempotent: the lease entry is
        removed atomically before re-enqueueing, so a concurrent worker cannot
        double-deliver the same job.
        """
        recovered = 0
        now = time.time()
        for payload, encoded in self.client.hgetall(self.lease_key).items():
            try:
                lease = json.loads(encoded)
            except ValueError:
                continue
            if lease.get("lease_expires_at", float("inf")) > now:
                continue
            if not self.client.hdel(self.lease_key, payload):
                continue
            self.client.rpush(self.queue_key, payload)
            recovered += 1
        return recovered

    def ping(self) -> bool:
        return bool(self.client.ping())

    def purge_for_test(self) -> None:
        self.client.delete(self.queue_key)


class OutboxPublisher:
    def __init__(self, repository: ResearchRepository, queue: ValkeyResearchQueue) -> None:
        self.repository = repository
        self.queue = queue

    def publish_pending(self, *, limit: int = 10) -> int:
        published = 0
        for event in self.repository.pending_outbox(limit=limit):
            try:
                if event.event_type == "research.run.requested":
                    self.queue.enqueue(ResearchJob.from_payload(event.payload))
                else:
                    self.queue.publish_event(event)
            except (RedisError, ValueError, KeyError, TypeError) as exc:
                self.repository.mark_outbox_failed(
                    event.outbox_event_id,
                    f"{exc.__class__.__name__}: {exc}",
                )
                continue
            self.repository.mark_outbox_published(event.outbox_event_id)
            published += 1
        return published
