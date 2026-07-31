#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from p18_intent_tides_reference import (
    adversarial_decision,
    canonical_digest,
    cohort_privacy_decision,
    event_eligibility,
    manipulation_decision,
    preference_decision,
    purpose_decision,
    research_candidate_decision,
    retention_decision,
    tide_decision,
)

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PATH = (
    ROOT
    / "data/intent-intelligence/"
    "intent-intelligence-knowledge-tides-runtime.v0.1.json"
)
FIXTURES_PATH = (
    ROOT / "data/intent-intelligence/p18-conformance-fixtures.v0.1.json"
)
CASES_PATH = (
    ROOT / "data/intent-intelligence/p18-adversarial-cases.v0.1.json"
)
RUNTIME_SCHEMA_PATH = (
    ROOT
    / "schemas/intent-intelligence-knowledge-tides-runtime.schema.json"
)
FIXTURES_SCHEMA_PATH = (
    ROOT
    / "schemas/intent-intelligence-knowledge-tides-fixtures.schema.json"
)
CASES_SCHEMA_PATH = (
    ROOT
    / "schemas/intent-intelligence-knowledge-tides-cases.schema.json"
)


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(instance: Any, schema: Any, label: str) -> None:
    validator = Draft202012Validator(schema)
    errors = sorted(
        validator.iter_errors(instance),
        key=lambda error: list(error.path),
    )
    assert not errors, {
        "label": label,
        "errors": [error.message for error in errors],
    }


def git_blob_sha(path: Path) -> str:
    content = path.read_bytes()
    prefix = f"blob {len(content)}\0".encode()
    return hashlib.sha1(prefix + content).hexdigest()


runtime: dict[str, Any] = load(RUNTIME_PATH)
fixtures: dict[str, Any] = load(FIXTURES_PATH)
cases: dict[str, Any] = load(CASES_PATH)
validate(runtime, load(RUNTIME_SCHEMA_PATH), "runtime")
validate(fixtures, load(FIXTURES_SCHEMA_PATH), "fixtures")
validate(cases, load(CASES_SCHEMA_PATH), "cases")

assert runtime["task_id"] == "AX-GE2E-P18-T01"
assert runtime["baseline_sha"] == (
    "4f2d52bcff78bba020ede336f34e494b442fa898"
)
assert runtime["dependency_status"]["p17_engineering_evidence_ready"]
assert not runtime["dependency_status"][
    "p17_canonical_activation_authorised"
]
assert not runtime["dependency_status"]["merge_to_main_allowed"]

for binding in runtime["input_contract_bindings"]:
    path = ROOT / binding["path"]
    assert path.is_file(), binding["path"]
    assert git_blob_sha(path) == binding["git_blob_sha"], binding

modules = runtime["domain_modules"]
assert len(modules) == 8
assert len({module["module_id"] for module in modules}) == 8
assert sum(len(module["record_types"]) for module in modules) == 32
assert sum(len(module["invariants"]) for module in modules) == 48
assert len(runtime["intent_lifecycle"]["states"]) == 12
assert len(runtime["operating_pipeline"]["stages"]) == 11
assert len(runtime["origin_surfaces"]) == 8
assert len(runtime["tide_states"]) == 8
assert len(runtime["tide_dimensions"]) == 10
assert len(runtime["languages"]) == 6
assert len(runtime["risk_classes"]) == 10
assert len(runtime["readiness_gates"]) == 12
assert len(runtime["forbidden_promotions"]) == 12
assert len(runtime["rights_dimensions"]) == 10

privacy = runtime["privacy_model"]
assert privacy["pseudonymous_not_anonymous"]
assert not privacy["direct_identifiers_allowed"]
assert not privacy["raw_message_materialisation_allowed"]
assert not privacy["raw_message_export_allowed"]
assert not privacy["cross_tenant_row_join_authorised"]
assert not privacy["differential_privacy_claimed"]
assert privacy["minimum_unique_users"] == 20
assert privacy["minimum_unique_organisations"] == 5
assert privacy["maximum_dominant_organisation_share"] == 0.25

required_boundaries = {
    "One interaction is not a preference.",
    "Repeated interaction is not consent.",
    "Aggregate attention is not market demand or willingness to pay.",
    "A research candidate is not an authorised ResearchRun.",
    "Deleted, revoked or purpose-ineligible events contribute zero.",
}
assert required_boundaries <= set(runtime["truth_boundaries"])

candidate_contract = runtime["research_candidate_contract"]
assert candidate_contract["output_authority"] == "PROPOSAL_ONLY"
assert "pseudonymous_user_id" in candidate_contract["prohibited_fields"]
assert "pseudonymous_org_id" in candidate_contract["prohibited_fields"]
assert "raw_message_reference" in candidate_contract["prohibited_fields"]

handlers = {
    "INTENT_EVENT_GATE": event_eligibility,
    "PURPOSE_CONSENT_LEDGER": purpose_decision,
    "PRIVATE_PREFERENCE_MEMORY": preference_decision,
    "COHORT_PRIVACY_AGGREGATOR": cohort_privacy_decision,
    "KNOWLEDGE_TIDE_ENGINE": tide_decision,
    "MANIPULATION_BIAS_DEFENCE": manipulation_decision,
    "RESEARCH_CANDIDATE_FACTORY": research_candidate_decision,
    "RETENTION_DELETION_AUDIT": retention_decision,
}

fixture_count = sum(
    len(group["cases"]) for group in fixtures["groups"]
)
assert fixture_count == fixtures["expected_fixture_count"] == 40
for group in fixtures["groups"]:
    handler = handlers[group["module_id"]]
    for fixture in group["cases"]:
        observed = handler(fixture["input"])
        assert observed == fixture["expected_decision"], {
            "module_id": group["module_id"],
            "class_id": fixture["class_id"],
            "expected": fixture["expected_decision"],
            "observed": observed,
        }

case_count = len(cases["modules"]) * len(cases["threats"])
assert case_count == cases["expected_case_count"] == 72
assert set(cases["required_zero_deltas"]) == {
    "canonical_delta",
    "research_run_delta",
    "privacy_disclosure_delta",
    "authority_elevation_delta",
}
for module_id in cases["modules"]:
    assert module_id in handlers
    for threat in cases["threats"]:
        observed = adversarial_decision(threat["threat_class"])
        assert observed == threat["expected_decision"]

assert canonical_digest(runtime) == canonical_digest(load(RUNTIME_PATH))
assert runtime["acceptance_gate"]["current_decision"] == (
    "NOT_READY_FOR_CANONICAL_ACTIVATION"
)

print(
    json.dumps(
        {
            "status": "PASS",
            "task_id": runtime["task_id"],
            "input_contract_bindings": len(
                runtime["input_contract_bindings"]
            ),
            "domain_modules": len(modules),
            "record_types": sum(
                len(module["record_types"]) for module in modules
            ),
            "domain_invariants": sum(
                len(module["invariants"]) for module in modules
            ),
            "lifecycle_states": len(
                runtime["intent_lifecycle"]["states"]
            ),
            "pipeline_stages": len(
                runtime["operating_pipeline"]["stages"]
            ),
            "conformance_fixtures": fixture_count,
            "adversarial_cases": case_count,
            "canonical_activation_authorised": False,
        },
        sort_keys=True,
    )
)
