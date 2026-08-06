#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from jsonschema import Draft202012Validator

from p09_grants_reference import (
    application_readiness,
    call_current,
    canonical_digest,
    consortium_decision,
    deadline_open,
    eligibility_decision,
    imported_authority,
    may_submit_application,
    normalize_award,
    validate_funding_request,
)

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_SCHEMA = ROOT / "schemas/grants-application-workspace-runtime.schema.json"
FIXTURES_SCHEMA = ROOT / "schemas/grants-application-workspace-fixtures.schema.json"
CASES_SCHEMA = ROOT / "schemas/grants-application-workspace-cases.schema.json"
RUNTIME = ROOT / "data/grants/grants-application-workspace-runtime.v0.1.json"
FIXTURES = ROOT / "data/grants/p09-conformance-fixtures.v0.1.json"
CASES = ROOT / "data/grants/p09-adversarial-cases.v0.1.json"
ROLLBACK_PLAN = ROOT / "data/grants/p09-rollback-plan.v0.1.json"
PROGRAMME = ROOT / "data/programmes/global-e2e-tasks-p05-p09.v1.4.json"
P02_LIBRARIES = ROOT / "data/ontology/library-contracts.v0.1.json"
P05_FOUNDATIONS = ROOT / "data/foundations/foundational-library-runtime.v0.1.json"
P06_DOCUMENTS = (
    ROOT
    / "data/document-intelligence/multilingual-document-intelligence-runtime.v0.1.json"
)
P07_OPERATIONS = (
    ROOT
    / "data/opportunity-operations/opportunity-operations-core-runtime.v0.1.json"
)
P08_PROCUREMENT = (
    ROOT
    / "data/procurement/global-procurement-bid-workspace-runtime.v0.1.json"
)
SOURCE_CATALOGUE = (
    ROOT
    / "data/sources/grants-and-non-dilutive-funding-catalogue.v0.1.json"
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
    P08_PROCUREMENT,
    SOURCE_CATALOGUE,
)
for path in paths:
    assert path.is_file(), f"missing {path.relative_to(ROOT)}"

runtime_schema = json.loads(RUNTIME_SCHEMA.read_text(encoding="utf-8"))
fixtures_schema = json.loads(FIXTURES_SCHEMA.read_text(encoding="utf-8"))
cases_schema = json.loads(CASES_SCHEMA.read_text(encoding="utf-8"))
runtime = json.loads(RUNTIME.read_text(encoding="utf-8"))
fixtures = json.loads(FIXTURES.read_text(encoding="utf-8"))
cases = json.loads(CASES.read_text(encoding="utf-8"))
programme = json.loads(PROGRAMME.read_text(encoding="utf-8"))
p02 = json.loads(P02_LIBRARIES.read_text(encoding="utf-8"))
p05 = json.loads(P05_FOUNDATIONS.read_text(encoding="utf-8"))
p06 = json.loads(P06_DOCUMENTS.read_text(encoding="utf-8"))
p07 = json.loads(P07_OPERATIONS.read_text(encoding="utf-8"))
p08 = json.loads(P08_PROCUREMENT.read_text(encoding="utf-8"))
catalogue = json.loads(SOURCE_CATALOGUE.read_text(encoding="utf-8"))

for schema in (runtime_schema, fixtures_schema, cases_schema):
    Draft202012Validator.check_schema(schema)

Draft202012Validator(runtime_schema).validate(runtime)
Draft202012Validator(fixtures_schema).validate(fixtures)
Draft202012Validator(cases_schema).validate(cases)

task = next(
    item for item in programme["tasks"] if item["task_id"] == "AX-GE2E-P09-T01"
)
assert task["state"] == "BLOCKED"
assert task["objective"] == (
    "Implement grants intelligence and the Application Workspace."
)
assert task["dependencies"]["tasks"] == ["AX-GE2E-P07-T01"]
assert task["dependencies"]["phases"] == ["P07"]
assert task["acceptance_evidence"][0]["status"] == "MISSING"

