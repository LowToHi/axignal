#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data/scenarios"
S = ROOT / "schemas"
BASE = "4f0b2deed5fce5d852cded1e5e186d8319865e16"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def blob(path: str) -> str:
    result = subprocess.run(
        ["git", "rev-parse", f"{BASE}:{path}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def reference():
    path = ROOT / "scripts/p19_scenarios_reference.py"
    spec = importlib.util.spec_from_file_location("p19_ref", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


runtime = load(D / "scenarios-calibration-outcomes-runtime.v0.1.json")
fixtures = load(D / "p19-conformance-fixtures.v0.1.json")
cases = load(D / "p19-adversarial-cases.v0.1.json")
for name, data in [("runtime", runtime), ("fixtures", fixtures), ("cases", cases)]:
    schema = load(S / f"scenarios-calibration-outcomes-{name}.schema.json")
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(data)

tasks = load(ROOT / "data/programmes/global-e2e-tasks-p15-p19.v1.4.json")
task = [item for item in tasks["tasks"] if item["task_id"] == "AX-GE2E-P19-T01"]
assert len(task) == 1 and task[0]["state"] == "BLOCKED"
assert task[0]["dependencies"]["tasks"] == ["AX-GE2E-P18-T01"]
assert "baselines" in task[0]["objective"].lower()
assert "model demotion" in task[0]["objective"].lower()

bindings = [
    ("data/intent-intelligence/intent-intelligence-knowledge-tides-runtime.v0.1.json",
     "7d81f381a2c84b652ff7bb0fe9ca139654ed6467"),
    ("data/cross-library/cross-library-intelligence-runtime.v0.1.json",
     "179598e5f0da59da2ff937b354db877cb7979e64"),
    ("schemas/research-candidate.schema.json",
     "0361e16e6c5714e97510d683ceca58ed941cba9a"),
    ("schemas/aggregate-intent-signal.schema.json",
     "0a9a51c048c2044a1a500006e602252e69b41e45"),
    ("schemas/claim.schema.json",
     "8afeac6dd681482019a851eb45516de2183a1272"),
]
assert runtime["base"] == BASE
for path, expected in bindings:
    assert blob(path) == expected
assert runtime["counts"] == {
    "bindings": 5, "modules": 8, "records": 32, "invariants": 48,
    "states": 12, "stages": 11, "catalogues": 6,
    "items_per_catalogue": 10, "authorities": 8, "risks": 10,
    "gates": 12, "fixtures": 40, "cases": 72,
}
flags = runtime["flags"]
for key in ["p18_ready", "as_of", "vintage", "revision", "immutable",
            "separate_eval", "automatic_lowering", "claim_admission"]:
    assert flags[key]
for key in ["p18_canonical", "p01", "main", "automatic_raising",
            "partial_final", "missing_false"]:
    assert not flags[key]
fixture_count = len(fixtures["modules"]) * len(fixtures["fixture_classes"])
case_count = len(cases["modules"]) * len(cases["threats"])
assert fixture_count == 40 and case_count == 72
assert fixtures["expected"]["canonical_delta"] == 0
assert cases["expected"]["decision"] == "DENY"
assert cases["expected"]["canonical_delta"] == 0
assert cases["expected"]["model_promotion_delta"] == 0
assert cases["expected"]["holdout_contamination_delta"] == 0

ref = reference()
assert ref.as_of_record_eligible(
    available_at="2026-01-01T00:00:00Z",
    cutoff_at="2026-02-01T00:00:00Z",
)["decision"] == "ALLOW"
assert ref.as_of_record_eligible(
    available_at="2026-03-01T00:00:00Z",
    cutoff_at="2026-02-01T00:00:00Z",
)["reason"] == "FUTURE_DATA_LEAKAGE"
assert round(ref.binary_scores(0.8, 1)["brier_score"], 8) == 0.04
partial = ref.reconcile_outcome(state="PARTIAL", evidence_complete=False)
assert partial["decision"] == "REVIEW_REQUIRED"
thresholds = {
    "minimum_sample_count": 50,
    "maximum_brier_score": 0.20,
    "maximum_ece": 0.05,
}
assert ref.calibration_decision(
    sample_count=100,
    brier_score=0.15,
    expected_calibration_error=0.04,
    thresholds=thresholds,
)["decision"] == "PASS"
assert ref.calibration_decision(
    sample_count=100,
    brier_score=0.15,
    expected_calibration_error=0.04,
    thresholds=thresholds,
    leakage_detected=True,
)["decision"] == "DEMOTE"
assert ref.demotion_decision(
    current_status="ACTIVE_LIMITED",
    hard_triggers=[],
    consecutive_material_breaches=2,
)["decision"] == "DEMOTED"
assert ref.may_promote_model(
    authority="MODEL",
    current_status="DEMOTED",
    gates=["PASS"] * 12,
    new_frozen_holdout_passed=True,
)["decision"] == "DENY"

print(json.dumps({
    "status": "PASS",
    "task_id": "AX-GE2E-P19-T01",
    "input_contract_bindings": 5,
    "domain_modules": 8,
    "record_types": 32,
    "domain_invariants": 48,
    "lifecycle_states": 12,
    "pipeline_stages": 11,
    "readiness_gates": 12,
    "conformance_fixtures": fixture_count,
    "adversarial_cases": case_count,
    "canonical_activation_authorised": False,
}, sort_keys=True))
