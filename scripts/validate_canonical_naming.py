#!/usr/bin/env python3
"""Fail when active repository artifacts contain superseded AXIGNAL naming."""

from __future__ import annotations

import argparse
import pathlib
import sys
from collections.abc import Iterable

# Construct superseded forms without embedding them literally in this validator.
FORBIDDEN = (
    "A" + "SIGNAL",
    "a" + "signal.com",
    "A" + "SIGNAL-GOAL-001",
    "A" + "signal",
)
TEXT_SUFFIXES = {
    ".md",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".html",
    ".css",
    ".sql",
    ".sh",
}
EXCLUDED_PARTS = {".git", "node_modules", ".next", "dist", "build", "coverage"}

# These files document the naming correction itself. They are manually reviewed.
REFERENCE_FILES = {
    "AGENTS.md",
    "docs/adr/ADR-001-brand-domain-repository.md",
    "docs/contracts/README.md",
    "docs/contracts/18-development-agent-governance.md",
    "docs/roadmap/README.md",
    "docs/roadmap/00-goal-lock.md",
    "docs/roadmap/01-phase-map.md",
    "docs/roadmap/05-dependency-and-gates.md",
    "scripts/validate_canonical_naming.py",
    "scripts/migrate_canonical_naming.py",
}


def iter_text_files(root: pathlib.Path) -> Iterable[pathlib.Path]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in EXCLUDED_PARTS for part in path.parts):
            continue
        relative = path.relative_to(root).as_posix()
        if relative in REFERENCE_FILES or relative.startswith("docs/archive/"):
            continue
        if path.suffix.lower() in TEXT_SUFFIXES or path.name in {"Dockerfile", "Makefile"}:
            yield path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args()
    root = pathlib.Path(args.root).resolve()

    defects: list[str] = []
    for path in iter_text_files(root):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for line_number, line in enumerate(text.splitlines(), start=1):
            for forbidden in FORBIDDEN:
                if forbidden in line:
                    relative = path.relative_to(root)
                    defects.append(f"{relative}:{line_number}: superseded naming detected")

    if defects:
        print("Canonical naming validation FAILED:")
        for defect in defects:
            print(f"- {defect}")
        print("\nRequired active identity: AXIGNAL / axignal.com / AXIGNAL-GOAL-001")
        return 1

    print("Canonical naming validation PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
