#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "docs/tasks/active/2026-08-04_axignal-c0-canonical-reconciliation.v1.json"
CONTRACT = ROOT / "apps/landing/lib/candidate-pricing-contract.ts"
ADAPTER = ROOT / "apps/landing/lib/candidate-pricing.ts"
RECONCILED_PATHS = {
    "apps/landing/lib/candidate-pricing-contract.ts",
    "apps/landing/lib/candidate-pricing.ts",
}


def main() -> int:
    document = json.loads(LEDGER.read_text(encoding="utf-8"))
    assert document["schema"] == "axignal.c0.canonical-reconciliation.v1"
    assert document["state"] == "TREE_RECONCILED_AWAITING_EXACT_HEAD_MATRIX"

    preserved = set(document["wp2_only_paths_preserved"])
    assert RECONCILED_PATHS <= preserved
    preserved -= RECONCILED_PATHS

    contract = CONTRACT.read_text(encoding="utf-8")
    adapter = ADAPTER.read_text(encoding="utf-8")
    assert 'from "./canonical-commercial-contract"' in contract
    assert "AXIGNAL_PRICE_BOOK" in contract
    assert 'from "./landing-data"' not in contract
    assert 'from "./landing-data"' not in adapter
    assert "type CandidatePlan" in adapter

    document["policy"]["wp2_only_files_under_imported_directories"] = (
        "PRESERVED_UNLESS_EXPLICITLY_RECONCILED_TO_WP1_AUTHORITY"
    )
    document["wp2_only_paths_preserved"] = sorted(preserved)
    document["c0_reconciled_wp2_only_paths"] = [
        {
            "path": "apps/landing/lib/candidate-pricing-contract.ts",
            "resolution": "BIND_RUNTIME_ADAPTER_TO_WP1_CANONICAL_PRICE_BOOK",
            "reason": (
                "Preserve fail-closed commercial runtime validation while removing "
                "the retired public CandidatePlan authority."
            ),
        },
        {
            "path": "apps/landing/lib/candidate-pricing.ts",
            "resolution": "IMPORT_PLAN_TYPE_FROM_RECONCILED_RUNTIME_ADAPTER",
            "reason": (
                "The server-only compatibility adapter no longer depends on the "
                "WP1 landing presentation model."
            ),
        },
    ]
    document["c0_reconciliation_tests"] = [
        "apps/landing/tests/candidate-pricing-contract.test.ts",
        "pnpm --filter @axignal/landing typecheck",
        "pnpm --filter @axignal/landing build",
    ]
    document["output_markers"] = [
        document.pop("output_marker"),
        "AX_C0_PRICING_AUTHORITY_RECONCILIATION_PASS",
    ]

    LEDGER.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "PASS",
                "marker": "AX_C0_PRICING_AUTHORITY_RECONCILIATION_PASS",
                "reconciled_paths": sorted(RECONCILED_PATHS),
                "preserved_wp2_only_paths": len(preserved),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
