from __future__ import annotations

import argparse
import json
from pathlib import Path

from axignal_api.o01_quality_common import O01QualityCampaignError
from axignal_api.o01_quality_execute import run_campaign

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--authority-envelope", type=Path, required=True)
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        result = run_campaign(
            plan_path=args.plan,
            authority_envelope_path=args.authority_envelope,
            raw_dir=args.raw_dir,
            output_dir=args.output_dir,
        )
    except (
        KeyError,
        OSError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        O01QualityCampaignError,
    ) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
