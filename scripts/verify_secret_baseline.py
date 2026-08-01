from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

BASELINE_PATH = Path("data/security/reviewed-secret-baseline.v1.json")
EXCLUDE_PATTERN = (
    r"(^|/)(\.git|\.pytest_cache|\.ruff_cache|pnpm-lock\.yaml|.*\.lock|"
    r"test-results|playwright-report|bandit-report\.json|pip-audit-report\.json|"
    r"coverage-python\.xml|detect-secrets-report\.json|"
    r"reviewed-secret-baseline\.v1\.json)(/|$)"
)
Record = tuple[str, int, str, str]


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Unable to load {path}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return payload


def _scan() -> tuple[list[Record], Counter[str], int]:
    completed = subprocess.run(
        [
            "detect-secrets",
            "scan",
            "--all-files",
            "--exclude-files",
            EXCLUDE_PATTERN,
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError("detect-secrets scan failed")
    try:
        report = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("detect-secrets returned invalid JSON") from exc
    results = report.get("results")
    if not isinstance(results, dict):
        raise RuntimeError("detect-secrets report has no results object")

    records: list[Record] = []
    detector_counts: Counter[str] = Counter()
    for path, findings in results.items():
        if not isinstance(path, str) or not isinstance(findings, list):
            raise RuntimeError("detect-secrets returned an invalid finding group")
        for finding in findings:
            if not isinstance(finding, dict):
                raise RuntimeError("detect-secrets returned an invalid finding")
            detector = str(finding["type"])
            record = (
                path,
                int(finding["line_number"]),
                detector,
                str(finding["hashed_secret"]),
            )
            records.append(record)
            detector_counts[detector] += 1
    records.sort()
    return records, detector_counts, len(results)


def _inventory_digest(records: list[Record]) -> str:
    encoded = json.dumps(
        records,
        ensure_ascii=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_baseline(payload: dict[str, Any]) -> None:
    if payload.get("schema") != "axignal.reviewed-secret-baseline.v1":
        raise RuntimeError("Unsupported reviewed secret baseline schema")
    if payload.get("detector") != {"name": "detect-secrets", "version": "1.5.0"}:
        raise RuntimeError("The reviewed baseline must pin detect-secrets 1.5.0")
    if payload.get("review_state") != "VERIFIED_FALSE_POSITIVES_ONLY":
        raise RuntimeError("The secret baseline has not been fully reviewed")
    if payload.get("secret_values_stored") is not False:
        raise RuntimeError("The reviewed baseline must not store secret values")
    if payload.get("production_secret_confirmed") is not False:
        raise RuntimeError("A confirmed production secret blocks baseline acceptance")
    expected_digest = payload.get("canonical_inventory_sha256")
    if (
        not isinstance(expected_digest, str)
        or len(expected_digest) != 64
        or any(character not in "0123456789abcdef" for character in expected_digest)
    ):
        raise RuntimeError("The baseline inventory digest is invalid")


def main() -> int:
    try:
        baseline = _load_json(BASELINE_PATH)
        _validate_baseline(baseline)
        records, detector_counts, file_count = _scan()
    except RuntimeError as exc:
        print(json.dumps({"status": "ERROR", "detail": str(exc)}, sort_keys=True))
        return 2

    observed_digest = _inventory_digest(records)
    expected_detector_counts = baseline.get("detector_counts")
    status = "PASS"
    failures: list[str] = []
    if baseline.get("finding_count") != len(records):
        status = "FAIL"
        failures.append("finding_count_changed")
    if baseline.get("file_count") != file_count:
        status = "FAIL"
        failures.append("file_count_changed")
    if baseline.get("canonical_inventory_sha256") != observed_digest:
        status = "FAIL"
        failures.append("exact_inventory_changed")
    if expected_detector_counts != dict(sorted(detector_counts.items())):
        status = "FAIL"
        failures.append("detector_counts_changed")

    result = {
        "schema": "axignal.secret-baseline-verification.v1",
        "status": status,
        "finding_count": len(records),
        "file_count": file_count,
        "detector_counts": dict(sorted(detector_counts.items())),
        "observed_inventory_sha256": observed_digest,
        "failures": failures,
        "secret_values_emitted": False,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
