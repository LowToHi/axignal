from __future__ import annotations

import argparse
import json
from pathlib import Path

from axignal_api.f01_rights_authority import (
    REQUIRED_DECISION_FIELDS,
    F01RightsAuthorityDecision,
    build_github_identity_signature,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--github-login", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    value = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit("Decision input must be a JSON object")
    unsigned_fields = REQUIRED_DECISION_FIELDS.difference({"signature"})
    if set(value) != unsigned_fields:
        raise SystemExit(
            "Unsigned decision must contain exactly the required non-signature fields"
        )
    candidate = dict(value)
    candidate["signature"] = "pending-signature-value-that-is-long-enough"
    decision = F01RightsAuthorityDecision.model_validate(candidate)
    candidate["signature"] = build_github_identity_signature(
        decision,
        github_login=args.github_login,
    )
    print(json.dumps(candidate, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
