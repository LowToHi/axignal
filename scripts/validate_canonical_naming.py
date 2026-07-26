#!/usr/bin/env python3
"""Fail when active repository artifacts contain superseded AXIGNAL naming."""

from __future__ import annotations

import argparse
import pathlib
import sys
from collections.abc import Iterable

FORBIDDEN = ("ASIGNAL", "asignal.com", "ASIGNAL-GOAL-001")
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


def iter_text_files(root: pathlib.Path) -> Iterable[pathlib.Path]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in EXCLUDED_PARTS for part in path.parts):
            continue
        if "docs/archive" in path.as_posix():
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
                    defects.append(f"{path.relative_to(root)}:{line_number}: forbidden {forbidden!r}")

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
