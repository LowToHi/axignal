#!/usr/bin/env python3
"""Normalize retention-days for actions/upload-artifact steps.

Dry-run is the default. Pass --apply to write files. The transformer only edits
recognizable upload-artifact steps with a with: mapping. Dynamic retention values
are reported and left untouched. No workflow triggers, jobs or commands change.
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

STEP_RE = re.compile(r"^(\s*)-\s+(?:name|uses):")
WITH_RE = re.compile(r"^(\s*)with:\s*$", re.I)
KEY_RE = re.compile(r"^(\s*)([A-Za-z0-9_-]+):\s*(.*?)\s*$")


def load_policy(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != "axignal.actions-storage-policy.v1":
        raise SystemExit(f"unexpected policy schema: {payload.get('schema')}")
    return payload


def scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def classify(name: str, policy: dict[str, Any]) -> str:
    lowered = name.lower()
    rules = policy["classification"]
    if any(fragment in lowered for fragment in rules["contractual_name_fragments"]):
        return "contractual"
    if any(fragment in lowered for fragment in rules["diagnostic_name_fragments"]):
        return "diagnostic"
    return "ephemeral"


def find_step_start(lines: list[str], index: int) -> tuple[int, int]:
    cursor = index
    while cursor >= 0:
        match = STEP_RE.match(lines[cursor])
        if match:
            return cursor, len(match.group(1))
        cursor -= 1
    raise ValueError(f"cannot find step start for line {index + 1}")


def find_step_end(lines: list[str], start: int, step_indent: int) -> int:
    cursor = start + 1
    while cursor < len(lines):
        match = STEP_RE.match(lines[cursor])
        if match and len(match.group(1)) <= step_indent:
            break
        cursor += 1
    return cursor


@dataclass
class Change:
    workflow: str
    line: int
    artifact_name: str
    classification: str
    previous: str | None
    replacement: int | None
    action: str


def transform(path: Path, policy: dict[str, Any], root: Path) -> tuple[str, list[Change]]:
    original = path.read_text(encoding="utf-8")
    had_final_newline = original.endswith("\n")
    lines = original.splitlines()
    changes: list[Change] = []
    upload_indexes = [index for index, line in enumerate(lines) if "actions/upload-artifact@" in line]

    for upload_index in reversed(upload_indexes):
        try:
            step_start, step_indent = find_step_start(lines, upload_index)
        except ValueError:
            changes.append(Change(str(path.relative_to(root)), upload_index + 1, "<unknown>", "ephemeral", None, None, "unrecognized-step"))
            continue
        step_end = find_step_end(lines, step_start, step_indent)

        with_index: int | None = None
        with_indent: int | None = None
        for cursor in range(upload_index + 1, step_end):
            match = WITH_RE.match(lines[cursor])
            if match:
                with_index = cursor
                with_indent = len(match.group(1))
                break
        if with_index is None or with_indent is None:
            changes.append(Change(str(path.relative_to(root)), upload_index + 1, "<missing-with>", "ephemeral", None, None, "missing-with-block"))
            continue

        mapping_indent: int | None = None
        mapping_end = with_index + 1
        fields: dict[str, tuple[int, str, int]] = {}
        while mapping_end < step_end:
            line = lines[mapping_end]
            if not line.strip() or line.lstrip().startswith("#"):
                mapping_end += 1
                continue
            key_match = KEY_RE.match(line)
            indent = len(line) - len(line.lstrip())
            if indent <= with_indent:
                break
            if key_match:
                key_indent = len(key_match.group(1))
                if mapping_indent is None:
                    mapping_indent = key_indent
                if key_indent == mapping_indent:
                    fields[key_match.group(2).lower()] = (mapping_end, scalar(key_match.group(3)), key_indent)
            mapping_end += 1

        if mapping_indent is None:
            mapping_indent = with_indent + 2

        artifact_name = fields.get("name", (-1, "<dynamic-or-missing>", mapping_indent))[1]
        artifact_class = classify(artifact_name, policy)
        desired = int(policy["retention_days"][artifact_class])
        retention = fields.get("retention-days")

        if retention is None:
            lines.insert(mapping_end, " " * mapping_indent + f"retention-days: {desired}")
            changes.append(Change(str(path.relative_to(root)), upload_index + 1, artifact_name, artifact_class, None, desired, "insert"))
            continue

        retention_index, raw_value, retention_indent = retention
        if "${{" in raw_value:
            changes.append(Change(str(path.relative_to(root)), upload_index + 1, artifact_name, artifact_class, raw_value, None, "dynamic-rejected"))
            continue
        try:
            current = int(raw_value)
        except ValueError:
            changes.append(Change(str(path.relative_to(root)), upload_index + 1, artifact_name, artifact_class, raw_value, None, "invalid-rejected"))
            continue
        if current > desired or current < 1:
            lines[retention_index] = " " * retention_indent + f"retention-days: {desired}"
            changes.append(Change(str(path.relative_to(root)), upload_index + 1, artifact_name, artifact_class, str(current), desired, "replace"))
        else:
            changes.append(Change(str(path.relative_to(root)), upload_index + 1, artifact_name, artifact_class, str(current), current, "keep"))

    transformed = "\n".join(lines) + ("\n" if had_final_newline else "")
    return transformed, list(reversed(changes))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--policy", default="config/actions-storage-policy.json")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--report", default="reports/actions-retention-migration.json")
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    policy = load_policy(root / args.policy)
    all_changes: list[Change] = []
    changed_files: list[str] = []
    rejected: list[Change] = []

    for path in sorted((root / ".github" / "workflows").glob("*.y*ml")):
        before = path.read_text(encoding="utf-8")
        after, changes = transform(path, policy, root)
        all_changes.extend(changes)
        rejected.extend(
            change
            for change in changes
            if change.action.endswith("rejected")
            or change.action.startswith("missing-")
            or change.action == "unrecognized-step"
        )
        if before == after:
            continue
        changed_files.append(str(path.relative_to(root)))
        if args.apply:
            path.write_text(after, encoding="utf-8")
        else:
            diff = difflib.unified_diff(
                before.splitlines(),
                after.splitlines(),
                fromfile=str(path.relative_to(root)),
                tofile=str(path.relative_to(root)),
                lineterm="",
            )
            print("\n".join(diff))

    report = {
        "schema": "axignal.actions-retention-migration.v1",
        "apply": args.apply,
        "changed_file_count": len(changed_files),
        "changed_files": changed_files,
        "step_count": len(all_changes),
        "insert_count": sum(change.action == "insert" for change in all_changes),
        "replace_count": sum(change.action == "replace" for change in all_changes),
        "keep_count": sum(change.action == "keep" for change in all_changes),
        "rejected_count": len(rejected),
        "rejected": [asdict(change) for change in rejected],
        "changes": [asdict(change) for change in all_changes],
    }
    report_path = root / args.report
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))

    if rejected:
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
