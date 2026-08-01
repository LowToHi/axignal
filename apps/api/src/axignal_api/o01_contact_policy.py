from __future__ import annotations

from dataclasses import dataclass

from axignal_api.procurement_domain import (
    ContactChannelType,
    ContactDataClass,
    ContactPolicyDecision,
    ProcurementContactChannel,
)

O01_CONTACT_POLICY_VERSION = "o01-ted-contact-policy@0.2.0"


@dataclass(frozen=True, slots=True)
class ContactPolicyOutcome:
    data_class: ContactDataClass
    decision: ContactPolicyDecision
    permitted_channel_types: frozenset[ContactChannelType]
    persistence_mode: str
    source_link_required: bool
    conditions: tuple[str, ...]


_POLICY: dict[ContactDataClass, ContactPolicyOutcome] = {
    ContactDataClass.INSTITUTIONAL: ContactPolicyOutcome(
        data_class=ContactDataClass.INSTITUTIONAL,
        decision=ContactPolicyDecision.ALLOW,
        permitted_channel_types=frozenset(
            {
                ContactChannelType.PROCUREMENT_PLATFORM,
                ContactChannelType.BUYER_PROFILE,
                ContactChannelType.OFFICIAL_FORM,
            }
        ),
        persistence_mode="OPPORTUNITY_SCOPED_REFERENCE_AFTER_TYPED_APPROVAL",
        source_link_required=True,
        conditions=(
            "official procurement purpose only",
            "source provenance required",
            "no marketing, export or global person search",
        ),
    ),
    ContactDataClass.FUNCTIONAL_NON_PERSONAL: ContactPolicyOutcome(
        data_class=ContactDataClass.FUNCTIONAL_NON_PERSONAL,
        decision=ContactPolicyDecision.ALLOW,
        permitted_channel_types=frozenset(
            {
                ContactChannelType.FUNCTIONAL_EMAIL,
                ContactChannelType.OFFICIAL_PHONE,
            }
        ),
        persistence_mode="OPPORTUNITY_SCOPED_REFERENCE_AFTER_TYPED_APPROVAL",
        source_link_required=True,
        conditions=(
            "endpoint must represent an organisation or function",
            "source provenance required",
            "no marketing, export or cross-opportunity reuse",
        ),
    ),
    ContactDataClass.PROFESSIONAL_PERSONAL: ContactPolicyOutcome(
        data_class=ContactDataClass.PROFESSIONAL_PERSONAL,
        decision=ContactPolicyDecision.CONTEXTUAL,
        permitted_channel_types=frozenset(
            {
                ContactChannelType.NAMED_PROFESSIONAL_EMAIL,
                ContactChannelType.NAMED_PROFESSIONAL_PHONE,
            }
        ),
        persistence_mode="OPPORTUNITY_SCOPED_REFERENCE_PENDING_TYPED_PRIVACY_DECISION",
        source_link_required=True,
        conditions=(
            "published in the source for the same procurement procedure",
            "strictly necessary for procedure-specific communication",
            "tenant and opportunity scope required",
            "no marketing, export, global search or cross-opportunity reuse",
            "endpoint and message body excluded from audit payloads",
            "retention and deletion require typed Privacy/Data Rights approval",
        ),
    ),
    ContactDataClass.AMBIGUOUS_PERSONAL: ContactPolicyOutcome(
        data_class=ContactDataClass.AMBIGUOUS_PERSONAL,
        decision=ContactPolicyDecision.LINK_ONLY,
        permitted_channel_types=frozenset({ContactChannelType.SOURCE_LINK_ONLY}),
        persistence_mode="SOURCE_LINK_ONLY_NO_ENDPOINT_PERSISTENCE",
        source_link_required=True,
        conditions=(
            "do not persist the ambiguous endpoint",
            "open only the source-native notice or buyer profile",
            "reclassify or block before any direct communication action",
        ),
    ),
    ContactDataClass.BLOCKED: ContactPolicyOutcome(
        data_class=ContactDataClass.BLOCKED,
        decision=ContactPolicyDecision.BLOCK,
        permitted_channel_types=frozenset(),
        persistence_mode="DENIED",
        source_link_required=False,
        conditions=(
            "do not persist, index, search, reveal or act on the endpoint",
            "record aggregate rejection evidence only",
        ),
    ),
}


def evaluate_o01_contact_policy(
    *,
    data_class: ContactDataClass,
    channel_type: ContactChannelType,
) -> ContactPolicyOutcome:
    outcome = _POLICY[data_class]
    if channel_type not in outcome.permitted_channel_types:
        if data_class is ContactDataClass.BLOCKED:
            raise ValueError("Blocked contact data has no permitted channel type")
        raise ValueError(
            f"{channel_type} is not permitted for O01 data class {data_class}"
        )
    return outcome


def validate_o01_contact_channel(
    channel: ProcurementContactChannel,
) -> ContactPolicyOutcome:
    outcome = evaluate_o01_contact_policy(
        data_class=channel.data_class,
        channel_type=channel.channel_type,
    )
    if channel.policy_decision is not outcome.decision:
        raise ValueError(
            "Contact policy decision does not match the O01 contextual policy"
        )
    if channel.purpose != "PROCUREMENT_PROCEDURE_COMMUNICATION":
        raise ValueError("O01 contact channels are limited to procurement communication")
    if channel.searchable_globally or channel.exportable or channel.marketing_use:
        raise ValueError("O01 contact channels cannot become CRM or marketing data")
    return outcome


def policy_matrix() -> tuple[ContactPolicyOutcome, ...]:
    return tuple(_POLICY[data_class] for data_class in ContactDataClass)
