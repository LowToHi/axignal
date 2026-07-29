from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from redis import Redis
from redis.exceptions import RedisError

from axignal_api.connectors.ted_xml import SOURCE_ID, TEDXMLConnector
from axignal_api.procurement_persistent_types import POLICY_VERSION


@dataclass(frozen=True)
class ProcurementOutboxEvent:
    event_id: UUID
    aggregate_id: UUID
    event_type: str
    payload: dict[str, Any]
    attempts: int


@dataclass(frozen=True)
class ProcurementRetrievalJob:
    tenant_id: UUID
    research_run_id: UUID
    publication_numbers: tuple[str, ...]
    source_id: str = SOURCE_ID

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> ProcurementRetrievalJob:
        if payload.get("schema_version") != 1:
            raise ValueError("Unsupported procurement retrieval job schema")
        if payload.get("job_kind") != "PROCUREMENT_TED_RETRIEVAL":
            raise ValueError("Unexpected procurement retrieval job kind")
        source_id = str(payload.get("source_id", ""))
        if source_id != SOURCE_ID:
            raise ValueError("Unexpected procurement source")
        raw_numbers = payload.get("publication_numbers")
        if not isinstance(raw_numbers, list) or not 1 <= len(raw_numbers) <= 4:
            raise ValueError("Procurement retrieval job has an invalid notice count")
        numbers = tuple(str(item) for item in raw_numbers)
        if len(set(numbers)) != len(numbers):
            raise ValueError("Procurement retrieval job repeats publication numbers")
        for number in numbers:
            TEDXMLConnector.validate_publication_number(number)
        return cls(
            tenant_id=UUID(str(payload["tenant_id"])),
            research_run_id=UUID(str(payload["research_run_id"])),
            publication_numbers=numbers,
            source_id=source_id,
        )

    def as_payload(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "job_kind": "PROCUREMENT_TED_RETRIEVAL",
            "tenant_id": str(self.tenant_id),
            "research_run_id": str(self.research_run_id),
            "source_id": self.source_id,
            "publication_numbers": list(self.publication_numbers),
        }


@dataclass(frozen=True)
class ProcurementAdmissionJob:
    tenant_id: UUID
    research_run_id: UUID
    admission_handoff_id: UUID
    expected_package_hash: str
    publication_numbers: tuple[str, ...]
    policy_version: str = POLICY_VERSION

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> ProcurementAdmissionJob:
        if payload.get("schema_version") != 1:
            raise ValueError("Unsupported procurement admission job schema")
        if payload.get("job_kind") != "PROCUREMENT_ADMISSION_REVIEW":
            raise ValueError("Unexpected procurement admission job kind")
        package_hash = str(payload.get("expected_package_hash", ""))
        if not package_hash.startswith("sha256:") or len(package_hash) != 71:
            raise ValueError("Procurement admission package hash is invalid")
        policy_version = str(payload.get("policy_version", ""))
        if policy_version != POLICY_VERSION:
            raise ValueError("Procurement admission policy version is unsupported")
        raw_numbers = payload.get("publication_numbers")
        if not isinstance(raw_numbers, list) or not 1 <= len(raw_numbers) <= 4:
            raise ValueError("Procurement admission job has an invalid notice count")
        numbers = tuple(str(item) for item in raw_numbers)
        if len(set(numbers)) != len(numbers):
            raise ValueError("Procurement admission job repeats publication numbers")
        for number in numbers:
            TEDXMLConnector.validate_publication_number(number)
        return cls(
            tenant_id=UUID(str(payload["tenant_id"])),
            research_run_id=UUID(str(payload["research_run_id"])),
            admission_handoff_id=UUID(str(payload["admission_handoff_id"])),
            expected_package_hash=package_hash,
            publication_numbers=numbers,
            policy_version=policy_version,
        )

    def as_payload(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "job_kind": "PROCUREMENT_ADMISSION_REVIEW",
            "tenant_id": str(self.tenant_id),
            "research_run_id": str(self.research_run_id),
            "admission_handoff_id": str(self.admission_handoff_id),
            "expected_package_hash": self.expected_package_hash,
            "publication_numbers": list(self.publication_numbers),
            "policy_version": self.policy_version,
        }


