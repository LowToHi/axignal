from __future__ import annotations

import argparse
import json
from pathlib import Path

from axignal_api.gate7_o01_runtime import run_campaign
from axignal_api.o01_quality_common import O01QualityCampaignError
from axignal_api.o01_quality_failure import (
    diagnose_frozen_first_request,
    purge_ephemeral_directory,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--authority-envelope", type=Path, required=True)
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--kill-switch-path", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = run_campaign(
            plan_path=args.plan,
            authority_envelope_path=args.authority_envelope,
            raw_dir=args.raw_dir,
            output_dir=args.output_dir,
            kill_switch_path=args.kill_switch_path,
        )
    except (
        KeyError,
        OSError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        O01QualityCampaignError,
    ) as exc:
        raw_directory_existed = purge_ephemeral_directory(args.raw_dir)
        failure: dict[str, object] = {
            "schema_version": "axignal.o01-campaign-failure/v0.6",
            "status": "FAIL",
            "output": "O01_QUALITY_COVERAGE_LAG_FAIL",
            "failure_stage": "CAMPAIGN_EXECUTION",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "raw_directory_existed": raw_directory_existed,
            "raw_directory_removed": not args.raw_dir.exists(),
            "raw_plaintext_uploaded": False,
            "fabricated_evidence": 0,
            "check_query_syntax": False,
            "source_scope": "ALL",
            "source_state": "CANDIDATE",
            "public_claim_contribution": False,
        }
        if "TED returned HTTP " in str(exc):
            failure["failure_stage"] = "TED_SEARCH_HTTP"
            try:
                failure["ted_diagnostic_probe"] = diagnose_frozen_first_request(
                    args.plan
                )
            except Exception as diagnostic_exc:
                failure["ted_diagnostic_probe"] = {
                    "status": "DIAGNOSTIC_FAILED_CLOSED",
                    "error_type": type(diagnostic_exc).__name__,
                    "raw_response_retained": False,
                }
        args.output_dir.mkdir(parents=True, exist_ok=True)
        failure_path = args.output_dir / "campaign-failure.v0.6.json"
        failure_path.write_text(
            json.dumps(failure, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(failure, ensure_ascii=False, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
