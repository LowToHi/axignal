#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas/library-contract-catalog.schema.json"
CATALOG_PATH = ROOT / "data/ontology/library-contracts.v0.1.json"
CASES_PATH = ROOT / "data/ontology/p02-adversarial-cases.v0.1.json"
REGISTRY_PATH = ROOT / "data/ontology/global-ontology-registry.v0.1.json"
P01_GATE_PATH = ROOT / "docs/gates/AX-GE2E-P01-gate-v1.4.json"

for path in (SCHEMA_PATH, CATALOG_PATH, CASES_PATH, REGISTRY_PATH, P01_GATE_PATH):
    assert path.is_file(), f"missing {path.relative_to(ROOT)}"

schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
cases_document = json.loads(CASES_PATH.read_text(encoding="utf-8"))
registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
p01_gate = json.loads(P01_GATE_PATH.read_text(encoding="utf-8"))

Draft202012Validator.check_schema(schema)
schema_errors = sorted(
    Draft202012Validator(schema).iter_errors(catalog),
    key=lambda error: list(error.path),
)
assert not schema_errors, [error.message for error in schema_errors]

FOUNDATIONAL_IDS = {f"AX-LIB-F0{index}" for index in range(1, 8)}
OPPORTUNITY_IDS = {f"AX-LIB-O0{index}" for index in range(1, 10)}
EXPECTED_IDS = FOUNDATIONAL_IDS | OPPORTUNITY_IDS
REQUIRED_OPPORTUNITY_ROLES = {
    "problem_or_anomaly",
    "affected_entity_or_payer",
    "scale_or_frequency",
    "market_access",
    "competition",
    "operational_feasibility",
    "legal_or_regulatory_risk",
    "ai_absorption_risk",
    "contradictions",
    "unknowns",
    "invalidation_conditions",
}

assert catalog["task_id"] == "AX-GE2E-P02-T01"
assert catalog["status"] == "DRAFT_INDIVIDUAL_CONTRACTS"
assert catalog["canonical_activation_authorised"] is False
assert registry["canonical_activation_authorised"] is False
assert p01_gate["truth_boundary"]["p02_authorised"] is False
assert p01_gate["truth_boundary"]["primary_research_complete"] is False

contracts = catalog["contracts"]
assert len(contracts) == 16
by_id = {item["library_id"]: item for item in contracts}
assert set(by_id) == EXPECTED_IDS
assert len(by_id) == len(contracts)

registry_entries = {
    item["library_id"]: item
    for item in registry["foundational_libraries"] + registry["opportunity_libraries"]
}
assert set(registry_entries) == EXPECTED_IDS

profiles = catalog["profiles"]
shared = profiles["shared_invariants"]
assert shared["rights_ambiguity"] == "RESTRICTED"
assert shared["generative_direct_admission"] is False
assert shared["evidence_immutable"] is True
assert shared["source_native_values_preserved"] is True
assert shared["unknown_unavailable_zero_distinct"] is True
assert shared["canonical_ledger_mutation_from_workspace"] is False
assert shared["public_product_availability"] is False
assert shared["rollback_preserves_lineage"] is True
assert set(profiles["opportunity_graph_roles"]) == REQUIRED_OPPORTUNITY_ROLES

for library_id, item in by_id.items():
    registry_item = registry_entries[library_id]
    assert item["canonical_name"] == registry_item["canonical_name"], library_id
    assert item["version"] == registry_item["contract_version"], library_id
    assert item["state"] == registry_item["state"] == "DRAFT", library_id
    assert len(item["exclusions"]) >= 3
    assert len(item["tests"]) >= 5

    if library_id in FOUNDATIONAL_IDS:
        assert item["kind"] == "FOUNDATIONAL"
        assert item["dependencies"] == []
        assert item["workspace_type"] is None
        assert item["opportunity_roles"] == []
    else:
        assert item["kind"] == "OPPORTUNITY"
        assert set(item["dependencies"]) == FOUNDATIONAL_IDS
        assert item["workspace_type"] == registry_item["workspace_type"]
        assert item["opportunity_roles"] == ["$profile:opportunity_graph_roles"]
        assert item["lifecycle"] == ["$profile:opportunity_lifecycle"]

assert "SPLIT" in by_id["AX-LIB-F02"]["lifecycle"]
assert "CANDIDATE_MATCH" in by_id["AX-LIB-F02"]["lifecycle"]
assert {"CPV", "NUTS", "NAICS", "PSC", "NACE", "ISIC", "HS", "SITC", "CPC"}.issubset(
    set(by_id["AX-LIB-F03"]["taxonomy_refs"])
)
assert {
    "published_at",
    "retrieved_at",
    "observed_at",
    "event_at",
    "valid_from",
    "valid_to",
    "effective_from",
    "effective_to",
    "revised_at",
    "vintage_at",
    "recorded_at",
}.issubset(set(by_id["AX-LIB-F04"]["time_axes"]))
assert "RESTRICTED" in by_id["AX-LIB-F06"]["lifecycle"]
assert "REVOKED" in by_id["AX-LIB-F06"]["lifecycle"]


