from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import verify_gate7_o01_retained_evidence_v8 as implementation

PUBLISHED_KEY = "direct_first-seen-timestamp-claimed"
INTERNAL_ALIAS = "direct_first_seen_timestamp_claimed"


def _adapt_lag_schema(value: dict[str, Any], *, context: str) -> dict[str, Any]:
    if PUBLISHED_KEY not in value:
        raise implementation.VerificationError(
            f"Published lag key is missing in {context}: {PUBLISHED_KEY}"
        )
    if INTERNAL_ALIAS in value:
        raise implementation.VerificationError(
            f"Unexpected pre-existing verifier alias in {context}: {INTERNAL_ALIAS}"
        )
    if value[PUBLISHED_KEY] is not False:
        raise implementation.VerificationError(
            f"Exact first-seen timestamp claim enabled in {context}"
        )
    adapted = dict(value)
    adapted[INTERNAL_ALIAS] = value[PUBLISHED_KEY]
    return adapted


def schema_aware_load_json(path: Path) -> dict[str, Any]:
    value = implementation.load_json(path)
    if path.name == "publication-lag-report.v0.1.json":
        return _adapt_lag_schema(value, context=path.name)
    if path.name == "final-result.v0.1.json":
        adapted = dict(value)
        adapted["lag"] = _adapt_lag_schema(
            value["lag"],
            context=f"{path.name}.lag",
        )
        return adapted
    return value


def verify(
    plan_path: Path,
    artifact_metadata_path: Path,
    evidence_dir: Path,
) -> dict[str, Any]:
    original_loader = implementation.load_json
    implementation.load_json = schema_aware_load_json
    try:
        result = implementation.verify(
            plan_path,
            artifact_metadata_path,
            evidence_dir,
        )
    finally:
        implementation.load_json = original_loader
    result["verifier_schema_adapter"] = {
        "published_key": PUBLISHED_KEY,
        "internal_alias": INTERNAL_ALIAS,
        "source_files_mutated": False,
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--artifact-metadata", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = verify(
            args.plan.resolve(),
            args.artifact_metadata.resolve(),
            args.evidence_dir.resolve(),
        )
    except (
        KeyError,
        OSError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        implementation.VerificationError,
    ) as exc:
        result = {
            "schema_version": (
                "axignal.o01-history-frequency-lag-"
                "verification-repair-result/v0.2"
            ),
            "status": "FAIL",
            "output": "O01_HISTORY_FREQUENCY_LAG_RETAINED_EVIDENCE_FAIL",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "repair_ted_network_requests": 0,
            "source_files_mutated": False,
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
        return 1

    result["schema_version"] = (
        "axignal.o01-history-frequency-lag-verification-repair-result/v0.2"
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
