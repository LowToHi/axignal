#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P19_HEAD = "3136579a4da91cd79c4cfdcd4b28b4a324565226"
PLAN = ROOT / "data/enterprise/p20-rollback-plan.v0.1.json"
P19_FILES = [
    "data/scenarios/scenarios-calibration-outcomes-runtime.v0.1.json",
    "data/scenarios/p19-adversarial-cases.v0.1.json",
    "data/scenarios/p19-conformance-fixtures.v0.1.json",
    "schemas/scenarios-calibration-outcomes-runtime.schema.json",
    "schemas/scenarios-calibration-outcomes-cases.schema.json",
    "schemas/scenarios-calibration-outcomes-fixtures.schema.json",
    "docs/scenarios/P19-scenarios-calibration-outcomes-v0.1.md",
]
EXPECTED_RESTORED_FILES = {
    ".github/workflows/executable-spine.yml",
    "scripts/verify_p19_rollback.py",
}

plan = json.loads(PLAN.read_text(encoding="utf-8"))
assert plan["baseline_sha"] == P19_HEAD
assert len(plan["restored_baseline_files"]) == len(EXPECTED_RESTORED_FILES)
assert set(plan["restored_baseline_files"]) == EXPECTED_RESTORED_FILES
for relative_path in P19_FILES:
    assert (ROOT / relative_path).is_file(), relative_path

print(
    json.dumps(
        {
            "status": "PASS",
            "task_id": "AX-GE2E-P19-T01",
            "verification_head": P19_HEAD,
            "forward_compatible_integrity_guard": True,
            "restored_baseline_files": len(EXPECTED_RESTORED_FILES),
            "byte_exact_rehearsal_delegated_to": "AX-GE2E-P20-T01",
        },
        sort_keys=True,
    )
)
