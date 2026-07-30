#!/usr/bin/env python3
from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

from jsonschema import Draft202012Validator

from p11_infrastructure_reference import (
    canonical_digest,
    financing_decision,
    imported_authority,
    may_execute_external_action,
    normalize_project_outcome,
    permit_land_decision,
    project_current,
    project_readiness,
    stage_evidence_decision,
)

ROOT = Path(__file__).resolve().parents[1]

RUNTIME_SCHEMA = (
    ROOT
    / "schemas/infrastructure-project-pursuit-workspace-runtime.schema.json"
)
FIXTURES_SCHEMA = (
    ROOT
    / "schemas/infrastructure-project-pursuit-workspace-fixtures.schema.json"
)
CASES_SCHEMA = (
    ROOT
    / "schemas/infrastructure-project-pursuit-workspace-cases.schema.json"
)
RUNTIME = (
    ROOT
    / "data/infrastructure/"
    "infrastructure-project-pursuit-workspace-runtime.v0.1.json"
)
FIXTURES = (
    ROOT
    / "data/infrastructure/p11-conformance-fixtures.v0.1.json"
)
CASES = (
    ROOT
    / "data/infrastructure/p11-adversarial-cases.v0.1.json"
)
ROLLBACK_PLAN = (
    ROOT
    / "data/infrastructure/p11-rollback-plan.v0.1.json"
)
PROGRAMME = (
    ROOT
    / "data/programmes/global-e2e-tasks-p10-p14.v1.4.json"
)
P02_LIBRARIES = ROOT / "data/ontology/library-contracts.v0.1.json"
P05_FOUNDATIONS = (
    ROOT
    / "data/foundations/foundational-library-runtime.v0.1.json"
)
P06_DOCUMENTS = (
    ROOT
    / "data/document-intelligence/"
    "multilingual-document-intelligence-runtime.v0.1.json"
)
P07_OPERATIONS = (
    ROOT
    / "data/opportunity-operations/"
    "opportunity-operations-core-runtime.v0.1.json"
)
P10_REGULATORY = (
    ROOT
    / "data/regulatory/"
    "regulatory-market-entry-workspace-runtime.v0.1.json"
)
SOURCE_CATALOGUE = (
    ROOT
    / "data/sources/"
    "infrastructure-and-capital-projects-catalogue.v0.1.json"
)

paths = (
    RUNTIME_SCHEMA,
    FIXTURES_SCHEMA,
    CASES_SCHEMA,
    RUNTIME,
    FIXTURES,
    CASES,
    ROLLBACK_PLAN,
    PROGRAMME,
    P02_LIBRARIES,
    P05_FOUNDATIONS,
    P06_DOCUMENTS,
    P07_OPERATIONS,
    P10_REGULATORY,
    SOURCE_CATALOGUE,
)
for path in paths:
    assert path.is_file(), f"missing {path.relative_to(ROOT)}"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


runtime_schema = load(RUNTIME_SCHEMA)
fixtures_schema = load(FIXTURES_SCHEMA)
cases_schema = load(CASES_SCHEMA)
runtime = load(RUNTIME)
fixtures = load(FIXTURES)
cases = load(CASES)
programme = load(PROGRAMME)
p02 = load(P02_LIBRARIES)
p05 = load(P05_FOUNDATIONS)
p06 = load(P06_DOCUMENTS)
p07 = load(P07_OPERATIONS)
p10 = load(P10_REGULATORY)
catalogue = load(SOURCE_CATALOGUE)

for schema in (runtime_schema, fixtures_schema, cases_schema):
    Draft202012Validator.check_schema(schema)
Draft202012Validator(runtime_schema).validate(runtime)
Draft202012Validator(fixtures_schema).validate(fixtures)
Draft202012Validator(cases_schema).validate(cases)

task = next(
    item
    for item in programme["tasks"]
    if item["task_id"] == "AX-GE2E-P11-T01"
)
assert task["phase"] == "P11"
assert task["state"] == "BLOCKED"
assert task["objective"] == (
    "Implement infrastructure intelligence and the Project Pursuit Workspace."
)
assert task["dependencies"]["tasks"] == ["AX-GE2E-P07-T01"]
assert task["prohibited_scope"] == [
    "No unauthorised launch, admission or canonical authority."
]

library = next(
    item
    for item in p02["contracts"]
    if item["library_id"] == "AX-LIB-O04"
)
binding = runtime["infrastructure_library_binding"]
for key in (
    "library_id",
    "workspace_type",
    "canonical_name",
    "entities",
    "predicates",
    "events",
    "taxonomy_refs",
):
    assert binding[key] == library[key]

