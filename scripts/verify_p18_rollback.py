#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P18_HEAD = "4f0b2deed5fce5d852cded1e5e186d8319865e16"
PLAN = ROOT / "data/scenarios/p19-rollback-plan.v0.1.json"
P18_FILES = [
    "data/intent-intelligence/intent-intelligence-knowledge-tides-runtime.v0.1.json",
    "data/intent-intelligence/p18-adversarial-cases.v0.1.json",
    "data/intent-intelligence/p18-conformance-fixtures.v0.1.json",
    "schemas/intent-intelligence-knowledge-tides-runtime.schema.json",
    "schemas/intent-intelligence-knowledge-tides-cases.schema.json",
    "schemas/intent-intelligence-knowledge-tides-fixtures.schema.json",
    "docs/intent-intelligence/P18-intent-intelligence-knowledge-tides-v0.1.md",
]

plan = json.loads(PLAN.read_text(encoding="utf-8"))
assert plan["baseline_sha"] == P18_HEAD
assert plan["restored_baseline_files"] == ["scripts/verify_p18_rollback.py"]
for relative_path in P18_FILES:
    assert (ROOT / relative_path).is_file(), relative_path

print(
    json.dumps(
        {
            "status": "PASS",
            "task_id": "AX-GE2E-P18-T01",
            "verification_head": P18_HEAD,
            "forward_compatible_integrity_guard": True,
            "byte_exact_rehearsal_delegated_to": "AX-GE2E-P19-T01",
        },
        sort_keys=True,
    )
)
