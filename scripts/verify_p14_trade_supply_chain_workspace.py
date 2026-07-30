#!/usr/bin/env python3
from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from p14_trade_supply_reference import (
    canonical_digest,
    classification_decision,
    customs_measure_decision,
    flow_observation_decision,
    flow_value_valid,
    imported_authority,
    may_execute_external_action,
    normalize_supply_outcome,
    route_event_decision,
    supply_readiness,
)

ROOT = Path(__file__).resolve().parents[1]
PATHS = {
    "runtime_schema": ROOT / "schemas/trade-supply-chain-workspace-runtime.schema.json",
    "fixtures_schema": ROOT / "schemas/trade-supply-chain-workspace-fixtures.schema.json",
    "cases_schema": ROOT / "schemas/trade-supply-chain-workspace-cases.schema.json",
    "runtime": (
        ROOT
        / "data/trade-supply-chain/trade-supply-chain-workspace-runtime.v0.1.json"
    ),
    "fixtures": (
        ROOT / "data/trade-supply-chain/p14-conformance-fixtures.v0.1.json"
    ),
    "cases": ROOT / "data/trade-supply-chain/p14-adversarial-cases.v0.1.json",
    "rollback": ROOT / "data/trade-supply-chain/p14-rollback-plan.v0.1.json",
    "programme": ROOT / "data/programmes/global-e2e-tasks-p10-p14.v1.4.json",
    "libraries": ROOT / "data/ontology/library-contracts.v0.1.json",
    "p05": ROOT / "data/foundations/foundational-library-runtime.v0.1.json",
    "p06": (
        ROOT
        / "data/document-intelligence/multilingual-document-intelligence-runtime.v0.1.json"
    ),
    "p07": (
        ROOT / "data/opportunity-operations/opportunity-operations-core-runtime.v0.1.json"
    ),
    "p13": (
        ROOT
        / "data/sovereign-macro/sovereign-macro-strategy-workspace-runtime.v0.1.json"
    ),
    "catalogue": (
        ROOT / "data/sources/trade-supply-chain-market-flows-catalogue.v0.1.json"
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
p13 = load(PATHS["p13"])
catalogue = load(PATHS["catalogue"])

task = next(
    item
    for item in programme["tasks"]
    if item["task_id"] == "AX-GE2E-P14-T01"
)
assert task["phase"] == "P14"
assert task["state"] == "BLOCKED"
assert task["objective"] == (
    "Implement global trade and supply intelligence and the "
    "Supply Opportunity Workspace."
)
assert task["dependencies"]["tasks"] == ["AX-GE2E-P07-T01"]
assert task["prohibited_scope"] == [
    "No unauthorised launch, admission or canonical authority."
]

library = next(
    item
    for item in libraries["contracts"]
    if item["library_id"] == "AX-LIB-O07"
)
binding = runtime["trade_library_binding"]
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
assert p13["task_id"] == "AX-GE2E-P13-T01"
assert p13["canonical_activation_authorised"] is False
assert (
    runtime["dependency_status"]["p13_engineering_head"]
    == "0089864b1a3f3d88a0980ecaf4e6dd129299e021"
)

assert catalogue["catalogue_id"] == "AX-TRADE-SOURCE-CATALOGUE-001"
assert catalogue["library_id"] == "AX-LIB-O07"
assert catalogue["status"] == "RESEARCH_CATALOGUE_NOT_PRODUCT_AVAILABILITY"
assert len(catalogue["sources"]) == 4
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
assert len(runtime["trade_opportunity_lifecycle"]["states"]) == 12
assert len(runtime["operating_pipeline"]["stages"]) == 11
for key, expected in (
    ("trade_value_classes", 10),
    ("flow_measure_types", 10),
    ("customs_measure_types", 10),
    ("route_event_types", 10),
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
    item["canonical_write"] is False and item["external_action"] is False
    for item in fixtures["expected_by_class"].values()
)

case_count = len(cases["scopes"]) * len(cases["threats"])
assert case_count == 72
assert all(
    item["canonical_delta"] == 0 and item["external_action_delta"] == 0
    for item in cases["expected_by_threat"].values()
)

assert canonical_digest({"b": 2, "a": 1}) == canonical_digest({"a": 1, "b": 2})
assert (
    flow_observation_decision(
        value_class="REPORTED_VALUE",
        period_known=True,
        vintage_current=True,
        unit_known=True,
        missing=False,
        rights_active=True,
    )
    == "PASS"
)
assert (
    flow_observation_decision(
        value_class="REPORTED_VALUE",
        period_known=True,
        vintage_current=True,
        unit_known=True,
        missing=True,
        rights_active=True,
    )
    == "REVIEW_REQUIRED"
)
assert (
    flow_observation_decision(
        value_class="REPORTED_VALUE",
        period_known=True,
        vintage_current=True,
        unit_known=True,
        missing=False,
        rights_active=False,
    )
    == "DENY"
)
assert (
    classification_decision(
        source_code_present=True,
        taxonomy_version_present=True,
        mapping_observed=True,
        ambiguous=False,
    )
    == "PASS"
)
assert (
    classification_decision(
        source_code_present=True,
        taxonomy_version_present=False,
        mapping_observed=True,
        ambiguous=False,
    )
    == "DENY"
)
assert (
    classification_decision(
        source_code_present=True,
        taxonomy_version_present=True,
        mapping_observed=False,
        ambiguous=True,
    )
    == "REVIEW_REQUIRED"
)
assert (
    customs_measure_decision(
        state="IN_FORCE",
        jurisdiction_resolved=True,
        effective_date_current=True,
        observed=True,
        legal_review_current=True,
    )
    == "PASS"
)
assert (
    customs_measure_decision(
        state="ANNOUNCED",
        jurisdiction_resolved=True,
        effective_date_current=False,
        observed=True,
        legal_review_current=False,
    )
    == "REVIEW_REQUIRED"
)
assert (
    customs_measure_decision(
        state="REPEALED",
        jurisdiction_resolved=True,
        effective_date_current=True,
        observed=True,
        legal_review_current=True,
    )
    == "DENY"
)
assert (
    route_event_decision(
        event_type="PORT_DISRUPTION",
        observed=True,
        status_current=True,
        closure_confirmed=False,
    )
    == "PASS"
)
assert (
    route_event_decision(
        event_type="PORT_CLOSURE",
        observed=True,
        status_current=True,
        closure_confirmed=False,
    )
    == "REVIEW_REQUIRED"
)
assert flow_value_valid(
    value=Decimal("0"),
    missing=False,
    suppressed=False,
) == "OBSERVED"
assert flow_value_valid(
    value=None,
    missing=True,
    suppressed=False,
) == "UNKNOWN"

required_gates = runtime["readiness_gates"]
passing_gates = {gate: "PASS" for gate in required_gates}
assert supply_readiness(passing_gates, required_gates) == "READY"
review_gates = dict(passing_gates)
review_gates[required_gates[0]] = "REVIEW_REQUIRED"
assert supply_readiness(review_gates, required_gates) == "REVIEW_REQUIRED"
deny_gates = dict(passing_gates)
deny_gates[required_gates[0]] = "DENY"
assert supply_readiness(deny_gates, required_gates) == "DENY"
assert supply_readiness({}, required_gates) == "NOT_READY"

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
assert normalize_supply_outcome(
    "ORDER_PLACED",
    observed_evidence=True,
) == "ORDER_PLACED"
assert normalize_supply_outcome(
    "ORDER_PLACED",
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
assert (
    runtime["acceptance_gate"]["current_decision"]
    == "NOT_READY_FOR_CANONICAL_ACTIVATION"
)

print(
    json.dumps(
        {
            "status": "PASS",
            "task_id": "AX-GE2E-P14-T01",
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
