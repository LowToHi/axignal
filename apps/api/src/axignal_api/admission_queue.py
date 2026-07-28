from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from redis import Redis
from redis.exceptions import RedisError

POLICY_VERSION = "document-observed-fact@0.1.0"


@dataclass(frozen=True)
class AdmissionReviewJob:
    admission_handoff_id: UUID
    research_run_id: UUID
    tenant_id: UUID
    expected_package_hash: str
    policy_version: str = POLICY_VERSION

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> AdmissionReviewJob:
        if payload.get("schema_version") != 1:
            raise ValueError("Unsupported admission job schema version")
        if payload.get("job_kind") != "ADMISSION_REVIEW":
            raise ValueError("Unexpected admission job kind")
        package_hash = str(payload["expected_package_hash"])
        if not package_hash.startswith("sha256:") or len(package_hash) != 71:
            raise ValueError("Admission job package hash is invalid")
        policy_version = str(payload.get("policy_version", ""))
        if policy_version != POLICY_VERSION:
            raise ValueError("Admission policy version is not supported")
        return cls(
            admission_handoff_id=UUID(str(payload["admission_handoff_id"])),
            research_run_id=UUID(str(payload["research_run_id"])),
            tenant_id=UUID(str(payload["tenant_id"])),
            expected_package_hash=package_hash,
            policy_version=policy_version,
        )

    def as_payload(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "job_kind": "ADMISSION_REVIEW",
            "admission_handoff_id": str(self.admission_handoff_id),
            "research_run_id": str(self.research_run_id),
            "tenant_id": str(self.tenant_id),
            "expected_package_hash": self.expected_package_hash,
            "policy_version": self.policy_version,
        }


class ValkeyAdmissionQueue:
    def __init__(self, url: str, *, queue_key: str) -> None:
        self.client = Redis.from_url(url, decode_responses=True)
        self.queue_key = queue_key

    def enqueue(self, job: AdmissionReviewJob) -> None:
        encoded = json.dumps(job.as_payload(), sort_keys=True, separators=(",", ":"))
        self.client.rpush(self.queue_key, encoded)

    def dequeue(self, *, timeout_seconds: int = 1) -> AdmissionReviewJob | None:
        result = self.client.blpop(self.queue_key, timeout=timeout_seconds)
        if result is None:
            return None
        _, encoded = result
        payload = json.loads(encoded)
        if not isinstance(payload, dict):
            raise ValueError("Admission queue payload must be an object")
        return AdmissionReviewJob.from_payload(payload)

    def ping(self) -> bool:
        return bool(self.client.ping())

    def purge_for_test(self) -> None:
        self.client.delete(self.queue_key)


@dataclass(frozen=True)
class AdmissionOutboxEvent:
    event_id: UUID
    aggregate_id: UUID
    event_type: str
    payload: dict[str, Any]
    attempts: int


class AdmissionOutboxPublisher:
    def __init__(self, repository: Any, queue: ValkeyAdmissionQueue) -> None:
        self.repository = repository
        self.queue = queue

    def publish_pending(self, *, limit: int = 10) -> int:
        published = 0
        for event in self.repository.pending_admission_outbox(limit=limit):
            try:
                if event.event_type != "admission.handoff.requested":
                    raise ValueError(f"Unsupported admission outbox event {event.event_type}")
                self.queue.enqueue(AdmissionReviewJob.from_payload(event.payload))
            except (RedisError, ValueError, KeyError, TypeError) as exc:
                self.repository.mark_admission_outbox_failed(
                    event.event_id,
                    f"{exc.__class__.__name__}: {exc}",
                )
                continue
            self.repository.mark_admission_outbox_published(event.event_id)
            published += 1
        return published
