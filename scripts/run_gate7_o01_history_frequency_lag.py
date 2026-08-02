from __future__ import annotations

import argparse
import json
from pathlib import Path

from axignal_api.o01_history_frequency_lag import run_campaign
from axignal_api.o01_quality_common import O01QualityCampaignError


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Execute the frozen AX-LIB-O01 history, frequency and lag campaign"
    )
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    try:
        result = run_campaign(args.plan, args.output_dir)
    except (
        KeyError,
        OSError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        O01QualityCampaignError,
    ) as exc:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        failure = {
            "schema_version": "axignal.o01-history-frequency-lag-failure/v0.1",
            "status": "FAIL",
            "output": "O01_HISTORY_FREQUENCY_LAG_FAIL",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "raw_notice_payloads_persisted": False,
            "daily_package_bodies_persisted": False,
            "contact_values_persisted": False,
            "fabricated_evidence": 0,
            "synthetic_evidence": 0,
            "claim_contribution": False,
            "gate7_closed": False,
            "public_launch": "NO_GO",
        }
        (args.output_dir / "campaign-failure.v0.1.json").write_text(
            json.dumps(failure, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(failure, ensure_ascii=False, sort_keys=True))
        return 1

    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
