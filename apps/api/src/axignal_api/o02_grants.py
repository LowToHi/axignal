"""O02 — Grants (WP6).

Canonical grants library per contract WP6:

- source admission (contracts from official EU funding sources, e.g.
  CORDIS/Funding & Tenders Portal as the reference source family);
- grants ontology (call, topic, budget, rate, beneficiary, award);
- eligibility rules (typed, evidence-backed);
- calls/topics lifecycle;
- budgets and funding rates;
- beneficiaries and awards;
- Application Workspace lifecycle;
- E2E journey and rollback.

Fixtures are allowed during development; a library is never declared
complete on fixtures alone (live source admission is a separate task).
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

GRANTS_SOURCE_ID = "src_funding_tenders_portal"


class CallState(StrEnum):
    DRAFT = "DRAFT"
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


CALL_FORWARD: dict[CallState, set[CallState]] = {
    CallState.DRAFT: {CallState.OPEN, CallState.CANCELLED},
    CallState.OPEN: {CallState.CLOSED, CallState.CANCELLED},
    CallState.CLOSED: set(),
    CallState.CANCELLED: set(),
}


class GrantCall(BaseModel):
    """A funding call with typed lifecycle."""

    schema_version: Literal["axignal.o02.call.v1"] = "axignal.o02.call.v1"
    call_id: str = Field(min_length=3, max_length=120)
    source_id: str = GRANTS_SOURCE_ID
    title: str = Field(min_length=3, max_length=300)
    state: CallState = CallState.DRAFT
    opens_at: date | None = None
    closes_at: date | None = None
    total_budget_eur: float | None = Field(default=None, ge=0.0)
    content_hash: str | None = Field(default=None, pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_call(self) -> GrantCall:
        if self.opens_at and self.closes_at and self.opens_at > self.closes_at:
            raise ValueError("opens_at must be <= closes_at")
        if self.state == CallState.OPEN and not (self.opens_at and self.closes_at):
            raise ValueError("OPEN calls require opens_at and closes_at")
        return self

    def transition(self, target: CallState) -> GrantCall:
        if target not in CALL_FORWARD[self.state]:
            raise ValueError(
                f"illegal call transition {self.state.value} -> {target.value}"
            )
        return self.model_copy(update={"state": target})


class EligibilityRule(BaseModel):
    """A typed eligibility rule with evidence."""

    schema_version: Literal["axignal.o02.eligibility.v1"] = "axignal.o02.eligibility.v1"
    rule_id: str = Field(min_length=3, max_length=120)
    call_id: str
    criterion: str = Field(min_length=5, max_length=500)
    category: Literal["ENTITY_TYPE", "GEOGRAPHY", "FUNDING_RATE", "BUDGET", "DEADLINE", "OTHER"]
    source_ref: str | None = None

    @model_validator(mode="after")
    def validate_rule(self) -> EligibilityRule:
        if self.category == "DEADLINE" and not self.source_ref:
            raise ValueError("DEADLINE rules require source_ref")
        return self


class GrantTopic(BaseModel):
    """A topic within a call."""

    schema_version: Literal["axignal.o02.topic.v1"] = "axignal.o02.topic.v1"
    topic_id: str = Field(min_length=3, max_length=120)
    call_id: str
    title: str = Field(min_length=3, max_length=300)
    funding_rate_pct: float | None = Field(default=None, ge=0.0, le=100.0)
    indicative_budget_eur: float | None = Field(default=None, ge=0.0)

    @model_validator(mode="after")
    def validate_topic(self) -> GrantTopic:
        if self.funding_rate_pct is None and self.indicative_budget_eur is None:
            raise ValueError("topic requires funding_rate_pct or indicative_budget_eur")
        return self


class BeneficiaryAward(BaseModel):
    """A beneficiary award with evidence."""

    schema_version: Literal["axignal.o02.award.v1"] = "axignal.o02.award.v1"
    award_id: str = Field(min_length=3, max_length=120)
    topic_id: str
    beneficiary_entity_id: str = Field(min_length=3, max_length=120)
    awarded_amount_eur: float = Field(ge=0.0)
    awarded_at: date
    evidence_ref: str | None = None

    @model_validator(mode="after")
    def validate_award(self) -> BeneficiaryAward:
        if self.awarded_amount_eur > 0 and not self.evidence_ref:
            raise ValueError("awards require evidence_ref")
        return self


class ApplicationState(StrEnum):
    DRAFT = "DRAFT"
    ELIGIBILITY_CHECKED = "ELIGIBILITY_CHECKED"
    READY_FOR_APPROVAL = "READY_FOR_APPROVAL"
    APPROVED = "APPROVED"
    SUBMITTED = "SUBMITTED"
    WITHDRAWN = "WITHDRAWN"


APPLICATION_FORWARD: dict[ApplicationState, set[ApplicationState]] = {
    ApplicationState.DRAFT: {ApplicationState.ELIGIBILITY_CHECKED, ApplicationState.WITHDRAWN},
    ApplicationState.ELIGIBILITY_CHECKED: {
        ApplicationState.READY_FOR_APPROVAL,
        ApplicationState.WITHDRAWN,
    },
    ApplicationState.READY_FOR_APPROVAL: {
        ApplicationState.APPROVED,
        ApplicationState.WITHDRAWN,
    },
    ApplicationState.APPROVED: {
        ApplicationState.SUBMITTED,
        ApplicationState.WITHDRAWN,
    },
    ApplicationState.SUBMITTED: set(),
    ApplicationState.WITHDRAWN: set(),
}


class ApplicationWorkspace(BaseModel):
    """A grant application workspace (tenant-scoped)."""

    schema_version: Literal["axignal.o02.application-workspace.v1"] = (
        "axignal.o02.application-workspace.v1"
    )
    workspace_id: UUID
    tenant_id: UUID
    topic_id: str
    state: ApplicationState = ApplicationState.DRAFT
    approved_by: str | None = None
    approved_at: datetime | None = None
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def validate_workspace(self) -> ApplicationWorkspace:
        if (
            self.state == ApplicationState.APPROVED
            and (not self.approved_by or self.approved_at is None)
        ):
            raise ValueError(
                "APPROVED applications require approved_by and approved_at"
            )
        return self

    def transition(self, target: ApplicationState) -> ApplicationWorkspace:
        if target not in APPLICATION_FORWARD[self.state]:
            raise ValueError(
                f"illegal application transition {self.state.value} -> {target.value}"
            )
        return self.model_copy(update={"state": target})


def grants_source_manifest() -> dict[str, str]:
    """Canonical O02 source admission contract (reference data)."""
    return {
        "source_id": GRANTS_SOURCE_ID,
        "library_id": "O02",
        "source_type": "INSTITUTIONAL_API",
        "state": "DISCOVERED",
        "commercial_use": "PENDING_HUMAN_DECISION",
        "product_shell": "AXIGNAL_OPPORTUNITY_INTELLIGENCE",
    }
