#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from p17_cross_library_reference import (
    canonical_digest,
    compose_authority,
    cross_library_readiness,
    dependency_projection_decision,
    entity_bridge_decision,
    imported_authority,
    may_execute_external_action,
    may_publish_workspace_projection,
    normalize_cross_library_outcome,
    surface_projection_decision,
    temporal_alignment_decision,
)

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    "rs": "schemas/cross-library-intelligence-runtime.schema.json",
    "fs": "schemas/cross-library-intelligence-fixtures.schema.json",
    "cs": "schemas/cross-library-intelligence-cases.schema.json",
    "r": "data/cross-library/cross-library-intelligence-runtime.v0.1.json",
    "f": "data/cross-library/p17-conformance-fixtures.v0.1.json",
    "c": "data/cross-library/p17-adversarial-cases.v0.1.json",
    "p": "data/programmes/global-e2e-tasks-p15-p19.v1.4.json",
    "p06": (
        "data/document-intelligence/"
        "multilingual-document-intelligence-runtime.v0.1.json"
    ),
    "p07": (
        "data/opportunity-operations/"
        "opportunity-operations-core-runtime.v0.1.json"
    ),
}
EXPECTED = [
    ("P08", "AX-GE2E-P08-T01", "AX-LIB-O01", "3e28e08a12d02701d4ab312edfbedc56fcd8bb59"),
    ("P09", "AX-GE2E-P09-T01", "AX-LIB-O02", "841e068f0a8e86e6d89733d3958ecd43f0d7eca7"),
    ("P10", "AX-GE2E-P10-T01", "AX-LIB-O03", "563acd353ba3a90d253d582b7c19f1554fd011b1"),
    ("P11", "AX-GE2E-P11-T01", "AX-LIB-O04", "315d88731939c1904fcca7be4e5b58d4615ab423"),
    ("P12", "AX-GE2E-P12-T01", "AX-LIB-O05", "96b89d8e7bdd7712dae476eeb97e1240c7846f22"),
    ("P13", "AX-GE2E-P13-T01", "AX-LIB-O06", "0089864b1a3f3d88a0980ecaf4e6dd129299e021"),
    ("P14", "AX-GE2E-P14-T01", "AX-LIB-O07", "f0ae67f8d38afbdb36e1b2e3d56e955b173fbe8d"),
    ("P15", "AX-GE2E-P15-T01", "AX-LIB-O08", "ef0d252eecde429d7ff30dbbce82b75ab1a7aac3"),
    ("P16", "AX-GE2E-P16-T01", "AX-LIB-O09", "daf3b4339051dfa3317e89f61e520e51ea36fbb7"),
]


def load(rel: str) -> dict[str, Any]:
    path = ROOT / rel
    assert path.is_file(), rel
    return json.loads(path.read_text(encoding="utf-8"))


schemas = [load(FILES[key]) for key in ("rs", "fs", "cs")]
runtime, fixtures, cases = [load(FILES[key]) for key in ("r", "f", "c")]
for schema in schemas:
    Draft202012Validator.check_schema(schema)
for schema, instance in zip(schemas, (runtime, fixtures, cases), strict=True):
    Draft202012Validator(schema).validate(instance)

tasks = load(FILES["p"])["tasks"]
task = next(item for item in tasks if item["task_id"] == "AX-GE2E-P17-T01")
assert task["phase"] == "P17" and task["state"] == "BLOCKED"
assert task["dependencies"]["phases"] == [item[0] for item in EXPECTED]
assert task["dependencies"]["tasks"] == [item[1] for item in EXPECTED]
assert task["prohibited_scope"] == [
    "No unauthorised launch, admission or canonical authority."
]

p06, p07 = load(FILES["p06"]), load(FILES["p07"])
assert runtime["languages"] == [
    item["language_tag"]
    for item in p06["language_profile"]["languages"]
]
assert runtime["rights_dimensions"] == p07["rights_dimensions"]
required = runtime["approval_contract_reference"]["required_approval_types"]
assert set(required).issubset(p07["approval_contract"]["approval_types"])

bindings = runtime["source_library_bindings"]
assert len(bindings) == 9
for binding, expected in zip(bindings, EXPECTED, strict=True):
    actual = (
        binding["phase"],
        binding["task_id"],
        binding["library_id"],
        binding["engineering_head"],
    )
    assert actual == expected
    dependency = load(binding["runtime_path"])
    assert dependency["task_id"] == binding["task_id"]
    assert dependency["canonical_activation_authorised"] is False
    assert binding["engineering_evidence_ready"] is True
    assert binding["canonical_activation_authorised"] is False
    assert binding["product_admitted"] is False
    assert binding["composition_mode"] == "ENGINEERING_CANDIDATE_ONLY"

boundary = runtime["composition_boundary"]
assert boundary["canonical_composition_requires_product_admission"] is True
assert boundary["engineering_composition_mode"] == "CANDIDATE_ONLY"
assert boundary["direct_source_ingestion_authorised"] is False
assert boundary["direct_source_catalogue_entries"] == []
assert boundary["cross_tenant_composition_authorised"] is False
assert boundary["external_action_authorised"] is False
assert boundary["canonical_write_authorised"] is False

