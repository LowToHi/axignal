#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import p24_acceptance_reference as reference

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "data/acceptance/global-acceptance-paid-evidence-launch-runtime.v0.1.json"
FIXTURES = ROOT / "data/acceptance/p24-conformance-fixtures.v0.1.json"
CASES = ROOT / "data/acceptance/p24-adversarial-cases.v0.1.json"
EVIDENCE_TEMPLATE = ROOT / "data/acceptance/p24-evidence-manifest-template.v0.1.json"
P22_RUNTIME = ROOT / "data/production/production-slo-dr-security-runtime.v0.1.json"
P23_HEAD = "dec5473ad590fdb5de941d6b383e2ab01136befe"


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


runtime = load(RUNTIME)
fixtures = load(FIXTURES)
cases = load(CASES)
evidence_template = load(EVIDENCE_TEMPLATE)
p22_runtime = load(P22_RUNTIME)

assert runtime["task_id"] == "AX-GE2E-P24-T01"
assert runtime["baseline_sha"] == P23_HEAD
assert runtime["state"] == "BLOCKED_PENDING_REAL_EVIDENCE"
assert runtime["engineering_evidence_ready"] is True

for field in (
    "global_acceptance_authorised",
    "controlled_live_pilot_authorised",
    "public_launch_authorised",
    "general_availability_authorised",
    "stripe_live_authorised",
    "paid_media_authorised",
    "external_action_authorised",
    "canonical_activation_authorised",
):
    assert runtime[field] is False, field

assert len(runtime["input_contract_bindings"]) == 7
assert len(runtime["modules"]) == 8
assert len(runtime["record_types"]) == 32
assert len(runtime["invariants"]) == 50
assert len(runtime["lifecycle_states"]) == 12
assert len(runtime["pipeline_stages"]) == 11
assert len(runtime["global_journeys"]) == 10
assert len(runtime["readiness_gates"]) == 22
assert len(runtime["authority_classes"]) == 9
assert len(runtime["risk_classes"]) == 10
assert len(runtime["stop_conditions"]) == 10
assert len(fixtures["fixtures"]) == 24
assert len(cases["cases"]) == 24

p22_transitive = {
    item["task_id"]: item["path"] for item in p22_runtime["input_contract_bindings"]
}
for binding in runtime["input_contract_bindings"]:
    assert binding["engineering_evidence_ready"] is True
    assert binding["activation_authorised"] is False
    candidate = ROOT / binding["path"]
    if candidate.is_file():
        continue
    task_id = binding["task_id"]
    assert task_id in {"AX-GE2E-P17-T01", "AX-GE2E-P18-T01"}, binding
    assert p22_transitive.get(task_id) == binding["path"], binding

assert all(item["evidence_state"] == "MISSING" for item in runtime["global_journeys"])
paid = runtime["paid_evidence_contract"]
assert len(paid["levels"]) == 3
assert paid["minimum_independent_paid_tenants_for_bounded_launch"] == 1
assert paid["minimum_completed_value_workflows_per_tenant"] == 1
assert paid["minimum_observation_days"] == 14
assert paid["founder_or_related_party_payment_counts_as_customer_evidence"] is False
assert paid["test_clock_counts_as_real_renewal"] is False
assert paid["evidence_state"] == "MISSING"

assert {item["mode"] for item in runtime["launch_modes"]} == {
    "NO_GO",
    "CONTROLLED_LIVE_PILOT",
    "BOUNDED_PUBLIC_LAUNCH",
    "GENERAL_AVAILABILITY",
}

assert evidence_template["status"] == "TEMPLATE_NOT_EVIDENCE"
assert evidence_template["contains_secrets"] is False
assert evidence_template["contains_private_customer_payloads"] is False
assert evidence_template["launch_decision"] == "NO_GO"
for section in ("sandbox_billing", "controlled_live_payment", "independent_paid_customer"):
    assert evidence_template[section]["status"] == "MISSING"

for fixture in fixtures["fixtures"]:
    assert fixture["expected_decision"] == "PASS_ENGINEERING_ONLY"
    assert fixture["launch_mode"] == "NO_GO"
    assert fixture["real_evidence"] is False
    assert fixture["paid_customer"] is False
    assert fixture["human_launch_authority"] is False
    assert fixture["evidence_preserved"] is True

assert all(value == 0 for value in cases["required_zero_deltas"].values())
assert all(
    case["expected_decision"] == "DENY_OR_QUARANTINE" for case in cases["cases"]
)

assert reference.exact_head_decision(
    expected_head="a", observed_head="a", artifact_digest_match=True, ci_pass=True
) == "PASS"
assert reference.exact_head_decision(
    expected_head="a", observed_head="b", artifact_digest_match=True, ci_pass=True
) == "DENY"
assert reference.exact_head_decision(
    expected_head="a", observed_head="a", artifact_digest_match=False, ci_pass=True
) == "QUARANTINE"

assert reference.journey_evidence_decision(
    required_environment="STAGING",
    observed_environment="STAGING",
    completed=True,
    evidence_preserved=True,
    contains_secret_or_private_payload=False,
) == "PASS"
assert reference.journey_evidence_decision(
    required_environment="STAGING",
    observed_environment="FIXTURE",
    completed=True,
    evidence_preserved=True,
    contains_secret_or_private_payload=False,
) == "DENY"
assert reference.journey_evidence_decision(
    required_environment="STAGING",
    observed_environment="STAGING",
    completed=True,
    evidence_preserved=True,
    contains_secret_or_private_payload=True,
) == "QUARANTINE"

