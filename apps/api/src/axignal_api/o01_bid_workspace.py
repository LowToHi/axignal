"""O01 — Relevance, Qualification and Bid Workspace (WP5-T08..T11).

- T08: relevance and qualification scoring with dimensional evidence
  (never one opaque score; user attention is not an economic claim);
- T09: Bid Workspace lifecycle for an opportunity;
- T10: approvals and readiness (human authority before submission);
- T11: official handoff record (submission or activation).

Rules:
- qualification requires dimensional evidence; a single opaque score is
  prohibited;
- the Bid Workspace does not create entitlement;
- submission requires explicit human approval and a recorded handoff.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class QualificationDimension(StrEnum):
    FIT = "FIT"
    COMPETITION = "COMPETITION"
    CAPACITY = "CAPACITY"
    TIMING = "TIMING"
    VALUE = "VALUE"


class RelevanceEvidence(BaseModel):
    """A single dimensional relevance/qualification evidence."""

    schema_version: Literal["axignal.o01.relevance.v1"] = "axignal.o01.relevance.v1"
    evidence_id: str = Field(min_length=3, max_length=120)
    opportunity_id: str
    dimension: QualificationDimension
    score: float = Field(ge=0.0, le=1.0)
    basis: str = Field(min_length=10, max_length=2000)
    evidence_refs: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_evidence(self) -> RelevanceEvidence:
        if not self.evidence_refs:
            raise ValueError(
                "relevance evidence requires evidence_refs "
                "(no unsupported scores)"
            )
        return self


class QualificationDecision(BaseModel):
    """A dimensional qualification decision (never a single opaque score)."""

    schema_version: Literal["axignal.o01.qualification.v1"] = "axignal.o01.qualification.v1"
    decision_id: str = Field(min_length=3, max_length=120)
    opportunity_id: str
    dimensions: dict[QualificationDimension, float]
    overall: Literal["GO", "NO_GO", "REVIEW"]
    decided_by: str
    decided_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    evidence_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_decision(self) -> QualificationDecision:
        if not self.dimensions:
            raise ValueError("qualification requires at least one dimension")
        if set(self.dimensions) != set(QualificationDimension):
            raise ValueError(
                "all five dimensions are required "
                "(FIT, COMPETITION, CAPACITY, TIMING, VALUE)"
            )
        for dimension, score in self.dimensions.items():
            if score < 0.0 or score > 1.0:
                raise ValueError(
                    f"score for {dimension.value} must be in [0, 1]"
                )
        if self.overall == "GO" and not self.evidence_ids:
            raise ValueError("GO decisions require evidence_ids")
        return self


class BidWorkspaceState(StrEnum):
    DRAFT = "DRAFT"
    QUALIFIED = "QUALIFIED"
    READY_FOR_APPROVAL = "READY_FOR_APPROVAL"
    APPROVED = "APPROVED"
    SUBMITTED = "SUBMITTED"
    WITHDRAWN = "WITHDRAWN"


BID_FORWARD: dict[BidWorkspaceState, set[BidWorkspaceState]] = {
    BidWorkspaceState.DRAFT: {BidWorkspaceState.QUALIFIED, BidWorkspaceState.WITHDRAWN},
    BidWorkspaceState.QUALIFIED: {
        BidWorkspaceState.READY_FOR_APPROVAL,
        BidWorkspaceState.WITHDRAWN,
    },
    BidWorkspaceState.READY_FOR_APPROVAL: {
        BidWorkspaceState.APPROVED,
        BidWorkspaceState.WITHDRAWN,
    },
    BidWorkspaceState.APPROVED: {
        BidWorkspaceState.SUBMITTED,
        BidWorkspaceState.WITHDRAWN,
    },
    BidWorkspaceState.SUBMITTED: set(),
    BidWorkspaceState.WITHDRAWN: set(),
}


class BidWorkspace(BaseModel):
    """A procurement bid workspace lifecycle (T09)."""

    schema_version: Literal["axignal.o01.bid-workspace.v1"] = "axignal.o01.bid-workspace.v1"
    workspace_id: UUID
    tenant_id: UUID
    opportunity_id: str
    state: BidWorkspaceState = BidWorkspaceState.DRAFT
    qualification_decision_id: str | None = None
    approved_by: str | None = None
    approved_at: datetime | None = None
    handoff_record_id: str | None = None
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def validate_workspace(self) -> BidWorkspace:
        if self.state in (
            BidWorkspaceState.QUALIFIED,
            BidWorkspaceState.READY_FOR_APPROVAL,
            BidWorkspaceState.APPROVED,
            BidWorkspaceState.SUBMITTED,
        ) and self.qualification_decision_id is None:
            raise ValueError(
                "qualified bid workspaces require qualification_decision_id"
            )
        if (
            self.state == BidWorkspaceState.APPROVED
            and (not self.approved_by or self.approved_at is None)
        ):
            raise ValueError(
                "APPROVED bid workspaces require approved_by and approved_at"
            )
        if self.state == BidWorkspaceState.SUBMITTED and not self.handoff_record_id:
            raise ValueError("SUBMITTED bid workspaces require handoff_record_id")
        return self

    def transition(self, target: BidWorkspaceState) -> BidWorkspace:
        if target not in BID_FORWARD[self.state]:
            raise ValueError(
                f"illegal bid workspace transition {self.state.value} -> {target.value}"
            )
        return self.model_copy(update={"state": target})


class ApprovalRecord(BaseModel):
    """A human approval record (T10)."""

    schema_version: Literal["axignal.o01.approval.v1"] = "axignal.o01.approval.v1"
    approval_id: str = Field(min_length=3, max_length=120)
    workspace_id: UUID
    tenant_id: UUID
    approved_by: str = Field(min_length=2, max_length=200)
    approved_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    scope: Literal["SUBMISSION", "EXTERNAL_PRESENTATION", "ACTIVATION"] = "SUBMISSION"
    evidence_refs: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_approval(self) -> ApprovalRecord:
        if self.scope == "EXTERNAL_PRESENTATION" and not self.evidence_refs:
            raise ValueError(
                "external presentation approvals require evidence_refs"
            )
        return self


class HandoffRecord(BaseModel):
    """An official submission or activation handoff (T11)."""

    schema_version: Literal["axignal.o01.handoff.v1"] = "axignal.o01.handoff.v1"
    handoff_id: str = Field(min_length=3, max_length=120)
    workspace_id: UUID
    tenant_id: UUID
    kind: Literal["SUBMISSION", "ACTIVATION"]
    target: str = Field(min_length=3, max_length=300)
    performed_by: str
    performed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    approval_id: str
    outcome_ref: str | None = None

    @model_validator(mode="after")
    def validate_handoff(self) -> HandoffRecord:
        if not self.target.strip():
            raise ValueError("handoff target must not be empty")
        return self