assert p05["task_id"] == "AX-GE2E-P05-T01"
assert p05["canonical_activation_authorised"] is False
assert p06["task_id"] == "AX-GE2E-P06-T01"
assert p06["canonical_activation_authorised"] is False
assert runtime["languages"] == [
    item["language_tag"]
    for item in p06["language_profile"]["languages"]
]
assert p07["task_id"] == "AX-GE2E-P07-T01"
assert p07["canonical_activation_authorised"] is False
assert runtime["rights_dimensions"] == p07["rights_dimensions"]
assert set(runtime["required_approvals"]).issubset(
    set(p07["approval_contract"]["approval_types"])
)
assert p10["task_id"] == "AX-GE2E-P10-T01"
assert p10["canonical_activation_authorised"] is False
assert (
    runtime["dependency_status"]["p10_engineering_head"]
    == "563acd353ba3a90d253d582b7c19f1554fd011b1"
)

assert catalogue["catalogue_id"] == "AX-INFRA-SOURCE-CATALOGUE-001"
assert catalogue["library_id"] == "AX-LIB-O04"
assert len(catalogue["sources"]) == 6
assert catalogue["principles"]["listed_does_not_mean_admitted"] is True
assert catalogue["principles"]["scraping_assumed_permitted"] is False
assert catalogue["principles"]["public_coverage_authorised"] is False
assert all(
    source["product_admitted"] is False
    and source["rights_status"] == "UNREVIEWED"
    for source in catalogue["sources"]
)

modules = runtime["domain_modules"]
assert len(modules) == 8
assert len({item["module_id"] for item in modules}) == 8
assert sum(len(item["record_types"]) for item in modules) == 32
assert sum(len(item["invariants"]) for item in modules) == 48
assert len(runtime["infrastructure_project_lifecycle"]["states"]) == 12
assert len(runtime["operating_pipeline"]["stages"]) == 11
assert len(runtime["stage_evidence_classes"]) == 10
assert len(runtime["permit_land_types"]) == 10
assert len(runtime["financing_value_types"]) == 10
assert len(runtime["risk_classes"]) == 10
assert len(runtime["readiness_gates"]) == 12
assert len(runtime["rights_dimensions"]) == 10

fixture_count = len(fixtures["modules"]) * len(fixtures["classes"])
assert fixture_count == 40
assert set(fixtures["modules"]) == {
    item["module_id"] for item in modules
}
assert all(
    item["canonical_write"] is False
    and item["external_action"] is False
    for item in fixtures["expected_by_class"].values()
)

case_count = len(cases["scopes"]) * len(cases["threats"])
assert case_count == 72
assert all(
    item["canonical_delta"] == 0
    and item["external_action_delta"] == 0
    for item in cases["expected_by_threat"].values()
)

assert canonical_digest({"b": 2, "a": 1}) == canonical_digest(
    {"a": 1, "b": 2}
)
assert project_current(
    status="ANNOUNCED",
    version_current=True,
    withdrawn=False,
) == "PASS"
assert project_current(
    status="ANNOUNCED",
    version_current=False,
    withdrawn=False,
) == "REVIEW_REQUIRED"
assert project_current(
    status="CANCELLED",
    version_current=True,
    withdrawn=True,
) == "DENY"

assert stage_evidence_decision(["VERIFIED", "VERIFIED"]) == "PASS"
assert stage_evidence_decision(["REPORTED"]) == "REVIEW_REQUIRED"
assert stage_evidence_decision(["WITHDRAWN"]) == "DENY"

assert financing_decision(
    project_cost=Decimal("100"),
    committed_debt=Decimal("60"),
    committed_equity=Decimal("30"),
    grant_support=Decimal("10"),
    state="COMMITTED",
    observed_evidence=True,
) == "PASS"
assert financing_decision(
    project_cost=Decimal("100"),
    committed_debt=Decimal("110"),
    committed_equity=Decimal("0"),
    grant_support=Decimal("0"),
    state="COMMITTED",
    observed_evidence=True,
) == "DENY"
assert financing_decision(
    project_cost=Decimal("100"),
    committed_debt=Decimal("60"),
    committed_equity=Decimal("30"),
    grant_support=Decimal("10"),
    state="INDICATIVE",
    observed_evidence=False,
) == "REVIEW_REQUIRED"

