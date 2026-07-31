#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "data/production/production-slo-dr-security-runtime.v0.1.json"
FIXTURES = ROOT / "data/production/p22-conformance-fixtures.v0.1.json"
CASES = ROOT / "data/production/p22-adversarial-cases.v0.1.json"
REFERENCE = ROOT / "scripts/p22_production_reference.py"
P21_HEAD = "ee196e3cd8d7027adf92eb40e04868a5ad6e7594"


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


spec = importlib.util.spec_from_file_location("p22_reference", REFERENCE)
assert spec and spec.loader
reference = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reference)

runtime = load(RUNTIME)
fixtures = load(FIXTURES)
cases = load(CASES)

assert runtime["task_id"] == "AX-GE2E-P22-T01"
assert runtime["baseline_sha"] == P21_HEAD
assert runtime["state"] == "BLOCKED"
assert runtime["engineering_evidence_ready"] is True
for field in (
    "production_deployment_authorised",
    "public_traffic_authorised",
    "stripe_live_authorised",
    "external_action_authorised",
    "canonical_activation_authorised",
):
    assert runtime[field] is False, field

assert len(runtime["input_contract_bindings"]) == 5
assert len(runtime["modules"]) == 8
assert len(runtime["record_types"]) == 32
assert len(runtime["invariants"]) == 48
assert len(runtime["lifecycle_states"]) == 12
assert len(runtime["pipeline_stages"]) == 11
assert len(runtime["readiness_gates"]) == 12
assert len(runtime["authority_classes"]) == 8
assert len(runtime["risk_classes"]) == 10
assert len(fixtures["fixtures"]) == 24
assert len(cases["cases"]) == 16

for binding in runtime["input_contract_bindings"]:
    assert binding["engineering_evidence_ready"] is True
    assert binding["canonical_activation_authorised"] is False
    assert (ROOT / binding["path"]).is_file(), binding["path"]

slo = runtime["slo_contract"]
assert slo["window_days"] == 30
assert {service["service"] for service in slo["services"]} == {"api", "web", "worker"}
assert reference.availability_bps(good=999, total=1000) == 9990
assert reference.latency_compliant(observed_ms=499, threshold_ms=500) is True
assert reference.latency_compliant(observed_ms=501, threshold_ms=500) is False
assert reference.alert_decision(burn_rate_value=15.0, window_hours=1) == "PAGE"
assert reference.alert_decision(burn_rate_value=1.1, window_hours=72) == "TICKET"
assert reference.alert_decision(burn_rate_value=0.5, window_hours=72) == "NONE"

assert reference.release_decision(
    immutable_artifact=True,
    exact_revision=True,
    staging_smoke=True,
    rollback_test=True,
    slo_instrumented=True,
    security_acceptance_signed=True,
    critical_findings=0,
    human_release_approval=True,
) == "ALLOW_PRODUCTION_DEPLOYMENT"
assert reference.release_decision(
    immutable_artifact=True,
    exact_revision=True,
    staging_smoke=True,
    rollback_test=True,
    slo_instrumented=True,
    security_acceptance_signed=True,
    critical_findings=0,
    human_release_approval=False,
) == "DENY"

postgres = next(item for item in runtime["dr_contract"]["tiers"] if item["asset"] == "postgres_primary")
assert reference.restore_decision(
    encrypted_backup=True,
    digest_verified=True,
    isolated_target=True,
    recovered_point_age_minutes=10,
    elapsed_minutes=45,
    rpo_minutes=postgres["rpo_minutes"],
    rto_minutes=postgres["rto_minutes"],
    consistency_verified=True,
) == "PASS_DR_EXERCISE"
assert reference.restore_decision(
    encrypted_backup=True,
    digest_verified=False,
    isolated_target=True,
    recovered_point_age_minutes=10,
    elapsed_minutes=45,
    rpo_minutes=postgres["rpo_minutes"],
    rto_minutes=postgres["rto_minutes"],
    consistency_verified=True,
) == "FAIL_CLOSED"

now = datetime(2026, 7, 31, tzinfo=UTC)
assert reference.risk_acceptance_decision(
    severity="CRITICAL",
    approver_role="RISK_ACCEPTOR",
    expires_at=now + timedelta(days=7),
    now=now,
) == "DENY"
assert reference.risk_acceptance_decision(
    severity="HIGH",
    approver_role="RISK_ACCEPTOR",
    expires_at=now + timedelta(days=7),
    now=now,
) == "ALLOW_TEMPORARY"
assert reference.risk_acceptance_decision(
    severity="HIGH",
    approver_role="RISK_ACCEPTOR",
    expires_at=now - timedelta(seconds=1),
    now=now,
) == "DENY"

security = runtime["security_acceptance"]
controls = {control: "PASS" for control in security["required_controls"]}
assert reference.security_acceptance(
    controls=controls,
    required_controls=security["required_controls"],
    critical_findings=0,
    high_findings_without_acceptance=0,
) == "PASS_ENGINEERING_ACCEPTANCE"
assert reference.security_acceptance(
    controls=controls,
    required_controls=security["required_controls"],
    critical_findings=1,
    high_findings_without_acceptance=0,
) == "BLOCK"

assert reference.production_readiness(
    {gate: "PASS" for gate in runtime["readiness_gates"]},
    runtime["readiness_gates"],
) == "READY_FOR_TYPED_HUMAN_PRODUCTION_APPROVAL"
assert reference.production_readiness(
    {gate: ("FAIL" if gate == "restore_test_passed" else "PASS") for gate in runtime["readiness_gates"]},
    runtime["readiness_gates"],
) == "BLOCKED"

for fixture in fixtures["fixtures"]:
    assert fixture["production_deployment"] is False
    assert fixture["public_traffic"] is False
    assert fixture["stripe_live"] is False
    assert fixture["external_action"] is False
    assert fixture["canonical_write"] is False
    assert fixture["evidence_preserved"] is True

assert all(value == 0 for value in cases["required_zero_deltas"].values())
for case in cases["cases"]:
    assert case["expected_decision"] == "DENY_OR_QUARANTINE"

print(json.dumps({
    "status": "PASS",
    "task_id": runtime["task_id"],
    "baseline_sha": runtime["baseline_sha"],
    "modules": len(runtime["modules"]),
    "invariants": len(runtime["invariants"]),
    "readiness_gates": len(runtime["readiness_gates"]),
    "conformance_fixtures": len(fixtures["fixtures"]),
    "adversarial_cases": len(cases["cases"]),
    "production_deployment_authorised": runtime["production_deployment_authorised"],
    "stripe_live_authorised": runtime["stripe_live_authorised"],
}, sort_keys=True))