class _ValkeyJSONQueue:
    def __init__(self, url: str, *, queue_key: str) -> None:
        self.client = Redis.from_url(url, decode_responses=True)
        self.queue_key = queue_key

    def _enqueue(self, payload: dict[str, Any]) -> None:
        self.client.rpush(
            self.queue_key,
            json.dumps(payload, sort_keys=True, separators=(",", ":")),
        )

    def _dequeue_payload(self, *, timeout_seconds: int) -> dict[str, Any] | None:
        result = self.client.blpop(self.queue_key, timeout=timeout_seconds)
        if result is None:
            return None
        _, encoded = result
        payload = json.loads(encoded)
        if not isinstance(payload, dict):
            raise ValueError("Procurement queue payload must be an object")
        return payload

    def ping(self) -> bool:
        return bool(self.client.ping())

    def purge_for_test(self) -> None:
        self.client.delete(self.queue_key)


class ValkeyProcurementRetrievalQueue(_ValkeyJSONQueue):
    def enqueue(self, job: ProcurementRetrievalJob) -> None:
        self._enqueue(job.as_payload())

    def dequeue(self, *, timeout_seconds: int = 1) -> ProcurementRetrievalJob | None:
        payload = self._dequeue_payload(timeout_seconds=timeout_seconds)
        return None if payload is None else ProcurementRetrievalJob.from_payload(payload)


class ValkeyProcurementAdmissionQueue(_ValkeyJSONQueue):
    def enqueue(self, job: ProcurementAdmissionJob) -> None:
        self._enqueue(job.as_payload())

    def dequeue(self, *, timeout_seconds: int = 1) -> ProcurementAdmissionJob | None:
        payload = self._dequeue_payload(timeout_seconds=timeout_seconds)
        return None if payload is None else ProcurementAdmissionJob.from_payload(payload)


class ProcurementRetrievalOutboxPublisher:
    def __init__(self, repository: Any, queue: ValkeyProcurementRetrievalQueue) -> None:
        self.repository = repository
        self.queue = queue

    def publish_pending(self, *, limit: int = 20) -> int:
        published = 0
        for event in self.repository.pending_retrieval_outbox(limit=limit):
            try:
                if event.event_type != "research.procurement.requested":
                    raise ValueError(
                        f"Unsupported procurement retrieval event {event.event_type}"
                    )
                self.queue.enqueue(ProcurementRetrievalJob.from_payload(event.payload))
            except (RedisError, ValueError, KeyError, TypeError) as exc:
                self.repository.mark_retrieval_outbox_failed(
                    event.event_id,
                    f"{exc.__class__.__name__}: {exc}",
                )
                continue
            self.repository.mark_retrieval_outbox_published(event.event_id)
            published += 1
        return published


class ProcurementAdmissionOutboxPublisher:
    def __init__(self, repository: Any, queue: ValkeyProcurementAdmissionQueue) -> None:
        self.repository = repository
        self.queue = queue

    def publish_pending(self, *, limit: int = 20) -> int:
        published = 0
        for event in self.repository.pending_admission_outbox(limit=limit):
            try:
                if event.event_type != "admission.procurement.requested":
                    raise ValueError(
                        f"Unsupported procurement admission event {event.event_type}"
                    )
                self.queue.enqueue(ProcurementAdmissionJob.from_payload(event.payload))
            except (RedisError, ValueError, KeyError, TypeError) as exc:
                self.repository.mark_admission_outbox_failed(
                    event.event_id,
                    f"{exc.__class__.__name__}: {exc}",
                )
                continue
            self.repository.mark_admission_outbox_published(event.event_id)
            published += 1
        return published
