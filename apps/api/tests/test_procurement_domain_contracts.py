from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest
from pydantic import ValidationError

from axignal_api.procurement_domain import (
    AuditEvent,
    Clarification,
    ClarificationState,
    ContactAction,
    ContactChannelType,
    ContactDataClass,
    ContactPolicyDecision,
    FactOrigin,
    Opportunity,
    OpportunityVersion,
    ProcurementContactChannel,
    ProcurementFact,
    SourceProvenance,
    TenderWorkspace,
    WorkspaceState,
)

NOW = datetime(2026, 8, 1, 18, 0, tzinfo=UTC)
TENANT_ID = UUID("11111111-1111-4111-8111-111111111111")
WORKSPACE_ID = UUID("22222222-2222-4222-8222-222222222222")


def provenance() -> SourceProvenance:
    return SourceProvenance(
        source_id="src_ted_search_api_v3",
        source_notice_id="123456-2026",
        source_url="https://ted.europa.eu/en/notice/-/detail/123456-2026",
        retrieved_at=NOW,
        source_version="ted-search-api-v3@2026-08-01",
        transformation_disclosure="Normalised by AXIGNAL",
    )


def version() -> OpportunityVersion:
    return OpportunityVersion(
        opportunity_id="opp_123456_2026",
        source_notice_id="123456-2026",
        source_version="ted-search-api-v3@2026-08-01",
        observed_at=NOW,
        content_digest="sha256:" + "a" * 64,
    )


def test_institutional_channel_is_allowed_and_workspace_references_it() -> None:
    channel = ProcurementContactChannel(
        channel_id="channel_platform",
        opportunity_id="opp_123456_2026",
        source_notice_id="123456-2026",
        source_url="https://ted.europa.eu/en/notice/-/detail/123456-2026",
        channel_type=ContactChannelType.PROCUREMENT_PLATFORM,
        organisation_name="Example Contracting Authority",
        endpoint="https://procurement.example.eu/procedure/ABC-2026-001",
        data_class=ContactDataClass.INSTITUTIONAL,
        policy_decision=ContactPolicyDecision.ALLOW,
        allowed_actions=frozenset({ContactAction.OPEN}),
        last_verified_at=NOW,
    )
    fact = ProcurementFact(
        fact_id="fact_deadline",
        predicate="submission_deadline",
        value="2026-09-01T12:00:00Z",
        origin=FactOrigin.SOURCE_FACT,
        provenance=provenance(),
    )
    opportunity = Opportunity(
        opportunity_id="opp_123456_2026",
        current_version=version(),
        title="Example tender",
        buyer_organisation="Example Contracting Authority",
        facts=(fact,),
        contact_channels=(channel,),
    )
    workspace = TenderWorkspace(
        workspace_id=WORKSPACE_ID,
        tenant_id=TENANT_ID,
        opportunity_id=opportunity.opportunity_id,
        opportunity_version=opportunity.current_version,
        subscriber_profile_version="subscriber-profile@1",
        assessment_version="opportunity-assessment@1",
        contact_channel_ids=(channel.channel_id,),
        created_by="usr_bid_manager",
        created_at=NOW,
    )

    assert workspace.state is WorkspaceState.CREATED
    assert channel.searchable_globally is False
    assert channel.exportable is False
    assert channel.marketing_use is False


def test_named_professional_channel_is_contextual_not_crm_data() -> None:
    channel = ProcurementContactChannel(
        channel_id="channel_named_email",
        opportunity_id="opp_123456_2026",
        source_notice_id="123456-2026",
        source_url="https://ted.europa.eu/en/notice/-/detail/123456-2026",
        channel_type=ContactChannelType.NAMED_PROFESSIONAL_EMAIL,
        organisation_name="Example Contracting Authority",
        contact_name="Published Procurement Officer",
        contact_role="Clarifications",
        endpoint="mailto:officer@example.eu",
        data_class=ContactDataClass.PROFESSIONAL_PERSONAL,
        policy_decision=ContactPolicyDecision.CONTEXTUAL,
        allowed_actions=frozenset(
            {
                ContactAction.REVEAL,
                ContactAction.COPY,
                ContactAction.COMPOSE_PROCEDURE_QUERY,
            }
        ),
        last_verified_at=NOW,
    )

    assert channel.policy_decision is ContactPolicyDecision.CONTEXTUAL
    assert channel.searchable_globally is False
    assert channel.exportable is False
    assert channel.marketing_use is False


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("searchable_globally", True),
        ("exportable", True),
        ("marketing_use", True),
    ],
)
def test_contact_channels_cannot_become_crm_or_marketing_data(
    field: str,
    value: bool,
) -> None:
    payload = {
        "channel_id": "channel_named_email",
        "opportunity_id": "opp_123456_2026",
        "source_notice_id": "123456-2026",
        "source_url": "https://ted.europa.eu/en/notice/-/detail/123456-2026",
        "channel_type": ContactChannelType.NAMED_PROFESSIONAL_EMAIL,
        "organisation_name": "Example Contracting Authority",
        "contact_name": "Published Procurement Officer",
        "endpoint": "mailto:officer@example.eu",
        "data_class": ContactDataClass.PROFESSIONAL_PERSONAL,
        "policy_decision": ContactPolicyDecision.CONTEXTUAL,
        "allowed_actions": [ContactAction.REVEAL],
        "last_verified_at": NOW,
        field: value,
    }
    with pytest.raises(ValidationError, match="CRM or marketing"):
        ProcurementContactChannel.model_validate(payload)


