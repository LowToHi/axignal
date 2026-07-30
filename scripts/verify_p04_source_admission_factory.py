#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_SCHEMA_PATH = ROOT / "schemas/connector-sdk-registry.schema.json"
CASES_SCHEMA_PATH = ROOT / "schemas/source-admission-cases.schema.json"
REGISTRY_PATH = ROOT / "data/connectors/connector-sdk-registry.v0.1.json"
CASES_PATH = ROOT / "data/connectors/p04-adversarial-cases.v0.1.json"
PROGRAMME_PATH = ROOT / "data/programmes/global-e2e-tasks-p00-p04.v1.4.json"
P03_REGISTRY_PATH = ROOT / "data/security/security-identity-rights-registry.v0.1.json"
P02_REGISTRY_PATH = ROOT / "data/ontology/global-ontology-registry.v0.1.json"

for path in (
    REGISTRY_SCHEMA_PATH,
    CASES_SCHEMA_PATH,
    REGISTRY_PATH,
    CASES_PATH,
    PROGRAMME_PATH,
    P03_REGISTRY_PATH,
    P02_REGISTRY_PATH,
):
    assert path.is_file(), f"missing {path.relative_to(ROOT)}"

registry_schema = json.loads(REGISTRY_SCHEMA_PATH.read_text(encoding="utf-8"))
cases_schema = json.loads(CASES_SCHEMA_PATH.read_text(encoding="utf-8"))
registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
programme = json.loads(PROGRAMME_PATH.read_text(encoding="utf-8"))
p03_registry = json.loads(P03_REGISTRY_PATH.read_text(encoding="utf-8"))
p02_registry = json.loads(P02_REGISTRY_PATH.read_text(encoding="utf-8"))

for schema in (registry_schema, cases_schema):
    Draft202012Validator.check_schema(schema)

for schema, instance, name in (
    (registry_schema, registry, "connector SDK registry"),
    (cases_schema, cases, "source admission cases"),
):
    errors = sorted(
        Draft202012Validator(schema).iter_errors(instance),
        key=lambda error: list(error.path),
    )
    assert not errors, f"{name}: {[error.message for error in errors]}"

tasks = {task["task_id"]: task for task in programme["tasks"]}
task = tasks["AX-GE2E-P04-T01"]
assert task["phase"] == "P04"
assert task["state"] == "BLOCKED"
assert task["dependencies"]["phases"] == ["P03"]
assert task["dependencies"]["tasks"] == ["AX-GE2E-P03-T01"]
assert "No unauthorised launch, admission or canonical authority." in task["prohibited_scope"]

dependency = registry["dependency_status"]
assert dependency["p03_engineering_head"] == (
    "3b950b1b111a0eb6e3b9b330cc15887db8699f3c"
)
assert dependency["p03_engineering_evidence_ready"] is True
assert dependency["p03_canonical_activation_authorised"] is False
assert dependency["p02_canonical_activation_authorised"] is False
assert dependency["p01_dependency_satisfied"] is False
assert dependency["merge_to_main_allowed"] is False
assert registry["canonical_activation_authorised"] is False
assert registry["acceptance_gate"]["current_decision"] == (
    "NOT_READY_FOR_CANONICAL_ACTIVATION"
)

assert p03_registry["task_id"] == "AX-GE2E-P03-T01"
assert p03_registry["canonical_activation_authorised"] is False
assert p02_registry["task_id"] == "AX-GE2E-P02-T01"
assert p02_registry["canonical_activation_authorised"] is False

expected_rights = {
    "collection",
    "transient_processing",
    "persistent_storage",
    "model_input",
    "derived_calculations",
    "internal_display",
    "customer_display",
    "export",
    "api_redistribution",
    "model_training_or_evaluation",
}
p04_rights = set(registry["source_profile_contract"]["rights_dimensions"])
p03_rights = set(
    p03_registry["source_rights_enforcement_contract"][
        "required_rights_dimensions"
    ]
)
assert p04_rights == expected_rights
assert p04_rights == p03_rights

expected_methods = {
    "describe_source",
    "preflight",
    "authenticate",
    "healthcheck",
    "fetch_page",
    "parse_payload",
    "normalize_records",
    "classify_records",
    "emit_candidate_objects",
    "checkpoint",
    "reconcile",
    "revoke",
}
sdk = registry["sdk_contract"]
assert set(sdk["adapter_methods"]) == expected_methods
assert all(value is False for value in sdk["authority_ceiling"].values())
assert "CanonicalSourceAdmission" in sdk["forbidden_outputs"]
assert "CanonicalClaim" in sdk["forbidden_outputs"]
assert "CandidateSourceObject" in sdk["candidate_outputs"]
assert "CandidateEvidenceObject" in sdk["candidate_outputs"]

