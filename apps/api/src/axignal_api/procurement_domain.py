from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from urllib.parse import urlparse
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


class FactOrigin(StrEnum):
    SOURCE_FACT = "SOURCE_FACT"
    NORMALIZED_FACT = "NORMALIZED_FACT"
    TRANSLATED_FACT = "TRANSLATED_FACT"
    EXTRACTED_REQUIREMENT = "EXTRACTED_REQUIREMENT"
    AXIGNAL_INFERENCE = "AXIGNAL_INFERENCE"
    AXIGNAL_RECOMMENDATION = "AXIGNAL_RECOMMENDATION"
    SUBSCRIBER_PROVIDED = "SUBSCRIBER_PROVIDED"


class ContactChannelType(StrEnum):
    PROCUREMENT_PLATFORM = "PROCUREMENT_PLATFORM"
    BUYER_PROFILE = "BUYER_PROFILE"
    OFFICIAL_FORM = "OFFICIAL_FORM"
    FUNCTIONAL_EMAIL = "FUNCTIONAL_EMAIL"
    NAMED_PROFESSIONAL_EMAIL = "NAMED_PROFESSIONAL_EMAIL"
    OFFICIAL_PHONE = "OFFICIAL_PHONE"
    NAMED_PROFESSIONAL_PHONE = "NAMED_PROFESSIONAL_PHONE"
    SOURCE_LINK_ONLY = "SOURCE_LINK_ONLY"


class ContactDataClass(StrEnum):
    INSTITUTIONAL = "INSTITUTIONAL"
    FUNCTIONAL_NON_PERSONAL = "FUNCTIONAL_NON_PERSONAL"
    PROFESSIONAL_PERSONAL = "PROFESSIONAL_PERSONAL"
    AMBIGUOUS_PERSONAL = "AMBIGUOUS_PERSONAL"
    BLOCKED = "BLOCKED"


class ContactPolicyDecision(StrEnum):
    ALLOW = "ALLOW"
    CONTEXTUAL = "CONTEXTUAL"
    LINK_ONLY = "LINK_ONLY"
    BLOCK = "BLOCK"


class ContactAction(StrEnum):
    OPEN = "OPEN"
    REVEAL = "REVEAL"
    COPY = "COPY"
    COMPOSE_PROCEDURE_QUERY = "COMPOSE_PROCEDURE_QUERY"
    CALL = "CALL"


class ContactStatus(StrEnum):
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    DISABLED = "DISABLED"
    ARCHIVED = "ARCHIVED"


class WorkspaceState(StrEnum):
    CREATED = "CREATED"
    QUALIFYING = "QUALIFYING"
    GO_REVIEW = "GO_REVIEW"
    NO_GO_REVIEW = "NO_GO_REVIEW"
    PREPARING = "PREPARING"
    AWAITING_INFORMATION = "AWAITING_INFORMATION"
    READY_FOR_INTERNAL_REVIEW = "READY_FOR_INTERNAL_REVIEW"
    READY_FOR_SUBSCRIBER_APPROVAL = "READY_FOR_SUBSCRIBER_APPROVAL"
    SUBSCRIBER_APPROVED = "SUBSCRIBER_APPROVED"
    PRESENTED_EXTERNALLY = "PRESENTED_EXTERNALLY"
    WITHDRAWN = "WITHDRAWN"
    CLOSED = "CLOSED"
    ARCHIVED = "ARCHIVED"


class ClarificationState(StrEnum):
    DRAFT = "DRAFT"
    INTERNAL_REVIEW = "INTERNAL_REVIEW"
    READY_FOR_USER_APPROVAL = "READY_FOR_USER_APPROVAL"
    USER_APPROVED = "USER_APPROVED"
    EXTERNAL_HANDOFF = "EXTERNAL_HANDOFF"
    SENT_CONFIRMED = "SENT_CONFIRMED"
    ANSWER_RECEIVED = "ANSWER_RECEIVED"
    ANSWER_APPLIED = "ANSWER_APPLIED"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class PolicyDecisionKind(StrEnum):
    ALLOW = "ALLOW"
    CONTEXTUAL = "CONTEXTUAL"
    LINK_ONLY = "LINK_ONLY"
    BLOCK = "BLOCK"


class SourceProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: str = Field(min_length=1)
    source_notice_id: str = Field(min_length=1)
    source_url: HttpUrl
    retrieved_at: datetime
    source_version: str = Field(min_length=1)
    transformation_disclosure: str | None = None


