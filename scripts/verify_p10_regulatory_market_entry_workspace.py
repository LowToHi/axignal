#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from jsonschema import Draft202012Validator

from p10_regulatory_reference import (
    applicability_decision,
    canonical_digest,
    control_coverage_decision,
    imported_authority,
    instrument_current,
    legal_effect_decision,
    market_entry_readiness,
    may_file_regulatory_action,
    normalize_enforcement_outcome,
)

ROOT = Path(__file__).resolve().parents[1]
PATHS = {
    "runtime": ROOT / "data/regulatory/regulatory-market-entry-workspace-runtime.v0.1.json",
    "fixtures": ROOT / "data/regulatory/p10-conformance-fixtures.v0.1.json",
    "cases": ROOT / "data/regulatory/p10-adversarial-cases.v0.1.json",
    "catalogue": ROOT / "data/sources/regulatory-and-policy-demand-catalogue.v0.1.json",
    "tasks": ROOT / "data/programmes/global-e2e-tasks-p10-p14.v1.4.json",
    "libraries": ROOT / "data/ontology/library-contracts.v0.1.json",
    "p07": ROOT / "data/opportunity-operations/opportunity-operations-core-runtime.v0.1.json",
    "p08": ROOT / "data/procurement/global-procurement-bid-workspace-runtime.v0.1.json",
    "p09": ROOT / "data/grants/grants-application-workspace-runtime.v0.1.json",
    "runtime_schema": ROOT / "schemas/regulatory-market-entry-workspace-runtime.schema.json",
    "fixtures_schema": ROOT / "schemas/regulatory-market-entry-workspace-fixtures.schema.json",
    "cases_schema": ROOT / "schemas/regulatory-market-entry-workspace-cases.schema.json",
}


def load(name: str) -> dict:
    path = PATHS[name]
    assert path.is_file(), f"missing {path.relative_to(ROOT)}"
    return json.loads(path.read_text(encoding="utf-8"))


runtime = load("runtime")
fixtures = load("fixtures")
cases = load("cases")
catalogue = load("catalogue")
tasks = load("tasks")
libraries = load("libraries")
p07 = load("p07")
p08 = load("p08")
p09 = load("p09")

for instance_name, schema_name in (
    ("runtime", "runtime_schema"),
    ("fixtures", "fixtures_schema"),
    ("cases", "cases_schema"),
):
    instance = locals()[instance_name]
    schema = load(schema_name)
    Draft202012Validator.check_schema(schema)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(instance),
        key=lambda error: list(error.path),
    )
    assert not errors, [error.message for error in errors]

task = next(
    item for item in tasks["tasks"]
    if item["task_id"] == "AX-GE2E-P10-T01"
)
assert task["phase"] == "P10"
assert task["state"] == "BLOCKED"
assert task["dependencies"]["tasks"] == ["AX-GE2E-P07-T01"]
assert task["prohibited_scope"] == [
    "No unauthorised launch, admission or canonical authority."
]

library = next(
    item for item in libraries["contracts"]
    if item["library_id"] == "AX-LIB-O03"
)
binding = runtime["regulatory_library_binding"]
assert library["canonical_name"] == "Regulatory and Policy Demand"
assert library["workspace_type"] == binding["workspace_type"]
for key in ("entities", "predicates", "events", "taxonomy_refs"):
    assert binding[key] == library[key]

dependency = runtime["dependency_status"]
assert dependency["normative_dependency_task"] == "AX-GE2E-P07-T01"
assert dependency["engineering_base_task"] == "AX-GE2E-P09-T01"
assert dependency["p09_engineering_head"] == (
    "841e068f0a8e86e6d89733d3958ecd43f0d7eca7"
)
assert dependency["merge_to_main_allowed"] is False
assert runtime["canonical_activation_authorised"] is False
for upstream in (p07, p08, p09):
    assert upstream["canonical_activation_authorised"] is False

modules = runtime["domain_modules"]
module_ids = [module["module_id"] for module in modules]
assert len(modules) == len(set(module_ids)) == 8
assert sum(len(module["record_types"]) for module in modules) == 32
assert sum(module["invariant_count"] for module in modules) == 48

lifecycle = runtime["regulatory_market_entry_lifecycle"]
assert len(lifecycle["states"]) == 12
assert len(lifecycle["allowed_transitions"]) == 23
assert "PROPOSED->APPLICABLE" not in lifecycle["allowed_transitions"]
assert "CONSULTATION_OPEN->APPLICABLE" not in lifecycle["allowed_transitions"]

pipeline = runtime["operating_pipeline"]
assert len(pipeline["stages"]) == 11
assert pipeline["default_decision"] == "DENY"
assert pipeline["indeterminate_as"] == "DENY"
assert pipeline["stages"][8]["authority"] == "HUMAN"
assert pipeline["stages"][9]["authority"] == "HUMAN"

assert len(runtime["applicability_contract"]["classes"]) == 10
assert len(runtime["obligation_contract"]["types"]) == 10
assert len(runtime["readiness_contract"]["gates"]) == 12
assert runtime["multilingual_contract"]["languages"] == [
    "en", "es", "fr", "de", "pt", "it"
]
assert len(runtime["rights_dimensions"]) == 10