dependency = runtime["dependency_status"]
assert dependency["normative_dependency_task"] == "AX-GE2E-P07-T01"
assert dependency["p07_engineering_head"] == "e30f800cb284f1381c28c4ccbc116a8da4a9fe92"
assert dependency["p07_engineering_evidence_ready"] is True
assert dependency["engineering_base_task"] == "AX-GE2E-P08-T01"
assert dependency["p08_engineering_head"] == "3e28e08a12d02701d4ab312edfbedc56fcd8bb59"
assert dependency["p08_engineering_evidence_ready"] is True
assert dependency["p08_canonical_activation_authorised"] is False
assert dependency["p07_canonical_activation_authorised"] is False
assert dependency["p06_canonical_activation_authorised"] is False
assert dependency["p05_canonical_activation_authorised"] is False
assert dependency["p04_canonical_activation_authorised"] is False
assert dependency["p03_canonical_activation_authorised"] is False
assert dependency["p02_canonical_activation_authorised"] is False
assert dependency["p01_dependency_satisfied"] is False
assert dependency["merge_to_main_allowed"] is False
assert runtime["canonical_activation_authorised"] is False
assert runtime["acceptance_gate"]["current_decision"] == (
    "NOT_READY_FOR_CANONICAL_ACTIVATION"
)

grant_contracts = [
    item
    for item in p02["contracts"]
    if item["library_id"] == "AX-LIB-O02"
]
assert len(grant_contracts) == 1
grant_contract = grant_contracts[0]
binding = runtime["grants_library_binding"]
assert grant_contract["kind"] == "OPPORTUNITY"
assert grant_contract["canonical_name"] == binding["canonical_name"]
assert grant_contract["workspace_type"] == binding["workspace_type"]
assert grant_contract["entities"] == binding["entities"]
assert grant_contract["predicates"] == binding["predicates"]
assert grant_contract["events"] == binding["events"]
assert grant_contract["taxonomy_refs"] == binding["taxonomy_refs"]
assert len(grant_contract["dependencies"]) == 7
assert "no application submission authority" in grant_contract["exclusions"]

expected_modules = [
    "CALL_REGISTRY",
    "FUNDER_PROGRAMME",
    "ELIGIBILITY_SCOPE",
    "CONSORTIUM_PARTNERS",
    "APPLICATION_WORKSPACE",
    "NARRATIVE_EVIDENCE",
    "BUDGET_CO_FINANCING",
    "SUBMISSION_AWARD",
]
assert [item["module_id"] for item in runtime["domain_modules"]] == expected_modules
assert len({item["service_id"] for item in runtime["domain_modules"]}) == 8
assert sum(len(item["record_types"]) for item in runtime["domain_modules"]) == 32
assert sum(len(item["invariants"]) for item in runtime["domain_modules"]) == 48
assert len(runtime["call_application_lifecycle"]["states"]) == 12
assert len(runtime["operating_pipeline"]["stages"]) == 11
assert len(runtime["criterion_contract"]["classes"]) == 10
assert len(runtime["readiness_contract"]["gates"]) == 12

rights = runtime["rights_dimensions"]
assert rights == p05["rights_dimensions"]
assert rights == p06["rights_dimensions"]
assert rights == p07["rights_dimensions"]
assert rights == p08["rights_dimensions"]
assert len(rights) == 10
assert runtime["multilingual_contract"]["languages"] == [
    item["language_tag"] for item in p06["language_profile"]["languages"]
]
assert len(runtime["multilingual_contract"]["languages"]) == 6

