"""Opportunity Operations — WP4 (T01-T12 core models).

Extends the existing procurement domain (Opportunity, TenderWorkspace,
Clarification, AuditEvent) with the Opportunity Operations layer:

- Pursuit (T02): lifecycle of pursuing an opportunity (qualified ->
  decision -> active -> won/lost/withdrawn), always tenant-scoped;
- Outcome (T09): terminal result of a pursuit with evidence;
- Learning (T10): derived, evidence-linked lessons;
- Workspace Factory (T11): composes a workspace from a pursuit and its
  opportunity, enforcing tenant isolation and type consistency;
- rollback (T12): a workspace can be rolled back to a prior version.

The generic E2E journey (T12) is in opportunity_operations_e2e.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from axignal_api.procurement_domain import Opportunity, TenderWorkspace


class PursuitState(StrEnum):
    QUALIFIED = "QUALIFIED"
    DECISION_REVIEW = "DECISION_REVIEW"
    ACTIVE = "ACTIVE"
    WON = "WON"
    LOST = "LOST"
    WITHDRAWN = "WITHDRAWN"


PURSUIT_FORWARD: dict[PursuitState, set[PursuitState]] = {
    PursuitState.QUALIFIED: {PursuitState.DECISION_REVIEW, PursuitState.WITHDRAWN},
    PursuitState.DECISION_REVIEW: {PursuitState.ACTIVE, PursuitState.WITHDRAWN},
    PursuitState.ACTIVE: {PursuitState.WON, PursuitState.LOST, PursuitState.WITHDRAWN},
    PursuitState.WON: set(),
    PursuitState.LOST: set(),
    PursuitState.WITHDRAWN: set(),
}


class Pursuit(BaseModel):
    """A tenant-scoped pursuit lifecycle."""

    schema_version: Literal["axignal.wp4.pursuit.v1"] = "axignal.wp4.pursuit.v1"
    pursuit_id: str = Field(pattern=r"^prs_[A-Za-z0-9_-]{8,}$")
    tenant_id: UUID
    opportunity_id: str
    state: PursuitState = PursuitState.QUALIFIED
    workspace_id: UUID | None = None
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    decided_by: str | None = None
    decided_at: datetime | None = None
    outcome_id: str | None = None
    evidence_refs: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_pursuit(self) -> Pursuit:
        if (
            self.state in (PursuitState.ACTIVE, PursuitState.WON, PursuitState.LOST)
            and self.workspace_id is None
        ):
            raise ValueError(
                "ACTIVE/WON/LOST pursuits require a workspace_id"
            )
        if (
            self.state in (PursuitState.WON, PursuitState.LOST, PursuitState.WITHDRAWN)
            and (not self.decided_by or self.decided_at is None)
        ):
            raise ValueError(
                "terminal pursuit states require decided_by and decided_at"
            )
        if self.state == PursuitState.WON and not self.outcome_id:
            raise ValueError("WON pursuits require an outcome_id")
        return self

    def transition(self, target: PursuitState, *, decided_by: str) -> Pursuit:
        if target not in PURSUIT_FORWARD[self.state]:
            raise ValueError(
                f"illegal pursuit transition {self.state.value} -> {target.value}"
            )
        update: dict[str, object] = {"state": target}
        if target in (PursuitState.WON, PursuitState.LOST, PursuitState.WITHDRAWN):
            update["decided_by"] = decided_by
            update["decided_at"] = datetime.now(UTC)
        return self.model_copy(update=update)


class Outcome(BaseModel):
    """A terminal pursuit outcome with evidence."""

    schema_version: Literal["axignal.wp4.outcome.v1"] = "axignal.wp4.outcome.v1"
    outcome_id: str = Field(pattern=r"^out_[A-Za-z0-9_-]{8,}$")
    pursuit_id: str
    tenant_id: UUID
    result: Literal["WON", "LOST", "WITHDRAWN"]
    decided_at: datetime
    evidence_refs: list[str] = Field(default_factory=list)
    notes: str | None = None

    @model_validator(mode="after")
    def validate_outcome(self) -> Outcome:
        if self.result != "WITHDRAWN" and not self.evidence_refs:
            raise ValueError("WON/LOST outcomes require evidence_refs")
        return self


class Learning(BaseModel):
    """An evidence-linked lesson derived from an outcome."""

    schema_version: Literal["axignal.wp4.learning.v1"] = "axignal.wp4.learning.v1"
    learning_id: str = Field(pattern=r"^lrn_[A-Za-z0-9_-]{8,}$")
    tenant_id: UUID
    outcome_id: str
    insight: str = Field(min_length=10, max_length=2000)
    evidence_refs: list[str] = Field(default_factory=list)
    derived_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def validate_learning(self) -> Learning:
        if not self.evidence_refs:
            raise ValueError("learning requires evidence_refs (no unsupported lessons)")
        return self


class WorkspaceFactory:
    """Composes tenant workspaces from opportunities and pursuits (T11)."""

    def __init__(self) -> None:
        self._workspaces: dict[UUID, TenderWorkspace] = {}

    def create(
        self,
        *,
        workspace_id: UUID,
        tenant_id: UUID,
        pursuit: Pursuit,
        opportunity: Opportunity,
        subscriber_profile_version: str,
        assessment_version: str,
        created_by: str,
        created_at: datetime | None = None,
    ) -> TenderWorkspace:
        if pursuit.tenant_id != tenant_id:
            raise ValueError("pursuit tenant does not match workspace tenant")
        if pursuit.opportunity_id != opportunity.opportunity_id:
            raise ValueError(
                "pursuit opportunity does not match the opportunity"
            )
        workspace = TenderWorkspace(
            workspace_id=workspace_id,
            tenant_id=tenant_id,
            opportunity_id=opportunity.opportunity_id,
            opportunity_version=opportunity.current_version,
            subscriber_profile_version=subscriber_profile_version,
            assessment_version=assessment_version,
            created_by=created_by,
            created_at=created_at or datetime.now(UTC),
        )
        self._workspaces[workspace_id] = workspace
        return workspace

    def get(self, workspace_id: UUID) -> TenderWorkspace | None:
        return self._workspaces.get(workspace_id)

    def get_for_tenant(self, workspace_id: UUID, tenant_id: UUID) -> TenderWorkspace | None:
        workspace = self._workspaces.get(workspace_id)
        if workspace is None or workspace.tenant_id != tenant_id:
            return None
        return workspace

    def rollback(
        self,
        workspace_id: UUID,
        *,
        tenant_id: UUID,
        prior: TenderWorkspace,
    ) -> TenderWorkspace:
        """Roll back a workspace to a prior version (T12, tenant-scoped)."""
        current = self.get_for_tenant(workspace_id, tenant_id)
        if current is None:
            raise ValueError("workspace not found for tenant")
        if prior.workspace_id != workspace_id or prior.tenant_id != tenant_id:
            raise ValueError("prior workspace belongs to another workspace/tenant")
        self._workspaces[workspace_id] = prior
        return prior

    def __len__(self) -> int:
        return len(self._workspaces)
