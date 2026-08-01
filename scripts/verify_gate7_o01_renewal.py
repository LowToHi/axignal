from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / (
    "data/acceptance/approvals/AX-LIB-O01-approval-renewal-policy.v0.1.json"
)
LEGAL_SNAPSHOT_PATH = ROOT / (
    "data/acceptance/legal/AX-LIB-O01-TED-official-terms-snapshot.v0.1.json"
)
RENEWAL_SOURCE_PATH = ROOT / "apps/api/src/axignal_api/o01_approval_renewal.py"
RENEWAL_TEST_PATH = ROOT / "apps/api/tests/test_o01_approval_renewal.py"
PREPARER_PATH = ROOT / "scripts/prepare_gate7_o01_renewal.py"
EXPECTED_CHANGE_CLASSES = {
    "NO_MATERIAL_CHANGE",
    "BASELINE_REQUIRED",
    "MATERIAL_TECHNICAL_CHANGE",
    "MATERIAL_TERMS_CHANGE",
    "AUTHORITY_SURFACE_CHANGE",
    "EVIDENCE_UNAVAILABLE",
}
EXPECTED_HUMAN_ACTIONS = {
    "LEGAL_DECISION",
    "PRIVACY_DATA_RIGHTS_DECISION",
    "CONDITIONS",
    "EXPIRY",
    "SIGNATURE",
}
REQUIRED_FORBIDDEN_ACTIONS = {
    "CREATE_HUMAN_SIGNATURE",
    "COPY_OR_REUSE_PRIOR_SIGNATURE",
    "EXTEND_APPROVAL_EXPIRY",
    "AUTO_APPROVE_LEGAL",
    "AUTO_APPROVE_PRIVACY_DATA_RIGHTS",
    "AUTHORISE_CAMPAIGN_EXECUTION",
    "INCREASE_EXTERNAL_REQUEST_BUDGET",
    "ADMIT_TED_TO_PRODUCT",
    "ENABLE_PUBLIC_CLAIMS",
    "ENABLE_PUBLIC_LAUNCH",
}


