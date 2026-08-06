#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from p16_innovation_ip_reference import (
    canonical_digest,
    citation_decision,
    grant_claim_decision,
    imported_authority,
    innovation_readiness,
    licence_signal_decision,
    may_execute_external_action,
    normalize_innovation_outcome,
    patent_status_decision,
    relationship_decision,
    research_output_decision,
)

ROOT = Path(__file__).resolve().parents[1]
PATHS = {
    "runtime_schema": (
        ROOT / "schemas/innovation-ip-workspace-runtime.schema.json"
    ),
    "fixtures_schema": (
        ROOT / "schemas/innovation-ip-workspace-fixtures.schema.json"
    ),
    "cases_schema": ROOT / "schemas/innovation-ip-workspace-cases.schema.json",
    "runtime": (
        ROOT / "data/innovation-ip/innovation-ip-workspace-runtime.v0.1.json"
    ),
    "fixtures": (
        ROOT / "data/innovation-ip/p16-conformance-fixtures.v0.1.json"
    ),
    "cases": ROOT / "data/innovation-ip/p16-adversarial-cases.v0.1.json",
    "rollback": ROOT / "data/innovation-ip/p16-rollback-plan.v0.1.json",
    "programme": ROOT / "data/programmes/global-e2e-tasks-p15-p19.v1.4.json",
    "libraries": ROOT / "data/ontology/library-contracts.v0.1.json",
    "p05": ROOT / "data/foundations/foundational-library-runtime.v0.1.json",
    "p06": (
        ROOT
        / "data/document-intelligence/"
        "multilingual-document-intelligence-runtime.v0.1.json"
    ),
    "p07": (
        ROOT
        / "data/opportunity-operations/"
        "opportunity-operations-core-runtime.v0.1.json"
    ),
    "p15": (
        ROOT
        / "data/energy-climate/"
        "energy-climate-transition-workspace-runtime.v0.1.json"
    ),
    "catalogue": (
        ROOT / "data/sources/innovation-research-ip-catalogue.v0.1.json"
    ),
}

for path in PATHS.values():
    assert path.is_file(), f"missing {path.relative_to(ROOT)}"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


runtime_schema = load(PATHS["runtime_schema"])
fixtures_schema = load(PATHS["fixtures_schema"])
cases_schema = load(PATHS["cases_schema"])
runtime = load(PATHS["runtime"])
fixtures = load(PATHS["fixtures"])
cases = load(PATHS["cases"])

for schema in (runtime_schema, fixtures_schema, cases_schema):
    Draft202012Validator.check_schema(schema)
Draft202012Validator(runtime_schema).validate(runtime)
Draft202012Validator(fixtures_schema).validate(fixtures)
Draft202012Validator(cases_schema).validate(cases)

programme = load(PATHS["programme"])
libraries = load(PATHS["libraries"])
p05 = load(PATHS["p05"])
p06 = load(PATHS["p06"])
p07 = load(PATHS["p07"])
p15 = load(PATHS["p15"])
catalogue = load(PATHS["catalogue"])


task = next(
    item
    for item in programme["tasks"]
    if item["task_id"] == "AX-GE2E-P16-T01"
)
assert task["phase"] == "P16"
assert task["state"] == "BLOCKED"
assert task["objective"] == (
    "Implement patent/research intelligence and the "
    "Innovation Opportunity Workspace."
)
assert task["dependencies"]["tasks"] == ["AX-GE2E-P07-T01"]
assert task["prohibited_scope"] == [
    "No unauthorised launch, admission or canonical authority."
]

library = next(
    item
    for item in libraries["contracts"]
    if item["library_id"] == "AX-LIB-O09"
)
binding = runtime["innovation_ip_library_binding"]
for key in (
    "library_id",
    "workspace_type",
    "canonical_name",
    "entities",
    "predicates",
    "events",
    "taxonomy_refs",
    "exclusions",
):
    assert binding[key] == library[key]

assert p05["canonical_activation_authorised"] is False
assert p06["canonical_activation_authorised"] is False
assert runtime["languages"] == [
    item["language_tag"] for item in p06["language_profile"]["languages"]
]
assert p07["canonical_activation_authorised"] is False
assert runtime["rights_dimensions"] == p07["rights_dimensions"]
assert set(runtime["required_approvals"]).issubset(
    set(p07["approval_contract"]["approval_types"])
)
assert p15["task_id"] == "AX-GE2E-P15-T01"
assert p15["canonical_activation_authorised"] is False
assert runtime["dependency_status"]["p15_engineering_head"] == (
    "ef0d252eecde429d7ff30dbbce82b75ab1a7aac3"
)

assert catalogue["catalogue_id"] == "AX-INNOVATION-SOURCE-CATALOGUE-001"
assert catalogue["library_id"] == "AX-LIB-O09"
assert catalogue["status"] == "RESEARCH_CATALOGUE_NOT_PRODUCT_AVAILABILITY"
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
assert len({module["module_id"] for module in modules}) == 8
assert sum(len(module["record_types"]) for module in modules) == 32
assert sum(len(module["invariants"]) for module in modules) == 48
assert len(runtime["innovation_opportunity_lifecycle"]["states"]) == 12
assert len(runtime["operating_pipeline"]["stages"]) == 11
for key, expected in (
    ("patent_status_types", 10),
    ("research_output_types", 10),
    ("relationship_authority_classes", 10),
    ("evidence_quality_classes", 10),
    ("risk_classes", 10),
    ("readiness_gates", 12),
    ("rights_dimensions", 10),
):
    assert len(runtime[key]) == expected