assert permit_land_decision(
    {"permit": "GRANTED", "land": "SECURED"}
) == "PASS"
assert permit_land_decision(
    {"permit": "APPLIED", "land": "SECURED"}
) == "REVIEW_REQUIRED"
assert permit_land_decision(
    {"permit": "REJECTED", "land": "SECURED"}
) == "DENY"

required_gates = runtime["readiness_gates"]
passing_gates = {gate: "PASS" for gate in required_gates}
assert project_readiness(passing_gates, required_gates) == "READY"
review_gates = dict(passing_gates)
review_gates["FINANCING_STATUS_VERIFIED"] = "REVIEW_REQUIRED"
assert project_readiness(
    review_gates,
    required_gates,
) == "REVIEW_REQUIRED"
deny_gates = dict(passing_gates)
deny_gates["PERMITS_AND_LAND_RESOLVED"] = "DENY"
assert project_readiness(deny_gates, required_gates) == "DENY"
assert project_readiness({}, required_gates) == "NOT_READY"

assert may_execute_external_action(
    actor_type="HUMAN_EXTERNAL_ACTION_AUTHORITY",
    readiness="READY",
    approvals_current=True,
    rights_active=True,
    project_is_current=True,
    channel_verified=True,
    audit_chain_valid=True,
    kill_switch_active=False,
)
assert not may_execute_external_action(
    actor_type="MODEL",
    readiness="READY",
    approvals_current=True,
    rights_active=True,
    project_is_current=True,
    channel_verified=True,
    audit_chain_valid=True,
    kill_switch_active=False,
)
assert not may_execute_external_action(
    actor_type="HUMAN_EXTERNAL_ACTION_AUTHORITY",
    readiness="READY",
    approvals_current=False,
    rights_active=True,
    project_is_current=True,
    channel_verified=True,
    audit_chain_valid=True,
    kill_switch_active=False,
)

assert normalize_project_outcome(
    "CONTRACT_AWARDED",
    observed_evidence=True,
) == "CONTRACT_AWARDED"
assert normalize_project_outcome(
    "CONTRACT_AWARDED",
    observed_evidence=False,
) == "UNKNOWN"
assert imported_authority("APPROVED") == "CANDIDATE_ONLY"

dependency = runtime["dependency_status"]
for key in (
    "p07_canonical_activation_authorised",
    "p10_canonical_activation_authorised",
    "p09_canonical_activation_authorised",
    "p08_canonical_activation_authorised",
    "p06_canonical_activation_authorised",
    "p05_canonical_activation_authorised",
    "p04_canonical_activation_authorised",
    "p03_canonical_activation_authorised",
    "p02_canonical_activation_authorised",
    "p01_dependency_satisfied",
    "merge_to_main_allowed",
):
    assert dependency[key] is False
assert runtime["canonical_activation_authorised"] is False
assert (
    runtime["acceptance_gate"]["current_decision"]
    == "NOT_READY_FOR_CANONICAL_ACTIVATION"
)

result = {
    "status": "PASS",
    "task_id": "AX-GE2E-P11-T01",
    "domain_modules": len(modules),
    "infrastructure_library_bindings": 1,
    "source_catalogue_entries": len(catalogue["sources"]),
    "record_types": sum(len(item["record_types"]) for item in modules),
    "domain_invariants": sum(len(item["invariants"]) for item in modules),
    "lifecycle_states": len(
        runtime["infrastructure_project_lifecycle"]["states"]
    ),
    "pipeline_stages": len(runtime["operating_pipeline"]["stages"]),
    "stage_evidence_classes": len(runtime["stage_evidence_classes"]),
    "permit_land_types": len(runtime["permit_land_types"]),
    "financing_value_types": len(runtime["financing_value_types"]),
    "risk_classes": len(runtime["risk_classes"]),
    "readiness_gates": len(runtime["readiness_gates"]),
    "languages": len(runtime["languages"]),
    "rights_dimensions": len(runtime["rights_dimensions"]),
    "conformance_fixtures": fixture_count,
    "adversarial_cases": case_count,
    "canonical_activation_authorised": False,
    "p10_canonical_activation_authorised": False,
    "p09_canonical_activation_authorised": False,
    "p08_canonical_activation_authorised": False,
    "p07_canonical_activation_authorised": False,
    "p06_canonical_activation_authorised": False,
    "p05_canonical_activation_authorised": False,
    "p04_canonical_activation_authorised": False,
    "p03_canonical_activation_authorised": False,
    "p02_canonical_activation_authorised": False,
    "p01_dependency_satisfied": False,
}
print(json.dumps(result, sort_keys=True))
