from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from axignal_api.o01_campaign_authority import (
    REQUIRED_AUTHORITIES,
    REQUIRED_DECISION_FIELDS,
    CampaignAuthorityDecision,
    VerifiedDecision,
    evaluate_campaign_authority,
    parse_utc,
    result_payload,
    verify_human_signature,
)

JSON_FENCE = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL | re.IGNORECASE)


class AuthorityExtractionError(RuntimeError):
    """Raised when typed human authority cannot be evaluated safely."""


def sha256_file(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_comments(path: Path) -> list[dict[str, Any]]:
    value = load_json(path)
    if not isinstance(value, list):
        raise AuthorityExtractionError(f"Comment input must be an array: {path}")
    return [item for item in value if isinstance(item, dict)]


def candidate_objects(body: str) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for match in JSON_FENCE.finditer(body):
        try:
            value = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            candidates.append(value)
    return candidates


def extract_latest_verified(
    comments: list[dict[str, Any]],
    *,
    authority: str,
    expected_head_sha: str,
    expected_manifest_reference: str,
) -> VerifiedDecision | None:
    matches: list[VerifiedDecision] = []
    for comment in comments:
        user = comment.get("user")
        if not isinstance(user, dict):
            continue
        author = user.get("login")
        user_type = user.get("type")
        if not isinstance(author, str) or not isinstance(user_type, str):
            continue
        for candidate in candidate_objects(str(comment.get("body") or "")):
            if candidate.get("authority") != authority:
                continue
            if set(candidate) != REQUIRED_DECISION_FIELDS:
                continue
            try:
                decision = CampaignAuthorityDecision.model_validate(candidate)
            except ValueError:
                continue
            if decision.head_sha != expected_head_sha:
                continue
            if decision.manifest_reference != expected_manifest_reference:
                continue
            if not verify_human_signature(
                decision,
                comment_author=author,
                comment_user_type=user_type,
            ):
                continue
            matches.append(
                VerifiedDecision(
                    decision=decision,
                    comment_id=int(comment.get("id") or 0),
                    comment_url=comment.get("html_url") or comment.get("url"),
                    comment_author=author,
                    comment_created_at=comment.get("created_at"),
                    comment_updated_at=comment.get("updated_at"),
                )
            )
    if not matches:
        return None
    return max(matches, key=lambda item: item.comment_id)


def materialize(
    *,
    manifest_path: Path,
    legal_comments_path: Path,
    privacy_comments_path: Path,
    output_dir: Path,
    now: datetime,
) -> dict[str, Any]:
    manifest = load_json(manifest_path)
    if not isinstance(manifest, dict):
        raise AuthorityExtractionError("Authority manifest must be a JSON object")
    manifest_reference = sha256_file(manifest_path)
    target = manifest["target"]
    evidence = manifest["official_evidence"]
    contract = manifest["decision_contract"]
    expected_head = str(target["head_sha"])

    comment_inputs = {
        "LEGAL": load_comments(legal_comments_path),
        "PRIVACY_DATA_RIGHTS": load_comments(privacy_comments_path),
    }
    verified: dict[str, VerifiedDecision] = {}
    for authority in sorted(REQUIRED_AUTHORITIES):
        decision = extract_latest_verified(
            comment_inputs[authority],
            authority=authority,
            expected_head_sha=expected_head,
            expected_manifest_reference=manifest_reference,
        )
        if decision is not None:
            verified[authority] = decision

    evaluation = evaluate_campaign_authority(
        verified,
        expected_head_sha=expected_head,
        expected_manifest_reference=manifest_reference,
        evidence_expires_at=parse_utc(evidence["evidence_expires_at"]),
        decision_max_expires_at=parse_utc(contract["decision_max_expires_at"]),
        now=now,
    )
    result = result_payload(
        evaluation,
        manifest_reference=manifest_reference,
        target_head_sha=expected_head,
        evidence_expires_at=parse_utc(evidence["evidence_expires_at"]),
        decision_sources=verified,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    result_path = output_dir / "result.v0.1.json"
    result_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    envelope_path = output_dir / "campaign-authority-envelope.v0.1.json"
    if evaluation.execution_authorised:
        envelope = {
            "schema_version": "axignal.o01-campaign-authority-envelope/v0.1",
            "manifest_reference": manifest_reference,
            "head_sha": expected_head,
            "effective_expiry": result["effective_expiry"],
            "decisions": {
                authority: {
                    "decision": source.decision.model_dump(mode="json"),
                    "source": result["decision_sources"][authority],
                }
                for authority, source in sorted(verified.items())
            },
            "authority_boundary": result["authority_boundary"],
            "output": "O01_CAMPAIGN_AUTHORISED",
        }
        envelope_path.write_text(
            json.dumps(envelope, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    elif envelope_path.exists():
        envelope_path.unlink()
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--legal-comments", type=Path, required=True)
    parser.add_argument("--privacy-comments", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--require-authorised", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        result = materialize(
            manifest_path=args.manifest,
            legal_comments_path=args.legal_comments,
            privacy_comments_path=args.privacy_comments,
            output_dir=args.output_dir,
            now=datetime.now(UTC),
        )
    except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    if args.require_authorised and not result["execution_authorised"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
