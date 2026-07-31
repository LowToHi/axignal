#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "data/intent-intelligence/p18-rollback-plan.v0.1.json"


def run(*args: str, text: bool = True) -> str | bytes:
    result = subprocess.run(
        args,
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=text,
    )
    return result.stdout


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def baseline_has_path(baseline: str, relative_path: str) -> bool:
    result = subprocess.run(
        ["git", "cat-file", "-e", f"{baseline}:{relative_path}"],
        cwd=ROOT,
        check=False,
        capture_output=True,
    )
    return result.returncode == 0


plan: dict[str, Any] = json.loads(
    PLAN_PATH.read_text(encoding="utf-8")
)
baseline = plan["baseline_sha"]
changed = sorted(
    item
    for item in str(
        run("git", "diff", "--name-only", f"{baseline}...HEAD")
    ).splitlines()
    if item
)
expected = sorted(plan["expected_changed_paths"])
assert changed == expected, {
    "unexpected": sorted(set(changed) - set(expected)),
    "missing": sorted(set(expected) - set(changed)),
}

before = {
    relative_path: digest(ROOT / relative_path)
    for relative_path in plan["preserved_p17_authority_files"]
}

for relative_path in plan["p18_only_artifacts"]:
    path = ROOT / relative_path
    assert path.is_file(), relative_path
    assert not baseline_has_path(baseline, relative_path), relative_path
    path.unlink()

for relative_path in plan["p18_only_artifacts"]:
    assert not (ROOT / relative_path).exists(), relative_path

for relative_path in plan["restored_baseline_files"]:
    content = run("git", "show", f"{baseline}:{relative_path}", text=False)
    assert isinstance(content, bytes)
    path = ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)

for relative_path, expected_digest in before.items():
    assert digest(ROOT / relative_path) == expected_digest, relative_path

print(
    json.dumps(
        {
            "status": "PASS",
            "task_id": "AX-GE2E-P18-T01",
            "baseline_sha": baseline,
            "changed_paths": len(changed),
            "removed_p18_artifacts": len(
                plan["p18_only_artifacts"]
            ),
            "preserved_p17_authority_files": len(before),
            "residual_paths": 0,
            "rolled_back_tree_equals_baseline": True,
        },
        sort_keys=True,
    )
)