fixture_count = len(fixtures["modules"]) * len(fixtures["classes"])
assert fixture_count == 40
assert set(fixtures["modules"]) == {
    module["module_id"] for module in modules
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
assert patent_status_decision(
    state="PATENT_GRANTED",
    jurisdiction_resolved=True,
    status_current=True,
    observed=True,
    rights_active=True,
) == "PASS"
assert patent_status_decision(
    state="APPLICATION_PUBLISHED",
    jurisdiction_resolved=False,
    status_current=True,
    observed=True,
    rights_active=True,
) == "REVIEW_REQUIRED"
assert patent_status_decision(
    state="PATENT_REVOKED",
    jurisdiction_resolved=True,
    status_current=True,
    observed=True,
    rights_active=True,
) == "DENY"
assert grant_claim_decision(
    source_state="APPLICATION_PUBLISHED",
    grant_event_observed=False,
    jurisdiction_resolved=True,
    status_current=True,
) == "DENY"
assert grant_claim_decision(
    source_state="PATENT_GRANTED",
    grant_event_observed=True,
    jurisdiction_resolved=True,
    status_current=True,
) == "PASS"
assert relationship_decision(
    relationship_class="OBSERVED_ASSIGNEE",
    exact_entity=True,
    time_current=True,
    lawful_scope=True,
) == "PASS"
assert relationship_decision(
    relationship_class="PROPOSED_ENTITY_MATCH",
    exact_entity=True,
    time_current=True,
    lawful_scope=True,
) == "REVIEW_REQUIRED"
assert relationship_decision(
    relationship_class="OBSERVED_INVENTOR",
    exact_entity=True,
    time_current=True,
    lawful_scope=False,
) == "DENY"
assert citation_decision(
    citation_observed=True,
    source_current=True,
    legal_conclusion_requested=False,
) == "PASS"
assert citation_decision(
    citation_observed=True,
    source_current=True,
    legal_conclusion_requested=True,
) == "DENY"
assert research_output_decision(
    output_type="JOURNAL_ARTICLE",
    published=True,
    withdrawn=False,
    rights_active=True,
    peer_reviewed_claim=True,
) == "PASS"
assert research_output_decision(
    output_type="PREPRINT",
    published=True,
    withdrawn=False,
    rights_active=True,
    peer_reviewed_claim=True,
) == "DENY"
assert licence_signal_decision(
    state="EXECUTED",
    observed=True,
    terms_current=True,
    executed_evidence=True,
) == "PASS"
assert licence_signal_decision(
    state="DISCUSSION",
    observed=True,
    terms_current=True,
    executed_evidence=False,
) == "REVIEW_REQUIRED"

required_gates = runtime["readiness_gates"]
passing_gates = {gate: "PASS" for gate in required_gates}
assert innovation_readiness(passing_gates, required_gates) == "READY"
review_gates = dict(passing_gates)
review_gates[required_gates[0]] = "REVIEW_REQUIRED"
assert innovation_readiness(
    review_gates,
    required_gates,
) == "REVIEW_REQUIRED"
deny_gates = dict(passing_gates)
deny_gates[required_gates[0]] = "DENY"
assert innovation_readiness(deny_gates, required_gates) == "DENY"
assert innovation_readiness({}, required_gates) == "NOT_READY"

assert may_execute_external_action(
    actor_type="HUMAN_EXTERNAL_ACTION_AUTHORITY",
    readiness="READY",
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
    readiness="READY",
    approvals_current=True,
    rights_active=True,
    legal_review_current=True,
    recipient_verified=True,
    channel_verified=True,
    audit_chain_valid=True,
    kill_switch_active=False,
)
assert normalize_innovation_outcome(
    "DISCUSSION_OPENED",
    observed_evidence=True,
) == "DISCUSSION_OPENED"
assert normalize_innovation_outcome(
    "DISCUSSION_OPENED",
    observed_evidence=False,
) == "UNKNOWN"
assert imported_authority("APPROVED") == "CANDIDATE_ONLY"

for key, value in runtime["dependency_status"].items():
    if key.endswith("canonical_activation_authorised") or key in {
        "p01_dependency_satisfied",
        "merge_to_main_allowed",
    }:
        assert value is False
assert runtime["canonical_activation_authorised"] is False
assert runtime["acceptance_gate"]["current_decision"] == (
    "NOT_READY_FOR_CANONICAL_ACTIVATION"
)

print(
    json.dumps(
        {
            "status": "PASS",
            "task_id": "AX-GE2E-P16-T01",
            "domain_modules": len(modules),
            "record_types": sum(
                len(module["record_types"]) for module in modules
            ),
            "domain_invariants": sum(
                len(module["invariants"]) for module in modules
            ),
            "source_catalogue_entries": len(catalogue["sources"]),
            "conformance_fixtures": fixture_count,
            "adversarial_cases": case_count,
            "canonical_activation_authorised": False,
        },
        sort_keys=True,
    )
)
