from __future__ import annotations

import argparse
import json
from pathlib import Path

from axignal_api.o01_quality_http import NetworkBudget
from probe_gate7_o01_history_contract import probe_search


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    budget = NetworkBudget(4)
    probes = [
        probe_search(
            query="publication-date >= 20260701 AND publication-date <= 20260731",
            pagination_mode="PAGE_NUMBER",
            budget=budget,
        ),
        probe_search(
            query="publication-date >= 20150101 AND publication-date <= 20260802",
            pagination_mode="PAGE_NUMBER",
            budget=budget,
        ),
        probe_search(
            query="publication-date >= 20150101 AND publication-date <= 20260802",
            pagination_mode="ITERATION",
            budget=budget,
        ),
        probe_search(
            query="publication-date >= 20160101 AND publication-date <= 20161231",
            pagination_mode="ITERATION",
            budget=budget,
        ),
    ]
    result = {
        "schema_version": "axignal.o01-search-query-contract-probe/v0.2",
        "status": "PASS",
        "output": "O01_SEARCH_QUERY_CONTRACT_PROBE_COMPLETE",
        "network_requests_used": budget.used,
        "network_requests_maximum": budget.maximum,
        "probes": probes,
        "all_queries_without_sort_clause": all(
            "SORT" not in item["query"] for item in probes
        ),
        "raw_search_responses_retained": False,
        "claim_contribution": False,
        "gate7_closed": False,
        "public_launch": "NO_GO",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
