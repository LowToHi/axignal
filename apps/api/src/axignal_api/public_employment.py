"""WP16 — Public Employment architectural proof (second shell).

Architectural proof of AXIGNAL_PUBLIC_EMPLOYMENT over the shared Core,
without product launch:

- domain model (candidate, exam, call);
- manifest (second-shell Domain Manifest);
- routes (draft, non-indexable);
- vocabulary (Spanish public-employment domain terms);
- roles/capabilities;
- application/examination workspace;
- eligibility policy states;
- fixture E2E;
- official source technical probe (referenced, not asserted live);
- audit/export;
- retention/deletion.

All states remain DRAFT/hidden/non-indexable; no checkout, no public
launch, no live billing (contract gates).
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

SHELL_ID = "AXIGNAL_PUBLIC_EMPLOYMENT"


class CandidateState(StrEnum):
    REGISTERED = "REGISTERED"
    ELIGIBLE = "ELIGIBLE"
    NOT_ELIGIBLE = "NOT_ELIGIBLE"
    EXAM_REGISTERED = "EXAM_REGISTERED"
    PASSED = "PASSED"
    NOT_PASSED = "NOT_PASSED"


class CandidateRecord(BaseModel):
    """A candidate record (minimal, purpose-bound)."""

    schema_version: Literal["axignal.pe.candidate.v1"] = "axignal.pe.candidate.v1"
    candidate_id: str = Field(min_length=3, max_length=120)
    tenant_id: UUID
    state: CandidateState = CandidateState.REGISTERED
    eligibility_ruleset: str | None = None
    registered_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def validate_candidate(self) -> CandidateRecord:
        if (
            self.state in (CandidateState.ELIGIBLE, CandidateState.NOT_ELIGIBLE)
            and not self.eligibility_ruleset
        ):
            raise ValueError("eligibility states require an eligibility_ruleset")
        return self


class ExamCall(BaseModel):
    """A public-employment examination call (DRAFT state)."""

    schema_version: Literal["axignal.pe.call.v1"] = "axignal.pe.call.v1"
    call_id: str = Field(min_length=3, max_length=120)
    title: str = Field(min_length=3, max_length=300)
    jurisdiction_id: str = Field(pattern=r"^[A-Z]{2}$")
    opens_at: date | None = None
    closes_at: date | None = None
    published: bool = False

    @model_validator(mode="after")
    def validate_call(self) -> ExamCall:
        if self.published:
            raise ValueError(
                "Public Employment calls cannot be published "
                "(DRAFT/hidden until authorized)"
            )
        if self.opens_at and self.closes_at and self.opens_at > self.closes_at:
            raise ValueError("opens_at must be <= closes_at")
        return self


class ApplicationWorkspace(BaseModel):
    """An application/examination workspace (tenant-scoped)."""

    schema_version: Literal["axignal.pe.application.v1"] = "axignal.pe.application.v1"
    workspace_id: UUID
    tenant_id: UUID
    candidate_id: str
    call_id: str
    state: Literal["DRAFT", "SUBMITTED", "IN_REVIEW", "CLOSED"] = "DRAFT"
    created_by: str

    @model_validator(mode="after")
    def validate_workspace(self) -> ApplicationWorkspace:
        if self.state == "SUBMITTED" and not self.candidate_id:
            raise ValueError("SUBMITTED applications require candidate_id")
        return self


class EligibilityPolicy(BaseModel):
    """A typed eligibility policy state."""

    schema_version: Literal["axignal.pe.eligibility-policy.v1"] = "axignal.pe.eligibility-policy.v1"
    policy_id: str = Field(min_length=3, max_length=120)
    ruleset: str = Field(min_length=5, max_length=500)
    state: Literal["DRAFT", "APPROVED", "SUPERSEDED"] = "DRAFT"
    source_ref: str | None = None

    @model_validator(mode="after")
    def validate_policy(self) -> EligibilityPolicy:
        if self.state == "APPROVED" and not self.source_ref:
            raise ValueError("APPROVED policies require source_ref")
        return self


class ShellManifest(BaseModel):
    """The second-shell Domain Manifest (DRAFT)."""

    schema_version: Literal["axignal.pe.manifest.v1"] = "axignal.pe.manifest.v1"
    shell_id: Literal["AXIGNAL_PUBLIC_EMPLOYMENT"] = "AXIGNAL_PUBLIC_EMPLOYMENT"
    manifest_version: str = "0.1.0-draft"
    domain: str = "public-employment"
    indexable: bool = False
    checkout_enabled: bool = False
    public_copy: bool = False
    public_launch_authorized: bool = False
    live_billing: bool = False

    @model_validator(mode="after")
    def validate_manifest(self) -> ShellManifest:
        if self.indexable or self.checkout_enabled or self.public_copy:
            raise ValueError(
                "Public Employment must remain hidden/non-indexable/"
                "no-checkout (DRAFT gate)"
            )
        if self.public_launch_authorized or self.live_billing:
            raise ValueError(
                "Public Employment has no launch or live-billing authority"
            )
        return self


def routes() -> list[dict[str, str]]:
    """Draft routes; all hidden from public discovery."""
    return [
        {"path": "/empleo-publico", "state": "DRAFT_HIDDEN", "indexable": "false"},
        {"path": "/empleo-publico/convocatorias", "state": "DRAFT_HIDDEN", "indexable": "false"},
        {"path": "/empleo-publico/candidatura", "state": "DRAFT_HIDDEN", "indexable": "false"},
    ]


def roles_capabilities() -> dict[str, list[str]]:
    """Second-shell roles and capabilities (server-side)."""
    return {
        "candidate": ["apply", "track_application"],
        "examiner": ["review_application"],
        "admin": ["manage_calls"],
    }


def vocabulary() -> dict[str, str]:
    """Spanish public-employment vocabulary (canonical)."""
    return {
        "convocatoria": "call",
        "candidato": "candidate",
        "examen": "examination",
        "oposición": "competitive examination",
        "temario": "syllabus",
        "tribunal": "examination board",
        "nota de corte": "pass mark",
    }
