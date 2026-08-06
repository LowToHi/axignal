#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs/tasks/active/2026-08-04_axignal-e2e-blocker-ownership.v1.json"
EXPECTED_IDS = {f"AX-SW-BLK-{index:03d}" for index in range(1, 16)}
EXPECTED_COUNTS = {"C1": 5, "C3": 5, "C4": 3, "C14": 2}
CLOSED_IDS = {
    "AX-SW-BLK-001",
    "AX-SW-BLK-002",
    "AX-SW-BLK-003",
    "AX-SW-BLK-011",
    "AX-SW-BLK-014",
}


def main() -> int:
    document = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert document["schema"] == "axignal.e2e.blocker-ownership.v1"
    assert document["contract_id"] == "AX-GE2E-CLOSURE-EXECUTION-002"
    assert document["work_package"] == "WP2_CLASSIFY_PR167_BLOCKERS_BY_CLOSURE_CLAUSE"
    assert document["source_pull_request"] == 167
    assert document["source_snapshot_sha"] == "213b4ebc068b79af508648ace98d5c2ff136298e"

    blockers = document["blockers"]
    ids = [blocker["id"] for blocker in blockers]
    assert len(ids) == len(set(ids)) == 15
    assert set(ids) == EXPECTED_IDS

    allowed = set(document["allowed_owner_clauses"])
    assert allowed == set(EXPECTED_COUNTS)
    owners = Counter()
    for blocker in blockers:
        owner = blocker.get("owner_clause")
        assert isinstance(owner, str) and owner in allowed
        assert not isinstance(owner, list)
        owners[owner] += 1

        disposition = blocker.get("disposition")
        if blocker["id"] in CLOSED_IDS:
            assert owner == "C1"
            assert disposition == "CLOSED_ON_SOURCE_SNAPSHOT"
        else:
            assert owner != "C1"
            assert disposition == "DEFERRED_TO_OWNER_CLAUSE"

        dependencies = blocker.get("downstream_dependencies", [])
        assert owner not in dependencies
        assert len(dependencies) == len(set(dependencies))

    assert dict(owners) == EXPECTED_COUNTS
    assert document["summary"] == {
        "total": 15,
        **EXPECTED_COUNTS,
        "closed_on_source_snapshot": 5,
        "deferred_to_owner_clause": 10,
    }
    assert document["invariants"]["exactly_one_owner_per_blocker"] is True
    assert document["invariants"]["partial_is_not_closed"] is True
    assert document["invariants"]["downstream_dependency_is_not_coownership"] is True
    assert document["invariants"]["human_authority_is_never_automatically_manufactured"] is True
    assert document["invariants"]["public_launch_authorized"] is False

    accessibility = next(item for item in blockers if item["id"] == "AX-SW-BLK-013")
    assert accessibility["retained_external_authorities"] == ["HUMAN_ACCESSIBILITY_AUTHORITY"]
    assert document["output_marker"] == "AX_WP2_BLOCKER_OWNERSHIP_PASS"

    print(
        json.dumps(
            {
                "status": "PASS",
                "marker": document["output_marker"],
                "source_snapshot_sha": document["source_snapshot_sha"],
                "owners": dict(owners),
                "closed": len(CLOSED_IDS),
                "deferred": len(blockers) - len(CLOSED_IDS),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
