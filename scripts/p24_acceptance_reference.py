from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal

Decision = Literal["PASS", "DENY", "QUARANTINE", "NO_GO"]
LaunchMode = Literal[
    "NO_GO",
    "CONTROLLED_LIVE_PILOT",
    "BOUNDED_PUBLIC_LAUNCH",
    "GENERAL_AVAILABILITY",
]


@dataclass(frozen=True)
class Approval:
    authority: str
    manifest_digest: str
    approved: bool
    expired: bool = False


def exact_head_decision(
    *,
    expected_head: str,
    observed_head: str,
    artifact_digest_match: bool,
    ci_pass: bool,
) -> Decision:
    if expected_head != observed_head:
        return "DENY"
    if not artifact_digest_match:
        return "QUARANTINE"
    return "PASS" if ci_pass else "DENY"


def journey_evidence_decision(
    *,
    required_environment: str,
    observed_environment: str,
    completed: bool,
    evidence_preserved: bool,
    contains_secret_or_private_payload: bool,
) -> Decision:
    if required_environment != observed_environment:
        return "DENY"
    if contains_secret_or_private_payload:
        return "QUARANTINE"
    if not completed or not evidence_preserved:
        return "DENY"
    return "PASS"


def renewal_evidence_decision(
    *,
    later_billing_period: bool,
    provider_delivered_event: bool,
    settled: bool,
    used_test_clock: bool,
    require_real_period: bool,
) -> Decision:
    if require_real_period and used_test_clock:
        return "DENY"
    if not later_billing_period or not provider_delivered_event or not settled:
        return "DENY"
    return "PASS"


def controlled_live_payment_decision(
    *,
    restricted_live_key: bool,
    live_product_and_price: bool,
    real_charge: bool,
    settled_invoice: bool,
    signed_live_webhook: bool,
    ledger_reconciled: bool,
    entitlement_matches: bool,
    cancellation_or_refund_verified: bool,
) -> Decision:
    checks = (
        restricted_live_key,
        live_product_and_price,
        real_charge,
        settled_invoice,
        signed_live_webhook,
        ledger_reconciled,
        entitlement_matches,
        cancellation_or_refund_verified,
    )
    return "PASS" if all(checks) else "DENY"


def independent_paid_customer_decision(
    *,
    unrelated_external_tenant: bool,
    terms_accepted: bool,
    privacy_accepted: bool,
    settled_invoice: bool,
    signed_provider_events: bool,
    ledger_reconciled: bool,
    entitlement_matches: bool,
    completed_value_workflows: int,
    minimum_value_workflows: int,
    observed_days: int,
    minimum_observation_days: int,
    active_dispute: bool,
    refunded_during_observation: bool,
) -> Decision:
    if active_dispute or refunded_during_observation:
        return "DENY"
    checks = (
        unrelated_external_tenant,
        terms_accepted,
        privacy_accepted,
        settled_invoice,
        signed_provider_events,
        ledger_reconciled,
        entitlement_matches,
        completed_value_workflows >= minimum_value_workflows,
        observed_days >= minimum_observation_days,
    )
    return "PASS" if all(checks) else "DENY"


def approval_set_decision(
    *,
    required_authorities: Sequence[str],
    approvals: Sequence[Approval],
    acceptance_manifest_digest: str,
) -> Decision:
    by_authority = {approval.authority: approval for approval in approvals}
    for authority in required_authorities:
        approval = by_authority.get(authority)
        if approval is None:
            return "DENY"
        if not approval.approved or approval.expired:
            return "DENY"
        if approval.manifest_digest != acceptance_manifest_digest:
            return "DENY"
    return "PASS"


def all_gates_pass(gates: Mapping[str, str], required_gates: Sequence[str]) -> bool:
    return all(gates.get(gate) == "PASS" for gate in required_gates)


def launch_mode_decision(
    *,
    requested_mode: LaunchMode,
    gates: Mapping[str, str],
    active_stop_conditions: Sequence[str],
    manifest_approval: Decision,
) -> LaunchMode:
    if active_stop_conditions or manifest_approval != "PASS":
        return "NO_GO"

    pilot_gates = (
        "P17_EXACT_HEAD_PASS",
        "P18_EXACT_HEAD_PASS",
        "P19_EXACT_HEAD_PASS",
        "P20_EXACT_HEAD_PASS",
        "P21_SANDBOX_E2E_PASS",
        "P22_PRODUCTION_READINESS_PASS",
        "P23_REAL_UX_PASS",
        "GLOBAL_JOURNEYS_PASS",
        "SECURITY_ACCEPTANCE_PASS",
        "DR_RESTORE_PASS",
        "SLO_HEALTH_PASS",
        "ACCESSIBILITY_PASS",
        "PRIVACY_LEGAL_PASS",
        "LIVE_BILLING_READINESS_PASS",
        "CONTROLLED_LIVE_PAYMENT_PASS",
        "FINANCE_RECONCILIATION_PASS",
        "PRODUCT_APPROVAL_PASS",
        "SECURITY_APPROVAL_PASS",
        "SRE_APPROVAL_PASS",
        "FINANCE_APPROVAL_PASS",
        "LEGAL_APPROVAL_PASS",
    )
    if not all_gates_pass(gates, pilot_gates):
        return "NO_GO"
    if requested_mode == "CONTROLLED_LIVE_PILOT":
        return "CONTROLLED_LIVE_PILOT"

    public_gates = (*pilot_gates, "INDEPENDENT_PAID_CUSTOMER_PASS")
    if not all_gates_pass(gates, public_gates):
        return "CONTROLLED_LIVE_PILOT"
    if requested_mode == "BOUNDED_PUBLIC_LAUNCH":
        return "BOUNDED_PUBLIC_LAUNCH"

    ga_gates = (
        *public_gates,
        "RENEWAL_EVIDENCE_PASS",
        "COHORT_STABILITY_PASS",
        "SUPPORT_READINESS_PASS",
    )
    if not all_gates_pass(gates, ga_gates):
        return "BOUNDED_PUBLIC_LAUNCH"
    return "GENERAL_AVAILABILITY"


def cohort_expansion_decision(
    *,
    current_tenants: int,
    requested_tenants: int,
    mode_cap: int | None,
    slo_healthy: bool,
    error_budget_frozen: bool,
    fast_burn_alert: bool,
    active_stop_conditions: Sequence[str],
    human_approved: bool,
) -> Decision:
    if requested_tenants <= current_tenants:
        return "DENY"
    if mode_cap is not None and requested_tenants > mode_cap:
        return "DENY"
    if not slo_healthy or error_budget_frozen or fast_burn_alert:
        return "DENY"
    if active_stop_conditions or not human_approved:
        return "DENY"
    return "PASS"


def rollback_decision(
    *,
    stop_condition_active: bool,
    rollback_artifact_verified: bool,
    billing_evidence_preserved: bool,
    audit_history_preserved: bool,
    entitlements_reconciled_to_provider: bool,
) -> Decision:
    if not stop_condition_active:
        return "DENY"
    checks = (
        rollback_artifact_verified,
        billing_evidence_preserved,
        audit_history_preserved,
        entitlements_reconciled_to_provider,
    )
    return "PASS" if all(checks) else "QUARANTINE"
