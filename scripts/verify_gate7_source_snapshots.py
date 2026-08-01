from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any, Iterator

ROOT = Path(__file__).resolve().parents[1]
COVERAGE_DIR = ROOT / "data" / "acceptance" / "library-coverage"


class SourceSnapshotError(RuntimeError):
    """Raised when a repository-backed Gate 7 evidence reference is invalid."""


def iter_evidence(node: Any, location: str = "$") -> Iterator[tuple[str, dict[str, Any]]]:
    if isinstance(node, dict):
        if {"kind", "reference", "sha256", "expires_at"}.issubset(node):
            yield location, node
        for key, value in node.items():
            yield from iter_evidence(value, f"{location}.{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from iter_evidence(value, f"{location}[{index}]")


def repository_path(reference: str) -> Path:
    logical = PurePosixPath(reference)
    if logical.is_absolute() or ".." in logical.parts or not logical.parts:
        raise SourceSnapshotError(f"Unsafe SOURCE_SNAPSHOT reference: {reference}")
    candidate = (ROOT / Path(*logical.parts)).resolve()
    try:
        candidate.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise SourceSnapshotError(
            f"SOURCE_SNAPSHOT escapes repository root: {reference}"
        ) from exc
    return candidate


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify() -> dict[str, Any]:
    coverage_files = sorted(COVERAGE_DIR.glob("AX-LIB-*.json"))
    checked: list[dict[str, str]] = []
    seen: dict[str, str] = {}

    for coverage_file in coverage_files:
        payload = json.loads(coverage_file.read_text(encoding="utf-8"))
        for location, evidence in iter_evidence(payload):
            if evidence["kind"] != "SOURCE_SNAPSHOT":
                continue
            reference = evidence["reference"]
            expected = evidence["sha256"]
            target = repository_path(reference)
            if not target.is_file() or target.is_symlink():
                raise SourceSnapshotError(
                    f"{coverage_file.relative_to(ROOT)}:{location}: "
                    f"SOURCE_SNAPSHOT is missing, not a regular file, or a symlink: {reference}"
                )
            actual = sha256_file(target)
            if actual != expected:
                raise SourceSnapshotError(
                    f"{coverage_file.relative_to(ROOT)}:{location}: "
                    f"SHA-256 mismatch for {reference}: expected {expected}, got {actual}"
                )
            previous = seen.get(reference)
            if previous is not None and previous != expected:
                raise SourceSnapshotError(
                    f"Conflicting SHA-256 values for SOURCE_SNAPSHOT {reference}"
                )
            seen[reference] = expected
            checked.append(
                {
                    "coverage_file": str(coverage_file.relative_to(ROOT)),
                    "location": location,
                    "reference": reference,
                    "sha256": actual,
                }
            )

    return {
        "status": "PASS",
        "coverage_files": len(coverage_files),
        "source_snapshots_checked": len(checked),
        "snapshots": checked,
    }


def main() -> int:
    try:
        result = verify()
    except (OSError, ValueError, json.JSONDecodeError, SourceSnapshotError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
