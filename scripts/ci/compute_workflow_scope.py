#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import json
import os
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Resolve AXIGNAL incremental CI scope.")
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--group", required=True)
    parser.add_argument("--changed-files", required=True, type=Path)
    parser.add_argument("--labels-json", default="[]")
    parser.add_argument("--full-matrix", action="store_true")
    return parser.parse_args()


def matches(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)


def main() -> int:
    args = parse_args()
    manifest: dict[str, Any] = json.loads(args.manifest.read_text(encoding="utf-8"))
    groups = manifest["groups"]
    if args.group not in groups:
        raise SystemExit(f"unknown group: {args.group}")

    changed = [
        line.strip()
        for line in args.changed_files.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    labels = set(json.loads(args.labels_json or "[]"))
    policy = manifest["policy"]
    architecture_patterns = policy["architecture_paths_force_full_matrix"]
    architecture_change = any(matches(path, architecture_patterns) for path in changed)
    full_matrix = bool(
        args.full_matrix
        or policy["full_matrix_label"] in labels
        or architecture_change
    )

    selected: dict[str, bool] = {}
    reasons: dict[str, str] = {}
    for workflow_id in groups[args.group]:
        config = manifest["workflows"][workflow_id]
        mode = config["mode"]
        if full_matrix:
            run = True
            reason = "full_matrix"
        elif mode == "always":
            run = True
            reason = "always"
        elif mode == "full_only":
            run = False
            reason = "full_only"
        else:
            run = any(matches(path, config["paths"]) for path in changed)
            reason = "affected" if run else "not_affected"
        selected[workflow_id] = run
        reasons[workflow_id] = reason

    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        raise SystemExit("GITHUB_OUTPUT is required")
    with Path(output_path).open("a", encoding="utf-8") as output:
        for workflow_id, run in selected.items():
            output.write(f"run_{workflow_id}={'true' if run else 'false'}\n")
        output.write(f"selected_count={sum(selected.values())}\n")
        output.write(f"full_matrix={'true' if full_matrix else 'false'}\n")

    report = {
        "schema": "axignal.ci-scope-decision.v1",
        "group": args.group,
        "full_matrix": full_matrix,
        "architecture_change": architecture_change,
        "changed_files": changed,
        "selected": selected,
        "reasons": reasons,
    }
    Path(f"ci-scope-{args.group}.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
