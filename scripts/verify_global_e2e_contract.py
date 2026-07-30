#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = [
    "docs/contracts/30-global-e2e-development-contract-v1.4.md",
    "docs/adr/ADR-015-finished-global-product-before-public-launch.md",
    "docs/roadmap/14-global-e2e-development-program-v1.4.md",
    "docs/gates/AX-GE2E-P00-gate-v1.4.json",
    "data/libraries/global-opportunity-library-registry.v1.4.json",
    "data/sources/global-opportunity-source-catalogue-index.v1.4.json",
    "skills/global-e2e-routing.yaml",
    "data/programmes/global-e2e-task-registry.v1.4.json",
]

for rel in REQUIRED:
    path = ROOT / rel
    assert path.is_file(), f"missing {rel}"

schema = json.loads((ROOT / "schemas/task.schema.json").read_text(encoding="utf-8"))
validator = Draft202012Validator(schema)

task_index = json.loads(
    (ROOT / "data/programmes/global-e2e-task-registry.v1.4.json").read_text(
        encoding="utf-8"
    )
)
assert len(task_index["shards"]) == 5

tasks = []
for shard in task_index["shards"]:
    data = json.loads((ROOT / shard["path"]).read_text(encoding="utf-8"))
    assert len(data["tasks"]) == shard["task_count"]
    tasks.extend(data["tasks"])

assert len(tasks) == 25
for index, task in enumerate(tasks):
    phase = f"P{index:02d}"
    errors = sorted(validator.iter_errors(task), key=lambda item: list(item.path))
    assert not errors, (task["task_id"], [error.message for error in errors])
    assert task["phase"] == phase
    assert task["task_id"] == f"AX-GE2E-{phase}-T01"

p00 = tasks[0]
p01 = tasks[1]
assert p00["state"] == "ACCEPTED"
assert p00["rollback"]["tested"] is True
p00_required = [item for item in p00["acceptance_evidence"] if item["required"]]
assert p00_required
assert all(item["status"] in {"PRESENT", "PASS"} for item in p00_required)
assert any(
    item.get("location") == "docs/gates/AX-GE2E-P00-gate-v1.4.json"
    and item["status"] == "PASS"
    for item in p00_required
)
assert p01["state"] == "IN_PROGRESS"
assert p01["dependencies"]["phases"] == ["P00"]
assert p01["dependencies"]["tasks"] == ["AX-GE2E-P00-T01"]
assert all(task["state"] == "BLOCKED" for task in tasks[2:])
assert len({task["task_id"] for task in tasks}) == 25

registry = json.loads(
    (ROOT / "data/libraries/global-opportunity-library-registry.v1.4.json").read_text(
        encoding="utf-8"
    )
)
assert registry["public_launch_authorised"] is False
assert registry["partial_launch_allowed"] is False
assert registry["global_coverage_claim_authorised"] is False
assert len(registry["foundational_libraries"]) == 7
assert len(registry["opportunity_libraries"]) == 9
assert not any(item["accepted"] for item in registry["foundational_libraries"])
assert not any(item["commercial"] for item in registry["opportunity_libraries"])

index = json.loads(
    (ROOT / "data/sources/global-opportunity-source-catalogue-index.v1.4.json").read_text(
        encoding="utf-8"
    )
)
assert index["public_global_coverage_authorised"] is False
assert len(index["catalogues"]) == 9

for entry in index["catalogues"][1:]:
    catalogue = json.loads((ROOT / entry["catalogue"]).read_text(encoding="utf-8"))
    assert catalogue["status"] == "RESEARCH_CATALOGUE_NOT_PRODUCT_AVAILABILITY"
    assert catalogue["principles"]["listed_does_not_mean_admitted"] is True
    assert catalogue["principles"]["public_coverage_authorised"] is False
    assert catalogue["sources"]
    assert not any(source["product_admitted"] for source in catalogue["sources"])
    assert all(source["initial_state"] == "DISCOVERED" for source in catalogue["sources"])

procurement = json.loads(
    (ROOT / "data/sources/global-public-procurement-catalogue.v0.2.json").read_text(
        encoding="utf-8"
    )
)
assert procurement["status"] == "RESEARCH_CATALOGUE_NOT_PRODUCT_AVAILABILITY"
assert procurement["principles"]["public_global_coverage_authorised"] is False

current = (ROOT / "docs/roadmap/06-current-execution-state.md").read_text(
    encoding="utf-8"
)
phase_map = (ROOT / "docs/roadmap/01-phase-map.md").read_text(encoding="utf-8")
task_catalogue = (ROOT / "docs/roadmap/02-task-catalogue.md").read_text(
    encoding="utf-8"
)
assert '"public_launch_authorised": false' in current
assert '"partial_launch_allowed": false' in current
assert "| P00 | `ACCEPTED` |" in current
assert "| P01 | `IN_PROGRESS` |" in current
assert "| `P00` | `ACCEPTED` |" in phase_map
assert "| `P01` | `IN_PROGRESS` |" in phase_map
assert "`AX-GE2E-P00-T01`" in task_catalogue and "`ACCEPTED`" in task_catalogue
assert "`AX-GE2E-P01-T01`" in task_catalogue and "`IN_PROGRESS`" in task_catalogue

routing = yaml.safe_load(
    (ROOT / "skills/global-e2e-routing.yaml").read_text(encoding="utf-8")
)
assert routing["programme"] == "P00-P24"
assert [item["phase"] for item in routing["phase_routes"]] == [
    f"P{i:02d}" for i in range(25)
]
assert all(item["gate_reviewer"] == "gate-evaluator" for item in routing["phase_routes"])

gate = json.loads(
    (ROOT / "docs/gates/AX-GE2E-P00-gate-v1.4.json").read_text(encoding="utf-8")
)
assert gate["gate_id"] == "AX-GE2E-P00-GATE-001"
assert gate["task_id"] == "AX-GE2E-P00-T01"
assert gate["review_authority"]["type"] == "HUMAN_PRODUCT_AUTHORITY"
assert gate["review_authority"]["decision"] == "APPROVED"
assert gate["disposition"] == "PASS"
assert gate["task_state"] == "ACCEPTED"
assert gate["next_authorised_phase"] == "P01"
assert gate["next_authorised_task"] == "AX-GE2E-P01-T01"
assert gate["rollback_rehearsal"]["result"] == "PASS"
assert gate["rollback_rehearsal"]["comparison_status"] == "identical"
assert gate["rollback_rehearsal"]["residual_files"] == 0
assert gate["truth_boundary"]["public_launch_authorised"] is False
assert gate["truth_boundary"]["global_product_rollback_tested"] is False

p13_runtime = (
    ROOT
    / "data/sovereign-macro/sovereign-macro-strategy-workspace-runtime.v0.1.json"
)
if p13_runtime.is_file():
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/verify_p13_sovereign_macro_strategy_workspace.py")],
        cwd=ROOT,
        check=True,
    )

print(
    json.dumps(
        {
            "status": "PASS",
            "tasks": len(tasks),
            "p00_state": p00["state"],
            "p00_rollback_tested": p00["rollback"]["tested"],
            "p01_state": p01["state"],
            "foundational_libraries": len(registry["foundational_libraries"]),
            "opportunity_libraries": len(registry["opportunity_libraries"]),
            "catalogues": len(index["catalogues"]),
            "p13_engineering_verifier_executed": p13_runtime.is_file(),
            "public_launch_authorised": False,
            "global_product_rollback_tested": False,
        },
        sort_keys=True,
    )
)
