#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = [
    "docs/contracts/30-global-e2e-development-contract-v1.4.md",
    "docs/adr/ADR-015-finished-global-product-before-public-launch.md",
    "docs/roadmap/14-global-e2e-development-program-v1.4.md",
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

assert tasks[0]["state"] == "IN_PROGRESS"
assert all(task["state"] == "BLOCKED" for task in tasks[1:])
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

current = (ROOT / "docs/roadmap/06-current-execution-state.md").read_text(encoding="utf-8")
assert '"public_launch_authorised": false' in current
assert '"partial_launch_allowed": false' in current
assert "AX-GE2E-P00-T01" in current

routing = yaml.safe_load(
    (ROOT / "skills/global-e2e-routing.yaml").read_text(encoding="utf-8")
)
assert routing["programme"] == "P00-P24"
assert [item["phase"] for item in routing["phase_routes"]] == [
    f"P{i:02d}" for i in range(25)
]
assert all(item["gate_reviewer"] == "gate-evaluator" for item in routing["phase_routes"])

print(
    json.dumps(
        {
            "status": "PASS",
            "tasks": len(tasks),
            "foundational_libraries": len(registry["foundational_libraries"]),
            "opportunity_libraries": len(registry["opportunity_libraries"]),
            "catalogues": len(index["catalogues"]),
            "public_launch_authorised": False,
        },
        sort_keys=True,
    )
)
