#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "data/commercial/commercial-runtime-pricing-stripe-runtime.v0.1.json"
FIXTURES = ROOT / "data/commercial/p21-conformance-fixtures.v0.1.json"
CASES = ROOT / "data/commercial/p21-adversarial-cases.v0.1.json"
RUNTIME_SCHEMA = ROOT / "schemas/commercial-runtime-pricing-stripe-runtime.schema.json"
FIXTURE_SCHEMA = ROOT / "schemas/commercial-runtime-pricing-stripe-fixtures.schema.json"
CASE_SCHEMA = ROOT / "schemas/commercial-runtime-pricing-stripe-cases.schema.json"
REFERENCE = ROOT / "scripts/p21_commercial_reference.py"
P20_HEAD = "87b30a1035b557040dd33c5f0acedc62d0ebfa93"


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(document: Any, schema: Any) -> None:
    errors = sorted(
        Draft202012Validator(schema).iter_errors(document),
        key=lambda error: list(error.path),
    )
    assert not errors, [error.message for error in errors]


spec = importlib.util.spec_from_file_location("p21_reference", REFERENCE)
assert spec and spec.loader
reference = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reference)

runtime = load(RUNTIME)
fixtures = load(FIXTURES)
cases = load(CASES)
validate(runtime, load(RUNTIME_SCHEMA))
validate(fixtures, load(FIXTURE_SCHEMA))
validate(cases, load(CASE_SCHEMA))

assert runtime["baseline_sha"] == P20_HEAD
assert runtime["state"] == "BLOCKED"
assert runtime["engineering_evidence_ready"] is True
for field in (
    "canonical_activation_authorised",
    "commercial_activation_authorised",
    "public_launch_authorised",
    "live_payments_authorised",
    "external_action_authorised",
    "new_sources_authorised",
):
    assert runtime[field] is False, field

assert len(runtime["input_contract_bindings"]) == 5
assert len(runtime["modules"]) == 8
assert len(runtime["record_types"]) == 32
assert len(runtime["invariants"]) == 48
assert len(runtime["lifecycle_states"]) == 12
assert len(runtime["pipeline_stages"]) == 11
assert len(runtime["package_classes"]) == 10
assert len(runtime["price_dimensions"]) == 10
assert len(runtime["entitlement_classes"]) == 10
assert len(runtime["payment_states"]) == 10
assert len(runtime["cancellation_states"]) == 10
assert len(runtime["tax_classes"]) == 8
assert len(runtime["cost_classes"]) == 10
assert len(runtime["authority_classes"]) == 8
assert len(runtime["risk_classes"]) == 10
assert len(runtime["readiness_gates"]) == 12
assert len(runtime["rights_dimensions"]) == 10
assert len(fixtures["fixtures"]) == 40
assert len(cases["cases"]) == 72

for binding in runtime["input_contract_bindings"]:
    assert binding["head_sha"] == P20_HEAD
    assert binding["engineering_evidence_ready"] is True
    assert binding["canonical_activation_authorised"] is False
    assert binding["commercial_activation_authorised"] is False
    assert (ROOT / binding["path"]).is_file(), binding["path"]

pricing = runtime["pricing_contract"]
assert pricing["status"] == "CANDIDATE_ONLY"
assert pricing["price_source_of_truth"] == "SERVER_SIDE_VERSIONED_PRICE_BOOK"
assert pricing["stripe_price_ids"] == "ENVIRONMENT_BINDINGS_ONLY"
assert all(plan["commercial_activation_authorised"] is False for plan in pricing["plans"])
assert {plan["plan_code"] for plan in pricing["plans"]} == {
    "CONTROLLED_TRIAL_7D",
    "PROFESSIONAL_MONTHLY",
    "TEAM_MONTHLY",
    "ENTERPRISE_CONTRACT",
}

stripe = runtime["stripe_contract"]
assert stripe["api_version"] == "2026-06-24.dahlia"
assert stripe["mode"] == "SANDBOX_CONTRACT_ONLY"
assert stripe["credential_policy"] == "RESTRICTED_API_KEY_REFERENCE_ONLY"
assert stripe["dynamic_payment_methods"] is True
assert stripe["hardcoded_payment_method_types"] is False
assert stripe["webhook_signature_required"] is True
assert stripe["event_id_idempotency_required"] is True
assert stripe["livemode_authorised"] is False
assert stripe["production_keys_present"] is False
assert stripe["automatic_tax_requires_active_registration"] is True

economics = runtime["economics_contract"]
threshold = economics["candidate_thresholds"]["contribution_margin_floor_bps"]
assert threshold == 5500
scenario_statuses = {item["scenario_id"]: item["status"] for item in economics["scenarios"]}
assert scenario_statuses["PROFESSIONAL_REFERENCE"] == "PASS_CANDIDATE"
assert scenario_statuses["TEAM_REFERENCE"] == "PASS_CANDIDATE"
assert scenario_statuses["PROFESSIONAL_STRESS"] == "BLOCK_NEGATIVE_ECONOMIC_GATE"

server_mapping = {
    "PROFESSIONAL_MONTHLY": {
        "currency": "EUR",
        "provider_price_id": "price_sandbox_professional",
        "amount_minor": 14900,
        "status": "ACTIVE_SANDBOX",
    }
}
decision = reference.server_price_decision(
    requested_plan_code="PROFESSIONAL_MONTHLY",
    client_price_id="price_sandbox_professional",
    server_mapping=server_mapping,
    currency="EUR",
)
assert decision["decision"] == "ALLOW_CHECKOUT_REQUEST"
tampered = reference.server_price_decision(
    requested_plan_code="PROFESSIONAL_MONTHLY",
    client_price_id="price_attacker",
    server_mapping=server_mapping,
    currency="EUR",
)
assert tampered == {"decision": "DENY", "reason": "client_price_tampering"}