assert catalogue["catalogue_id"] == "AX-GRANTS-SOURCE-CATALOGUE-001"
assert catalogue["library_id"] == "AX-LIB-O02"
assert catalogue["status"] == "RESEARCH_CATALOGUE_NOT_PRODUCT_AVAILABILITY"
assert len(catalogue["sources"]) == 6
assert catalogue["principles"]["listed_does_not_mean_admitted"] is True
assert catalogue["principles"]["public_coverage_authorised"] is False
assert all(item["product_admitted"] is False for item in catalogue["sources"])
assert all(item["rights_status"] == "UNREVIEWED" for item in catalogue["sources"])
assert runtime["source_catalogue_contract"]["source_count"] == 6
assert runtime["source_catalogue_contract"]["all_sources_product_admitted"] is False
assert runtime["source_catalogue_contract"]["all_rights_reviewed"] is False
assert runtime["source_catalogue_contract"]["public_coverage_authorised"] is False

fixture_modules = fixtures["modules"]
fixture_classes = fixtures["fixture_classes"]
assert fixture_modules == expected_modules
assert fixture_classes == [
    "HAPPY_PATH",
    "INCOMPLETE_CONTEXT",
    "REVOKED_DEPENDENCY",
    "CROSS_TENANT",
    "AUTHORITY_ESCALATION",
]
assert len(fixture_modules) * len(fixture_classes) == 40
assert fixtures["expected"]["canonical_write"] is False
assert fixtures["expected"]["external_submission"] is False
assert fixtures["decision_by_class"]["HAPPY_PATH"] == "CANDIDATE"
assert fixtures["decision_by_class"]["INCOMPLETE_CONTEXT"] == "REVIEW_REQUIRED"
assert all(
    fixtures["decision_by_class"][name] == "DENY"
    for name in ("REVOKED_DEPENDENCY", "CROSS_TENANT", "AUTHORITY_ESCALATION")
)

case_modules = cases["modules"]
threat_profiles = cases["threat_profiles"]
assert case_modules == [*expected_modules, "CROSS_MODULE"]
assert len(case_modules) * len(threat_profiles) == 72
assert len({item["threat_id"] for item in threat_profiles}) == 8
assert cases["expected"]["canonical_delta"] == 0
assert cases["expected"]["external_submission_delta"] == 0
assert {item["expected_decision"] for item in threat_profiles} == {
    "DENY",
    "REVIEW_REQUIRED",
    "BLOCK",
    "QUARANTINE",
}

assert call_current("OPEN", False, True, True) is True
assert call_current("OPEN", False, False, True) is False
assert call_current("CLOSED", False, True, True) is False

now = datetime(2026, 7, 30, 12, tzinfo=UTC)
deadline = datetime(2026, 7, 31, 12, tzinfo=UTC)
assert deadline_open(now, deadline, True, True) is True
assert deadline_open(now, deadline, False, True) is False

assert eligibility_decision(["PASS", "NOT_APPLICABLE"], []) == "PASS"
assert eligibility_decision(["PASS", "UNKNOWN"], []) == "REVIEW_REQUIRED"
assert eligibility_decision(["PASS"], ["SANCTIONS"]) == "DENY"

required_roles = {"COORDINATOR", "BENEFICIARY"}
assert (
    consortium_decision(
        required_roles,
        {"COORDINATOR", "BENEFICIARY"},
        2,
        2,
        5,
        True,
        True,
    )
    == "PASS"
)
assert (
    consortium_decision(
        required_roles,
        {"BENEFICIARY"},
        2,
        2,
        5,
        True,
        True,
    )
    == "DENY"
)
assert (
    consortium_decision(
        required_roles,
        {"COORDINATOR", "BENEFICIARY"},
        2,
        2,
        5,
        True,
        False,
    )
    == "REVIEW_REQUIRED"
)

assert (
    validate_funding_request(
        Decimal("100"),
        Decimal("60"),
        Decimal("0.70"),
        Decimal("80"),
        True,
    )
    == "PASS"
)
assert (
    validate_funding_request(
        Decimal("100"),
        Decimal("80"),
        Decimal("0.70"),
        Decimal("90"),
        True,
    )
    == "DENY"
)
assert (
    validate_funding_request(
        Decimal("100"),
        Decimal("60"),
        Decimal("0.70"),
        Decimal("80"),
        False,
    )
    == "REVIEW_REQUIRED"
)

