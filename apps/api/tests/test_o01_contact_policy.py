from datetime import UTC, datetime

import pytest

from axignal_api.o01_contact_policy import (
    O01_CONTACT_POLICY_VERSION,
    evaluate_o01_contact_policy,
    policy_matrix,
    validate_o01_contact_channel,
)
from axignal_api.procurement_domain import (
    ContactAction,
    ContactChannelType,
    ContactDataClass,
    ContactPolicyDecision,
    ProcurementContactChannel,
)

NOW = datetime(2026, 8, 1, 20, 0, tzinfo=UTC)


def channel(**overrides: object) -> ProcurementContactChannel:
    values: dict[str, object] = {
        "channel_id": "channel_1",
        "opportunity_id": "opportunity_1",
        "source_notice_id": "notice_1",
        "source_url": "https://ted.europa.eu/en/notice/-/detail/1",
        "channel_type": ContactChannelType.PROCUREMENT_PLATFORM,
        "organisation_name": "Contracting Authority",
        "endpoint": "https://buyer.example.test/procurement/1",
        "data_class": ContactDataClass.INSTITUTIONAL,
        "policy_decision": ContactPolicyDecision.ALLOW,
        "allowed_actions": frozenset({ContactAction.OPEN}),
        "last_verified_at": NOW,
    }
    values.update(overrides)
    return ProcurementContactChannel.model_validate(values)


def test_policy_matrix_is_total_and_versioned() -> None:
    assert O01_CONTACT_POLICY_VERSION == "o01-ted-contact-policy@0.2.0"
    outcomes = policy_matrix()
    assert {item.data_class for item in outcomes} == set(ContactDataClass)
    assert {item.decision for item in outcomes} == {
        ContactPolicyDecision.ALLOW,
        ContactPolicyDecision.CONTEXTUAL,
        ContactPolicyDecision.LINK_ONLY,
        ContactPolicyDecision.BLOCK,
    }


@pytest.mark.parametrize(
    ("data_class", "channel_type", "decision"),
    [
        (
            ContactDataClass.INSTITUTIONAL,
            ContactChannelType.PROCUREMENT_PLATFORM,
            ContactPolicyDecision.ALLOW,
        ),
        (
            ContactDataClass.FUNCTIONAL_NON_PERSONAL,
            ContactChannelType.FUNCTIONAL_EMAIL,
            ContactPolicyDecision.ALLOW,
        ),
        (
            ContactDataClass.PROFESSIONAL_PERSONAL,
            ContactChannelType.NAMED_PROFESSIONAL_EMAIL,
            ContactPolicyDecision.CONTEXTUAL,
        ),
        (
            ContactDataClass.AMBIGUOUS_PERSONAL,
            ContactChannelType.SOURCE_LINK_ONLY,
            ContactPolicyDecision.LINK_ONLY,
        ),
    ],
)
def test_expected_policy_decisions(
    data_class: ContactDataClass,
    channel_type: ContactChannelType,
    decision: ContactPolicyDecision,
) -> None:
    outcome = evaluate_o01_contact_policy(
        data_class=data_class,
        channel_type=channel_type,
    )
    assert outcome.decision is decision


def test_named_professional_contact_is_contextual_and_opportunity_scoped() -> None:
    professional = channel(
        channel_type=ContactChannelType.NAMED_PROFESSIONAL_EMAIL,
        contact_name="Procurement Officer",
        endpoint="mailto:officer@example.test",
        data_class=ContactDataClass.PROFESSIONAL_PERSONAL,
        policy_decision=ContactPolicyDecision.CONTEXTUAL,
        allowed_actions=frozenset(
            {
                ContactAction.REVEAL,
                ContactAction.COPY,
                ContactAction.COMPOSE_PROCEDURE_QUERY,
            }
        ),
    )
    outcome = validate_o01_contact_channel(professional)
    assert outcome.persistence_mode.endswith("PENDING_TYPED_PRIVACY_DECISION")
    assert "cross-opportunity reuse" in " ".join(outcome.conditions)


def test_ambiguous_personal_data_degrades_to_source_link_only() -> None:
    ambiguous = channel(
        channel_type=ContactChannelType.SOURCE_LINK_ONLY,
        endpoint="https://ted.europa.eu/en/notice/-/detail/1",
        data_class=ContactDataClass.AMBIGUOUS_PERSONAL,
        policy_decision=ContactPolicyDecision.LINK_ONLY,
        allowed_actions=frozenset({ContactAction.OPEN}),
    )
    outcome = validate_o01_contact_channel(ambiguous)
    assert outcome.persistence_mode == "SOURCE_LINK_ONLY_NO_ENDPOINT_PERSISTENCE"


def test_overprivileged_or_misclassified_channels_fail_closed() -> None:
    with pytest.raises(ValueError, match="not permitted"):
        evaluate_o01_contact_policy(
            data_class=ContactDataClass.INSTITUTIONAL,
            channel_type=ContactChannelType.NAMED_PROFESSIONAL_EMAIL,
        )

    with pytest.raises(ValueError, match="Named professional contacts require CONTEXTUAL"):
        channel(
            channel_type=ContactChannelType.NAMED_PROFESSIONAL_EMAIL,
            contact_name="Procurement Officer",
            endpoint="mailto:officer@example.test",
            data_class=ContactDataClass.PROFESSIONAL_PERSONAL,
            policy_decision=ContactPolicyDecision.ALLOW,
            allowed_actions=frozenset({ContactAction.COPY}),
        )


def test_non_procurement_and_crm_use_remain_forbidden() -> None:
    with pytest.raises(ValueError, match="CRM or marketing"):
        channel(marketing_use=True)

    wrong_purpose = channel(purpose="SALES_OUTREACH")
    with pytest.raises(ValueError, match="procurement communication"):
        validate_o01_contact_channel(wrong_purpose)
