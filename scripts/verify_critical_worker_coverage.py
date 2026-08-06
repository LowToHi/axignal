#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

REPORT = Path(sys.argv[1] if len(sys.argv) > 1 else "critical-worker-coverage.json")
THRESHOLDS = {
    "apps/api/src/axignal_api/runtime_invariants.py": 100.0,
    "apps/api/src/axignal_api/retention_worker.py": 85.0,
    "apps/api/src/axignal_api/proposal_publisher.py": 75.0,
    "apps/api/src/axignal_api/scheduler_service.py": 70.0,
    "apps/api/src/axignal_api/admission_runtime.py": 80.0,
    "apps/api/src/axignal_api/proposal_worker.py": 75.0,
    "apps/api/src/axignal_api/worker.py": 70.0,
}


def main() -> None:
    payload = json.loads(REPORT.read_text(encoding="utf-8"))
    files = payload.get("files")
    if not isinstance(files, dict):
        raise SystemExit("Coverage report does not contain a files object")

    failures: list[str] = []
    evidence: dict[str, float] = {}
    for path, threshold in THRESHOLDS.items():
        item = files.get(path)
        if not isinstance(item, dict):
            failures.append(f"{path}: missing from coverage report")
            continue
        summary = item.get("summary")
        if not isinstance(summary, dict):
            failures.append(f"{path}: missing coverage summary")
            continue
        percent = float(summary.get("percent_covered", 0.0))
        evidence[path] = round(percent, 2)
        if percent + 1e-9 < threshold:
            failures.append(
                f"{path}: {percent:.2f}% is below required {threshold:.2f}%"
            )

    print(
        json.dumps(
            {
                "schema": "axignal.critical-worker-coverage.v0.1",
                "thresholds": THRESHOLDS,
                "actual": evidence,
                "status": "FAIL" if failures else "PASS",
            },
            sort_keys=True,
        )
    )
    if failures:
        raise SystemExit("\n".join(failures))


if __name__ == "__main__":
    main()