expected_gate_ids = {
    "G01_LEGAL_AUTHORITY",
    "G02_RIGHTS_MATRIX",
    "G03_PRIVACY_CLASSIFICATION",
    "G04_SECURITY_PREFLIGHT",
    "G05_PROVENANCE",
    "G06_SCHEMA_CONFORMANCE",
    "G07_QUALITY_THRESHOLDS",
    "G08_TEMPORAL_SEMANTICS",
    "G09_TAXONOMY_MAPPING",
    "G10_IDEMPOTENCY",
    "G11_RATE_AND_COST",
    "G12_OUTAGE_POLICY",
    "G13_REVOCATION_AND_DELETION",
    "G14_OBSERVABILITY",
    "G15_ROLLBACK",
    "G16_HUMAN_ADMISSION",
}
pipeline = registry["admission_pipeline"]
gates = {gate["gate_id"]: gate for gate in pipeline["gate_catalog"]}
assert set(gates) == expected_gate_ids
assert pipeline["default_decision"] == "DENY"
assert "INDETERMINATE" in pipeline["decision_states"]
assert all(gate["pass_state"] == "PASS" for gate in gates.values())
assert all(
    gate["fail_state"] in {"DENY", "QUARANTINE", "SUSPEND"}
    for gate in gates.values()
)
stage_gate_ids = {
    gate_id
    for stage in pipeline["stages"]
    for gate_id in stage["required_gate_ids"]
}
assert stage_gate_ids == expected_gate_ids
assert gates["G16_HUMAN_ADMISSION"]["human_authority_required"] is True

lifecycle = registry["lifecycle_contract"]
states = set(lifecycle["states"])
assert states == {
    "CANDIDATE",
    "SANDBOX",
    "VALIDATED",
    "PRODUCT_ADMITTED",
    "SUSPENDED",
    "REVOKED",
    "RETIRED",
}
transitions = set(lifecycle["allowed_transitions"])
assert "VALIDATED->PRODUCT_ADMITTED" in transitions
assert not any(
    transition.startswith("REVOKED->")
    and not transition.endswith("->RETIRED")
    for transition in transitions
)

profiles = registry["reference_profiles"]
assert len(profiles) == 4
assert len({profile["profile_id"] for profile in profiles}) == 4
assert all(profile["profile_kind"] == "REFERENCE_ONLY" for profile in profiles)
assert all(profile["admission_authorised"] is False for profile in profiles)
assert all(profile["state"] != "PRODUCT_ADMITTED" for profile in profiles)
assert all(
    set(profile["rights_snapshot"]) == expected_rights
    for profile in profiles
)
assert all(
    profile["endpoint_origin"].endswith(".example.invalid")
    for profile in profiles
)
revoked = next(
    profile for profile in profiles if profile["profile_id"] == "AX-SRC-REF-REVOKED"
)
assert revoked["state"] == "REVOKED"
assert set(revoked["rights_snapshot"].values()) == {"DENY"}

threats = cases["threats"]
adversarial = cases["adversarial_cases"]
assert len(threats) == 32
assert len(adversarial) == 32
threat_by_id = {threat["threat_id"]: threat for threat in threats}
assert len(threat_by_id) == 32
assert len({case["case_id"] for case in adversarial}) == 32
assert {case["threat_id"] for case in adversarial} == set(threat_by_id)
for case in adversarial:
    threat = threat_by_id[case["threat_id"]]
    assert case["expected_gate_id"] == threat["control_gate_id"]
    assert case["expected_result"] == threat["required_result"]
    assert case["canonical_admission_delta"] == 0
    assert case["expected_gate_id"] in gates

required_alerts = {
    "undeclared_network_destination",
    "secret_material_detected",
    "pagination_nontermination",
    "schema_drift_detected",
    "kill_switch_bypass_attempt",
    "revoked_source_activity",
    "connector_authority_escalation_attempt",
    "rollback_residue_detected",
}
assert required_alerts <= set(registry["observability"]["alerts"])
assert {
    "stop_fetch",
    "stop_materialisation",
    "invalidate_allow_cache",
    "cancel_queued_work",
    "emit_tombstones",
} <= set(registry["revocation_contract"]["required_actions"])
assert {
    "exact_origin_allowlist",
    "redirect_revalidation",
    "dns_rebinding_defence",
    "private_address_denial",
    "payload_size_limit",
    "archive_expansion_limit",
} <= set(registry["security_contract"]["network_controls"])

print(
    json.dumps(
        {
            "status": "PASS",
            "task_id": registry["task_id"],
            "adapter_methods": len(sdk["adapter_methods"]),
            "admission_gates": len(gates),
            "pipeline_stages": len(pipeline["stages"]),
            "reference_profiles": len(profiles),
            "rights_dimensions": len(p04_rights),
            "threats": len(threats),
            "adversarial_cases": len(adversarial),
            "canonical_activation_authorised": False,
            "p03_canonical_activation_authorised": False,
            "p02_canonical_activation_authorised": False,
            "p01_dependency_satisfied": False,
        },
        sort_keys=True,
    )
)
