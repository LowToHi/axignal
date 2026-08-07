"""O03 — Regulation (WP7).

Canonical regulation library per contract WP7:

- source admission (official legal publications; reference source family:
  EUR-Lex and national gazettes);
- legal document lifecycle;
- jurisdiction and effective dates;
- obligations (typed, evidence-backed);
- affected sectors;
- amendments and repeals;
- Market Entry & Compliance Workspace;
- legal-authority disclosures (the model never asserts legal authority);
- E2E journey and rollback.

Legal authority disclosure rule: the workspace records what a regulation
says and its official reference; it never issues legal advice or claims
authoritative interpretation.
"""

from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

REGULATION_SOURCE_ID = "src_eur_lex"


class LegalDocumentState(StrEnum):
    IN_FORCE = "IN_FORCE"
    AMENDED = "AMENDED"
    REPEALED = "REPEALED"
    PENDING_PUBLICATION = "PENDING_PUBLICATION"


class LegalDocument(BaseModel):
    """A legal document with typed lifecycle and authority disclosure."""

    schema_version: Literal["axignal.o03.document.v1"] = "axignal.o03.document.v1"
    document_id: str = Field(min_length=3, max_length=120)
    source_id: str = REGULATION_SOURCE_ID
    official_citation: str = Field(min_length=5, max_length=300)
    jurisdiction_id: str = Field(pattern=r"^[A-Z]{2}$|^EU$")
    state: LegalDocumentState = LegalDocumentState.PENDING_PUBLICATION
    published_at: date | None = None
    effective_at: date | None = None
    affected_sectors: list[str] = Field(default_factory=list)
    official_url: str | None = None
    content_hash: str | None = Field(default=None, pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_document(self) -> LegalDocument:
        if self.state in (LegalDocumentState.IN_FORCE, LegalDocumentState.AMENDED):
            if not self.effective_at:
                raise ValueError("IN_FORCE/AMENDED documents require effective_at")
            if not self.official_url:
                raise ValueError(
                    "IN_FORCE/AMENDED documents require official_url "
                    "(legal authority disclosure)"
                )
        if self.published_at and self.effective_at and self.published_at > self.effective_at:
            raise ValueError("published_at must be <= effective_at")
        return self


class Obligation(BaseModel):
    """A typed obligation extracted from a legal document."""

    schema_version: Literal["axignal.o03.obligation.v1"] = "axignal.o03.obligation.v1"
    obligation_id: str = Field(min_length=3, max_length=120)
    document_id: str
    article_ref: str = Field(min_length=2, max_length=80)
    subject: str = Field(min_length=5, max_length=500)
    obligation_type: Literal["PROHIBITION", "REQUIREMENT", "REPORTING", "DEADLINE"]
    evidence_ref: str | None = None

    @model_validator(mode="after")
    def validate_obligation(self) -> Obligation:
        if self.obligation_type == "DEADLINE" and not self.evidence_ref:
            raise ValueError("DEADLINE obligations require evidence_ref")
        return self


class AmendmentRecord(BaseModel):
    """An amendment or repeal between legal documents."""

    schema_version: Literal["axignal.o03.amendment.v1"] = "axignal.o03.amendment.v1"
    amendment_id: str = Field(min_length=3, max_length=120)
    amends_document_id: str
    amends_article_ref: str | None = None
    amended_by_document_id: str
    kind: Literal["AMENDMENT", "REPEAL"]
    effective_at: date
    evidence_ref: str | None = None

    @model_validator(mode="after")
    def validate_amendment(self) -> AmendmentRecord:
        if self.amends_document_id == self.amended_by_document_id:
            raise ValueError("a document cannot amend itself")
        if not self.evidence_ref:
            raise ValueError("amendments/repeals require evidence_ref")
        return self


class ComplianceState(StrEnum):
    ASSESSING = "ASSESSING"
    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    REMEDIATION = "REMEDIATION"
    CLOSED = "CLOSED"


class MarketEntryWorkspace(BaseModel):
    """A market entry & compliance workspace (tenant-scoped)."""

    schema_version: Literal["axignal.o03.compliance-workspace.v1"] = (
        "axignal.o03.compliance-workspace.v1"
    )
    workspace_id: UUID
    tenant_id: UUID
    document_id: str
    state: ComplianceState = ComplianceState.ASSESSING
    created_by: str
    legal_authority_disclosed: bool = False

    @model_validator(mode="after")
    def validate_workspace(self) -> MarketEntryWorkspace:
        if self.state in (
            ComplianceState.COMPLIANT,
            ComplianceState.NON_COMPLIANT,
            ComplianceState.CLOSED,
        ) and not self.legal_authority_disclosed:
            raise ValueError(
                "compliance conclusions require legal-authority disclosure"
            )
        return self

    def close(self, *, disclosed: bool = True) -> MarketEntryWorkspace:
        if not disclosed:
            raise ValueError("closing a compliance workspace requires legal-authority disclosure")
        return self.model_copy(
            update={
                "state": ComplianceState.CLOSED,
                "legal_authority_disclosed": True,
            }
        )


def regulation_source_manifest() -> dict[str, str]:
    """Canonical O03 source admission contract (reference data)."""
    return {
        "source_id": REGULATION_SOURCE_ID,
        "library_id": "O03",
        "source_type": "INSTITUTIONAL_API",
        "state": "DISCOVERED",
        "commercial_use": "PENDING_HUMAN_DECISION",
        "product_shell": "AXIGNAL_OPPORTUNITY_INTELLIGENCE",
    }
