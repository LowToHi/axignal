from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOTS = (ROOT / "apps/web", ROOT / "apps/landing")
TOKENS = (
    "draftMode(",
    "setPreviewData(",
    "clearPreviewData(",
    "__prerender_bypass",
    "__next_preview_data",
)
ALLOWED_SUFFIXES = {".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx"}


def main() -> int:
    findings: list[dict[str, object]] = []
    for source_root in SOURCE_ROOTS:
        for path in sorted(source_root.rglob("*")):
            if not path.is_file() or path.suffix not in ALLOWED_SUFFIXES:
                continue
            if any(part in {"node_modules", ".next"} for part in path.parts):
                continue
            for line_number, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(),
                1,
            ):
                for token in TOKENS:
                    if token in line:
                        findings.append(
                            {
                                "path": path.relative_to(ROOT).as_posix(),
                                "line": line_number,
                                "token": token,
                            }
                        )

    payload = {
        "schema": "axignal.inactive-next-preview-mode.v1",
        "status": "PASS" if not findings else "FAIL",
        "checked_roots": [path.relative_to(ROOT).as_posix() for path in SOURCE_ROOTS],
        "findings": findings,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if not findings else 1


if __name__ == "__main__":
    sys.exit(main())