surfaces = runtime["surface_contracts"]
assert [item["surface_id"] for item in surfaces] == [
    "GLOBE", "GRAPH", "TIMELINE", "NAVIGATOR"
]
assert all(
    len(item["required_lineage"]) >= 8
    and len(item["prohibited_promotions"]) >= 3
    for item in surfaces
)
modules = runtime["domain_modules"]
assert len(modules) == len({item["module_id"] for item in modules}) == 8
assert sum(len(item["record_types"]) for item in modules) == 32
assert sum(len(item["invariants"]) for item in modules) == 48
assert len(runtime["cross_library_lifecycle"]["states"]) == 12
assert len(runtime["operating_pipeline"]["stages"]) == 11
for key, count in (
    ("bridge_relation_classes", 10),
    ("evidence_projection_classes", 10),
    ("contradiction_classes", 10),
    ("authority_classes", 10),
    ("risk_classes", 10),
    ("readiness_gates", 12),
    ("projection_required_fields", 12),
    ("forbidden_promotions", 12),
    ("languages", 6),
    ("rights_dimensions", 10),
):
    assert len(runtime[key]) == count

assert len(fixtures["modules"]) * len(fixtures["classes"]) == 40
assert set(fixtures["modules"]) == {item["module_id"] for item in modules}
for expected in fixtures["expected_by_class"].values():
    assert expected["canonical_write"] is False
    assert expected["external_action"] is False
    assert expected["contradiction_preserved"] is True
assert len(cases["scopes"]) * len(cases["threats"]) == 72
assert set(cases["scopes"]) == {item["library_id"] for item in bindings}
for expected in cases["expected_by_threat"].values():
    for key in (
        "canonical_delta",
        "external_action_delta",
        "tenant_disclosure_delta",
        "authority_elevation_delta",
    ):
        assert expected[key] == 0

assert canonical_digest({"b": 2, "a": 1}) == canonical_digest({"a": 1, "b": 2})
assert compose_authority([
    "PROPOSAL_ONLY", "CANDIDATE_ONLY", "TYPED_HUMAN_APPROVAL"
]) == "CANDIDATE_ONLY"
assert compose_authority([]) == "RESTRICTED"
assert dependency_projection_decision(
    engineering_evidence_ready=True,
    product_admitted=False,
    canonical_activation_authorised=False,
    rights_active=True,
    kill_switch_active=False,
) == "REVIEW_REQUIRED"
assert entity_bridge_decision(
    exact_identifier=True,
    scoped_alias=False,
    tenant_match=False,
    jurisdiction_compatible=True,
    human_review_current=True,
) == "DENY"
assert temporal_alignment_decision(
    valid_time_present=True,
    transaction_time_present=True,
    timezone_resolved=True,
    vintage_preserved=True,
    revision_lineage_preserved=True,
    axes_collapsed=True,
) == "DENY"
assert surface_projection_decision(
    surface="GRAPH",
    source_authority="CANDIDATE_ONLY",
    rights_active=True,
    tenant_match=True,
    contradiction_preserved=True,
    traceable=True,
) == "PASS"
gates = {gate: "PASS" for gate in runtime["readiness_gates"]}
assert cross_library_readiness(gates, runtime["readiness_gates"]) == "READY"
assert cross_library_readiness({}, runtime["readiness_gates"]) == "NOT_READY"
assert may_publish_workspace_projection(
    readiness="READY",
    tenant_match=True,
    rights_active=True,
    traceable=True,
    authority_state="CANDIDATE_ONLY",
)
assert may_execute_external_action(
    actor_type="HUMAN_EXTERNAL_ACTION_AUTHORITY",
    approvals_current=True,
    rights_active=True,
    legal_review_current=True,
    recipient_verified=True,
    channel_verified=True,
    audit_chain_valid=True,
    kill_switch_active=False,
)
assert not may_execute_external_action(
    actor_type="MODEL",
    approvals_current=True,
    rights_active=True,
    legal_review_current=True,
    recipient_verified=True,
    channel_verified=True,
    audit_chain_valid=True,
    kill_switch_active=False,
)
assert normalize_cross_library_outcome(
    "PROJECTION_REVIEWED", observed_evidence=False
) == "UNKNOWN"
assert imported_authority("APPROVED") == "CANDIDATE_ONLY"
for key, value in runtime["dependency_status"].items():
    blocked = key.endswith("canonical_activation_authorised") or key in {
        "all_dependencies_canonically_admitted",
        "p01_dependency_satisfied",
        "merge_to_main_allowed",
    }
    if blocked:
        assert value is False
assert runtime["canonical_activation_authorised"] is False
assert runtime["acceptance_gate"]["current_decision"] == (
    "NOT_READY_FOR_CANONICAL_ACTIVATION"
)
print(json.dumps({
    "status": "PASS",
    "task_id": "AX-GE2E-P17-T01",
    "source_library_bindings": 9,
    "surface_contracts": 4,
    "domain_modules": 8,
    "record_types": 32,
    "domain_invariants": 48,
    "lifecycle_states": 12,
    "pipeline_stages": 11,
    "conformance_fixtures": 40,
    "adversarial_cases": 72,
    "canonical_activation_authorised": False,
}, sort_keys=True))
