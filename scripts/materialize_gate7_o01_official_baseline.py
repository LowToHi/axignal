from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from axignal_api.o01_official_baseline import (
    BaselineError,
    RetrievalPolicy,
    calculate_evidence_expiry,
    canonical_bytes,
    classify_terms_change,
    fetch_official_document,
    load_previous_baseline,
    sha256_bytes,
)

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / (
    "data/acceptance/approvals/"
    "AX-LIB-O01-official-online-baseline-contract.v0.1.json"
)
DEFAULT_OUTPUT_DIR = ROOT / "artifacts/o01-official-baseline/current"
PACKAGE_NAME = "official-online-baseline.v0.1.json"


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise BaselineError(f"{path} must contain a JSON object")
    return value


def git_value(*arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise BaselineError("Git identity resolution failed")
    return result.stdout.strip()


def iso_z(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def materialize(
    *,
    output_dir: Path,
    previous_baseline_path: Path | None,
    now: datetime,
) -> dict[str, Any]:
    if now.tzinfo is None:
        raise BaselineError("Current time requires a timezone")
    contract = load_json(CONTRACT_PATH)
    exact_head_sha = git_value("rev-parse", "HEAD")
    git_tree_sha = git_value("rev-parse", "HEAD^{tree}")
    expected_sha = os.environ.get("AXIGNAL_EXACT_SHA", exact_head_sha)
    if exact_head_sha != expected_sha:
        raise BaselineError("Baseline checkout does not match AXIGNAL_EXACT_SHA")

    network = contract["network_policy"]
    challenge_markers = tuple(str(item) for item in contract["challenge_markers"])
    policy = RetrievalPolicy(
        allowed_hosts=frozenset(str(item) for item in network["allowed_hosts"]),
        max_redirects=int(network["max_redirects"]),
        max_response_bytes=int(network["max_response_bytes"]),
        timeout_seconds=float(network["timeout_seconds"]),
        allowed_content_types=frozenset({"text/html", "application/xhtml+xml"}),
        challenge_markers=challenge_markers,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    documents_dir = output_dir / "documents"
    documents_dir.mkdir(parents=True, exist_ok=True)

    observations: dict[str, dict[str, Any]] = {}
    for document in contract["official_documents"]:
        retrieved = fetch_official_document(document, policy=policy, observed_at=now)
        content_path = documents_dir / f"{retrieved.document_id}.normalized.txt"
        content_path.write_text(retrieved.normalized_text + "\n", encoding="utf-8")
        observations[retrieved.document_id] = {
            "document_id": retrieved.document_id,
            "publisher": retrieved.publisher,
            "status": retrieved.status,
            "requested_url": retrieved.requested_url,
            "final_url": retrieved.final_url,
            "http_status": retrieved.http_status,
            "content_type": retrieved.content_type,
            "observed_at": retrieved.observed_at,
            "content_sha256": retrieved.content_sha256,
            "normalized_text_bytes": retrieved.normalized_text_bytes,
            "normalized_content_path": str(content_path.relative_to(output_dir)),
            "critical_anchors_expected": retrieved.critical_anchors_expected,
            "critical_anchors_present": retrieved.critical_anchors_present,
            "resolved_addresses": list(retrieved.resolved_addresses),
            "selected_address": retrieved.selected_address,
            "etag": retrieved.etag,
            "last_modified": retrieved.last_modified,
        }

    previous = load_previous_baseline(previous_baseline_path)
    previous_documents = previous.get("documents") if previous is not None else None
    if previous_documents is not None and not isinstance(previous_documents, dict):
        raise BaselineError("Previous baseline documents must be an object")
    terms_change_class = classify_terms_change(observations, previous_documents)

    retention = contract["retention"]
    evidence_expiry = calculate_evidence_expiry(
        observed_at=now,
        evidence_freshness_days=int(retention["evidence_freshness_days"]),
        artifact_retention_days=int(retention["artifact_retention_days"]),
        artifact_safety_margin_days=int(retention["artifact_safety_margin_days"]),
    )
    previous_digest = None
    if previous_baseline_path is not None and previous_baseline_path.is_file():
        previous_digest = sha256_bytes(previous_baseline_path.read_bytes())

    package = {
        "schema_version": "axignal.o01-official-online-baseline/v0.1",
        "task_id": contract["task_id"],
        "gate_id": contract["gate_id"],
        "library_id": contract["library_id"],
        "source_id": contract["source_id"],
        "generated_at": iso_z(now),
        "exact_head_sha": exact_head_sha,
        "git_tree_sha": git_tree_sha,
        "official_online_baseline": "PRESENT",
        "official_terms_available": True,
        "terms_change_class": terms_change_class.value,
        "evidence_expiry": iso_z(evidence_expiry),
        "evidence_expiry_status": "VALID",
        "documents": observations,
        "previous_baseline_digest": previous_digest,
        "network_controls": {
            "https_allowlist_enforced": True,
            "url_credentials_forbidden": True,
            "private_and_non_global_addresses_rejected": True,
            "connection_pinned_to_validated_address": True,
            "redirects_revalidated": True,
            "proxy_environment_used": False,
            "bounded_response_bytes": int(network["max_response_bytes"]),
            "bounded_redirects": int(network["max_redirects"]),
            "bounded_timeout_seconds": float(network["timeout_seconds"]),
        },
        "authority_boundary": {
            "automatic_human_signature": False,
            "automatic_human_approval": False,
            "permissions_generated": False,
            "campaign_authority": False,
            "source_admission": False,
            "public_launch": "NO_GO",
        },
    }
    package["baseline_payload_digest"] = sha256_bytes(canonical_bytes(package))
    package_bytes = canonical_bytes(package)
    baseline_artifact_digest = sha256_bytes(package_bytes)

    package_path = output_dir / PACKAGE_NAME
    package_path.write_bytes(package_bytes)
    (output_dir / f"{PACKAGE_NAME}.sha256").write_text(
        f"{baseline_artifact_digest}  {PACKAGE_NAME}\n",
        encoding="utf-8",
    )

    result = {
        "status": "PASS",
        "output": "O01_OFFICIAL_BASELINE_PASS",
        "task_id": contract["task_id"],
        "exact_head_sha": exact_head_sha,
        "git_tree_sha": git_tree_sha,
        "official_online_baseline": "PRESENT",
        "official_terms_available": True,
        "terms_change_class": terms_change_class.value,
        "evidence_expiry": iso_z(evidence_expiry),
        "evidence_expiry_status": "VALID",
        "automatic_human_signature": False,
        "automatic_human_approval": False,
        "permissions_generated": False,
        "campaign_authority": False,
        "source_admission": False,
        "public_launch": "NO_GO",
        "documents": len(observations),
        "baseline_digest": baseline_artifact_digest,
        "package_path": str(package_path.relative_to(ROOT)),
        "notification_deduplication_key": ":".join(
            (
                exact_head_sha,
                baseline_artifact_digest,
                terms_change_class.value,
                iso_z(evidence_expiry),
            )
        ),
    }
    (output_dir / "result.v0.1.json").write_bytes(canonical_bytes(result))
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--previous-baseline", type=Path)
    parser.add_argument("--now")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    now = (
        datetime.fromisoformat(args.now.replace("Z", "+00:00"))
        if args.now
        else datetime.now(UTC)
    )
    try:
        result = materialize(
            output_dir=args.output_dir,
            previous_baseline_path=args.previous_baseline,
            now=now,
        )
    except (
        BaselineError,
        KeyError,
        OSError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        print(
            json.dumps(
                {
                    "status": "FAIL",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                },
                sort_keys=True,
            )
        )
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
