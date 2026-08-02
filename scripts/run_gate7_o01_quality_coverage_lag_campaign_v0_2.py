from __future__ import annotations

import argparse
import json
from pathlib import Path

from axignal_api.gate7_o01_runtime import run_campaign_v0_2
from axignal_api.o01_quality_common import O01QualityCampaignError
from axignal_api.o01_quality_failure import (
    diagnose_frozen_first_request,
    purge_ephemeral_directory,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--authority-envelope", type=Path, required=True)
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--kill-switch-path", type=Path, required=True)
    return parser


def failure_payload(
    exc: Exception,
    *,
    plan_path: Path,
    raw_dir: Path,
) -> dict[str, object]:
    raw_directory_existed = purge_ephemeral_directory(raw_dir)
    payload: dict[str, object] = {
        "schema_version": "axignal.o01-campaign-failure/v0.2",
        "status": "FAIL",
        "output": "O01_QUALITY_COVERAGE_LAG_FAIL",
        "failure_stage": "CAMPAIGN_EXECUTION",
        "error_type": type(exc).__name__,
        "error": str(exc),
        "raw_directory_existed": raw_directory_existed,
        "raw_directory_removed": not raw_dir.exists(),
        "raw_plaintext_uploaded": False,
        "fabricated_evidence": 0,
        "source_state": "CANDIDATE",
        "public_claim_contribution": False,
    }
    if "TED returned HTTP " in str(exc):
        payload["failure_stage"] = "TED_SEARCH_HTTP"
        try:
            payload["ted_diagnostic_probe"] = diagnose_frozen_first_request(
                plan_path
            )
        except Exception as diagnostic_exc:
            payload["ted_diagnostic_probe"] = {
                "status": "DIAGNOSTIC_FAILED_CLOSED",
                "error_type": type(diagnostic_exc).__name__,
                "raw_response_retained": False,
            }
    return payload


def main() -> int:
    args = build_parser().parse_args()
    try:
        result = run_campaign_v0_2(
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
        failure = failure_payload(
            exc,
            plan_path=args.plan,
            raw_dir=args.raw_dir,
        )
        args.output_dir.mkdir(parents=True, exist_ok=True)
        failure_path = args.output_dir / "campaign-failure.v0.2.json"
        failure_path.write_text(
            json.dumps(failure, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )
        print(json.dumps(failure, ensure_ascii=False, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
