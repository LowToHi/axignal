from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from redis import Redis
from redis.exceptions import RedisError


@dataclass(frozen=True)
class DocumentProposalBudget:
    max_documents: int = 1
    max_model_calls: int = 1
    max_input_tokens: int = 12_000
    max_output_tokens: int = 2_500

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> DocumentProposalBudget:
        budget = cls(
            max_documents=int(payload.get("max_documents", 1)),
            max_model_calls=int(payload.get("max_model_calls", 1)),
            max_input_tokens=int(payload.get("max_input_tokens", 12_000)),
            max_output_tokens=int(payload.get("max_output_tokens", 2_500)),
        )
        if budget.max_documents != 1 or budget.max_model_calls != 1:
            raise ValueError("Document proposal v0.1 permits exactly one document and model call")
        if budget.max_input_tokens <= 0 or budget.max_output_tokens <= 0:
            raise ValueError("Document proposal token budgets must be positive")
        return budget

    def as_payload(self) -> dict[str, int]:
        return {
            "max_documents": self.max_documents,
            "max_model_calls": self.max_model_calls,
            "max_input_tokens": self.max_input_tokens,
            "max_output_tokens": self.max_output_tokens,
        }


@dataclass(frozen=True)
class DocumentProposalJob:
    tenant_id: UUID
    research_run_id: UUID
    source_id: str
    document_id: str
    pipeline_version: str
    budget: DocumentProposalBudget

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> DocumentProposalJob:
        if payload.get("schema_version") != 2:
            raise ValueError("Unsupported document proposal job schema version")
        if payload.get("job_kind") != "DOCUMENT_PROPOSAL":
            raise ValueError("Unexpected proposal job kind")
        source_id = str(payload["source_id"])
        document_id = str(payload["document_id"])
        pipeline_version = str(payload["pipeline_version"])
        if not source_id or not document_id.startswith("doc_"):
            raise ValueError("Document proposal job source or document identity is invalid")
        return cls(
            tenant_id=UUID(str(payload["tenant_id"])),
            research_run_id=UUID(str(payload["research_run_id"])),
            source_id=source_id,
            document_id=document_id,
            pipeline_version=pipeline_version,
            budget=DocumentProposalBudget.from_payload(dict(payload.get("budget", {}))),
        )

    def as_payload(self) -> dict[str, Any]:
        return {
            "schema_version": 2,
            "job_kind": "DOCUMENT_PROPOSAL",
            "tenant_id": str(self.tenant_id),
            "research_run_id": str(self.research_run_id),
            "source_id": self.source_id,
            "document_id": self.document_id,
            "pipeline_version": self.pipeline_version,
            "budget": self.budget.as_payload(),
        }


class ValkeyDocumentProposalQueue:
    def __init__(self, url: str, *, queue_key: str) -> None:
        self.client = Redis.from_url(url, decode_responses=True)
        self.queue_key = queue_key

    def enqueue(self, job: DocumentProposalJob) -> None:
        encoded = json.dumps(job.as_payload(), sort_keys=True, separators=(",", ":"))
        self.client.rpush(self.queue_key, encoded)

    def dequeue(self, *, timeout_seconds: int = 1) -> DocumentProposalJob | None:
        result = self.client.blpop(self.queue_key, timeout=timeout_seconds)
        if result is None:
            return None
        _, encoded = result
        payload = json.loads(encoded)
        if not isinstance(payload, dict):
            raise ValueError("Document proposal queue payload must be an object")
        return DocumentProposalJob.from_payload(payload)

    def ping(self) -> bool:
        return bool(self.client.ping())

    def purge_for_test(self) -> None:
        self.client.delete(self.queue_key)


@dataclass(frozen=True)
class ProposalOutboxEvent:
    event_id: UUID
    aggregate_id: UUID
    event_type: str
    payload: dict[str, Any]
    attempts: int


class ProposalOutboxPublisher:
    def __init__(self, repository: Any, queue: ValkeyDocumentProposalQueue) -> None:
        self.repository = repository
        self.queue = queue

    def publish_pending(self, *, limit: int = 10) -> int:
        published = 0
        for event in self.repository.pending_proposal_outbox(limit=limit):
            try:
                if event.event_type != "research.document_proposal.requested":
                    raise ValueError(f"Unsupported proposal outbox event {event.event_type}")
                self.queue.enqueue(DocumentProposalJob.from_payload(event.payload))
            except (RedisError, ValueError, KeyError, TypeError) as exc:
                self.repository.mark_proposal_outbox_failed(
                    event.event_id,
                    f"{exc.__class__.__name__}: {exc}",
                )
                continue
            self.repository.mark_proposal_outbox_published(event.event_id)
            published += 1
        return published
