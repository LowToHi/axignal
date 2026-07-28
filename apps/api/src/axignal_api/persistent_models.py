from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class PersistentResearchRunCreate(BaseModel):
    context_id: str = Field(pattern=r"^ctx_[A-Za-z0-9_-]{8,}$")
    opportunity_id: str = Field(min_length=3, max_length=200)
    question: str = Field(min_length=3, max_length=8_000)
    include_private_knowledge: bool = False


class PersistentResearchRunAccepted(BaseModel):
    research_run_id: UUID
    state: Literal["QUEUED"]
    queue_delivery: Literal["PUBLISHED", "OUTBOX_PENDING"]
    source_ids: list[Literal["world-bank-wdi"]]
    synthetic: Literal[False] = False


class SourceView(BaseModel):
    source_id: str
    name: str
    rights_status: str
    license_id: str | None
    attribution_text: str | None
    admission_state: str
    kill_switch: bool


class EvidenceView(BaseModel):
    evidence_id: UUID
    source_id: str
    title: str
    relationship: str
    subject_id: str
    predicate: str
    observed_at: datetime
    numeric_value: str | None
    unit: str | None
    rights_status: str
    provisional: bool
    payload: dict[str, Any]


class CandidateClaimView(BaseModel):
    candidate_claim_id: UUID
    fingerprint: str
    statement: str
    kind: str
    state: str
    producer_type: str
    method_version: str
    canonical_claim_id: UUID | None
    rejection_reasons: list[str]


class CanonicalClaimView(BaseModel):
    canonical_claim_id: UUID
    fingerprint: str
    statement: str
    subject_id: str
    predicate: str
    object_value: dict[str, Any]
    observed_at: datetime
    epistemic_class: str
    state: Literal["ADMITTED"]
    admitted_by: Literal["DETERMINISTIC_RUNTIME"]
    admitted_at: datetime


class DossierView(BaseModel):
    dossier_id: UUID
    status: str
    title: str
    summary: str
    sections: list[dict[str, Any]]
    attribution: dict[str, Any]


class PersistentResearchRunView(BaseModel):
    research_run_id: UUID
    context_id: str
    opportunity_id: str
    question: str
    state: str
    private_knowledge_authorised: bool
    source_plan: list[dict[str, Any]]
    budgets: dict[str, Any]
    actual_usage: dict[str, Any]
    evidence: list[EvidenceView]
    candidate_claims: list[CandidateClaimView]
    canonical_claims: list[CanonicalClaimView]
    dossier: DossierView | None
    admission_batch_id: UUID | None
    error_code: str | None
    error_detail: str | None
    created_at: datetime
    updated_at: datetime
    synthetic: Literal[False] = False