event = reference.provider_event_decision(
    signature_valid=True,
    event_id="evt_001",
    seen_event_ids=set(),
    provider_account_match=True,
    livemode=False,
    expected_livemode=False,
    event_created_at=100,
    last_applied_created_at=99,
)
assert event["decision"] == "APPLY_TO_LEDGER"
duplicate = reference.provider_event_decision(
    signature_valid=True,
    event_id="evt_001",
    seen_event_ids={"evt_001"},
    provider_account_match=True,
    livemode=False,
    expected_livemode=False,
    event_created_at=100,
    last_applied_created_at=99,
)
assert duplicate["decision"] == "IGNORE_IDEMPOTENT"
assert reference.provider_event_decision(
    signature_valid=False,
    event_id="evt_bad",
    seen_event_ids=set(),
    provider_account_match=True,
    livemode=False,
    expected_livemode=False,
    event_created_at=100,
    last_applied_created_at=None,
)["decision"] == "QUARANTINE"

assert reference.derive_entitlement_state(
    subscription_state="ACTIVE",
    invoice_state="PAID_VERIFIED",
    tenant_active=True,
    policy_current=True,
    rights_current=True,
) == "ACTIVE_LIMITED"
assert reference.derive_entitlement_state(
    subscription_state="PAST_DUE",
    invoice_state="PAST_DUE",
    tenant_active=True,
    policy_current=True,
    rights_current=True,
) == "SUSPENDED"
assert reference.derive_entitlement_state(
    subscription_state="ACTIVE",
    invoice_state="PAID_VERIFIED",
    tenant_active=True,
    policy_current=False,
    rights_current=True,
) == "DENY"

assert reference.cancellation_decision(
    request_id="cancel-001",
    seen_request_ids=set(),
    mode="PERIOD_END",
    human_approved=False,
)["decision"] == "CANCEL_AT_PERIOD_END"
assert reference.cancellation_decision(
    request_id="cancel-002",
    seen_request_ids=set(),
    mode="IMMEDIATE",
    human_approved=False,
)["decision"] == "HUMAN_REVIEW_REQUIRED"
assert reference.refund_decision(
    payment_verified=True,
    amount_minor=5000,
    refundable_minor=14900,
    independent_approval=True,
)["decision"] == "ALLOW_PROVIDER_REFUND_REQUEST"
assert reference.tax_decision(
    automatic_tax_requested=True,
    active_registration=False,
    customer_location_evidence=True,
) == "DENY_REGISTRATION_REQUIRED"

margin = reference.margin_scenario(
    net_revenue_minor=14900,
    variable_costs_minor=[1800, 700, 500, 500, 1200, 300],
    contribution_margin_floor_bps=5500,
)
assert margin["contribution_margin_minor"] == 9900
assert margin["decision"] == "PASS_CANDIDATE"
stress = reference.margin_scenario(
    net_revenue_minor=14900,
    variable_costs_minor=[5000, 1800, 900, 500, 2200, 1000],
    contribution_margin_floor_bps=5500,
)
assert stress["decision"] == "BLOCK"

assert reference.commercial_readiness(
    {gate: "PASS" for gate in runtime["readiness_gates"]}
) == "READY_ENGINEERING_ONLY"
assert reference.may_activate_paid_entitlement(
    provider_event_verified=True,
    ledger_reconciled=True,
    policy_current=True,
    tenant_match=True,
    rights_current=True,
    human_commercial_activation=True,
) is True
assert reference.may_activate_paid_entitlement(
    provider_event_verified=True,
    ledger_reconciled=True,
    policy_current=True,
    tenant_match=True,
    rights_current=True,
    human_commercial_activation=False,
) is False
assert reference.may_launch_commercially(
    canonical_activation=False,
    launch_authority=True,
) is False

for fixture in fixtures["fixtures"]:
    assert fixture["canonical_write"] is False
    assert fixture["commercial_launch"] is False
    assert fixture["live_payment"] is False
    assert fixture["external_action"] is False
    assert fixture["cross_tenant_disclosure"] is False
    assert fixture["provider_event_idempotent"] is True
    assert fixture["evidence_preserved"] is True

zero_fields = (
    "canonical_delta",
    "external_action_delta",
    "cross_tenant_disclosure_delta",
    "authority_elevation_delta",
    "live_payment_delta",
    "revenue_recognition_delta",
    "entitlement_escalation_delta",
    "evidence_loss_delta",
)
assert set(cases["required_zero_deltas"]) == set(zero_fields)
assert all(cases["required_zero_deltas"][field] == 0 for field in zero_fields)
for case in cases["cases"]:
    assert case["expected_decision"] == "DENY_OR_QUARANTINE", case["case_id"]

print(
    json.dumps(
        {
            "status": "PASS",
            "task_id": "AX-GE2E-P21-T01",
            "input_contract_bindings": len(runtime["input_contract_bindings"]),
            "domain_modules": len(runtime["modules"]),
            "record_types": len(runtime["record_types"]),
            "domain_invariants": len(runtime["invariants"]),
            "lifecycle_states": len(runtime["lifecycle_states"]),
            "pipeline_stages": len(runtime["pipeline_stages"]),
            "readiness_gates": len(runtime["readiness_gates"]),
            "conformance_fixtures": len(fixtures["fixtures"]),
            "adversarial_cases": len(cases["cases"]),
            "commercial_activation_authorised": runtime[
                "commercial_activation_authorised"
            ],
        },
        sort_keys=True,
    )
)