def test_ambiguous_personal_data_is_link_only_or_blocked() -> None:
    with pytest.raises(ValidationError, match="LINK_ONLY or BLOCK"):
        ProcurementContactChannel(
            channel_id="channel_ambiguous",
            opportunity_id="opp_123456_2026",
            source_notice_id="123456-2026",
            source_url="https://ted.europa.eu/en/notice/-/detail/123456-2026",
            channel_type=ContactChannelType.NAMED_PROFESSIONAL_EMAIL,
            organisation_name="Ambiguous operator",
            contact_name="Unknown legal form",
            endpoint="mailto:person@example.eu",
            data_class=ContactDataClass.AMBIGUOUS_PERSONAL,
            policy_decision=ContactPolicyDecision.CONTEXTUAL,
            allowed_actions=frozenset({ContactAction.REVEAL}),
            last_verified_at=NOW,
        )


def test_link_only_channel_allows_only_open() -> None:
    with pytest.raises(ValidationError, match="LINK_ONLY permits only OPEN"):
        ProcurementContactChannel(
            channel_id="channel_link",
            opportunity_id="opp_123456_2026",
            source_notice_id="123456-2026",
            source_url="https://ted.europa.eu/en/notice/-/detail/123456-2026",
            channel_type=ContactChannelType.SOURCE_LINK_ONLY,
            organisation_name="Example Contracting Authority",
            endpoint="https://ted.europa.eu/en/notice/-/detail/123456-2026",
            data_class=ContactDataClass.AMBIGUOUS_PERSONAL,
            policy_decision=ContactPolicyDecision.LINK_ONLY,
            allowed_actions=frozenset({ContactAction.OPEN, ContactAction.COPY}),
            last_verified_at=NOW,
        )


def test_axignal_inference_requires_supporting_facts() -> None:
    with pytest.raises(ValidationError, match="supporting facts"):
        ProcurementFact(
            fact_id="assessment_1",
            predicate="strategic_fit",
            value="HIGH",
            origin=FactOrigin.AXIGNAL_INFERENCE,
            provenance=None,
        )


def test_external_communication_requires_subscriber_approval_and_confirmation() -> None:
    with pytest.raises(ValidationError, match="subscriber approval"):
        Clarification(
            clarification_id="clar_1",
            tenant_id=TENANT_ID,
            workspace_id=WORKSPACE_ID,
            procedure_reference="ABC-2026-001",
            question="Please clarify the solvency threshold.",
            rationale="The threshold is ambiguous.",
            channel_id="channel_platform",
            state=ClarificationState.EXTERNAL_HANDOFF,
            created_by="usr_bid_manager",
            created_at=NOW,
            external_handoff_at=NOW,
        )

    sent = Clarification(
        clarification_id="clar_1",
        tenant_id=TENANT_ID,
        workspace_id=WORKSPACE_ID,
        procedure_reference="ABC-2026-001",
        question="Please clarify the solvency threshold.",
        rationale="The threshold is ambiguous.",
        channel_id="channel_platform",
        state=ClarificationState.SENT_CONFIRMED,
        created_by="usr_bid_manager",
        created_at=NOW,
        approved_by="usr_bid_manager",
        approved_at=NOW,
        external_handoff_at=NOW,
        sent_confirmed_by="usr_bid_manager",
        sent_at=NOW,
    )
    assert sent.state is ClarificationState.SENT_CONFIRMED


def test_presented_workspace_requires_subscriber_confirmation() -> None:
    with pytest.raises(ValidationError, match="subscriber confirmation"):
        TenderWorkspace(
            workspace_id=WORKSPACE_ID,
            tenant_id=TENANT_ID,
            opportunity_id="opp_123456_2026",
            opportunity_version=version(),
            subscriber_profile_version="subscriber-profile@1",
            assessment_version="opportunity-assessment@1",
            state=WorkspaceState.PRESENTED_EXTERNALLY,
            created_by="usr_bid_manager",
            created_at=NOW,
        )


def test_audit_event_does_not_replicate_contact_endpoint() -> None:
    with pytest.raises(ValidationError, match="must not replicate"):
        AuditEvent(
            event_id="audit_1",
            tenant_id=TENANT_ID,
            workspace_id=WORKSPACE_ID,
            actor_id="usr_bid_manager",
            action="contact_channel_opened",
            object_type="ProcurementContactChannel",
            object_id="channel_named_email",
            occurred_at=NOW,
            details={"contact_email": "officer@example.eu"},
        )