assert reference.renewal_evidence_decision(
    later_billing_period=True,
    provider_delivered_event=True,
    settled=True,
    used_test_clock=True,
    require_real_period=True,
) == "DENY"
assert reference.renewal_evidence_decision(
    later_billing_period=True,
    provider_delivered_event=True,
    settled=True,
    used_test_clock=True,
    require_real_period=False,
) == "PASS"

live_kwargs = dict(
    restricted_live_key=True,
    live_product_and_price=True,
    real_charge=True,
    settled_invoice=True,
    signed_live_webhook=True,
    ledger_reconciled=True,
    entitlement_matches=True,
    cancellation_or_refund_verified=True,
)
assert reference.controlled_live_payment_decision(**live_kwargs) == "PASS"
assert reference.controlled_live_payment_decision(
    **{**live_kwargs, "settled_invoice": False}
) == "DENY"

customer_kwargs = dict(
    unrelated_external_tenant=True,
    terms_accepted=True,
    privacy_accepted=True,
    settled_invoice=True,
    signed_provider_events=True,
    ledger_reconciled=True,
    entitlement_matches=True,
    completed_value_workflows=1,
    minimum_value_workflows=1,
    observed_days=14,
    minimum_observation_days=14,
    active_dispute=False,
    refunded_during_observation=False,
)
assert reference.independent_paid_customer_decision(**customer_kwargs) == "PASS"
assert reference.independent_paid_customer_decision(
    **{**customer_kwargs, "unrelated_external_tenant": False}
) == "DENY"

required_authorities = (
    "PRODUCT_ACCEPTANCE_AUTHORITY",
    "SECURITY_ACCEPTANCE_AUTHORITY",
    "SRE_RELEASE_AUTHORITY",
    "FINANCE_BILLING_AUTHORITY",
    "LEGAL_PRIVACY_AUTHORITY",
)
approvals = [
    reference.Approval(authority=item, manifest_digest="sha256:manifest", approved=True)
    for item in required_authorities
]
approval_decision = reference.approval_set_decision(
    required_authorities=required_authorities,
    approvals=approvals,
    acceptance_manifest_digest="sha256:manifest",
)
assert approval_decision == "PASS"
assert reference.approval_set_decision(
    required_authorities=required_authorities,
    approvals=approvals,
    acceptance_manifest_digest="sha256:different",
) == "DENY"

all_gates = {gate: "PASS" for gate in runtime["readiness_gates"]}
assert reference.launch_mode_decision(
    requested_mode="CONTROLLED_LIVE_PILOT",
    gates=all_gates,
    active_stop_conditions=[],
    manifest_approval=approval_decision,
) == "CONTROLLED_LIVE_PILOT"
assert reference.launch_mode_decision(
    requested_mode="BOUNDED_PUBLIC_LAUNCH",
    gates=all_gates,
    active_stop_conditions=[],
    manifest_approval=approval_decision,
) == "BOUNDED_PUBLIC_LAUNCH"
assert reference.launch_mode_decision(
    requested_mode="GENERAL_AVAILABILITY",
    gates=all_gates,
    active_stop_conditions=[],
    manifest_approval=approval_decision,
) == "BOUNDED_PUBLIC_LAUNCH"

ga_gates = {
    **all_gates,
    "RENEWAL_EVIDENCE_PASS": "PASS",
    "COHORT_STABILITY_PASS": "PASS",
    "SUPPORT_READINESS_PASS": "PASS",
}
assert reference.launch_mode_decision(
    requested_mode="GENERAL_AVAILABILITY",
    gates=ga_gates,
    active_stop_conditions=[],
    manifest_approval=approval_decision,
) == "GENERAL_AVAILABILITY"
assert reference.launch_mode_decision(
    requested_mode="CONTROLLED_LIVE_PILOT",
    gates=all_gates,
    active_stop_conditions=["critical_security_finding"],
    manifest_approval=approval_decision,
) == "NO_GO"

assert reference.cohort_expansion_decision(
    current_tenants=5,
    requested_tenants=10,
    mode_cap=25,
    slo_healthy=True,
    error_budget_frozen=False,
    fast_burn_alert=False,
    active_stop_conditions=[],
    human_approved=True,
) == "PASS"
assert reference.cohort_expansion_decision(
    current_tenants=5,
    requested_tenants=30,
    mode_cap=25,
    slo_healthy=True,
    error_budget_frozen=False,
    fast_burn_alert=False,
    active_stop_conditions=[],
    human_approved=True,
) == "DENY"

assert reference.rollback_decision(
    stop_condition_active=True,
    rollback_artifact_verified=True,
    billing_evidence_preserved=True,
    audit_history_preserved=True,
    entitlements_reconciled_to_provider=True,
) == "PASS"
assert reference.rollback_decision(
    stop_condition_active=True,
    rollback_artifact_verified=True,
    billing_evidence_preserved=False,
    audit_history_preserved=True,
    entitlements_reconciled_to_provider=True,
) == "QUARANTINE"

print(
    json.dumps(
        {
            "status": "PASS_ENGINEERING_CONTRACT_ONLY",
            "task_id": runtime["task_id"],
            "baseline_sha": runtime["baseline_sha"],
            "upstream_bindings": len(runtime["input_contract_bindings"]),
            "global_journeys": len(runtime["global_journeys"]),
            "readiness_gates": len(runtime["readiness_gates"]),
            "conformance_fixtures": len(fixtures["fixtures"]),
            "adversarial_cases": len(cases["cases"]),
            "launch_decision": "NO_GO",
            "real_paid_evidence": "MISSING",
            "public_launch_authorised": runtime["public_launch_authorised"],
        },
        sort_keys=True,
    )
)
