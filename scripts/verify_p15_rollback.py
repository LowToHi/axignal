#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "data/energy-climate/p15-rollback-plan.v0.1.json"


def run(*args: str, text: bool = True, check: bool = True) -> str | bytes:
    result = subprocess.run(
        args,
        cwd=ROOT,
        check=check,
        capture_output=True,
        text=text,
    )
    return result.stdout


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


plan: dict[str, Any] = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
baseline = plan["baseline_sha"]
expected = set(plan["expected_changed_paths"])
changed_since_baseline = {
    item
    for item in str(
        run("git", "diff", "--name-only", f"{baseline}...HEAD")
    ).splitlines()
    if item
}

# P15 is an historical phase contract. A consolidated candidate legitimately
# contains later phases, so rollback authority is limited to the declared P15
# surface rather than the complete repository after the P14 baseline.
assert expected <= changed_since_baseline, {
    "missing_p15_paths": sorted(expected - changed_since_baseline),
}
outside_scope = sorted(changed_since_baseline - expected)

before = {
    rel: digest(ROOT / rel)
    for rel in plan["preserved_p14_authority_files"]
}

for rel in plan["p15_only_artifacts"]:
    path = ROOT / rel
    assert path.is_file(), rel
    path.unlink()

for rel in plan["restored_baseline_files"]:
    content = run("git", "show", f"{baseline}:{rel}", text=False)
    assert isinstance(content, bytes)
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)

after = {
    rel: digest(ROOT / rel)
    for rel in plan["preserved_p14_authority_files"]
}
assert before == after

worktree_changes = {
    item
    for item in str(run("git", "diff", "--name-only", "HEAD", "--", ".")).splitlines()
    if item
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
            "task_id": "AX-GE2E-P15-T01",
            "baseline_sha": baseline,
            "p15_scope_paths": len(expected),
            "repository_changes_outside_p15_scope": len(outside_scope),
            "restored_baseline_files": len(plan["restored_baseline_files"]),
            "rollback_mutations_outside_scope": 0,
            "preserved_p14_authority": True,
            "rolled_back_scope_equals_baseline": True,
            "whole_repository_rollback_claimed": False,
        },
        sort_keys=True,
    )
)
