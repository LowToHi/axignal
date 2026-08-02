from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = (
    ROOT
    / "data/acceptance/approvals/AX-LIB-O01-campaign-authority-manifest.v0.1.json"
)
EXPECTED_MANIFEST_REFERENCE = (
    "sha256:0c722eb4b02c4446ac26154b6ade49e1efb7b5c7787f8ac4925a0af8dd3d7898"
)
EXPECTED_HEAD = "b754b5641e5f17c5a084434aace4f939a4be0e84"
EXPECTED_TREE = "615efd6e8a7f3369292775dbcf3223f8cc006f29"
EXPECTED_CAMPAIGN_CONTRACT = (
    "sha256:d58bb462c1c29a2d4b2e3926d2f74a962bae463c4c4c2d25fd646c72c296653d"
)


def sha256_file(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise AssertionError("Time boundary requires timezone")
    return parsed.astimezone(UTC)


def main() -> int:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert sha256_file(MANIFEST_PATH) == EXPECTED_MANIFEST_REFERENCE
    assert manifest["schema_version"] == "axignal.o01-campaign-authority-manifest/v0.1"
    assert manifest["task_id"] == "AX-GE2E-G7-O01-B"
    assert manifest["library_id"] == "AX-LIB-O01"
    assert manifest["target"]["head_sha"] == EXPECTED_HEAD
    assert manifest["target"]["git_tree_sha"] == EXPECTED_TREE
    assert manifest["target"]["campaign_contract_sha256"] == EXPECTED_CAMPAIGN_CONTRACT
    assert manifest["decision_contract"]["required_authorities"] == [
        "LEGAL",
        "PRIVACY_DATA_RIGHTS",
    ]
    assert manifest["decision_contract"]["admitted_decisions"] == [
        "APPROVE",
        "APPROVE_WITH_CONDITIONS",
        "REJECT",
    ]
    assert manifest["decision_contract"]["required_fields"] == [
        "authority",
        "decision",
        "scope",
        "manifest_reference",
        "head_sha",
        "reviewed_at",
        "expires_at",
        "signature",
        "conditions",
    ]
    evidence_expiry = parse_time(
        manifest["official_evidence"]["evidence_expires_at"]
    )
    decision_max = parse_time(
        manifest["decision_contract"]["decision_max_expires_at"]
    )
    artifact_expiry = parse_time(
        manifest["official_evidence"]["artifact_expires_at"]
    )
    assert decision_max < evidence_expiry < artifact_expiry
    assert manifest["binding"] == {
        "automatic_human_approval": False,
        "automatic_human_signature": False,
        "permissions_generated_automatically": False,
        "survives_evidence_expiry": False,
        "survives_manifest_change": False,
        "survives_target_head_change": False,
    }
    assert manifest["non_authorisations"] == {
        "bid_submission_or_offer_presentation": False,
        "contact_marketing": False,
        "model_training_or_fine_tuning": False,
        "public_claims": False,
        "public_launch": "NO_GO",
        "public_redistribution": False,
        "ted_product_admission": False,
    }
    campaign_path = ROOT / manifest["target"]["campaign_contract_path"]
    assert sha256_file(campaign_path) == EXPECTED_CAMPAIGN_CONTRACT
    print(
        json.dumps(
            {
                "status": "PASS",
                "output": "O01_CAMPAIGN_AUTHORITY_CONTRACT_PASS",
                "manifest_reference": EXPECTED_MANIFEST_REFERENCE,
                "target_head_sha": EXPECTED_HEAD,
                "target_tree_sha": EXPECTED_TREE,
                "decisions_present": False,
                "automatic_human_signature": False,
                "automatic_human_approval": False,
                "campaign_authorised": False,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
