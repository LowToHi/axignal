from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import unicodedata
import urllib.error
import urllib.request
from datetime import UTC, datetime, timedelta
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from axignal_api.o01_approval_renewal import (
    AuthorityEnvelope,
    ChangeClass,
    RenewalPhase,
    classify_delta,
    evaluate_authority,
)
from materialize_gate7_o01_approval_manifest import materialize

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / (
    "data/acceptance/approvals/AX-LIB-O01-approval-renewal-policy.v0.1.json"
)
DEFAULT_FIXTURE_PATH = ROOT / (
    "data/acceptance/fixtures/o01-renewal/terms-observations.v0.1.json"
)
CURRENT_MANIFEST_PATH = ROOT / "artifacts/o01-legal-privacy/approval-manifest.v0.2.json"
OUTPUT_DIR = ROOT / "artifacts/o01-renewal"
PACKAGE_NAME = "renewal-package.v0.1.json"
MAX_RESPONSE_BYTES = 5 * 1024 * 1024
USER_AGENT = "AXIGNAL-O01-Authority-Renewal/0.1"
TECHNICAL_PATH_PREFIXES = (
    "apps/api/src/",
    "apps/worker/src/",
    "deploy/",
    "docker/",
)


class RenewalPreparationError(RuntimeError):
    """Raised when a renewal package cannot be prepared safely."""


class VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._ignored_depth = 0
        self.parts: list[str] = []

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        del attrs
        if tag.casefold() in {"script", "style", "noscript", "svg"}:
            self._ignored_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.casefold() in {"script", "style", "noscript", "svg"}:
            self._ignored_depth = max(0, self._ignored_depth - 1)

    def handle_data(self, data: str) -> None:
        if self._ignored_depth == 0 and data.strip():
            self.parts.append(data)


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RenewalPreparationError(f"Missing JSON input: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RenewalPreparationError(f"Invalid JSON input: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise RenewalPreparationError(f"JSON input must be an object: {path}")
    return value


def canonical_bytes(value: dict[str, Any]) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return f"sha256:{hashlib.sha256(value).hexdigest()}"


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise RenewalPreparationError(f"Timestamp requires a timezone: {value}")
    return parsed.astimezone(UTC)


def iso_z(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def normalise_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold()
    value = re.sub(r"[^\w]+", " ", value, flags=re.UNICODE)
    return " ".join(value.split())


def extract_visible_text(body: bytes, content_type: str) -> str:
    encoding = "utf-8"
    match = re.search(r"charset=([^;\s]+)", content_type, flags=re.IGNORECASE)
    if match:
        encoding = match.group(1).strip('"\'')
    decoded = body.decode(encoding, errors="replace")
    parser = VisibleTextParser()
    parser.feed(decoded)
    return normalise_text(" ".join(parser.parts))


def fetch_document(
    document: dict[str, Any],
    *,
    allowed_hosts: frozenset[str],
    observed_at: datetime,
) -> dict[str, Any]:
    url = str(document["url"])
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in allowed_hosts:
        return {
            "status": "UNAVAILABLE",
            "url": url,
            "error": "Document URL is outside the official HTTPS allowlist",
        }

    request = urllib.request.Request(
        url,
        headers={
            "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.1",
            "User-Agent": USER_AGENT,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
            final_url = response.geturl()
            final = urlparse(final_url)
            if final.scheme != "https" or final.hostname not in allowed_hosts:
                raise RenewalPreparationError("Official document redirected outside allowlist")
            body = response.read(MAX_RESPONSE_BYTES + 1)
            if len(body) > MAX_RESPONSE_BYTES:
                raise RenewalPreparationError("Official document exceeded response limit")
            content_type = response.headers.get("Content-Type", "text/html")
            visible = extract_visible_text(body, content_type)
            expected = [normalise_text(item) for item in document["critical_anchors"]]
            missing = [anchor for anchor in expected if anchor not in visible]
            return {
                "status": "PASS" if not missing else "ANCHOR_MISMATCH",
                "url": url,
                "final_url": final_url,
                "http_status": int(response.status),
                "content_type": content_type,
                "etag": response.headers.get("ETag"),
                "last_modified": response.headers.get("Last-Modified"),
                "observed_at": iso_z(observed_at),
                "content_sha256": sha256_bytes(visible.encode("utf-8")),
                "normalised_text_bytes": len(visible.encode("utf-8")),
                "critical_anchors_expected": len(expected),
                "critical_anchors_present": len(expected) - len(missing),
                "missing_anchors": missing,
            }
    except (
        OSError,
        TimeoutError,
        urllib.error.HTTPError,
        urllib.error.URLError,
        RenewalPreparationError,
    ) as exc:
        return {
            "status": "UNAVAILABLE",
            "url": url,
            "observed_at": iso_z(observed_at),
            "error_type": type(exc).__name__,
            "error": str(exc)[:500],
        }


def observe_terms(
    policy: dict[str, Any],
    *,
    online: bool,
    fixture_path: Path,
    now: datetime,
) -> dict[str, Any]:
    expected_ids = {item["document_id"] for item in policy["official_documents"]}
    if not online:
        fixture = load_json(fixture_path)
        documents = fixture.get("documents")
        if not isinstance(documents, dict) or set(documents) != expected_ids:
            raise RenewalPreparationError("Terms fixture document set does not match policy")
        return {
            "schema_version": "axignal.o01-terms-observations/v0.1",
            "mode": "OFFLINE_TEST_FIXTURE",
            "observed_at": fixture["observed_at"],
            "expires_at": fixture["expires_at"],
            "documents": documents,
        }

    allowed_hosts = frozenset(policy["official_source_hosts"])
    documents = {
        item["document_id"]: fetch_document(
            item,
            allowed_hosts=allowed_hosts,
            observed_at=now,
        )
        for item in policy["official_documents"]
    }
    return {
        "schema_version": "axignal.o01-terms-observations/v0.1",
        "mode": "ONLINE_OFFICIAL_SOURCE_CHECK",
        "observed_at": iso_z(now),
        "expires_at": iso_z(now + timedelta(days=30)),
        "documents": documents,
    }


def git_value(*arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RenewalPreparationError(f"Git command failed: {detail}")
    return result.stdout.strip()


def technical_paths_changed(previous_head: str | None) -> tuple[str, ...]:
    if not previous_head:
        return ()
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{previous_head}..HEAD"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return ("UNRESOLVED_GIT_DIFF",)
    return tuple(
        sorted(
            path
            for path in result.stdout.splitlines()
            if path.startswith(TECHNICAL_PATH_PREFIXES)
        )
    )


def load_previous_package(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.is_file():
        return None
    return load_json(path)


def load_authority_envelope(path: Path | None) -> AuthorityEnvelope | None:
    if path is None or not path.is_file():
        return None
    return AuthorityEnvelope.model_validate(load_json(path))


def decision_template(
    authority: str,
    *,
    head_sha: str,
    manifest_digest: str,
    maximum_expiry: str,
    change_class: str,
) -> dict[str, Any]:
    return {
        "authority": authority,
        "decision": None,
        "scope": (
            "AX-LIB-O01 bounded private evidence campaign renewal; "
            f"change class reviewed: {change_class}"
        ),
        "manifest_digest": manifest_digest,
        "head_sha": head_sha,
        "timestamp": None,
        "expiry": None,
        "conditions": [f"Expiry must not exceed {maximum_expiry}"],
        "signature": None,
    }


def materialise_renewal(
    *,
    online: bool,
    fixture_path: Path,
    previous_package_path: Path | None,
    current_decisions_path: Path | None,
    output_dir: Path,
    now: datetime,
) -> dict[str, Any]:
    policy = load_json(POLICY_PATH)
    manifest_result = materialize()
    current_manifest = load_json(CURRENT_MANIFEST_PATH)
    current_manifest_digest = sha256_file(CURRENT_MANIFEST_PATH)
    head_sha = git_value("rev-parse", "HEAD")
    git_tree = git_value("rev-parse", "HEAD^{tree}")
    if current_manifest["head_sha"] != head_sha:
        raise RenewalPreparationError("Current approval manifest is not exact-head")
    if manifest_result["manifest_digest"] != current_manifest_digest:
        raise RenewalPreparationError("Current approval manifest digest mismatch")

    observations = observe_terms(
        policy,
        online=online,
        fixture_path=fixture_path,
        now=now,
    )
    previous = load_previous_package(previous_package_path)
    previous_files = previous.get("relevant_files") if previous else None
    previous_terms = (
        previous.get("terms_observations", {}).get("documents") if previous else None
    )
    previous_head = str(previous["head_sha"]) if previous else None
    delta = classify_delta(
        current_relevant_files=current_manifest["files"],
        previous_relevant_files=previous_files,
        current_terms=observations["documents"],
        previous_terms=previous_terms,
        technical_paths_changed=technical_paths_changed(previous_head),
    )

    envelope = load_authority_envelope(current_decisions_path)
    schedule = policy["schedule"]
    authority = evaluate_authority(
        envelope,
        expected_head_sha=head_sha,
        expected_manifest_digest=current_manifest_digest,
        now=now,
        renewal_window_days=int(schedule["renewal_window_days"]),
        urgent_window_days=int(schedule["urgent_window_days"]),
    )

    terms_expiry = parse_time(observations["expires_at"])
    artifact_safe_expiry = now + timedelta(days=27)
    maximum_expiry = min(terms_expiry, artifact_safe_expiry)
    review_path = policy["change_classes"][delta.change_class.value]["review_path"]
    package_status = (
        "BLOCKED_EVIDENCE_UNAVAILABLE"
        if delta.change_class is ChangeClass.EVIDENCE_UNAVAILABLE
        else "READY_FOR_TYPED_DECISIONS"
    )
    material_delta = delta.change_class not in {
        ChangeClass.NO_MATERIAL_CHANGE,
        ChangeClass.BASELINE_REQUIRED,
    }
    new_decisions_required = (
        not authority.execution_authorised
        or authority.phase is not RenewalPhase.NOT_DUE
        or material_delta
    )
    notification_triggers = set(policy["notification"]["notify_when"])
    notification_required = (
        authority.phase.value in notification_triggers
        or delta.change_class.value in notification_triggers
        or authority.status.value in notification_triggers
    )

    package = {
        "schema_version": "axignal.o01-approval-renewal-package/v0.1",
        "task_id": "AX-GE2E-G7-O01-T04",
        "generated_at": iso_z(now),
        "head_sha": head_sha,
        "git_tree": git_tree,
        "status": package_status,
        "mode": policy["mode"],
        "approval_target": {
            "head_sha": head_sha,
            "manifest_digest": current_manifest_digest,
        },
        "current_approval_manifest_digest": current_manifest_digest,
        "previous_package_digest": (
            sha256_file(previous_package_path)
            if previous_package_path is not None and previous_package_path.is_file()
            else None
        ),
        "relevant_files": current_manifest["files"],
        "terms_observations": observations,
        "delta": {
            "change_class": delta.change_class.value,
            "review_path": review_path,
            "changed_relevant_paths": list(delta.changed_relevant_paths),
            "changed_technical_paths": list(delta.changed_technical_paths),
            "reasons": list(delta.reasons),
        },
        "authority": {
            "status": authority.status.value,
            "phase": authority.phase.value,
            "effective_expiry": (
                iso_z(authority.effective_expiry)
                if authority.effective_expiry is not None
                else None
            ),
            "reasons": list(authority.reasons),
            "execution_authorised_before_package": authority.execution_authorised,
        },
        "renewal": {
            "new_typed_decisions_required": new_decisions_required,
            "automatic_approval": False,
            "automatic_signature": False,
            "automatic_expiry_extension": False,
            "maximum_expiry": iso_z(maximum_expiry),
            "overlapping_renewal_allowed": bool(
                schedule["overlapping_renewal_allowed"]
            ),
            "grace_period_seconds": int(schedule["grace_period_seconds"]),
        },
        "notification": {
            "required": notification_required,
            "issue_number": int(policy["notification"]["issue_number"]),
            "deduplication_key": ":".join(
                (
                    head_sha,
                    delta.change_class.value,
                    authority.status.value,
                    iso_z(authority.effective_expiry)
                    if authority.effective_expiry is not None
                    else "none",
                )
            ),
        },
        "campaign_effect": {
            "campaign_status": "BLOCKED",
            "execution_authorised": False,
            "external_request_budget": 0,
            "source_state": "CANDIDATE",
            "product_admitted": False,
            "public_claim_contribution": False,
            "public_launch_authorised": False,
        },
        "required_human_actions": policy["human_required_actions"],
        "forbidden_automatic_actions": policy["forbidden_automatic_actions"],
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    package_path = output_dir / PACKAGE_NAME
    content = canonical_bytes(package)
    package_path.write_bytes(content)
    package_digest = sha256_bytes(content)
    (output_dir / f"{PACKAGE_NAME}.sha256").write_text(
        f"{package_digest}  {PACKAGE_NAME}\n",
        encoding="utf-8",
    )
    for authority_name in ("LEGAL", "PRIVACY_DATA_RIGHTS"):
        template = decision_template(
            authority_name,
            head_sha=head_sha,
            manifest_digest=current_manifest_digest,
            maximum_expiry=iso_z(maximum_expiry),
            change_class=delta.change_class.value,
        )
        (output_dir / f"{authority_name.lower()}-decision-template.v0.1.json").write_bytes(
            canonical_bytes(template)
        )

    return {
        "status": "PASS",
        "task_id": "AX-GE2E-G7-O01-T04",
        "output": "O01_APPROVAL_RENEWAL_PACKAGE_READY",
        "head_sha": head_sha,
        "git_tree": git_tree,
        "approval_manifest_digest": current_manifest_digest,
        "package_path": str(package_path.relative_to(ROOT)),
        "package_digest": package_digest,
        "package_status": package_status,
        "change_class": delta.change_class.value,
        "authority_status": authority.status.value,
        "renewal_phase": authority.phase.value,
        "new_typed_decisions_required": new_decisions_required,
        "maximum_expiry": iso_z(maximum_expiry),
        "notification_required": notification_required,
        "execution_authorised": False,
        "external_request_budget": 0,
        "human_decisions_required": ["LEGAL", "PRIVACY_DATA_RIGHTS"],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--online", action="store_true")
    parser.add_argument("--terms-fixture", type=Path, default=DEFAULT_FIXTURE_PATH)
    parser.add_argument("--previous-package", type=Path)
    parser.add_argument("--current-decisions", type=Path)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--now")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    now = parse_time(args.now) if args.now else datetime.now(UTC)
    try:
        result = materialise_renewal(
            online=bool(args.online),
            fixture_path=args.terms_fixture,
            previous_package_path=args.previous_package,
            current_decisions_path=args.current_decisions,
            output_dir=args.output_dir,
            now=now,
        )
    except (
        KeyError,
        OSError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        RenewalPreparationError,
    ) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
