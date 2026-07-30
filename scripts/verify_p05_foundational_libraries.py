#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import Counter
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from jsonschema import Draft202012Validator

from p05_foundation_reference import (
    classify_entity_match,
    convert_money,
    evaluate_rights,
    least_authority,
    mapping_cardinality,
    may_write_canonical,
    preserve_value_state,
    resolve_document_anchor,
    resolve_interval,
)

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_SCHEMA = ROOT / "schemas/foundational-library-runtime.schema.json"
CASES_SCHEMA = ROOT / "schemas/foundational-library-cases.schema.json"
FIXTURES_SCHEMA = ROOT / "schemas/foundational-library-fixtures.schema.json"
RUNTIME = ROOT / "data/foundations/foundational-library-runtime.v0.1.json"
CASES = ROOT / "data/foundations/p05-adversarial-cases.v0.1.json"
FIXTURES = ROOT / "data/foundations/p05-conformance-fixtures.v0.1.json"
PROGRAMME = ROOT / "data/programmes/global-e2e-tasks-p05-p09.v1.4.json"
P02_LIBRARIES = ROOT / "data/ontology/library-contracts.v0.1.json"
P03_SECURITY = ROOT / "data/security/security-identity-rights-registry.v0.1.json"
P04_CONNECTORS = ROOT / "data/connectors/connector-sdk-registry.v0.1.json"

paths = (
    RUNTIME_SCHEMA,
    CASES_SCHEMA,
    FIXTURES_SCHEMA,
    RUNTIME,
    CASES,
    FIXTURES,
    PROGRAMME,
    P02_LIBRARIES,
    P03_SECURITY,
    P04_CONNECTORS,
)
for path in paths:
    assert path.is_file(), f"missing {path.relative_to(ROOT)}"

runtime_schema = json.loads(RUNTIME_SCHEMA.read_text(encoding="utf-8"))
cases_schema = json.loads(CASES_SCHEMA.read_text(encoding="utf-8"))
fixtures_schema = json.loads(FIXTURES_SCHEMA.read_text(encoding="utf-8"))
runtime = json.loads(RUNTIME.read_text(encoding="utf-8"))
cases = json.loads(CASES.read_text(encoding="utf-8"))
fixtures = json.loads(FIXTURES.read_text(encoding="utf-8"))
programme = json.loads(PROGRAMME.read_text(encoding="utf-8"))
p02 = json.loads(P02_LIBRARIES.read_text(encoding="utf-8"))
p03 = json.loads(P03_SECURITY.read_text(encoding="utf-8"))
p04 = json.loads(P04_CONNECTORS.read_text(encoding="utf-8"))

for schema in (runtime_schema, cases_schema, fixtures_schema):
    Draft202012Validator.check_schema(schema)

Draft202012Validator(runtime_schema).validate(runtime)
Draft202012Validator(cases_schema).validate(cases)
Draft202012Validator(fixtures_schema).validate(fixtures)

task = next(item for item in programme["tasks"] if item["task_id"] == "AX-GE2E-P05-T01")
assert task["state"] == "BLOCKED"
assert task["dependencies"]["tasks"] == ["AX-GE2E-P04-T01"]
assert task["dependencies"]["phases"] == ["P04"]
assert task["acceptance_evidence"][0]["status"] == "MISSING"

dependency = runtime["dependency_status"]
assert dependency["p04_engineering_head"] == (
    "2977a6cd4056969313cf7356070eedf6f7d85ed0"
)
assert dependency["p04_engineering_evidence_ready"] is True
assert dependency["p04_canonical_activation_authorised"] is False
assert dependency["p03_canonical_activation_authorised"] is False
assert dependency["p02_canonical_activation_authorised"] is False
assert dependency["p01_dependency_satisfied"] is False
assert dependency["merge_to_main_allowed"] is False
assert runtime["canonical_activation_authorised"] is False
assert runtime["acceptance_gate"]["current_decision"] == (
    "NOT_READY_FOR_CANONICAL_ACTIVATION"
)

expected_ids = [f"AX-LIB-F0{index}" for index in range(1, 8)]
runtime_ids = [item["library_id"] for item in runtime["libraries"]]
assert runtime_ids == expected_ids
assert len({item["service_id"] for item in runtime["libraries"]}) == 7