required_gates = set(runtime["readiness_contract"]["gates"])
passing_gates = {gate: "PASS" for gate in required_gates}
assert application_readiness(passing_gates, required_gates) == "READY"
review_gates = dict(passing_gates)
review_gates["CO_FINANCING_CONFIRMED"] = "UNKNOWN"
assert application_readiness(review_gates, required_gates) == "REVIEW_REQUIRED"
deny_gates = dict(passing_gates)
deny_gates["APPLICANT_ELIGIBLE"] = "DENY"
assert application_readiness(deny_gates, required_gates) == "DENY"

required_approvals = set(
    runtime["submission_award_contract"]["required_approvals"]
)
assert may_submit_application(
    "HUMAN_SUBMISSION_AUTHORITY",
    "READY",
    required_approvals,
    required_approvals,
    True,
    True,
    True,
    False,
    True,
) is True
assert may_submit_application(
    "MODEL",
    "READY",
    required_approvals,
    required_approvals,
    True,
    True,
    True,
    False,
    True,
) is False
assert may_submit_application(
    "HUMAN_SUBMISSION_AUTHORITY",
    "READY",
    required_approvals - {"LEGAL"},
    required_approvals,
    True,
    True,
    True,
    False,
    True,
) is False

assert normalize_award(False, "AWARDED") == "UNKNOWN"
assert normalize_award(True, "AWARDED") == "AWARDED"
assert normalize_award(True, "UNSUPPORTED") == "UNKNOWN"
assert imported_authority(True, True, True) == "CANDIDATE_ONLY"
assert imported_authority(False, True, True) == "QUARANTINE"
assert canonical_digest({"b": 2, "a": 1}) == canonical_digest(
    {"a": 1, "b": 2}
)

result = {
    "status": "PASS",
    "task_id": "AX-GE2E-P09-T01",
    "domain_modules": len(runtime["domain_modules"]),
    "grants_library_bindings": len(grant_contracts),
    "source_catalogue_entries": len(catalogue["sources"]),
    "record_types": sum(
        len(item["record_types"]) for item in runtime["domain_modules"]
    ),
    "domain_invariants": sum(
        len(item["invariants"]) for item in runtime["domain_modules"]
    ),
    "lifecycle_states": len(runtime["call_application_lifecycle"]["states"]),
    "pipeline_stages": len(runtime["operating_pipeline"]["stages"]),
    "criterion_classes": len(runtime["criterion_contract"]["classes"]),
    "readiness_gates": len(runtime["readiness_contract"]["gates"]),
    "languages": len(runtime["multilingual_contract"]["languages"]),
    "rights_dimensions": len(rights),
    "conformance_fixtures": len(fixture_modules) * len(fixture_classes),
    "adversarial_cases": len(case_modules) * len(threat_profiles),
    "canonical_activation_authorised": runtime[
        "canonical_activation_authorised"
    ],
    "p08_canonical_activation_authorised": dependency[
        "p08_canonical_activation_authorised"
    ],
    "p07_canonical_activation_authorised": dependency[
        "p07_canonical_activation_authorised"
    ],
    "p06_canonical_activation_authorised": dependency[
        "p06_canonical_activation_authorised"
    ],
    "p05_canonical_activation_authorised": dependency[
        "p05_canonical_activation_authorised"
    ],
    "p04_canonical_activation_authorised": dependency[
        "p04_canonical_activation_authorised"
    ],
    "p03_canonical_activation_authorised": dependency[
        "p03_canonical_activation_authorised"
    ],
    "p02_canonical_activation_authorised": dependency[
        "p02_canonical_activation_authorised"
    ],
    "p01_dependency_satisfied": dependency["p01_dependency_satisfied"],
}
print(json.dumps(result, sort_keys=True))
