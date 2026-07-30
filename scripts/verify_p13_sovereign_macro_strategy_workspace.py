#!/usr/bin/env python3
from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from p13_sovereign_macro_reference import (
    canonical_digest,
    comparability_decision,
    imported_authority,
    indicator_current,
    may_execute_external_action,
    normalize_outcome,
    public_finance_decision,
    strategy_readiness,
)

ROOT = Path(__file__).resolve().parents[1]
PATHS = {
    "runtime_schema": ROOT / "schemas/sovereign-macro-strategy-workspace-runtime.schema.json",
    "fixtures_schema": ROOT / "schemas/sovereign-macro-strategy-workspace-fixtures.schema.json",
    "cases_schema": ROOT / "schemas/sovereign-macro-strategy-workspace-cases.schema.json",
    "runtime": (
        ROOT
        / "data/sovereign-macro/sovereign-macro-strategy-workspace-runtime.v0.1.json"
    ),
    "fixtures": ROOT / "data/sovereign-macro/p13-conformance-fixtures.v0.1.json",
    "cases": ROOT / "data/sovereign-macro/p13-adversarial-cases.v0.1.json",
    "rollback": ROOT / "data/sovereign-macro/p13-rollback-plan.v0.1.json",
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
    "p12": (
        ROOT
        / "data/corporate/corporate-ownership-account-workspace-runtime.v0.1.json"
    ),
    "catalogue": (
        ROOT / "data/sources/sovereign-macro-public-investment-catalogue.v0.1.json"
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
p12 = load(PATHS["p12"])
catalogue = load(PATHS["catalogue"])

task = next(
    item
    for item in programme["tasks"]
    if item["task_id"] == "AX-GE2E-P13-T01"
)
assert task["phase"] == "P13"
assert task["state"] == "BLOCKED"
assert task["dependencies"]["tasks"] == ["AX-GE2E-P07-T01"]

library = next(
    item
    for item in libraries["contracts"]
    if item["library_id"] == "AX-LIB-O06"
)
binding = runtime["sovereign_macro_library_binding"]
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
assert p12["task_id"] == "AX-GE2E-P12-T01"
assert p12["canonical_activation_authorised"] is False
assert (
    runtime["dependency_status"]["p12_engineering_head"]
    == "96b89d8e7bdd7712dae476eeb97e1240c7846f22"
)

assert catalogue["catalogue_id"] == "AX-MACRO-SOURCE-CATALOGUE-001"
assert catalogue["library_id"] == "AX-LIB-O06"
assert len(catalogue["sources"]) == 7
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
assert len(runtime["country_strategy_lifecycle"]["states"]) == 12
assert len(runtime["operating_pipeline"]["stages"]) == 11
for key, expected in (
    ("macro_value_classes", 10),
    ("economic_transformations", 10),
    ("public_finance_states", 10),
    ("scenario_risk_classes", 10),
    ("readiness_gates", 12),
    ("rights_dimensions", 10),
):
    assert len(runtime[key]) == expected

fixture_count = len(fixtures["modules"]) * len(fixtures["classes"])
assert fixture_count == 40
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
    indicator_current(
        value_class="OBSERVED",
        vintage_current=True,
        withdrawn=False,
        rights_active=True,
    )
    == "PASS"
)
assert (
    indicator_current(
        value_class="FORECAST",
        vintage_current=True,
        withdrawn=False,
        rights_active=True,
    )
    == "REVIEW_REQUIRED"
)
assert (
    indicator_current(
        value_class="OBSERVED",
        vintage_current=True,
        withdrawn=True,
        rights_active=True,
    )
    == "DENY"
)

assert (
    comparability_decision(
        unit=True,
        scale=True,
        currency=True,
        price_basis=True,
        frequency=True,
        lineage=True,
    )
    == "PASS"
)
assert (
    comparability_decision(
        unit=False,
        scale=True,
        currency=True,
        price_basis=True,
        frequency=True,
        lineage=True,
    )
    == "REVIEW_REQUIRED"
)
assert (
    comparability_decision(
        unit=True,
        scale=True,
        currency=True,
        price_basis=True,
        frequency=True,
        lineage=False,
    )
    == "DENY"
)

assert (
    public_finance_decision(
        state="DISBURSED",
        amount=Decimal("1"),
        observed=True,
        rights_active=True,
    )
    == "PASS"
)
assert (
    public_finance_decision(
        state="ALLOCATED",
        amount=Decimal("1"),
        observed=True,
        rights_active=True,
    )
    == "REVIEW_REQUIRED"
)
assert (
    public_finance_decision(
        state="CANCELLED",
        amount=Decimal("1"),
        observed=True,
        rights_active=True,
    )
    == "DENY"
)

required_gates = runtime["readiness_gates"]
passing_gates = {gate: "PASS" for gate in required_gates}
assert strategy_readiness(passing_gates, required_gates) == "READY"
review_gates = dict(passing_gates)
review_gates[required_gates[0]] = "REVIEW_REQUIRED"
assert strategy_readiness(review_gates, required_gates) == "REVIEW_REQUIRED"
deny_gates = dict(passing_gates)
deny_gates[required_gates[0]] = "DENY"
assert strategy_readiness(deny_gates, required_gates) == "DENY"
assert strategy_readiness({}, required_gates) == "NOT_READY"

assert may_execute_external_action(
    actor_type="HUMAN_EXTERNAL_ACTION_AUTHORITY",
    readiness="READY",
    approvals=True,
    rights=True,
    document=True,
    recipient=True,
    channel=True,
    audit=True,
    kill_switch=False,
)
assert not may_execute_external_action(
    actor_type="MODEL",
    readiness="READY",
    approvals=True,
    rights=True,
    document=True,
    recipient=True,
    channel=True,
    audit=True,
    kill_switch=False,
)
assert normalize_outcome("MARKET_ENTRY_STARTED", observed=True) == "MARKET_ENTRY_STARTED"
assert normalize_outcome("MARKET_ENTRY_STARTED", observed=False) == "UNKNOWN"
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
            "task_id": "AX-GE2E-P13-T01",
            "domain_modules": len(modules),
            "record_types": sum(len(module["record_types"]) for module in modules),
            "domain_invariants": sum(len(module["invariants"]) for module in modules),
            "conformance_fixtures": fixture_count,
            "adversarial_cases": case_count,
            "canonical_activation_authorised": False,
        },
        sort_keys=True,
    )
)
