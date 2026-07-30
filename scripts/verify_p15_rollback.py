#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "data/energy-climate/p15-rollback-plan.v0.1.json"


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


plan: dict[str, Any] = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
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
            "task_id": "AX-GE2E-P15-T01",
            "baseline_sha": baseline,
            "changed_paths": len(changed),
            "restored_baseline_files": len(
                plan["restored_baseline_files"]
            ),
            "residual_paths": 0,
            "rolled_back_tree_equals_baseline": True,
        },
        sort_keys=True,
    )
)
