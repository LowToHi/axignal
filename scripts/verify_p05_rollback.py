#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "data/foundations/p05-rollback-plan.v0.1.json"
plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
baseline = plan["baseline_sha"]


def run(*args: str) -> str:
    completed = subprocess.run(
        args,
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


changed = sorted(
    path
    for path in run(
        "git",
        "diff",
        "--name-only",
        f"{baseline}...HEAD",
    ).splitlines()
    if path
)
expected = sorted(plan["expected_changed_paths"])
assert changed == expected, {
    "unexpected": sorted(set(changed) - set(expected)),
    "missing": sorted(set(expected) - set(changed)),
}

preserved_before = {
    path: file_hash(ROOT / path) for path in plan["preserved_p04_authority_files"]
}

for relative in plan["p05_only_artifacts"]:
    path = ROOT / relative
    assert path.is_file(), f"missing P05 artifact before rollback: {relative}"
    path.unlink()

for relative in plan["restored_baseline_files"]:
    content = subprocess.run(
        ["git", "show", f"{baseline}:{relative}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout
    (ROOT / relative).write_bytes(content)

for relative in plan["p05_only_artifacts"]:
    assert not (ROOT / relative).exists(), f"residual P05 artifact: {relative}"

preserved_after = {
    path: file_hash(ROOT / path) for path in plan["preserved_p04_authority_files"]
}
assert preserved_before == preserved_after, "P04 authority drift during P05 rollback"

diff = subprocess.run(
    ["git", "diff", "--quiet", baseline, "--", "."],
    cwd=ROOT,
    check=False,
)
assert diff.returncode == 0, "rolled-back tree differs from frozen P04 baseline"

result = {
    "status": "PASS",
    "task_id": "AX-GE2E-P05-T01",
    "baseline_sha": baseline,
    "changed_paths": len(changed),
    "removed_p05_artifacts": len(plan["p05_only_artifacts"]),
    "restored_baseline_files": len(plan["restored_baseline_files"]),
    "preserved_p04_authority_files": len(plan["preserved_p04_authority_files"]),
    "residual_paths": 0,
    "rolled_back_tree_equals_baseline": True,
}
print(json.dumps(result, sort_keys=True))
