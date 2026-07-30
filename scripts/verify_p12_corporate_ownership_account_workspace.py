#!/usr/bin/env python3
from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

from jsonschema import Draft202012Validator

from p12_corporate_reference import (
    account_readiness,
    canonical_digest,
    control_decision,
    corporate_action_decision,
    filing_current,
    imported_authority,
    may_execute_external_action,
    normalize_account_outcome,
    ownership_decision,
    personal_data_decision,
)

ROOT = Path(__file__).resolve().parents[1]

RUNTIME_SCHEMA = (
    ROOT / "schemas/corporate-ownership-account-workspace-runtime.schema.json"
)
FIXTURES_SCHEMA = (
    ROOT / "schemas/corporate-ownership-account-workspace-fixtures.schema.json"
)
CASES_SCHEMA = (
    ROOT / "schemas/corporate-ownership-account-workspace-cases.schema.json"
)
RUNTIME = (
    ROOT / "data/corporate/corporate-ownership-account-workspace-runtime.v0.1.json"
)
FIXTURES = ROOT / "data/corporate/p12-conformance-fixtures.v0.1.json"
CASES = ROOT / "data/corporate/p12-adversarial-cases.v0.1.json"
ROLLBACK_PLAN = ROOT / "data/corporate/p12-rollback-plan.v0.1.json"
PROGRAMME = ROOT / "data/programmes/global-e2e-tasks-p10-p14.v1.4.json"
P02_LIBRARIES = ROOT / "data/ontology/library-contracts.v0.1.json"
P05_FOUNDATIONS = (
    ROOT / "data/foundations/foundational-library-runtime.v0.1.json"
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
P11_INFRASTRUCTURE = (
    ROOT
    / "data/infrastructure/"
    "infrastructure-project-pursuit-workspace-runtime.v0.1.json"
)
SOURCE_CATALOGUE = (
    ROOT
    / "data/sources/"
    "corporate-filings-and-ownership-catalogue.v0.1.json"
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
    P11_INFRASTRUCTURE,
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
p11 = load(P11_INFRASTRUCTURE)
catalogue = load(SOURCE_CATALOGUE)

for schema in (runtime_schema, fixtures_schema, cases_schema):
    Draft202012Validator.check_schema(schema)
Draft202012Validator(runtime_schema).validate(runtime)
Draft202012Validator(fixtures_schema).validate(fixtures)
Draft202012Validator(cases_schema).validate(cases)

task = next(
    item
    for item in programme["tasks"]
    if item["task_id"] == "AX-GE2E-P12-T01"
)
assert task["phase"] == "P12"
assert task["state"] == "BLOCKED"
assert task["objective"] == (
    "Implement filings, ownership and the Account Opportunity Workspace."
)
assert task["dependencies"]["tasks"] == ["AX-GE2E-P07-T01"]
assert task["prohibited_scope"] == [
    "No unauthorised launch, admission or canonical authority."
]

library = next(
    item
    for item in p02["contracts"]
    if item["library_id"] == "AX-LIB-O05"
)
binding = runtime["corporate_library_binding"]
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
assert p11["task_id"] == "AX-GE2E-P11-T01"
assert p11["canonical_activation_authorised"] is False
assert (
    runtime["dependency_status"]["p11_engineering_head"]
    == "315d88731939c1904fcca7be4e5b58d4615ab423"
)

assert catalogue["catalogue_id"] == "AX-CORPORATE-SOURCE-CATALOGUE-001"
assert catalogue["library_id"] == "AX-LIB-O05"
assert len(catalogue["sources"]) == 5
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
assert len(runtime["corporate_account_lifecycle"]["states"]) == 12
assert len(runtime["operating_pipeline"]["stages"]) == 11
assert len(runtime["filing_evidence_classes"]) == 10
assert len(runtime["ownership_interest_types"]) == 10
assert len(runtime["corporate_action_types"]) == 10
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
assert filing_current(
    status="PUBLISHED",
    version_current=True,
    withdrawn=False,
    superseded=False,
) == "PASS"
assert filing_current(
    status="PUBLISHED",
    version_current=False,
    withdrawn=False,
    superseded=True,
) == "REVIEW_REQUIRED"
assert filing_current(
    status="WITHDRAWN",
    version_current=True,
    withdrawn=True,
    superseded=False,
) == "DENY"

assert ownership_decision(
    observed=True,
    rights_active=True,
    percentage=Decimal("51"),
    chain_complete=True,
    contested=False,
    beneficial_owner=False,
    beneficial_owner_authorised=False,
) == "PASS"
assert ownership_decision(
    observed=True,
    rights_active=True,
    percentage=Decimal("101"),
    chain_complete=True,
    contested=False,
    beneficial_owner=False,
    beneficial_owner_authorised=False,
) == "DENY"
assert ownership_decision(
    observed=True,
    rights_active=True,
    percentage=Decimal("51"),
    chain_complete=True,
    contested=False,
    beneficial_owner=True,
    beneficial_owner_authorised=False,
) == "DENY"
assert ownership_decision(
    observed=False,
    rights_active=True,
    percentage=None,
    chain_complete=False,
    contested=True,
    beneficial_owner=False,
    beneficial_owner_authorised=False,
) == "REVIEW_REQUIRED"

assert control_decision(
    basis="REGISTRY_DECLARATION",
    observed=True,
    contested=False,
) == "PASS"
assert control_decision(
    basis="OWNERSHIP_ONLY",
    observed=True,
    contested=False,
) == "REVIEW_REQUIRED"

assert personal_data_decision(
    purpose_bound=True,
    legal_basis_recorded=True,
    minimised=True,
    rights_active=True,
) == "PASS"
assert personal_data_decision(
    purpose_bound=False,
    legal_basis_recorded=True,
    minimised=True,
    rights_active=True,
) == "DENY"

assert corporate_action_decision(
    state="COMPLETED",
    observed_evidence=True,
    required_approvals_observed=True,
) == "PASS"
assert corporate_action_decision(
    state="ANNOUNCED",
    observed_evidence=True,
    required_approvals_observed=False,
) == "REVIEW_REQUIRED"
assert corporate_action_decision(
    state="CANCELLED",
    observed_evidence=True,
    required_approvals_observed=True,
) == "DENY"

required_gates = runtime["readiness_gates"]
passing_gates = {gate: "PASS" for gate in required_gates}
assert account_readiness(passing_gates, required_gates) == "READY"
review_gates = dict(passing_gates)
review_gates["OWNERSHIP_CHAIN_RESOLVED"] = "REVIEW_REQUIRED"
assert account_readiness(
    review_gates,
    required_gates,
) == "REVIEW_REQUIRED"
deny_gates = dict(passing_gates)
deny_gates["RIGHTS_AND_PRIVACY_CURRENT"] = "DENY"
assert account_readiness(deny_gates, required_gates) == "DENY"
assert account_readiness({}, required_gates) == "NOT_READY"

assert may_execute_external_action(
    actor_type="HUMAN_EXTERNAL_ACTION_AUTHORITY",
    readiness="READY",
    approvals_current=True,
    rights_active=True,
    privacy_cleared=True,
    recipient_verified=True,
    channel_verified=True,
    audit_chain_valid=True,
    kill_switch_active=False,
)
assert not may_execute_external_action(
    actor_type="MODEL",
    readiness="READY",
    approvals_current=True,
    rights_active=True,
    privacy_cleared=True,
    recipient_verified=True,
    channel_verified=True,
    audit_chain_valid=True,
    kill_switch_active=False,
)
assert not may_execute_external_action(
    actor_type="HUMAN_EXTERNAL_ACTION_AUTHORITY",
    readiness="READY",
    approvals_current=True,
    rights_active=True,
    privacy_cleared=False,
    recipient_verified=True,
    channel_verified=True,
    audit_chain_valid=True,
    kill_switch_active=False,
)

assert normalize_account_outcome(
    "TRANSACTION_COMPLETED",
    observed_evidence=True,
) == "TRANSACTION_COMPLETED"
assert normalize_account_outcome(
    "TRANSACTION_COMPLETED",
    observed_evidence=False,
) == "UNKNOWN"
assert imported_authority("APPROVED") == "CANDIDATE_ONLY"

dependency = runtime["dependency_status"]
for key in (
    "p07_canonical_activation_authorised",
    "p11_canonical_activation_authorised",
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
    "task_id": "AX-GE2E-P12-T01",
    "domain_modules": len(modules),
    "corporate_library_bindings": 1,
    "source_catalogue_entries": len(catalogue["sources"]),
    "record_types": sum(len(item["record_types"]) for item in modules),
    "domain_invariants": sum(len(item["invariants"]) for item in modules),
    "lifecycle_states": len(
        runtime["corporate_account_lifecycle"]["states"]
    ),
    "pipeline_stages": len(runtime["operating_pipeline"]["stages"]),
    "filing_evidence_classes": len(runtime["filing_evidence_classes"]),
    "ownership_interest_types": len(runtime["ownership_interest_types"]),
    "corporate_action_types": len(runtime["corporate_action_types"]),
    "risk_classes": len(runtime["risk_classes"]),
    "readiness_gates": len(runtime["readiness_gates"]),
    "languages": len(runtime["languages"]),
    "rights_dimensions": len(runtime["rights_dimensions"]),
    "conformance_fixtures": fixture_count,
    "adversarial_cases": case_count,
    "canonical_activation_authorised": False,
    "p11_canonical_activation_authorised": False,
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