source_contract = runtime["source_catalogue_contract"]
assert catalogue["catalogue_id"] == source_contract["catalogue_id"]
assert len(catalogue["sources"]) == source_contract["source_count"] == 6
assert all(source["product_admitted"] is False for source in catalogue["sources"])
assert all(source["rights_status"] == "UNREVIEWED" for source in catalogue["sources"])
assert catalogue["principles"]["public_coverage_authorised"] is False
assert source_contract["all_sources_product_admitted"] is False
assert source_contract["all_rights_reviewed"] is False
assert source_contract["public_coverage_authorised"] is False

authority = runtime["authority_model"]
assert authority["actors"]["MODEL"] == "PROPOSAL_ONLY"
assert authority["actors"]["WORKER"] == "BOUNDED_WORK_MUTATION"
assert authority["actors"]["HUMAN_FILING_AUTHORITY"] == "EXTERNAL_FILING_ONLY"
assert authority["least_authority_rule"] is True
assert "MODEL_DECLARE_APPLICABILITY" in authority["forbidden_actions"]
assert "WORKER_FILE" in authority["forbidden_actions"]

fixture_matrix = {
    (module_id, fixture_class)
    for module_id in fixtures["modules"]
    for fixture_class in fixtures["fixture_classes"]
}
assert fixtures["modules"] == module_ids
assert len(fixture_matrix) == fixtures["expected_fixture_count"] == 40
assert fixtures["canonical_write"] is False
assert fixtures["external_filing"] is False

case_matrix = {
    (scope, threat["threat"])
    for scope in cases["scopes"]
    for threat in cases["threats"]
}
assert len(case_matrix) == cases["expected_case_count"] == 72
assert cases["canonical_delta"] == 0
assert cases["external_filing_delta"] == 0

assert canonical_digest({"b": 2, "a": 1}) == canonical_digest({"a": 1, "b": 2})
assert instrument_current("APPLICABLE", False, True, True) is True
assert instrument_current("PROPOSED", False, True, True) is False
assert instrument_current("APPLICABLE", True, True, True) is False

now = datetime(2026, 7, 30, 12, tzinfo=UTC)
effective = datetime(2026, 7, 29, 12, tzinfo=UTC)
applicable_at = datetime(2026, 7, 30, 10, tzinfo=UTC)
assert legal_effect_decision(
    True, True, effective, applicable_at, now, True
) == "APPLICABLE"
assert legal_effect_decision(
    False, False, None, None, now, True
) == "NOT_BINDING"
assert legal_effect_decision(
    True, True, effective, applicable_at, now, False
) == "REVIEW_REQUIRED"

assert applicability_decision(["PASS", "PASS"], False, False) == "APPLIES"
assert applicability_decision(["PASS", "UNKNOWN"], False, False) == "REVIEW_REQUIRED"
assert applicability_decision(["PASS", "FAIL"], False, False) == "DOES_NOT_APPLY"
assert applicability_decision(["PASS", "PASS"], False, True) == "EXEMPT"

requirements = {"r1": "EFFECTIVE", "r2": "TESTED"}
assert control_coverage_decision(requirements, {"r1", "r2"}) == "PASS"
assert control_coverage_decision(
    {"r1": "PROPOSED", "r2": "TESTED"}, {"r1", "r2"}
) == "REVIEW_REQUIRED"

required_gates = set(runtime["readiness_contract"]["gates"])
passing_gates = {gate: "PASS" for gate in required_gates}
assert market_entry_readiness(passing_gates, required_gates) == "READY"
review_gates = dict(passing_gates)
review_gates["APPLICABILITY_ASSESSED"] = "CONTESTED"
assert market_entry_readiness(review_gates, required_gates) == "REVIEW_REQUIRED"

approvals = set(runtime["authorisation_filing_contract"]["required_approvals"])
assert may_file_regulatory_action(
    "HUMAN_FILING_AUTHORITY", "READY", approvals, approvals,
    True, True, True, True, False, True
) is True
assert may_file_regulatory_action(
    "MODEL", "READY", approvals, approvals,
    True, True, True, True, False, True
) is False
assert may_file_regulatory_action(
    "HUMAN_FILING_AUTHORITY", "READY", approvals, approvals,
    True, True, True, True, True, True
) is False

assert normalize_enforcement_outcome(True, "SANCTIONED") == "SANCTIONED"
assert normalize_enforcement_outcome(False, "SANCTIONED") == "UNKNOWN"
assert imported_authority(True, True, True) == "CANDIDATE_ONLY"
assert imported_authority(False, True, True) == "QUARANTINE"

result = {
    "status": "PASS",
    "task_id": "AX-GE2E-P10-T01",
    "domain_modules": len(modules),
    "regulatory_library_bindings": 1,
    "source_catalogue_entries": len(catalogue["sources"]),
    "record_types": sum(len(module["record_types"]) for module in modules),
    "domain_invariants": sum(module["invariant_count"] for module in modules),
    "lifecycle_states": len(lifecycle["states"]),
    "pipeline_stages": len(pipeline["stages"]),
    "applicability_classes": len(runtime["applicability_contract"]["classes"]),
    "obligation_types": len(runtime["obligation_contract"]["types"]),
    "readiness_gates": len(runtime["readiness_contract"]["gates"]),
    "languages": len(runtime["multilingual_contract"]["languages"]),
    "rights_dimensions": len(runtime["rights_dimensions"]),
    "conformance_fixtures": len(fixture_matrix),
    "adversarial_cases": len(case_matrix),
    "canonical_activation_authorised": False,
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