p02_foundations = [
    item for item in p02["contracts"] if item["kind"] == "FOUNDATIONAL"
]
assert [item["library_id"] for item in p02_foundations] == expected_ids
for implementation, contract in zip(runtime["libraries"], p02_foundations, strict=True):
    assert implementation["canonical_name"] == contract["canonical_name"]
    assert set(contract["entities"]).issubset(set(implementation["record_types"]))
    assert f"{implementation['library_id']}_DOMAIN_SEMANTICS" in (
        implementation["conformance_requirements"]
    )
    assert implementation["persistence"]["candidate_store"] == "TENANT_SCOPED_RLS"
    assert implementation["persistence"]["admitted_store"] == (
        "GLOBAL_APPEND_ONLY_LEDGER"
    )

rights = runtime["rights_dimensions"]
assert rights == p03["source_rights_enforcement_contract"]["required_rights_dimensions"]
assert rights == p04["source_profile_contract"]["rights_dimensions"]
assert len(rights) == 10

case_counts = Counter(item["library_id"] for item in cases["cases"])
for library_id in expected_ids:
    assert case_counts[library_id] == 6
assert case_counts["CROSS_LIBRARY"] == 7
assert len(cases["cases"]) == 49
assert all(item["canonical_delta"] == 0 for item in cases["cases"])
assert len({item["case_id"] for item in cases["cases"]}) == 49

fixture_counts = Counter(item["library_id"] for item in fixtures["fixtures"])
assert fixture_counts == Counter({library_id: 3 for library_id in expected_ids})
assert len(fixtures["fixtures"]) == 21
assert all(item["expected"]["canonical_write"] is False for item in fixtures["fixtures"])

serialized = json.dumps(runtime, sort_keys=True)
for forbidden in (
    "connector canonical authority",
    "model direct admission",
    "browser canonical mutation",
):
    assert forbidden not in serialized.lower()

assert preserve_value_state(None, "UNKNOWN") == (None, "UNKNOWN")
assert preserve_value_state(0, "ZERO") == (0, "ZERO")
assert resolve_interval(
    datetime(2026, 1, 1, tzinfo=UTC),
    datetime(2027, 1, 1, tzinfo=UTC),
    datetime(2026, 7, 30, tzinfo=UTC),
) is True
assert resolve_interval(None, None, datetime.now(UTC)) is None
assert convert_money(
    Decimal("10"),
    Decimal("1.25"),
    datetime(2026, 7, 30, tzinfo=UTC),
) == Decimal("12.50")
assert evaluate_rights("ALLOW", False) == "ALLOW"
assert evaluate_rights("ALLOW", True) == "DENY"
assert evaluate_rights("AMBIGUOUS", False) == "DENY"
assert resolve_document_anchor("doc:v2", "doc:v2") is True
assert resolve_document_anchor("doc:v2", "doc:v1") is False
assert least_authority(["ADMITTED", "CANDIDATE", "REVIEWED"]) == "CANDIDATE"
assert may_write_canonical("MODEL", True) is False
assert may_write_canonical("HUMAN_DATA_AUTHORITY", True) is True
assert may_write_canonical("HUMAN_DATA_AUTHORITY", False) is False
assert classify_entity_match(Decimal("0.99"), False) == "CANDIDATE_MATCH"
assert classify_entity_match(Decimal("0.50"), False) == "UNRESOLVED"
assert mapping_cardinality(2, 3) == "MANY_TO_MANY"

result = {
    "status": "PASS",
    "task_id": "AX-GE2E-P05-T01",
    "foundational_libraries": len(runtime["libraries"]),
    "reference_services": len({item["service_id"] for item in runtime["libraries"]}),
    "record_types": sum(len(item["record_types"]) for item in runtime["libraries"]),
    "domain_invariants": sum(
        len(item["domain_invariants"]) for item in runtime["libraries"]
    ),
    "rights_dimensions": len(rights),
    "conformance_fixtures": len(fixtures["fixtures"]),
    "adversarial_cases": len(cases["cases"]),
    "canonical_activation_authorised": runtime[
        "canonical_activation_authorised"
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