class RenewalVerificationError(RuntimeError):
    """Raised when the O01 approval-renewal contract is unsafe."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RenewalVerificationError(message)


def load_json(path: Path) -> dict[str, Any]:
    require(path.is_file(), f"Missing file: {path.relative_to(ROOT)}")
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"Expected JSON object: {path}")
    return value


def iter_signatures(node: Any, location: str = "$") -> list[tuple[str, Any]]:
    found: list[tuple[str, Any]] = []
    if isinstance(node, dict):
        for key, value in node.items():
            child = f"{location}.{key}"
            if key == "signature":
                found.append((child, value))
            found.extend(iter_signatures(value, child))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            found.extend(iter_signatures(value, f"{location}[{index}]"))
    return found


def verify_policy(policy: dict[str, Any], legal_snapshot: dict[str, Any]) -> None:
    require(
        policy["schema_version"] == "axignal.o01-approval-renewal-policy/v0.1",
        "Unexpected renewal-policy schema",
    )
    require(policy["task_id"] == "AX-GE2E-G7-O01-T04", "Task identity drift")
    require(policy["mode"] == "SEMI_AUTOMATIC", "Renewal mode is unsafe")

    schedule = policy["schedule"]
    require(schedule["cadence"] == "DAILY", "Renewal cadence drift")
    require(schedule["cron_utc"] == "17 6 * * *", "Renewal cron drift")
    require(schedule["renewal_window_days"] == 14, "Renewal window drift")
    require(schedule["urgent_window_days"] == 3, "Urgent window drift")
    require(schedule["grace_period_seconds"] == 0, "Expiry grace period is forbidden")
    require(schedule["overlapping_renewal_allowed"] is True, "Overlap is disabled")

    require(
        set(policy["human_required_actions"]) == EXPECTED_HUMAN_ACTIONS,
        "Human approval surface is incomplete",
    )
    require(
        set(policy["forbidden_automatic_actions"]) == REQUIRED_FORBIDDEN_ACTIONS,
        "Forbidden automatic-action set drift",
    )
    require(
        set(policy["change_classes"]) == EXPECTED_CHANGE_CLASSES,
        "Renewal change-class set drift",
    )

    invariants = policy["authority_invariants"]
    require(
        set(invariants["required_authorities"])
        == {"LEGAL", "PRIVACY_DATA_RIGHTS"},
        "Renewal authority set drift",
    )
    require(invariants["required_decision"] == "APPROVE", "Unsafe decision value")
    for key in (
        "approval_survives_head_change",
        "approval_survives_manifest_change",
        "approval_survives_terms_change",
        "execution_after_expiry",
        "automatic_signature_allowed",
        "automatic_expiry_extension_allowed",
    ):
        require(invariants[key] is False, f"Unsafe authority invariant: {key}")

    campaign = policy["campaign_effect"]
    require(campaign["campaign_status"] == "BLOCKED", "Campaign was unblocked")
    require(campaign["execution_authorised"] is False, "Execution was authorised")
    require(campaign["external_request_budget"] == 0, "External budget was enabled")
    require(campaign["source_state"] == "CANDIDATE", "TED source was activated")
    for key in (
        "product_admitted",
        "public_claim_contribution",
        "public_launch_authorised",
    ):
        require(campaign[key] is False, f"Unsafe campaign transition: {key}")

    source_documents = {
        item["document_id"]: item for item in legal_snapshot["source_documents"]
    }
    monitored_documents = {
        item["document_id"]: item for item in policy["official_documents"]
    }
    require(
        set(monitored_documents) == set(source_documents),
        "Terms monitor does not cover the complete official source snapshot",
    )
    allowed_hosts = set(policy["official_source_hosts"])
    for document_id, document in monitored_documents.items():
        require(
            document["url"] == source_documents[document_id]["url"],
            f"Official URL drift: {document_id}",
        )
        parsed = urlparse(document["url"])
        require(parsed.scheme == "https", f"Non-HTTPS official source: {document_id}")
        require(parsed.hostname in allowed_hosts, f"Non-allowlisted source: {document_id}")
        require(document["critical_anchors"], f"Missing legal anchors: {document_id}")


def verify_implementation_contract() -> None:
    source = RENEWAL_SOURCE_PATH.read_text(encoding="utf-8")
    tests = RENEWAL_TEST_PATH.read_text(encoding="utf-8")
    preparer = PREPARER_PATH.read_text(encoding="utf-8")
    for literal in (
        "class AuthorityStatus",
        "class RenewalPhase",
        "class ChangeClass",
        "def evaluate_authority",
        "def classify_delta",
        "execution_authorised=False",
    ):
        require(literal in source, f"Renewal source contract missing: {literal}")
    for literal in (
        "test_expiry_has_zero_grace_period_and_fails_closed",
        "test_head_or_manifest_binding_cannot_be_reused",
        "test_terms_change_is_material_and_blocks_abbreviated_review",
        "test_unavailable_official_evidence_fails_closed",
    ):
        require(literal in tests, f"Renewal test contract missing: {literal}")
    for literal in (
        "FETCH_OFFICIAL_TERMS_FROM_ALLOWLISTED_HOSTS",
        "machine_generated_decision",
        '"execution_authorised": False',
        '"external_request_budget": 0',
    ):
        require(literal in preparer, f"Renewal preparer contract missing: {literal}")


def verify() -> dict[str, Any]:
    policy = load_json(POLICY_PATH)
    legal_snapshot = load_json(LEGAL_SNAPSHOT_PATH)
    verify_policy(policy, legal_snapshot)
    verify_implementation_contract()
    for location, value in iter_signatures(policy):
        require(value in (None, ""), f"Machine signature in renewal policy: {location}")

    files = {
        str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (
            POLICY_PATH,
            LEGAL_SNAPSHOT_PATH,
            RENEWAL_SOURCE_PATH,
            RENEWAL_TEST_PATH,
            PREPARER_PATH,
        )
    }
    return {
        "status": "PASS",
        "task_id": "AX-GE2E-G7-O01-T04",
        "output": "O01_APPROVAL_RENEWAL_CONTRACT_PASS",
        "mode": "SEMI_AUTOMATIC",
        "change_classes": sorted(EXPECTED_CHANGE_CLASSES),
        "human_decisions_required": ["LEGAL", "PRIVACY_DATA_RIGHTS"],
        "automatic_signature": False,
        "automatic_expiry_extension": False,
        "grace_period_seconds": 0,
        "campaign_status": "BLOCKED",
        "execution_authorised": False,
        "external_request_budget": 0,
        "files": files,
    }


def main() -> int:
    try:
        result = verify()
    except (
        KeyError,
        OSError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        RenewalVerificationError,
    ) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
