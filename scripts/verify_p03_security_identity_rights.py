#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_SCHEMA_PATH = ROOT / "schemas/security-identity-rights-registry.schema.json"
THREAT_SCHEMA_PATH = ROOT / "schemas/security-threat-model.schema.json"
REGISTRY_PATH = ROOT / "data/security/security-identity-rights-registry.v0.1.json"
THREAT_MODEL_PATH = ROOT / "data/security/p03-threat-model.v0.1.json"
PROGRAMME_PATH = ROOT / "data/programmes/global-e2e-tasks-p00-p04.v1.4.json"
P02_REGISTRY_PATH = ROOT / "data/ontology/global-ontology-registry.v0.1.json"
P02_LIBRARY_PATH = ROOT / "data/ontology/library-contracts.v0.1.json"

for path in (
    REGISTRY_SCHEMA_PATH,
    THREAT_SCHEMA_PATH,
    REGISTRY_PATH,
    THREAT_MODEL_PATH,
    PROGRAMME_PATH,
    P02_REGISTRY_PATH,
    P02_LIBRARY_PATH,
):
    assert path.is_file(), f"missing {path.relative_to(ROOT)}"

registry_schema = json.loads(REGISTRY_SCHEMA_PATH.read_text(encoding="utf-8"))
threat_schema = json.loads(THREAT_SCHEMA_PATH.read_text(encoding="utf-8"))
registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
threat_model = json.loads(THREAT_MODEL_PATH.read_text(encoding="utf-8"))
programme = json.loads(PROGRAMME_PATH.read_text(encoding="utf-8"))
p02_registry = json.loads(P02_REGISTRY_PATH.read_text(encoding="utf-8"))
p02_libraries = json.loads(P02_LIBRARY_PATH.read_text(encoding="utf-8"))

for schema in (registry_schema, threat_schema):
    Draft202012Validator.check_schema(schema)

for schema, instance in (
    (registry_schema, registry),
    (threat_schema, threat_model),
):
    errors = sorted(
        Draft202012Validator(schema).iter_errors(instance),
        key=lambda error: list(error.path),
    )
    assert not errors, [error.message for error in errors]

assert registry["task_id"] == "AX-GE2E-P03-T01"
assert registry["status"] == "DRAFT_ENGINEERING_FOUNDATION"
assert registry["human_authorised_branch_start"] is True
assert registry["canonical_activation_authorised"] is False

dependency = registry["dependency_status"]
assert dependency["p02_task"] == "AX-GE2E-P02-T01"
assert dependency["p02_engineering_evidence_ready"] is True
assert dependency["p02_canonical_activation_authorised"] is False
assert dependency["p01_dependency_satisfied"] is False
assert dependency["merge_to_main_allowed"] is False
assert dependency["stacked_base_branch"] == (
    "agent/ax-ge2e-p02-global-ontology-contracts-v1.4"
)

subprocess.run(
    ["git", "cat-file", "-e", f'{dependency["p02_engineering_head"]}^{{commit}}'],
    cwd=ROOT,
    check=True,
    capture_output=True,
)

tasks = {task["task_id"]: task for task in programme["tasks"]}
p03_task = tasks["AX-GE2E-P03-T01"]
assert p03_task["state"] == "BLOCKED"
assert p03_task["dependencies"] == {
    "phases": ["P02"],
    "tasks": ["AX-GE2E-P02-T01"],
    "external": [],
}
assert p03_task["impacts"]["security"] == "CRITICAL"
assert p03_task["impacts"]["privacy"] == "CRITICAL"

assert p02_registry["task_id"] == "AX-GE2E-P02-T01"
assert p02_registry["canonical_activation_authorised"] is False
assert len(p02_libraries["contracts"]) == 16

assert len(registry["trust_principles"]) >= 10

