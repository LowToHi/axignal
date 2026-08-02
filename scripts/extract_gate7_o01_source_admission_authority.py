#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
API_SRC = ROOT / "apps" / "api" / "src"
sys.path.insert(0, str(API_SRC))

from axignal_api.o01_source_admission_authority import (  # noqa: E402
    REQUIRED_AUTHORITIES,
    REQUIRED_DECISION_FIELDS,
    SourceAdmissionDecision,
    VerifiedDecision,
    evaluate_source_admission_authority,
    result_payload,
    verify_human_signature,
)

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--closure", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--repository", default=os.getenv("GITHUB_REPOSITORY"))
    parser.add_argument("--token", default=os.getenv("GITHUB_TOKEN"))
    parser.add_argument("--now")
    parser.add_argument("--require-admitted", action="store_true")
    return parser.parse_args()


def _manifest_reference(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _api_json(url: str, *, token: str) -> Any:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "axignal-o01-source-admission",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def _extract_payloads(body: str) -> list[dict[str, Any]]:
    candidates = [body.strip()]
    candidates.extend(match.group(1) for match in _JSON_FENCE_RE.finditer(body))
    payloads: list[dict[str, Any]] = []
    for candidate in candidates:
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict) and set(payload) == REQUIRED_DECISION_FIELDS:
            payloads.append(payload)
    return payloads


def _evidence_status(
    closure: dict[str, Any],
    manifest: dict[str, Any],
) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    expected = manifest["evidence"]
    if closure.get("status") != "PASS":
        reasons.append("O01-C closure status is not PASS")
    if closure.get("output") != "O01_QUALITY_COVERAGE_LAG_PASS":
        reasons.append("O01-C closure output mismatch")
    evidence = closure.get("evidence", {})
    execution = closure.get("execution", {})
    thresholds = closure.get("thresholds", {})
    controls = closure.get("controls", {})
    boundary = closure.get("authority_boundary", {})
    checks = {
        "artifact_id": evidence.get("artifact_id") == expected["artifact_id"],
        "artifact_sha256": (
            evidence.get("artifact_sha256") == expected["artifact_sha256"]
        ),
        "execution_commit_sha": (
            evidence.get("execution_commit_sha") == expected["execution_commit_sha"]
        ),
        "sample_count": (
            execution.get("sample_count", 0) >= expected["minimum_sample_count"]
        ),
        "countries_observed": (
            execution.get("countries_observed", 0)
            >= expected["minimum_countries_observed"]
        ),
        "languages": (
            sorted(execution.get("languages_verified", []))
            == sorted(expected["required_languages"])
        ),
        "thresholds": thresholds.get("all_pass") is True,
        "human_authority": controls.get("human_authority_current") is True,
        "kill_switch": controls.get("kill_switch_tested") is True,
        "rollback": controls.get("rollback_tested") is True,
        "sealed_raw": controls.get("raw_responses_retained_securely") is True,
        "plaintext_removed": controls.get("plaintext_removed") is True,
        "plaintext_uploaded": controls.get("plaintext_uploaded") is False,
        "contact_values": controls.get("contact_values_persisted") is False,
        "source_candidate": boundary.get("source_state") == "CANDIDATE",
        "product_not_pre_admitted": boundary.get("product_admitted") is False,
        "public_launch_no_go": boundary.get("public_launch") == "NO_GO",
    }
    reasons.extend(name for name, passed in checks.items() if not passed)
    return not reasons, tuple(reasons)


def main() -> int:
    args = parse_args()
    if not args.repository or not args.token:
        raise SystemExit("GITHUB_REPOSITORY and GITHUB_TOKEN are required")

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    closure = json.loads(args.closure.read_text(encoding="utf-8"))
    manifest_reference = _manifest_reference(args.manifest)

    decisions: dict[str, VerifiedDecision] = {}
    for authority in sorted(REQUIRED_AUTHORITIES):
        issue_number = manifest["authorities"][authority]["issue_number"]
        url = (
            f"https://api.github.com/repos/{args.repository}/issues/"
            f"{issue_number}/comments?per_page=100"
        )
        try:
            comments = _api_json(url, token=args.token)
        except urllib.error.HTTPError as exc:
            raise SystemExit(
                f"Unable to read issue {issue_number}: HTTP {exc.code}"
            ) from exc
        for comment in comments:
            author = comment.get("user") or {}
            for payload in _extract_payloads(comment.get("body") or ""):
                try:
                    decision = SourceAdmissionDecision.model_validate(payload)
                except ValueError:
                    continue
                if decision.authority != authority:
                    continue
                if not verify_human_signature(
                    decision,
                    comment_author=author.get("login") or "",
                    comment_user_type=author.get("type") or "",
                ):
                    continue
                candidate = VerifiedDecision(
                    decision=decision,
                    issue_number=issue_number,
                    comment_id=int(comment["id"]),
                    comment_url=comment.get("html_url"),
                    comment_author=author["login"],
                    comment_user_type=author["type"],
                    comment_created_at=comment.get("created_at"),
                    comment_updated_at=comment.get("updated_at"),
                )
                previous = decisions.get(authority)
                if previous is None or (
                    candidate.comment_created_at or ""
                ) >= (previous.comment_created_at or ""):
                    decisions[authority] = candidate

    evidence_ready, evidence_reasons = _evidence_status(closure, manifest)
    now = (
        datetime.fromisoformat(args.now.replace("Z", "+00:00"))
        if args.now
        else datetime.now(UTC)
    )
    evaluation = evaluate_source_admission_authority(
        decisions,
        expected_head_sha=manifest["target_head_sha"],
        expected_manifest_reference=manifest_reference,
        expected_issues={
            authority: spec["issue_number"]
            for authority, spec in manifest["authorities"].items()
        },
        expected_scopes={
            authority: spec["scope"]
            for authority, spec in manifest["authorities"].items()
        },
        evidence_expires_at=manifest["evidence_expires_at"],
        decision_max_expires_at=manifest["decision_max_expires_at"],
        evidence_ready=evidence_ready,
        evidence_reasons=evidence_reasons,
        now=now,
    )
    payload = result_payload(
        evaluation,
        manifest_reference=manifest_reference,
        target_head_sha=manifest["target_head_sha"],
        evidence_expires_at=manifest["evidence_expires_at"],
        decision_sources=decisions,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    if args.require_admitted and not evaluation.admitted:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
