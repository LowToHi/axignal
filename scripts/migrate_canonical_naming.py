#!/usr/bin/env python3
"""Migrate active text artifacts to the canonical AXIGNAL identity."""

from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {
    ".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".py", ".ts",
    ".tsx", ".js", ".jsx", ".html", ".css", ".sql", ".sh"
}
EXCLUDED_PARTS = {".git", "node_modules", ".next", "dist", "build", "coverage"}
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
REPLACEMENTS = (
    ("A" + "SIGNAL-GOAL-001", "AXIGNAL-GOAL-001"),
    ("A" + "SIGNAL", "AXIGNAL"),
    ("A" + "signal", "Axignal"),
    ("a" + "signal.com", "axignal.com"),
)


def main() -> None:
    changed: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in EXCLUDED_PARTS for part in path.parts):
            continue
        relative = path.relative_to(ROOT).as_posix()
        if relative in REFERENCE_FILES or relative.startswith("docs/archive/"):
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in {"Dockerfile", "Makefile"}:
            continue
        try:
            original = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        updated = original
        for old, new in REPLACEMENTS:
            updated = updated.replace(old, new)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            changed.append(relative)

    print(f"Migrated {len(changed)} active files")
    for relative in changed:
        print(relative)


if __name__ == "__main__":
    main()