identity = registry["identity_contract"]
assert set(identity["principal_types"]) == {
    "HUMAN_USER",
    "SERVICE_PRINCIPAL",
    "WORKLOAD_IDENTITY",
    "BREAK_GLASS_PRINCIPAL",
}
assert {"ACTIVE", "SUSPENDED", "REVOKED", "EXPIRED"}.issubset(
    identity["status_values"]
)

organisation = registry["organisation_contract"]
assert set(organisation["resource_types"]) == {
    "ORGANISATION",
    "TENANT",
    "WORKSPACE",
}

membership = registry["membership_contract"]
assert {"INVITED", "ACTIVE", "SUSPENDED", "REVOKED", "EXPIRED"} == set(
    membership["status_values"]
)

authorization = registry["authorization_contract"]
assert authorization["default_decision"] == "DENY"
assert set(authorization["decision_states"]) == {
    "ALLOW",
    "DENY",
    "NOT_APPLICABLE",
    "INDETERMINATE",
}
capabilities = set(authorization["capabilities"])
role_templates = authorization["role_templates"]
role_ids = [role["role_id"] for role in role_templates]
assert len(role_ids) == len(set(role_ids))
for role in role_templates:
    assert set(role["capabilities"]).issubset(capabilities)

service_worker = next(
    role for role in role_templates if role["role_id"] == "SERVICE_WORKER"
)
assert set(service_worker["capabilities"]) == {"service:execute"}
assert not {
    "membership:manage",
    "security:manage",
    "rights:review",
    "export:approve",
    "billing:manage",
}.intersection(service_worker["capabilities"])
assert any(
    "different human principals" in rule
    for rule in authorization["separation_of_duties"]
)
assert any(
    "Client-supplied roles" in rule for rule in authorization["rules"]
)
assert any(
    "Model output" in rule for rule in authorization["rules"]
)
assert any(
    "INDETERMINATE is treated as DENY" in rule
    for rule in authorization["rules"]
)

session = registry["session_contract"]
assert {"Secure", "HttpOnly", "SameSite=Strict"}.issubset(
    session["cookie_requirements"]
)
assert "replay_detection" in session["required_controls"]
assert "credential_version_binding" in session["required_controls"]

rls = registry["rls_contract"]
assert set(rls["scope_columns"]) == {"tenant_id", "workspace_id"}
assert {
    "ENABLE_ROW_LEVEL_SECURITY",
    "FORCE_ROW_LEVEL_SECURITY",
    "NO_BYPASSRLS_APPLICATION_ROLE",
    "SAFE_SECURITY_DEFINER",
    "TRANSACTION_LOCAL_CONTEXT",
    "TABLE_OWNER_NOT_RUNTIME_ROLE",
}.issubset(rls["required_controls"])
assert any("Browser headers" in rule for rule in rls["rules"])
assert any("zero visible or mutable rows" in rule for rule in rls["rules"])

classification = registry["data_classification_contract"]
assert classification["default_when_unknown"] == "RESTRICTED"
assert set(classification["confidentiality_levels"]) == {
    "PUBLIC",
    "INTERNAL",
    "CONFIDENTIAL",
    "RESTRICTED",
}
assert {"PERSONAL", "SENSITIVE_PERSONAL", "SECRET", "SOURCE_RESTRICTED"}.issubset(
    classification["content_flags"]
)
assert any(
    "cannot lower" in rule for rule in classification["rules"]
)

rights = registry["source_rights_enforcement_contract"]
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
assert set(rights["required_rights_dimensions"]) == expected_rights
assert any("Kill-switch activation" in rule for rule in rights["rules"])
assert any("Ambiguous, missing, expired" in rule for rule in rights["rules"])

export = registry["export_contract"]
assert {"export:create", "export:approve"}.issubset(capabilities)
assert {"REQUESTED", "APPROVED", "MATERIALISED", "DELIVERED", "REVOKED"} <= set(
    export["states"]
)
assert any(
    "research:read never implies export:create" in rule
    for rule in export["rules"]
)
assert "manifest_hash" in export["required_fields"]
assert "source_rights_snapshot_ids" in export["required_fields"]

