from __future__ import annotations

from dataclasses import dataclass
import json
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
    def from_payload(cls, payload: dict[str, Any]) -> "ResearchJob":
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
