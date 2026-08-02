from __future__ import annotations

import argparse
import json
from pathlib import Path

import verify_gate7_o01_quality_coverage_lag_contract_v0_4 as proven
from materialize_gate7_o01_quality_coverage_lag_plan_v0_5 import materialize_plan

QUERY = (
    "buyer-country IN ({country}) AND publication-date = "
    "(20260701 <> 20260731) SORT BY publication-number"
)


class ContractError(RuntimeError):
    """Raised when the v0.5 contract cannot be evaluated."""


def configure_proven_verifier() -> None:
    proven.materialize_plan = materialize_plan
    proven.QUERY = QUERY


def verify_plan(path: Path) -> dict[str, object]:
    configure_proven_verifier()
    result = proven.verify_plan(path)
    if result.get("campaign_id") != "AX-LIB-O01-TED-QALAG-ML-CONTROLS-v0.5":
        raise ContractError("Campaign identity drift")
    if result.get("source_scope") != "ALL":
        raise ContractError("Historical scope regressed")
    result["output"] = "O01_QUALITY_COVERAGE_LAG_V0_5_PLAN_FROZEN"
    result["query_contract"] = QUERY
    return result


def verify_final(path: Path, result_dir: Path) -> dict[str, object]:
    configure_proven_verifier()
    result = proven.verify_final(path, result_dir)
    result["query_contract"] = QUERY
    result["canonical_date_range"] = True
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--result-dir", type=Path)
    args = parser.parse_args()
    try:
        result = (
            verify_final(args.plan, args.result_dir)
            if args.result_dir
            else verify_plan(args.plan)
        )
    except (
        KeyError,
        OSError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        ContractError,
        proven.ContractError,
    ) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 2 if args.result_dir and result["status"] != "PASS" else 0


if __name__ == "__main__":
    raise SystemExit(main())
