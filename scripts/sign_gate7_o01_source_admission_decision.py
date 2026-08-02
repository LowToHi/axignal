#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_SRC = ROOT / "apps" / "api" / "src"
sys.path.insert(0, str(API_SRC))

from axignal_api.o01_source_admission_authority import (  # noqa: E402
    SourceAdmissionDecision,
    build_github_identity_signature,
)

UNSIGNED_SIGNATURE = "pending-signature-" + "0" * 64


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--decision", required=True, type=Path)
    parser.add_argument("--github-login", required=True)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = json.loads(args.decision.read_text(encoding="utf-8"))
    payload["signature"] = UNSIGNED_SIGNATURE
    unsigned = SourceAdmissionDecision.model_validate(payload)
    payload["signature"] = build_github_identity_signature(
        unsigned,
        github_login=args.github_login,
    )
    signed = SourceAdmissionDecision.model_validate(payload)
    rendered = (
        json.dumps(
            signed.model_dump(mode="json"),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
