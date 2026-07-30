#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from jsonschema import Draft202012Validator

from p08_procurement_reference import (
    canonical_digest,
    commercial_validation,
    deadline_decision,
    eligibility_decision,
    lot_selection_decision,
    may_submit,
    normalize_award,
    notice_currentness,
    readiness_decision,
    requirement_coverage,
)

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_SCHEMA = ROOT / "schemas/global-procurement-bid-workspace-runtime.schema.json"
FIXTURES_SCHEMA = ROOT / "schemas/global-procurement-bid-workspace-fixtures.schema.json"
CASES_SCHEMA = ROOT / "schemas/global-procurement-bid-workspace-cases.schema.json"
RUNTIME = ROOT / "data/procurement/global-procurement-bid-workspace-runtime.v0.1.json"
FIXTURES = ROOT / "data/procurement/p08-conformance-fixtures.v0.1.json"
CASES = ROOT / "data/procurement/p08-adversarial-cases.v0.1.json"
PROGRAMME = ROOT / "data/programmes/global-e2e-tasks-p05-p09.v1.4.json"
P02_LIBRARIES = ROOT / "data/ontology/library-contracts.v0.1.json"
P06_DOCUMENTS = ROOT / (
    "data/document-intelligence/"
    "multilingual-document-intelligence-runtime.v0.1.json"
)
P07_OPERATIONS = ROOT / (
    "data/opportunity-operations/"
    "opportunity-operations-core-runtime.v0.1.json"
)

