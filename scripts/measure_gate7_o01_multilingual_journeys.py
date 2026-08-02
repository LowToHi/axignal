from __future__ import annotations

import argparse
import json
from pathlib import Path

from axignal_api.gate7_o01_multilingual import (
    load_retained_records,
    measure_multilingual_journeys,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    payloads = [
        path.read_bytes()
        for path in sorted(args.raw_dir.glob("retained-*-page-*.json"))
    ]
    records = load_retained_records(payloads)
    result = measure_multilingual_journeys(
        records,
        required_languages=list(plan["sampling"]["languages"]),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
