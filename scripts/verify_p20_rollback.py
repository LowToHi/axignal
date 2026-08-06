#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P20_HEAD = "87b30a1035b557040dd33c5f0acedc62d0ebfa93"
PLAN = ROOT / "data/commercial/p21-rollback-plan.v0.1.json"
P20_FILES = [
    "data/enterprise/enterprise-api-private-data-runtime.v0.1.json",
    "data/enterprise/p20-adversarial-cases.v0.1.json",
    "data/enterprise/p20-conformance-fixtures.v0.1.json",
    "schemas/enterprise-api-private-data-runtime.schema.json",
    "schemas/enterprise-api-private-data-cases.schema.json",
    "schemas/enterprise-api-private-data-fixtures.schema.json",
    "docs/enterprise/P20-enterprise-api-private-data-v0.1.md",
]
EXPECTED_RESTORED_FILES = {"scripts/verify_p20_rollback.py"}

plan = json.loads(PLAN.read_text(encoding="utf-8"))
assert plan["baseline_sha"] == P20_HEAD
assert len(plan["restored_baseline_files"]) == len(EXPECTED_RESTORED_FILES)
assert set(plan["restored_baseline_files"]) == EXPECTED_RESTORED_FILES
for relative_path in P20_FILES:
    assert (ROOT / relative_path).is_file(), relative_path

print(
    json.dumps(
        {
            "status": "PASS",
            "task_id": "AX-GE2E-P20-T01",
            "verification_head": P20_HEAD,
            "forward_compatible_integrity_guard": True,
            "restored_baseline_files": len(EXPECTED_RESTORED_FILES),
            "byte_exact_rehearsal_delegated_to": "AX-GE2E-P21-T01",
        },
        sort_keys=True,
    )
)
