#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

REPORT = Path(sys.argv[1] if len(sys.argv) > 1 else "critical-repository-coverage.json")
THRESHOLDS = {
    "apps/api/src/axignal_api/admission_repository.py": 85.0,
    "apps/api/src/axignal_api/billing_repository.py": 85.0,
    "apps/api/src/axignal_api/entitlement_repository.py": 80.0,
    "apps/api/src/axignal_api/identity_repository.py": 80.0,
    "apps/api/src/axignal_api/organic_repository.py": 80.0,
    "apps/api/src/axignal_api/proposal_repository.py": 65.0,
    "apps/api/src/axignal_api/retention_repository.py": 85.0,
    "apps/api/src/axignal_api/seat_repository.py": 80.0,
    "apps/api/src/axignal_api/ted_repository.py": 60.0,
}


def main() -> None:
    payload = json.loads(REPORT.read_text(encoding="utf-8"))
    files = payload.get("files")
    if not isinstance(files, dict):
        raise SystemExit("Coverage report does not contain a files object")

    failures: list[str] = []
    actual: dict[str, float] = {}
    for path, threshold in THRESHOLDS.items():
        entry = files.get(path)
        if not isinstance(entry, dict):
            failures.append(f"{path}: missing from coverage report")
            continue
        summary = entry.get("summary")
        if not isinstance(summary, dict):
            failures.append(f"{path}: missing coverage summary")
            continue
        percent = round(float(summary.get("percent_covered", 0.0)), 2)
        actual[path] = percent
        if percent + 1e-9 < threshold:
            failures.append(
                f"{path}: {percent:.2f}% is below required {threshold:.2f}%"
            )

    print(
        json.dumps(
            {
                "schema": "axignal.critical-repository-coverage.v0.1",
                "thresholds": THRESHOLDS,
                "actual": actual,
                "status": "FAIL" if failures else "PASS",
            },
            sort_keys=True,
        )
    )
    if failures:
        raise SystemExit("\n".join(failures))


if __name__ == "__main__":
    main()
