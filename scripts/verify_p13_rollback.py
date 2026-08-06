#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "data/sovereign-macro/p13-rollback-plan.v0.1.json"


def run(*args: str, check: bool = True) -> str:
    return subprocess.run(
        args,
        cwd=ROOT,
        check=check,
        capture_output=True,
        text=True,
    ).stdout


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
baseline = plan["baseline_sha"]
expected = set(plan["expected_changed_paths"])
changed_since_baseline = {
    path
    for path in run("git", "diff", "--name-only", f"{baseline}...HEAD").splitlines()
    if path
}

# P13 is an historical phase contract. In a consolidated candidate, later phases
# are expected to exist. The rollback authority is therefore exactly its declared
# surface, not the whole repository accumulated after the P12 baseline.
assert expected <= changed_since_baseline, {
    "missing_p13_paths": sorted(expected - changed_since_baseline),
}
outside_scope = sorted(changed_since_baseline - expected)

before = {
    path: digest(ROOT / path)
    for path in plan["preserved_p12_authority_files"]
}

for relative_path in plan["p13_only_artifacts"]:
    path = ROOT / relative_path
    assert path.is_file(), relative_path
    path.unlink()

for relative_path in plan["restored_baseline_files"]:
    content = subprocess.run(
        ["git", "show", f"{baseline}:{relative_path}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout
    (ROOT / relative_path).write_bytes(content)

after = {
    path: digest(ROOT / path)
    for path in plan["preserved_p12_authority_files"]
}
assert before == after

worktree_changes = {
    path
    for path in run("git", "diff", "--name-only", "HEAD", "--", ".").splitlines()
    if path
}
assert worktree_changes == expected, {
    "unexpected_rollback_mutations": sorted(worktree_changes - expected),
    "missing_rollback_mutations": sorted(expected - worktree_changes),
}

scope_result = subprocess.run(
    ["git", "diff", "--quiet", baseline, "--", *sorted(expected)],
    cwd=ROOT,
    check=False,
)
assert scope_result.returncode == 0

print(
    json.dumps(
        {
            "status": "PASS",
            "task_id": "AX-GE2E-P13-T01",
            "baseline_sha": baseline,
            "p13_scope_paths": len(expected),
            "repository_changes_outside_p13_scope": len(outside_scope),
            "restored_baseline_files": len(plan["restored_baseline_files"]),
            "rollback_mutations_outside_scope": 0,
            "preserved_p12_authority": True,
            "rolled_back_scope_equals_baseline": True,
            "whole_repository_rollback_claimed": False,
        },
        sort_keys=True,
    )
)