paths = (
    RUNTIME_SCHEMA,
    FIXTURES_SCHEMA,
    CASES_SCHEMA,
    RUNTIME,
    FIXTURES,
    CASES,
    PROGRAMME,
    P02_LIBRARIES,
    P06_DOCUMENTS,
    P07_OPERATIONS,
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
p06 = json.loads(P06_DOCUMENTS.read_text(encoding="utf-8"))
p07 = json.loads(P07_OPERATIONS.read_text(encoding="utf-8"))

for schema in (runtime_schema, fixtures_schema, cases_schema):
    Draft202012Validator.check_schema(schema)

Draft202012Validator(runtime_schema).validate(runtime)
Draft202012Validator(fixtures_schema).validate(fixtures)
Draft202012Validator(cases_schema).validate(cases)

task = next(item for item in programme["tasks"] if item["task_id"] == "AX-GE2E-P08-T01")
assert task["state"] == "BLOCKED"
assert task["dependencies"]["tasks"] == ["AX-GE2E-P07-T01"]
assert task["dependencies"]["phases"] == ["P07"]
assert task["acceptance_evidence"][0]["status"] == "MISSING"

dependency = runtime["dependency_status"]
assert dependency["p07_engineering_head"] == (
    "e30f800cb284f1381c28c4ccbc116a8da4a9fe92"
)
assert dependency["p07_engineering_evidence_ready"] is True
for key in (
    "p07_canonical_activation_authorised",
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
assert runtime["acceptance_gate"]["current_decision"] == (
    "NOT_READY_FOR_CANONICAL_ACTIVATION"
)

expected_modules = [
    "NOTICE_REGISTRY",
    "BUYER_PROCEDURE",
    "LOT_STRUCTURE",
    "REQUIREMENT_ELIGIBILITY",
    "BID_WORKSPACE",
    "DOCUMENT_PACK",
    "COMMERCIAL_MODEL",
    "SUBMISSION_AWARD",
]
assert [item["module_id"] for item in runtime["domain_modules"]] == expected_modules
assert len({item["service_id"] for item in runtime["domain_modules"]}) == 8
assert sum(len(item["record_types"]) for item in runtime["domain_modules"]) == 32
assert sum(len(item["invariants"]) for item in runtime["domain_modules"]) == 48

procurement = next(item for item in p02["contracts"] if item["library_id"] == "AX-LIB-O01")
binding = runtime["procurement_library_binding"]
assert procurement["kind"] == "OPPORTUNITY"
assert procurement["workspace_type"] == "Bid Workspace"
assert binding["library_id"] == procurement["library_id"]
assert binding["workspace_type"] == procurement["workspace_type"]
assert binding["entities"] == procurement["entities"]
assert binding["predicates"] == procurement["predicates"]
assert binding["events"] == procurement["events"]
assert binding["taxonomy_refs"] == procurement["taxonomy_refs"]
assert len(procurement["dependencies"]) == 7

assert runtime["rights_dimensions"] == p07["rights_dimensions"]
assert len(runtime["rights_dimensions"]) == 10
p06_languages = [item["language_tag"] for item in p06["language_profile"]["languages"]]
assert runtime["multilingual_contract"]["languages"] == p06_languages
assert len(runtime["notice_procedure_lifecycle"]["states"]) == 12
assert len(runtime["procurement_pipeline"]["stages"]) == 11
assert len(runtime["requirement_eligibility_contract"]["requirement_classes"]) == 9
assert len(runtime["readiness_contract"]["gates"]) == 10
assert "PURSUE" in p07["approval_contract"]["approval_types"]
assert "SUBMISSION_OR_ACTIVATION" in p07["approval_contract"]["approval_types"]

fixture_counts = Counter(item["module_id"] for item in fixtures["fixtures"])
assert fixture_counts == Counter({module_id: 5 for module_id in expected_modules})
assert len(fixtures["fixtures"]) == 40
assert all(not item["expected"]["canonical_write"] for item in fixtures["fixtures"])
assert all(not item["expected"]["external_submission"] for item in fixtures["fixtures"])
assert len({item["fixture_id"] for item in fixtures["fixtures"]}) == 40

case_counts = Counter(item["module_id"] for item in cases["cases"])
for module_id in expected_modules:
    assert case_counts[module_id] == 8
assert case_counts["CROSS_MODULE"] == 8
assert len(cases["cases"]) == 72
assert all(item["canonical_delta"] == 0 for item in cases["cases"])
assert all(item["external_submission_delta"] == 0 for item in cases["cases"])
assert len({item["case_id"] for item in cases["cases"]}) == 72

assert notice_currentness("CURRENT", False, True) == "PASS"
assert notice_currentness("WITHDRAWN", False, True) == "DENY"
assert notice_currentness("CURRENT", True, True) == "REVIEW_REQUIRED"
assert deadline_decision(
    "2026-07-30T12:00:00+00:00",
    "2026-07-31T12:00:00+00:00",
    True,
    False,
) == "PASS"
assert deadline_decision(
    "2026-07-31T13:00:00+00:00",
    "2026-07-31T12:00:00+00:00",
    True,
    False,
) == "DENY"
assert eligibility_decision(4, 4, 0, False) == "PASS"
assert eligibility_decision(4, 3, 1, False) == "REVIEW_REQUIRED"
assert eligibility_decision(4, 4, 0, True) == "FAIL"
exclusive = {frozenset({"lot-a", "lot-b"})}
assert lot_selection_decision({"lot-a"}, {"lot-a", "lot-b"}, exclusive) == "PASS"
assert lot_selection_decision({"lot-a", "lot-b"}, {"lot-a", "lot-b"}, exclusive) == "DENY"
assert requirement_coverage({"r1"}, {"r1"}, set(), set()) == "PASS"
assert requirement_coverage({"r1"}, set(), set(), {"r1"}) == "REVIEW_REQUIRED"
assert readiness_decision({"a": "PASS", "b": "PASS"}) == "READY"
assert readiness_decision({"a": "PASS", "b": "DENY"}) == "DENY"
assert commercial_validation(True, True, True, True, True) == "PASS"
assert commercial_validation(True, True, False, False, False) == "DENY"
assert may_submit(
    "HUMAN_SUBMISSION_AUTHORITY",
    "READY",
    True,
    True,
    True,
    True,
) is True
assert may_submit("WORKER", "READY", True, True, True, True) is False
assert normalize_award(False, "AWARD_OBSERVED") == "UNKNOWN"
assert normalize_award(True, "AWARD_OBSERVED") == "AWARD_OBSERVED"
assert canonical_digest({"b": 2, "a": 1}) == canonical_digest({"a": 1, "b": 2})

result = {
    "status": "PASS",
    "task_id": "AX-GE2E-P08-T01",
    "domain_modules": len(runtime["domain_modules"]),
    "procurement_library_bindings": 1,
    "record_types": sum(len(item["record_types"]) for item in runtime["domain_modules"]),
    "domain_invariants": sum(len(item["invariants"]) for item in runtime["domain_modules"]),
    "notice_states": len(runtime["notice_procedure_lifecycle"]["states"]),
    "pipeline_stages": len(runtime["procurement_pipeline"]["stages"]),
    "requirement_classes": len(
        runtime["requirement_eligibility_contract"]["requirement_classes"]
    ),
    "readiness_gates": len(runtime["readiness_contract"]["gates"]),
    "languages": len(runtime["multilingual_contract"]["languages"]),
    "rights_dimensions": len(runtime["rights_dimensions"]),
    "conformance_fixtures": len(fixtures["fixtures"]),
    "adversarial_cases": len(cases["cases"]),
    "canonical_activation_authorised": runtime["canonical_activation_authorised"],
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
