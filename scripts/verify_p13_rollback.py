#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "data/sovereign-macro/p13-rollback-plan.v0.1.json"


def run(*args: str) -> str:
    return subprocess.run(
        args,
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
baseline = plan["baseline_sha"]
changed = sorted(
    path
    for path in run("git", "diff", "--name-only", f"{baseline}...HEAD").splitlines()
    if path
)
expected = sorted(plan["expected_changed_paths"])
assert changed == expected, {
    "unexpected": sorted(set(changed) - set(expected)),
    "missing": sorted(set(expected) - set(changed)),
}

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
assert (
    subprocess.run(
        ["git", "diff", "--quiet", baseline, "--", "."],
        cwd=ROOT,
        check=False,
    ).returncode
    == 0
)

print(
    json.dumps(
        {
            "status": "PASS",
            "task_id": "AX-GE2E-P13-T01",
            "baseline_sha": baseline,
            "changed_paths": len(changed),
            "restored_baseline_files": len(plan["restored_baseline_files"]),
            "residual_paths": 0,
            "rolled_back_tree_equals_baseline": True,
        },
        sort_keys=True,
    )
)
