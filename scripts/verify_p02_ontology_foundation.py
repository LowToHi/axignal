#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas/global-ontology-registry.schema.json"
REGISTRY_PATH = ROOT / "data/ontology/global-ontology-registry.v0.1.json"
P01_GATE_PATH = ROOT / "docs/gates/AX-GE2E-P01-gate-v1.4.json"
DESIGN_PATH = ROOT / "docs/ontology/P02-global-ontology-and-library-contracts-v0.1.md"

for path in (SCHEMA_PATH, REGISTRY_PATH, P01_GATE_PATH, DESIGN_PATH):
    assert path.is_file(), f"missing {path.relative_to(ROOT)}"

schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
p01_gate = json.loads(P01_GATE_PATH.read_text(encoding="utf-8"))

Draft202012Validator.check_schema(schema)
errors = sorted(
    Draft202012Validator(schema).iter_errors(registry),
    key=lambda error: list(error.path),
)
assert not errors, [error.message for error in errors]

assert registry["task_id"] == "AX-GE2E-P02-T01"
assert registry["status"] == "DRAFT_IMPLEMENTATION_FOUNDATION"
assert registry["human_authorised_branch_start"] is True
assert registry["canonical_activation_authorised"] is False

assert registry["dependency_status"] == {
    "p01_task": "AX-GE2E-P01-T01",
    "p01_canonical_state": "IN_PROGRESS",
    "p01_dependency_satisfied": False,
    "merge_to_main_allowed": False,
}

assert p01_gate["task_id"] == "AX-GE2E-P01-T01"
assert p01_gate["state"] == "IN_PROGRESS"
assert p01_gate["decision"] == "NOT_READY_FOR_HUMAN_ACCEPTANCE"
assert p01_gate["truth_boundary"]["primary_research_complete"] is False
assert p01_gate["truth_boundary"]["p02_authorised"] is False

families = registry["contract_families"]
assert len(families) == 9
assert len({item["contract_id"] for item in families}) == 9
assert {item["name"] for item in families} == {
    "UniverseContract",
    "LibraryContract",
    "SourceContract",
    "EvidenceContract",
    "ClaimContract",
    "OpportunityContract",
    "EntityContract",
    "TaxonomyContract",
    "TemporalContract",
}

foundational = registry["foundational_libraries"]
opportunity = registry["opportunity_libraries"]
foundational_ids = {item["library_id"] for item in foundational}
opportunity_ids = {item["library_id"] for item in opportunity}

assert foundational_ids == {f"AX-LIB-F0{index}" for index in range(1, 8)}
assert opportunity_ids == {f"AX-LIB-O0{index}" for index in range(1, 10)}
assert all(item["state"] == "DRAFT" for item in foundational + opportunity)
assert not any(item["public_product_availability"] for item in foundational + opportunity)
assert all(set(item["dependencies"]) == foundational_ids for item in opportunity)

source = registry["source_contract"]
assert source["default_when_rights_ambiguous"] == "RESTRICTED"
assert {
    "DISCOVERED",
    "LEGAL_REVIEW",
    "TECHNICAL_PROBE",
    "EVIDENCE_READY",
    "PRODUCT_ADMITTED",
    "PRIVATE_ACCEPTANCE",
    "COMMERCIAL",
    "RESTRICTED",
    "SUSPENDED",
    "REVOKED",
    "REJECTED",
}.issubset(source["states"])
assert len(source["rights_dimensions"]) == 10

evidence = registry["evidence_contract"]
assert "content_hash" in evidence["required_fields"]
assert "rights_snapshot_id" in evidence["required_fields"]
assert set(evidence["immutable_fields"]).issubset(evidence["required_fields"])

claim = registry["claim_contract"]
assert {
    "OBSERVED_QUALITATIVE",
    "OBSERVED_QUANTITATIVE",
    "CALCULATED",
    "PREDICTIVE",
    "LEGAL_OR_REGULATORY",
}.issubset(claim["claim_types"])
assert {
    "PROPOSED",
    "RIGHTS_VALID",
    "ADMISSIBLE",
    "ACTIONABLE",
    "CONTESTED",
    "REJECTED",
    "QUARANTINED",
}.issubset(claim["epistemic_states"])

entity = registry["entity_contract"]
assert {"OBSERVED", "INFERRED", "HUMAN_ASSERTED"} == set(
    entity["relationship_modes"]
)
assert "MERGE" not in entity["resolution_states"]
assert "SPLIT" in entity["resolution_states"]

 taxonomy = registry["taxonomy_contract"]
assert {"CPV", "NUTS", "NAICS", "PSC", "NACE", "ISIC", "HS", "SITC", "CPC"} == set(
    taxonomy["required_taxonomies"]
)
assert "ADMITTED" in taxonomy["crosswalk_states"]
assert "PROPOSED" in taxonomy["crosswalk_states"]

temporal = registry["temporal_contract"]
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
} == set(temporal["time_axes"])

opportunity_contract = registry["opportunity_contract"]
assert {
    "Opportunity",
    "Pursuit",
    "Decision",
    "Requirement",
    "WorkItem",
    "Milestone",
    "Document",
    "Comment",
    "Approval",
    "Submission",
    "Outcome",
    "Learning",
    "ActivityEvent",
    "Template",
} == set(opportunity_contract["shared_entities"])

invariants = registry["cross_library_invariants"]
assert len(invariants) >= 10
assert len({item["invariant_id"] for item in invariants}) == len(invariants)

gate = registry["acceptance_gate"]
assert gate["current_decision"] == "NOT_READY_FOR_CANONICAL_ACTIVATION"
assert len(gate["required_before_canonical_activation"]) >= 10

print(
    json.dumps(
        {
            "status": "PASS",
            "task_id": registry["task_id"],
            "contract_families": len(families),
            "foundational_libraries": len(foundational),
            "opportunity_libraries": len(opportunity),
            "cross_library_invariants": len(invariants),
            "canonical_activation_authorised": False,
            "p01_dependency_satisfied": False,
        },
        sort_keys=True,
    )
)
