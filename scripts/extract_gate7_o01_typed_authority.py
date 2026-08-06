from __future__ import annotations

import argparse
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from axignal_api.o01_approval_renewal import (
    REQUIRED_AUTHORITIES,
    AuthorityEnvelope,
    TypedAuthorityDecision,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PREVIOUS_EVIDENCE_DIR = ROOT / "artifacts/o01-renewal/previous"
REQUIRED_FIELDS = {
    "authority",
    "decision",
    "scope",
    "manifest_digest",
    "head_sha",
    "timestamp",
    "expiry",
    "conditions",
    "signature",
}
JSON_FENCE = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL | re.IGNORECASE)


class AuthorityExtractionError(RuntimeError):
    """Raised when external typed authority is ambiguous or structurally unsafe."""


def parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise AuthorityExtractionError("Authority time boundary requires a timezone")
    return parsed.astimezone(UTC)


def flatten_comments(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list):
        result: list[dict[str, Any]] = []
        for item in value:
            result.extend(flatten_comments(item))
        return result
    return []


def load_comments(path: Path) -> list[dict[str, Any]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise AuthorityExtractionError(f"Comment input must be an array: {path}")
    return flatten_comments(value)


def candidate_objects(body: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for match in JSON_FENCE.finditer(body):
        try:
            value = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            result.append(value)
    return result


def discover_maximum_expiry(evidence_dir: Path) -> datetime | None:
    packages = sorted(evidence_dir.rglob("renewal-package.v0.1.json"))
    if not packages:
        return None
    if len(packages) != 1:
        raise AuthorityExtractionError(
            "Expected exactly one recovered renewal evidence package"
        )
    package = json.loads(packages[0].read_text(encoding="utf-8"))
    if package.get("terms_observations", {}).get("mode") != "ONLINE_OFFICIAL_SOURCE_CHECK":
        raise AuthorityExtractionError(
            "Recovered authority evidence was not produced from official online sources"
        )
    return parse_time(package["renewal"]["maximum_expiry"])


def extract_latest_decision(
    comments: list[dict[str, Any]],
    *,
    authority: str,
    expected_head_sha: str,
    expected_manifest_digest: str,
    maximum_expiry: datetime,
    now: datetime,
) -> tuple[TypedAuthorityDecision | None, dict[str, Any] | None]:
    matches: list[tuple[int, TypedAuthorityDecision, dict[str, Any]]] = []
    for comment in comments:
        body = str(comment.get("body") or "")
        for candidate in candidate_objects(body):
            if candidate.get("authority") != authority:
                continue
            if set(candidate) != REQUIRED_FIELDS:
                continue
            try:
                decision = TypedAuthorityDecision.model_validate(candidate)
            except ValueError:
                continue
            if (
                decision.head_sha != expected_head_sha
                or decision.manifest_digest != expected_manifest_digest
            ):
                continue
            if decision.timestamp.astimezone(UTC) > now:
                continue
            if decision.expiry.astimezone(UTC) > maximum_expiry:
                continue
            comment_id = int(comment.get("id") or 0)
            user = comment.get("user") if isinstance(comment.get("user"), dict) else {}
            comment_author = user.get("login")
            if not isinstance(comment_author, str) or not comment_author.strip():
                continue
            source = {
                "issue_comment_id": comment_id,
                "issue_comment_url": comment.get("html_url") or comment.get("url"),
                "comment_author": comment_author,
                "created_at": comment.get("created_at"),
                "updated_at": comment.get("updated_at"),
            }
            matches.append((comment_id, decision, source))

    if not matches:
        return None, None
    matches.sort(key=lambda item: item[0])
    _, decision, source = matches[-1]
    return decision, source


def extract(
    *,
    legal_comments_path: Path,
    privacy_comments_path: Path,
    expected_head_sha: str,
    expected_manifest_digest: str,
    maximum_expiry: datetime,
    now: datetime,
    output_path: Path,
) -> dict[str, Any]:
    decisions: list[TypedAuthorityDecision] = []
    sources: dict[str, Any] = {}
    inputs = {
        "LEGAL": load_comments(legal_comments_path),
        "PRIVACY_DATA_RIGHTS": load_comments(privacy_comments_path),
    }
    for authority in sorted(REQUIRED_AUTHORITIES):
        decision, source = extract_latest_decision(
            inputs[authority],
            authority=authority,
            expected_head_sha=expected_head_sha,
            expected_manifest_digest=expected_manifest_digest,
            maximum_expiry=maximum_expiry,
            now=now,
        )
        if decision is not None:
            decisions.append(decision)
            sources[authority] = source

    missing = sorted(REQUIRED_AUTHORITIES.difference(item.authority for item in decisions))
    if missing:
        if output_path.exists():
            output_path.unlink()
        return {
            "status": "MISSING" if len(missing) == 2 else "INCOMPLETE",
            "expected_head_sha": expected_head_sha,
            "expected_manifest_digest": expected_manifest_digest,
            "maximum_expiry": maximum_expiry.isoformat().replace("+00:00", "Z"),
            "authorities_found": sorted(item.authority for item in decisions),
            "authorities_missing": missing,
            "output_written": False,
            "sources": sources,
        }

    envelope = AuthorityEnvelope(
        head_sha=expected_head_sha,
        manifest_digest=expected_manifest_digest,
        decisions=tuple(decisions),
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        envelope.model_dump_json(indent=2) + "\n",
        encoding="utf-8",
    )
    return {
        "status": "COMPLETE",
        "expected_head_sha": expected_head_sha,
        "expected_manifest_digest": expected_manifest_digest,
        "maximum_expiry": maximum_expiry.isoformat().replace("+00:00", "Z"),
        "authorities_found": sorted(item.authority for item in decisions),
        "authorities_missing": [],
        "output_written": True,
        "output_path": str(output_path),
        "sources": sources,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--legal-comments", type=Path, required=True)
    parser.add_argument("--privacy-comments", type=Path, required=True)
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--expected-manifest", required=True)
    parser.add_argument("--maximum-expiry")
    parser.add_argument(
        "--previous-evidence-dir",
        type=Path,
        default=DEFAULT_PREVIOUS_EVIDENCE_DIR,
    )
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    now = datetime.now(UTC)
    try:
        maximum_expiry = (
            parse_time(args.maximum_expiry)
            if args.maximum_expiry
            else discover_maximum_expiry(args.previous_evidence_dir)
        )
        if maximum_expiry is None:
            if args.output.exists():
                args.output.unlink()
            result = {
                "status": "MISSING",
                "reason": "NO_PREVIOUS_ONLINE_EVIDENCE_PACKAGE",
                "expected_head_sha": args.expected_head,
                "expected_manifest_digest": args.expected_manifest,
                "authorities_found": [],
                "authorities_missing": sorted(REQUIRED_AUTHORITIES),
                "output_written": False,
            }
        else:
            result = extract(
                legal_comments_path=args.legal_comments,
                privacy_comments_path=args.privacy_comments,
                expected_head_sha=args.expected_head,
                expected_manifest_digest=args.expected_manifest,
                maximum_expiry=maximum_expiry,
                now=now,
                output_path=args.output,
            )
    except (OSError, TypeError, ValueError, json.JSONDecodeError, AuthorityExtractionError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