audit = registry["audit_contract"]
assert {"AUTHORIZATION_DECISION", "RIGHTS_DECISION", "EXPORT_DECISION"} <= set(
    audit["event_types"]
)
assert {"previous_event_hash", "event_hash"} <= set(audit["required_fields"])
assert any("exclude credentials" in rule for rule in audit["rules"])

break_glass = registry["break_glass_contract"]
assert {
    "independent_human_approval",
    "minimal_capability_scope",
    "short_expiry",
    "strong_authentication",
    "continuous_audit",
}.issubset(break_glass["required_controls"])
assert any(
    "unavailable to service principals" in rule
    for rule in break_glass["rules"]
)

assert len(registry["observability"]["metrics"]) >= 6
assert len(registry["observability"]["alerts"]) >= 6
assert registry["acceptance_gate"]["current_decision"] == (
    "NOT_READY_FOR_CANONICAL_ACTIVATION"
)
assert len(
    registry["acceptance_gate"]["required_before_canonical_activation"]
) >= 12

threats = threat_model["threats"]
cases = threat_model["adversarial_cases"]
assert len(threats) == 24
assert len(cases) == 24
threat_ids = {item["threat_id"] for item in threats}
case_ids = {item["case_id"] for item in cases}
assert len(threat_ids) == len(threats)
assert len(case_ids) == len(cases)
assert {item["adversarial_case_id"] for item in threats} == case_ids
assert {item["threat_id"] for item in cases} == threat_ids

threat_by_id = {item["threat_id"]: item for item in threats}
case_by_id = {item["case_id"]: item for item in cases}
for threat in threats:
    case = case_by_id[threat["adversarial_case_id"]]
    assert case["threat_id"] == threat["threat_id"]
    assert case["expected_decision"] == threat["expected_decision"]
    assert {
        "tenant_and_workspace_isolation",
        "server_authority",
        "source_rights",
        "auditability",
    } == set(case["must_preserve"])

required_categories = {
    "SPOOFING",
    "AUTHORIZATION",
    "ELEVATION_OF_PRIVILEGE",
    "CONFUSED_DEPUTY",
    "DATABASE",
    "SESSION",
    "DATA_EXFILTRATION",
    "RIGHTS",
    "AI_AUTHORITY",
    "DATA_CLASSIFICATION",
    "PRIVACY",
    "NON_DISCLOSURE",
    "BREAK_GLASS",
    "DELIVERY",
    "CACHE_ISOLATION",
    "AUDIT_TAMPERING",
    "AGGREGATION",
    "SEPARATION_OF_DUTIES",
    "PURPOSE_LIMITATION",
    "CREDENTIAL_EXPOSURE",
}
assert required_categories.issubset({item["category"] for item in threats})
assert threat_by_id["AX-P03-TH-002"]["expected_decision"] == "DENY_NON_DISCLOSING"
assert threat_by_id["AX-P03-TH-006"]["expected_decision"] == "FAIL_CLOSED"
assert threat_by_id["AX-P03-TH-013"]["expected_decision"] == "DENY"
assert threat_by_id["AX-P03-TH-020"]["expected_decision"] == (
    "ALERT_AND_FAIL_CLOSED"
)

print(
    json.dumps(
        {
            "status": "PASS",
            "task_id": registry["task_id"],
            "principal_types": len(identity["principal_types"]),
            "capabilities": len(capabilities),
            "role_templates": len(role_templates),
            "rights_dimensions": len(rights["required_rights_dimensions"]),
            "threats": len(threats),
            "adversarial_cases": len(cases),
            "canonical_activation_authorised": False,
            "p02_canonical_activation_authorised": False,
            "p01_dependency_satisfied": False,
        },
        sort_keys=True,
    )
)
