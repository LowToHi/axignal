from __future__ import annotations

import argparse
import json
from pathlib import Path

from axignal_api.gate7_o01_controls import (
    finalize_operational_controls,
    rehearse_kill_switch,
    write_boundary_checkpoint,
)


def load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def load_jsonl(path: Path) -> list[dict[str, object]]:
    if not path.is_file():
        return []
    values: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        value = json.loads(line)
        if isinstance(value, dict):
            values.append(value)
    return values


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    preflight = subparsers.add_parser("preflight")
    preflight.add_argument("--signal-path", type=Path, required=True)
    preflight.add_argument("--checkpoint", type=Path, required=True)
    preflight.add_argument("--output", type=Path, required=True)

    finalise = subparsers.add_parser("finalise")
    finalise.add_argument("--preflight", type=Path, required=True)
    finalise.add_argument("--checkpoint", type=Path, required=True)
    finalise.add_argument("--preliminary", type=Path, required=True)
    finalise.add_argument("--notification-ledger", type=Path, required=True)
    finalise.add_argument("--raw-retention", type=Path, required=True)
    finalise.add_argument("--output", type=Path, required=True)
    return parser


def write_result(path: Path, result: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "preflight":
        checkpoint = write_boundary_checkpoint(args.checkpoint)
        kill_switch = rehearse_kill_switch(args.signal_path)
        result: dict[str, object] = {
            "schema_version": "axignal.o01-operational-controls-preflight/v0.2",
            "status": "PASS" if kill_switch["pass"] else "FAIL",
            "checkpoint": checkpoint,
            "kill_switch": kill_switch,
            "external_network_requests": 0,
            "fabricated_evidence": 0,
        }
    else:
        preflight = load_json(args.preflight)
        result = finalize_operational_controls(
            checkpoint=load_json(args.checkpoint),
            kill_switch=preflight["kill_switch"],
            preliminary=load_json(args.preliminary),
            notification_entries=load_jsonl(args.notification_ledger),
            raw_retention=load_json(args.raw_retention),
        )
    write_result(args.output, result)
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