def evaluate_case(case: dict[str, Any]) -> dict[str, Any]:
    category = case["category"]
    data = case["input"]

    if category == "TEMPORAL_AMBIGUITY":
        assert data["published_at"] is None
        assert data["missing_reason"]
        return {
            "decision": "PRESERVE_UNKNOWN",
            "published_at": None,
            "must_not_equal_retrieved_at": True,
        }

    if category == "TEMPORAL_AXES":
        values = [data["published_at"], data["retrieved_at"], data["observed_at"]]
        return {"decision": "KEEP_AXES_DISTINCT", "distinct_axes": len(set(values))}

    if category == "ENTITY_RESOLUTION":
        assert data["left_id"] != data["right_id"]
        if data["resolution_state"] == "CANDIDATE_MATCH":
            return {"decision": "NO_SILENT_MERGE", "entity_count": 2}
        raise AssertionError("entity resolution case must remain candidate-only")

    if category == "ENTITY_SPLIT":
        assert data["resolution_state"] == "SPLIT"
        return {
            "decision": "REVERSIBLE_SPLIT",
            "predecessor_preserved": bool(data["predecessor_id"]),
            "successor_count": len(set(data["successor_ids"])),
        }

    if category == "TAXONOMY_CROSSWALK":
        mappings = [tuple(edge) for edge in data["mappings"]]
        forward = {(source, target) for source, target in mappings}
        reverse = {(target, source) for source, target in mappings}
        assert len(forward) == len(reverse)
        return {
            "decision": "REVERSIBLE_MANY_TO_MANY",
            "forward_edges": len(forward),
            "reverse_edges": len(reverse),
        }

    if category == "TAXONOMY_NATIVE_IMMUTABILITY":
        return {
            "decision": "PRESERVE_SOURCE_NATIVE",
            "source_native_code": data["source_native_code"],
            "source_native_label": data["source_native_label"],
        }

    if category == "AI_ADMISSION_BYPASS":
        assert data["producer"] == "GENERATIVE_MODEL"
        assert data["requested_epistemic_state"] == "ADMISSIBLE"
        return {"decision": "DENY_DIRECT_ADMISSION", "resulting_state": "PROPOSED"}

    if category == "RIGHTS_AMBIGUITY":
        assert data["technical_accessible"] is True
        assert data["rights_state"] == "AMBIGUOUS"
        return {"decision": "RESTRICT", "source_state": "RESTRICTED"}

    if category == "UNKNOWN_ZERO":
        assert data["source_value"] is None
        assert data["missing_reason"]
        return {"decision": "PRESERVE_UNKNOWN", "canonical_value": None, "is_zero": False}

    if category == "TENANT_PRIVATE_MUTATION":
        assert data["actor_scope"] == "TENANT_PRIVATE_WORKSPACE"
        assert data["target"] == "CANONICAL_CLAIM_LEDGER"
        return {"decision": "DENY_MUTATION", "canonical_mutation": False}

    if category == "SOURCE_KILL_SWITCH":
        assert data["kill_switch"] is True
        assert data["source_state"] in {"SUSPENDED", "REVOKED", "REJECTED"}
        return {"decision": "NO_NEW_CLAIM_CONTRIBUTION", "admitted_claims": 0}

    if category == "TREND_ONLY_ACTIONABILITY":
        assert set(data["claim_types"]) == {"TREND"}
        assert data["opportunity_state_requested"] == "ACTIONABLE"
        return {"decision": "DENY_ACTIONABLE", "resulting_state": "QUALIFYING"}

    raise AssertionError(f"unknown adversarial category: {category}")


cases = cases_document["cases"]
assert cases_document["task_id"] == "AX-GE2E-P02-T01"
assert len(cases) >= 12
assert len({case["case_id"] for case in cases}) == len(cases)

for case in cases:
    actual = evaluate_case(case)
    assert actual == case["expected"], {
        "case_id": case["case_id"],
        "expected": case["expected"],
        "actual": actual,
    }

print(
    json.dumps(
        {
            "status": "PASS",
            "task_id": catalog["task_id"],
            "individual_contracts": len(contracts),
            "foundational_contracts": len(FOUNDATIONAL_IDS),
            "opportunity_contracts": len(OPPORTUNITY_IDS),
            "adversarial_cases": len(cases),
            "canonical_activation_authorised": False,
            "p01_dependency_satisfied": False,
        },
        sort_keys=True,
    )
)
