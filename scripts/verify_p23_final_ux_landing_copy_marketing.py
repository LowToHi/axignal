#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "data/experience/final-ux-landing-copy-marketing-runtime.v0.1.json"
FIXTURES = ROOT / "data/experience/p23-conformance-fixtures.v0.1.json"
CASES = ROOT / "data/experience/p23-adversarial-cases.v0.1.json"
REFERENCE = ROOT / "scripts/p23_experience_reference.py"
P22_HEAD = "82ad182f7d662cb3deb034f88ea287f1422fc694"

runtime = json.loads(RUNTIME.read_text(encoding="utf-8"))
fixtures = json.loads(FIXTURES.read_text(encoding="utf-8"))
cases = json.loads(CASES.read_text(encoding="utf-8"))
spec = importlib.util.spec_from_file_location("p23_reference", REFERENCE)
assert spec and spec.loader
reference = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reference)

assert runtime["task_id"] == "AX-GE2E-P23-T01"
assert runtime["baseline_sha"] == P22_HEAD
assert runtime["state"] == "BLOCKED"
assert runtime["engineering_evidence_ready"] is True
for field in (
    "public_site_authorised",
    "public_campaigns_authorised",
    "paid_media_authorised",
    "production_traffic_authorised",
    "stripe_live_authorised",
    "canonical_activation_authorised",
):
    assert runtime[field] is False

assert len(runtime["input_contract_bindings"]) == 4
assert len(runtime["modules"]) == 8
assert len(runtime["record_types"]) == 32
assert len(runtime["invariants"]) == 48
assert len(runtime["lifecycle_states"]) == 12
assert len(runtime["pipeline_stages"]) == 11
assert len(runtime["primary_journeys"]) == 4
assert len(runtime["readiness_gates"]) == 14
assert len(runtime["authority_classes"]) == 9
assert len(runtime["risk_classes"]) == 10
assert len(fixtures["fixtures"]) == 24
assert len(cases["cases"]) == 16

landing = runtime["landing_contract"]
assert landing["hero"]["headline"] == (
    "Turn complex questions into decisions you can defend."
)
assert len(landing["sections"]) == 9
assert "zero hallucinations" in landing["prohibited_phrases"]
assert runtime["accessibility_contract"]["target"] == "WCAG_2_2_AA"
assert runtime["accessibility_contract"]["critical_defects_allowed"] == 0
assert runtime["seo_contract"]["indexing_default"] == "NOINDEX_UNTIL_APPROVED"
assert runtime["analytics_contract"]["raw_prompt_collection"] is False
assert runtime["analytics_contract"]["tenant_content_collection"] is False
assert runtime["marketing_contract"]["paid_media_default"] == "OFF"
assert runtime["marketing_contract"]["automated_publication"] is False

assert reference.claim_decision(
    evidence_status="SANDBOX_ONLY",
    public_use="NOT_YET",
    limitations_present=True,
) == "DENY"
assert reference.claim_decision(
    evidence_status="ENGINEERING_SUPPORTED",
    public_use="ALLOWED_WITH_SCOPE",
    limitations_present=False,
) == "REVIEW_REQUIRED"
assert reference.claim_decision(
    evidence_status="ENGINEERING_SUPPORTED",
    public_use="ALLOWED_WITH_SCOPE",
    limitations_present=True,
) == "ALLOW_BOUNDED"

all_gates = {gate: True for gate in runtime["readiness_gates"]}
assert reference.publication_decision(
    gates=all_gates,
    human_publication_authority=False,
) == "HUMAN_APPROVAL_REQUIRED"
assert reference.publication_decision(
    gates=all_gates,
    human_publication_authority=True,
) == "ALLOW_PUBLICATION"
all_gates["legal_pass"] = False
assert reference.publication_decision(
    gates=all_gates,
    human_publication_authority=True,
) == "BLOCK"

analytics = runtime["analytics_contract"]
assert reference.analytics_decision(
    event_name="landing_view",
    allowed_events=analytics["events"],
    consent="REJECTED",
    purpose="product",
    contains_private_content=False,
) == "ALLOW_MINIMISED_EVENT"
assert reference.analytics_decision(
    event_name="landing_view",
    allowed_events=analytics["events"],
    consent="REJECTED",
    purpose="marketing",
    contains_private_content=False,
) == "DENY_CONSENT_REQUIRED"
assert reference.analytics_decision(
    event_name="workspace_research_started",
    allowed_events=analytics["events"],
    consent="GRANTED",
    purpose="product",
    contains_private_content=True,
) == "DENY_PRIVATE_CONTENT"

experiment = runtime["experiment_contract"]
assert reference.experiment_decision(
    surface="headline",
    allowed_surfaces=experiment["allowed_surfaces"],
    forbidden_surfaces=experiment["forbidden_surfaces"],
    sample_declared=True,
    stopping_rule_declared=True,
    human_growth_approval=True,
) == "ALLOW_BOUNDED_EXPERIMENT"
assert reference.experiment_decision(
    surface="billing_amount",
    allowed_surfaces=experiment["allowed_surfaces"],
    forbidden_surfaces=experiment["forbidden_surfaces"],
    sample_declared=True,
    stopping_rule_declared=True,
    human_growth_approval=True,
) == "DENY_SURFACE"
assert reference.marketing_scale_decision(
    conversion_validated=True,
    contribution_positive=True,
    budget_within_limit=True,
    human_budget_approval=False,
) == "HUMAN_APPROVAL_REQUIRED"
assert reference.accessibility_release(
    critical_defects=0,
    keyboard_complete=True,
    semantics_verified=True,
    human_review_complete=True,
) == "PASS"
assert reference.performance_release(
    lcp_ms=2400,
    cls=0.08,
    inp_ms=180,
    budgets=runtime["performance_budgets"],
) == "PASS"
assert reference.pricing_presentation(
    server_amount_minor=14900,
    displayed_amount_minor=14900,
    server_currency="EUR",
    displayed_currency="EUR",
) == "PASS"
assert reference.pricing_presentation(
    server_amount_minor=14900,
    displayed_amount_minor=9900,
    server_currency="EUR",
    displayed_currency="EUR",
) == "BLOCK_PRICE_MISMATCH"

for fixture in fixtures["fixtures"]:
    assert fixture["expected_decision"] == "PASS_ENGINEERING_EVIDENCE"
assert fixtures["evidence_preserved"] is True
assert set(cases["required_zero_deltas"].values()) == {0}
for case in cases["cases"]:
    assert case["expected_decision"] == "DENY_OR_QUARANTINE"

print(
    json.dumps(
        {
            "status": "PASS",
            "task_id": runtime["task_id"],
            "modules": len(runtime["modules"]),
            "record_types": len(runtime["record_types"]),
            "invariants": len(runtime["invariants"]),
            "journeys": len(runtime["primary_journeys"]),
            "readiness_gates": len(runtime["readiness_gates"]),
            "conformance_fixtures": len(fixtures["fixtures"]),
            "adversarial_cases": len(cases["cases"]),
            "public_site_authorised": runtime["public_site_authorised"],
            "paid_media_authorised": runtime["paid_media_authorised"],
        },
        sort_keys=True,
    )
)
