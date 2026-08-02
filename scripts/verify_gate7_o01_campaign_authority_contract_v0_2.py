from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/acceptance/approvals/AX-LIB-O01-campaign-authority-manifest.v0.2.json"
CONTRACT = ROOT / "data/acceptance/campaigns/AX-LIB-O01-quality-coverage-lag-execution-contract.v0.2.json"
MANIFEST_REF = "sha256:00d1534e3b8acd4d09f66ce251e784af64f9db0e95ffe9db64884cfb83d78429"
CONTRACT_REF = "sha256:5c423557ce667cb0c952b4e28523b10690b7fbf97d14443bd96419864b62dbf5"
PRIOR_PLAN_REF = "sha256:7d323a9a920f1fe96832b5f6e631b4da257c3ce995ef433705aff95c3ed1643b"
PRIOR_ARTIFACT_REF = "sha256:6a3d55557d16459e546839a6170db02e618b3a4c31cfadf6761a0d2885dab47f"
TARGET_HEAD = "b754b5641e5f17c5a084434aace4f939a4be0e84"
TARGET_TREE = "615efd6e8a7f3369292775dbcf3223f8cc006f29"
QUERY = (
    "buyer-country IN ({country}) AND publication-date >= 20260701 "
    "AND publication-date <= 20260731 SORT BY publication-number"
)
COUNTRIES = [
    "AUT", "BEL", "CZE", "DEU", "ESP", "FRA",
    "IRL", "ITA", "NLD", "POL", "PRT", "SWE",
]


def digest(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def instant(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    assert parsed.tzinfo is not None
    return parsed.astimezone(UTC)


def main() -> int:
    manifest, contract = load(MANIFEST), load(CONTRACT)
    assert digest(MANIFEST) == MANIFEST_REF
    assert digest(CONTRACT) == CONTRACT_REF

    assert manifest["schema_version"] == (
        "axignal.o01-campaign-authority-manifest/v0.2"
    )
    assert manifest["task_id"] == "AX-GE2E-G7-O01-B-R1"
    assert manifest["campaign_id"].endswith("-v0.2")
    assert manifest["target"] == {
        "head_sha": TARGET_HEAD,
        "git_tree_sha": TARGET_TREE,
    }
    scope = manifest["authorised_scope"]
    assert scope["execution_contract_sha256"] == CONTRACT_REF
    assert (ROOT / scope["execution_contract_path"]).resolve() == (
        CONTRACT.resolve()
    )
    assert scope["private_campaign_only"] is True
    assert scope["public_claim_contribution"] is False
    remediation = manifest["remediation_evidence"]
    assert remediation["prior_plan_sha256"] == PRIOR_PLAN_REF
    assert remediation["prior_artifact_digest"] == PRIOR_ARTIFACT_REF
    assert remediation["prior_output"] == "O01_QUALITY_COVERAGE_LAG_FAIL"
    assert remediation["fabricated_evidence"] == 0
    assert remediation["raw_plaintext_uploaded"] is False

    decision = manifest["decision_contract"]
    assert decision["required_authorities"] == [
        "LEGAL", "PRIVACY_DATA_RIGHTS",
    ]
    assert decision["required_fields"] == [
        "authority", "decision", "scope", "manifest_reference", "head_sha",
        "reviewed_at", "expires_at", "signature", "conditions",
    ]
    assert decision["signature_scheme"] == "github-identity-v1"
    evidence_expiry = instant(
        manifest["official_evidence"]["evidence_expires_at"]
    )
    decision_expiry = instant(decision["decision_max_expires_at"])
    artifact_expiry = instant(
        manifest["official_evidence"]["artifact_expires_at"]
    )
    assert decision_expiry < evidence_expiry < artifact_expiry
    assert manifest["binding"] == {
        "automatic_human_approval": False,
        "automatic_human_signature": False,
        "permissions_generated_automatically": False,
        "survives_evidence_expiry": False,
        "survives_execution_contract_change": False,
        "survives_manifest_change": False,
        "survives_target_head_change": False,
    }
    assert manifest["non_authorisations"]["public_launch"] == "NO_GO"
    assert all(
        value is False
        for key, value in manifest["non_authorisations"].items()
        if key != "public_launch"
    )

    assert contract["schema_version"] == (
        "axignal.o01-quality-coverage-lag-execution-contract/v0.2"
    )
    assert contract["frozen_before_execution"] is True
    assert contract["campaign_id"].endswith("-v0.2")
    sampling = contract["sampling"]
    assert sampling["query_contract"] == QUERY
    assert sampling["countries"] == COUNTRIES
    assert sampling["languages"] == ["de", "en", "es", "fr", "it", "pt"]
    assert sampling["sample_size"] == 180
    assert sampling["target_per_country"] == 15
    assert sampling["page_size"] == 100
    assert sampling["pages_per_country"] == 2
    assert sampling["maximum_network_requests"] == 60
    assert sampling["maximum_attempts_per_request"] == 2
    permitted = contract["remediation_of"]["permitted_delta"]
    assert permitted["field"] == "sampling.query_contract"
    assert permitted["to"] == QUERY
    assert permitted["from"] == QUERY + " ASC"
    assert contract["remediation_of"][
        "all_other_experimental_parameters_unchanged"
    ] is True
    assert contract["non_authorisations"]["public_launch"] == "NO_GO"

    print(json.dumps({
        "status": "PASS",
        "output": "O01_CAMPAIGN_AUTHORITY_V0_2_CONTRACT_PASS",
        "manifest_reference": MANIFEST_REF,
        "execution_contract_sha256": CONTRACT_REF,
        "prior_plan_sha256": PRIOR_PLAN_REF,
        "only_permitted_delta": True,
        "automatic_human_signature": False,
        "automatic_human_approval": False,
        "campaign_authorised": False,
        "public_launch": "NO_GO",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
