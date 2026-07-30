#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from jsonschema import Draft202012Validator

from p07_opportunity_operations_reference import (
    approval_valid,
    audit_event_hash,
    canonical_digest,
    import_authority,
    learning_state,
    may_execute_external_action,
    normalize_outcome,
    qualification_decision,
    transition_allowed,
    work_readiness,
)

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_SCHEMA = ROOT / "schemas/opportunity-operations-core-runtime.schema.json"
FIXTURES_SCHEMA = ROOT / "schemas/opportunity-operations-core-fixtures.schema.json"
CASES_SCHEMA = ROOT / "schemas/opportunity-operations-core-cases.schema.json"
RUNTIME = ROOT / "data/opportunity-operations/opportunity-operations-core-runtime.v0.1.json"
FIXTURES = ROOT / "data/opportunity-operations/p07-conformance-fixtures.v0.1.json"
CASES = ROOT / "data/opportunity-operations/p07-adversarial-cases.v0.1.json"
PROGRAMME = ROOT / "data/programmes/global-e2e-tasks-p05-p09.v1.4.json"
P02_LIBRARIES = ROOT / "data/ontology/library-contracts.v0.1.json"
P05_FOUNDATIONS = ROOT / "data/foundations/foundational-library-runtime.v0.1.json"
P06_DOCUMENTS = (
    ROOT
    / "data/document-intelligence/multilingual-document-intelligence-runtime.v0.1.json"
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
    P05_FOUNDATIONS,
    P06_DOCUMENTS,
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

for schema in (runtime_schema, fixtures_schema, cases_schema):
    Draft202012Validator.check_schema(schema)

Draft202012Validator(runtime_schema).validate(runtime)
Draft202012Validator(fixtures_schema).validate(fixtures)
Draft202012Validator(cases_schema).validate(cases)

task = next(item for item in programme["tasks"] if item["task_id"] == "AX-GE2E-P07-T01")
assert task["state"] == "BLOCKED"
assert task["dependencies"]["tasks"] == ["AX-GE2E-P06-T01"]
assert task["dependencies"]["phases"] == ["P06"]
assert task["acceptance_evidence"][0]["status"] == "MISSING"

dependency = runtime["dependency_status"]
assert dependency["p06_engineering_head"] == "d6317f32caad4f916f1871c23753bacd36b4d9d6"
assert dependency["p06_engineering_evidence_ready"] is True
assert dependency["p06_canonical_activation_authorised"] is False
assert dependency["p05_canonical_activation_authorised"] is False
assert dependency["p04_canonical_activation_authorised"] is False
assert dependency["p03_canonical_activation_authorised"] is False
assert dependency["p02_canonical_activation_authorised"] is False
assert dependency["p01_dependency_satisfied"] is False
assert dependency["merge_to_main_allowed"] is False
assert runtime["canonical_activation_authorised"] is False
assert runtime["acceptance_gate"]["current_decision"] == "NOT_READY_FOR_CANONICAL_ACTIVATION"

expected_modules = [
    "OPPORTUNITY",
    "PURSUIT",
    "DECISION",
    "WORK",
    "APPROVAL",
    "OUTCOME",
    "LEARNING_PORTABILITY",
]
assert [item["module_id"] for item in runtime["core_modules"]] == expected_modules
assert len({item["service_id"] for item in runtime["core_modules"]}) == 7
assert sum(len(item["record_types"]) for item in runtime["core_modules"]) == 23
assert sum(len(item["invariants"]) for item in runtime["core_modules"]) == 42

opportunity_contracts = [item for item in p02["contracts"] if item["kind"] == "OPPORTUNITY"]
expected_libraries = [f"AX-LIB-O{index:02d}" for index in range(1, 10)]
assert [item["library_id"] for item in opportunity_contracts] == expected_libraries
assert runtime["opportunity_lifecycle"]["states"] == p02["profiles"]["opportunity_lifecycle"]
assert all(len(item["dependencies"]) == 7 for item in opportunity_contracts)
assert all(item["workspace_type"] for item in opportunity_contracts)

rights = runtime["rights_dimensions"]
assert rights == p05["rights_dimensions"]
assert rights == p06["rights_dimensions"]
assert len(rights) == 10
assert len(runtime["operating_pipeline"]["stages"]) == 10
assert len(runtime["approval_contract"]["approval_types"]) == 8
assert len(runtime["audit_contract"]["event_types"]) == 14

fixture_counts = Counter(item["module_id"] for item in fixtures["fixtures"])
assert fixture_counts == Counter({module_id: 5 for module_id in expected_modules})
assert len(fixtures["fixtures"]) == 35
assert all(item["expected"]["canonical_write"] is False for item in fixtures["fixtures"])
assert all(item["expected"]["external_action"] is False for item in fixtures["fixtures"])
assert len({item["fixture_id"] for item in fixtures["fixtures"]}) == 35

case_counts = Counter(item["module_id"] for item in cases["cases"])
for module_id in expected_modules:
    assert case_counts[module_id] == 8
assert case_counts["CROSS_MODULE"] == 7
assert len(cases["cases"]) == 63
assert all(item["canonical_delta"] == 0 for item in cases["cases"])
assert all(item["external_action_delta"] == 0 for item in cases["cases"])
assert len({item["case_id"] for item in cases["cases"]}) == 63

assert transition_allowed("DETECTED", "QUALIFYING") is True
assert transition_allowed("DETECTED", "APPROVED") is False
assert transition_allowed("LEARNING_CAPTURED", "IN_EXECUTION") is False
assert qualification_decision(True, False, True) == "QUALIFIED"
assert qualification_decision(False, False, True) == "REVIEW_REQUIRED"
assert qualification_decision(True, True, True) == "REJECTED"
assert work_readiness(["SATISFIED", "WAIVED_BY_HUMAN"]) == "READY"
assert work_readiness(["SATISFIED", "INVALIDATED"]) == "BLOCKED"
assert approval_valid("APPROVED", "requester-a", "approver-b", True, True, True) is True
assert approval_valid("APPROVED", "same", "same", True, True, True) is False

required = {"PURSUE", "BUDGET", "RIGHTS", "LEGAL", "DOCUMENT", "SUBMISSION_OR_ACTIVATION"}
assert may_execute_external_action(
    "HUMAN_SUBMISSION_AUTHORITY", required, required, True, True, True
) is True
assert may_execute_external_action("WORKER", required, required, True, True, True) is False
assert may_execute_external_action(
    "HUMAN_SUBMISSION_AUTHORITY", required - {"LEGAL"}, required, True, True, True
) is False
assert normalize_outcome(False, "WON") == "UNKNOWN"
assert normalize_outcome(True, "WON") == "WON"
assert learning_state("MODEL", True) == "PROPOSED"
assert learning_state("HUMAN_LEARNING_AUTHORITY", True) == "REVIEWED"
assert import_authority(True, True) == "CANDIDATE_ONLY"
assert import_authority(False, True) == "QUARANTINE"

payload_a = {"b": 2, "a": 1}
payload_b = {"a": 1, "b": 2}
assert canonical_digest(payload_a) == canonical_digest(payload_b)
event = {"event_id": "evt-1", "command": "TEST"}
assert audit_event_hash("0" * 64, event) == audit_event_hash("0" * 64, event)
assert audit_event_hash("0" * 64, event) != audit_event_hash("1" * 64, event)

result = {
    "status": "PASS",
    "task_id": "AX-GE2E-P07-T01",
    "core_modules": len(runtime["core_modules"]),
    "opportunity_library_bindings": len(opportunity_contracts),
    "record_types": sum(len(item["record_types"]) for item in runtime["core_modules"]),
    "domain_invariants": sum(len(item["invariants"]) for item in runtime["core_modules"]),
    "lifecycle_states": len(runtime["opportunity_lifecycle"]["states"]),
    "pipeline_stages": len(runtime["operating_pipeline"]["stages"]),
    "approval_types": len(runtime["approval_contract"]["approval_types"]),
    "rights_dimensions": len(rights),
    "conformance_fixtures": len(fixtures["fixtures"]),
    "adversarial_cases": len(cases["cases"]),
    "canonical_activation_authorised": runtime["canonical_activation_authorised"],
    "p06_canonical_activation_authorised": dependency["p06_canonical_activation_authorised"],
    "p05_canonical_activation_authorised": dependency["p05_canonical_activation_authorised"],
    "p04_canonical_activation_authorised": dependency["p04_canonical_activation_authorised"],
    "p03_canonical_activation_authorised": dependency["p03_canonical_activation_authorised"],
    "p02_canonical_activation_authorised": dependency["p02_canonical_activation_authorised"],
    "p01_dependency_satisfied": dependency["p01_dependency_satisfied"],
}
print(json.dumps(result, sort_keys=True))
