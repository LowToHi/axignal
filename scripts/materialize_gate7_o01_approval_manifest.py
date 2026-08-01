from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any

from verify_gate7_o01_legal_privacy_reconciliation import verify

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "artifacts/o01-legal-privacy"
MANIFEST_PATH = OUTPUT_DIR / "approval-manifest.v0.2.json"
DIGEST_PATH = OUTPUT_DIR / "approval-manifest.v0.2.sha256"
MAXIMUM_EXPIRY = "2026-08-31T23:59:59Z"

INPUT_PATHS = (
    ROOT / "data/acceptance/legal/AX-LIB-O01-TED-official-terms-snapshot.v0.1.json",
    ROOT / "data/acceptance/legal/AX-LIB-O01-TED-field-rights-matrix.v0.1.json",
    ROOT / "data/acceptance/legal/AX-LIB-O01-TED-contact-policy-reconciliation.v0.2.json",
    ROOT / "data/acceptance/approvals/AX-LIB-O01-legal-privacy-approval-request.v0.2.json",
    ROOT / "data/acceptance/campaigns/AX-LIB-O01-quality-lag-multilingual-controls.v0.1.json",
    ROOT / "data/contracts/AX-GE2E-G7-O01-T02-domain-contracts.v0.1.json",
    ROOT / "apps/api/src/axignal_api/procurement_domain.py",
    ROOT / "apps/api/src/axignal_api/o01_contact_policy.py",
    ROOT / "apps/api/tests/test_o01_contact_policy.py",
    ROOT / "scripts/verify_gate7_o01_legal_privacy_reconciliation.py",
    ROOT / "scripts/materialize_gate7_o01_approval_manifest.py",
)


class ManifestError(RuntimeError):
    """Raised when an exact-head approval manifest cannot be materialised."""


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
        raise ManifestError(f"Git command failed: {detail}")
    return result.stdout.strip()


def sha256_file(path: Path) -> str:
    if not path.is_file():
        raise ManifestError(f"Manifest input is missing: {path.relative_to(ROOT)}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exact_git_identity() -> tuple[str, str, str]:
    head = git_value("rev-parse", "HEAD")
    expected = os.environ.get("AXIGNAL_EXACT_SHA", head)
    if head != expected:
        raise ManifestError(f"Checkout head {head} does not equal expected head {expected}")
    tree = git_value("rev-parse", "HEAD^{tree}")
    committed_at = git_value("show", "-s", "--format=%cI", "HEAD")
    return head, tree, committed_at


def canonical_bytes(payload: dict[str, Any]) -> bytes:
    return (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def materialize() -> dict[str, Any]:
    reconciliation = verify()
    if reconciliation["status"] != "PASS":
        raise ManifestError("Reconciliation verifier did not pass")

    head, tree, committed_at = exact_git_identity()
    files = {
        str(path.relative_to(ROOT)): f"sha256:{sha256_file(path)}"
        for path in INPUT_PATHS
    }
    manifest: dict[str, Any] = {
        "schema_version": "axignal.o01-typed-approval-manifest/v0.2",
        "task_id": "AX-GE2E-G7-O01-T03",
        "campaign_id": "AX-LIB-O01-TED-QALAG-ML-CONTROLS-v0.1",
        "gate_id": "PUBLIC-LAUNCH-GATE-7",
        "library_id": "AX-LIB-O01",
        "source_id": "src_ted_search_api_v3",
        "head_sha": head,
        "git_tree": tree,
        "head_committed_at": committed_at,
        "maximum_expiry": MAXIMUM_EXPIRY,
        "status": "READY_FOR_TYPED_DECISIONS",
        "required_authorities": ["LEGAL", "PRIVACY_DATA_RIGHTS"],
        "required_decision": "APPROVE",
        "required_fields": [
            "authority",
            "decision",
            "scope",
            "manifest_digest",
            "head_sha",
            "timestamp",
            "expiry",
            "conditions",
            "signature",
        ],
        "contact_policy": reconciliation["contact_policy"],
        "policy_version": reconciliation["policy_version"],
        "legal_decision": "MISSING",
        "privacy_data_rights_decision": "MISSING",
        "campaign_status": "BLOCKED",
        "execution_authorised": False,
        "external_request_budget": 0,
        "source_state": "CANDIDATE",
        "product_admitted": False,
        "public_claim_contribution": False,
        "global_coverage_authorised": False,
        "multilingual_authorised": False,
        "public_launch_authorised": False,
        "approval_survives_head_change": False,
        "approval_survives_manifest_change": False,
        "files": files,
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    content = canonical_bytes(manifest)
    MANIFEST_PATH.write_bytes(content)
    digest = hashlib.sha256(content).hexdigest()
    DIGEST_PATH.write_text(f"sha256:{digest}  {MANIFEST_PATH.name}\n", encoding="utf-8")

    return {
        "status": "PASS",
        "task_id": manifest["task_id"],
        "head_sha": head,
        "git_tree": tree,
        "manifest_path": str(MANIFEST_PATH.relative_to(ROOT)),
        "manifest_digest": f"sha256:{digest}",
        "maximum_expiry": MAXIMUM_EXPIRY,
        "required_authorities": manifest["required_authorities"],
        "legal_decision": "MISSING",
        "privacy_data_rights_decision": "MISSING",
        "campaign_status": "BLOCKED",
        "external_request_budget": 0,
    }


def main() -> int:
    try:
        result = materialize()
    except (
        KeyError,
        OSError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        ManifestError,
    ) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