class ProcurementFact(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    fact_id: str = Field(min_length=1)
    predicate: str = Field(min_length=1)
    value: Any
    origin: FactOrigin
    provenance: SourceProvenance | None
    confidence: float | None = Field(default=None, ge=0, le=1)
    supporting_fact_ids: tuple[str, ...] = ()
    missing_information: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_origin(self) -> "ProcurementFact":
        if self.origin in {
            FactOrigin.SOURCE_FACT,
            FactOrigin.NORMALIZED_FACT,
            FactOrigin.TRANSLATED_FACT,
            FactOrigin.EXTRACTED_REQUIREMENT,
        } and self.provenance is None:
            raise ValueError("Source-derived facts require provenance")
        if self.origin in {
            FactOrigin.AXIGNAL_INFERENCE,
            FactOrigin.AXIGNAL_RECOMMENDATION,
        } and not self.supporting_fact_ids:
            raise ValueError("AXIGNAL conclusions require supporting facts")
        return self


class OpportunityVersion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    opportunity_id: str = Field(min_length=1)
    source_notice_id: str = Field(min_length=1)
    source_version: str = Field(min_length=1)
    observed_at: datetime
    source_updated_at: datetime | None = None
    content_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")


class ProcurementContactChannel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    channel_id: str = Field(min_length=1)
    opportunity_id: str = Field(min_length=1)
    source_notice_id: str = Field(min_length=1)
    source_url: HttpUrl
    channel_type: ContactChannelType
    organisation_name: str = Field(min_length=1)
    department: str | None = None
    contact_name: str | None = None
    contact_role: str | None = None
    endpoint: str | None = None
    data_class: ContactDataClass
    policy_decision: ContactPolicyDecision
    purpose: str = "PROCUREMENT_PROCEDURE_COMMUNICATION"
    searchable_globally: bool = False
    exportable: bool = False
    marketing_use: bool = False
    allowed_actions: frozenset[ContactAction] = frozenset()
    last_verified_at: datetime
    status: ContactStatus = ContactStatus.ACTIVE
    superseded_by: str | None = None

    @model_validator(mode="after")
    def validate_channel_policy(self) -> "ProcurementContactChannel":
        if self.searchable_globally or self.exportable or self.marketing_use:
            raise ValueError("Procurement contact channels cannot become CRM or marketing data")

        if self.data_class is ContactDataClass.BLOCKED:
            if self.policy_decision is not ContactPolicyDecision.BLOCK:
                raise ValueError("Blocked data must have a BLOCK policy decision")
            if self.endpoint is not None or self.allowed_actions:
                raise ValueError("Blocked data cannot expose endpoints or actions")
            return self

        if self.data_class is ContactDataClass.AMBIGUOUS_PERSONAL:
            if self.policy_decision not in {
                ContactPolicyDecision.LINK_ONLY,
                ContactPolicyDecision.BLOCK,
            }:
                raise ValueError("Ambiguous personal data must be LINK_ONLY or BLOCK")

        if self.data_class is ContactDataClass.PROFESSIONAL_PERSONAL:
            if self.policy_decision is not ContactPolicyDecision.CONTEXTUAL:
                raise ValueError("Named professional contacts require CONTEXTUAL policy")
            if self.channel_type not in {
                ContactChannelType.NAMED_PROFESSIONAL_EMAIL,
                ContactChannelType.NAMED_PROFESSIONAL_PHONE,
            }:
                raise ValueError("Professional personal data requires a named contact channel")
            if not self.contact_name:
                raise ValueError("Named professional channels require contact_name")

        if self.policy_decision is ContactPolicyDecision.BLOCK:
            if self.endpoint is not None or self.allowed_actions:
                raise ValueError("BLOCK decisions cannot expose endpoints or actions")
            return self

        if not self.endpoint:
            raise ValueError("Allowed contact channels require an endpoint")

        scheme = urlparse(self.endpoint).scheme.casefold()
        expected_schemes = {
            ContactChannelType.PROCUREMENT_PLATFORM: {"https"},
            ContactChannelType.BUYER_PROFILE: {"https"},
            ContactChannelType.OFFICIAL_FORM: {"https"},
            ContactChannelType.FUNCTIONAL_EMAIL: {"mailto"},
            ContactChannelType.NAMED_PROFESSIONAL_EMAIL: {"mailto"},
            ContactChannelType.OFFICIAL_PHONE: {"tel"},
            ContactChannelType.NAMED_PROFESSIONAL_PHONE: {"tel"},
            ContactChannelType.SOURCE_LINK_ONLY: {"https"},
        }
        if scheme not in expected_schemes[self.channel_type]:
            raise ValueError("Contact endpoint scheme does not match channel type")

        if self.policy_decision is ContactPolicyDecision.LINK_ONLY:
            if self.allowed_actions != frozenset({ContactAction.OPEN}):
                raise ValueError("LINK_ONLY permits only OPEN")

        if self.status is ContactStatus.SUPERSEDED and not self.superseded_by:
            raise ValueError("Superseded channels require a replacement reference")
        return self


class Opportunity(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    opportunity_id: str = Field(min_length=1)
    current_version: OpportunityVersion
    title: str = Field(min_length=1)
    buyer_organisation: str = Field(min_length=1)
    facts: tuple[ProcurementFact, ...]
    contact_channels: tuple[ProcurementContactChannel, ...] = ()

    @model_validator(mode="after")
    def validate_bindings(self) -> "Opportunity":
        if self.current_version.opportunity_id != self.opportunity_id:
            raise ValueError("Opportunity version belongs to another opportunity")
        if any(item.opportunity_id != self.opportunity_id for item in self.contact_channels):
            raise ValueError("Contact channel belongs to another opportunity")
        fact_ids = [item.fact_id for item in self.facts]
        if len(fact_ids) != len(set(fact_ids)):
            raise ValueError("Opportunity fact identifiers must be unique")
        return self


class TenderWorkspace(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    workspace_id: UUID
    tenant_id: UUID
    opportunity_id: str = Field(min_length=1)
    opportunity_version: OpportunityVersion
    subscriber_profile_version: str = Field(min_length=1)
    assessment_version: str = Field(min_length=1)
    state: WorkspaceState = WorkspaceState.CREATED
    contact_channel_ids: tuple[str, ...] = ()
    created_by: str = Field(min_length=1)
    created_at: datetime
    presented_externally_confirmed_by: str | None = None
    presented_externally_confirmed_at: datetime | None = None

    @model_validator(mode="after")
    def validate_workspace_state(self) -> "TenderWorkspace":
        if self.opportunity_version.opportunity_id != self.opportunity_id:
            raise ValueError("Workspace snapshot belongs to another opportunity")
        if len(self.contact_channel_ids) != len(set(self.contact_channel_ids)):
            raise ValueError("Workspace contact-channel references must be unique")
        if self.state is WorkspaceState.PRESENTED_EXTERNALLY:
            if not self.presented_externally_confirmed_by:
                raise ValueError("External presentation requires subscriber confirmation")
            if self.presented_externally_confirmed_at is None:
                raise ValueError("External presentation requires confirmation timestamp")
        return self


class Clarification(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    clarification_id: str = Field(min_length=1)
    tenant_id: UUID
    workspace_id: UUID
    procedure_reference: str = Field(min_length=1)
    related_requirement_ids: tuple[str, ...] = ()
    question: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    channel_id: str = Field(min_length=1)
    state: ClarificationState = ClarificationState.DRAFT
    created_by: str = Field(min_length=1)
    created_at: datetime
    approved_by: str | None = None
    approved_at: datetime | None = None
    external_handoff_at: datetime | None = None
    sent_confirmed_by: str | None = None
    sent_at: datetime | None = None

    @model_validator(mode="after")
    def validate_human_control(self) -> "Clarification":
        approval_states = {
            ClarificationState.USER_APPROVED,
            ClarificationState.EXTERNAL_HANDOFF,
            ClarificationState.SENT_CONFIRMED,
            ClarificationState.ANSWER_RECEIVED,
            ClarificationState.ANSWER_APPLIED,
            ClarificationState.CLOSED,
        }
        if self.state in approval_states and (not self.approved_by or self.approved_at is None):
            raise ValueError("External communication requires explicit subscriber approval")
        if self.state in {
            ClarificationState.EXTERNAL_HANDOFF,
            ClarificationState.SENT_CONFIRMED,
            ClarificationState.ANSWER_RECEIVED,
            ClarificationState.ANSWER_APPLIED,
            ClarificationState.CLOSED,
        } and self.external_handoff_at is None:
            raise ValueError("External states require a recorded handoff")
        if self.state in {
            ClarificationState.SENT_CONFIRMED,
            ClarificationState.ANSWER_RECEIVED,
            ClarificationState.ANSWER_APPLIED,
            ClarificationState.CLOSED,
        } and (not self.sent_confirmed_by or self.sent_at is None):
            raise ValueError("Sent state must be confirmed by the subscriber")
        return self


class PolicyDecisionRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    decision_id: str = Field(min_length=1)
    subject_type: str = Field(min_length=1)
    subject_id: str = Field(min_length=1)
    decision: PolicyDecisionKind
    policy_version: str = Field(min_length=1)
    reasons: tuple[str, ...] = Field(min_length=1)
    decided_at: datetime


class AuditEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    event_id: str = Field(min_length=1)
    tenant_id: UUID
    workspace_id: UUID | None = None
    actor_id: str = Field(min_length=1)
    action: str = Field(min_length=1)
    object_type: str = Field(min_length=1)
    object_id: str = Field(min_length=1)
    occurred_at: datetime
    source_version: str | None = None
    policy_version: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def reject_contact_replication(self) -> "AuditEvent":
        prohibited = {
            "contact_name",
            "contact_email",
            "email",
            "phone",
            "telephone",
            "endpoint",
            "message_body",
        }

        def iter_keys(value: Any) -> set[str]:
            if isinstance(value, dict):
                result = {str(key).casefold() for key in value}
                for item in value.values():
                    result.update(iter_keys(item))
                return result
            if isinstance(value, list):
                result: set[str] = set()
                for item in value:
                    result.update(iter_keys(item))
                return result
            return set()

        if prohibited.intersection(iter_keys(self.details)):
            raise ValueError("Audit details must not replicate contact endpoints or message bodies")
        return self
