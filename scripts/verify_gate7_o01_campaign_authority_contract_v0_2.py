from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/acceptance/approvals/AX-LIB-O01-campaign-authority-manifest.v0.2.json"
CONTRACT = ROOT / "data/acceptance/campaigns/AX-LIB-O01-quality-coverage-lag-execution-contract.v0.2.json"
PRIOR_PLAN = ROOT / "data/acceptance/campaigns/AX-LIB-O01-real-quality-coverage-lag-plan.v0.1.json"

MANIFEST_REF = "sha256:b5834a931d3ed7f9fa3e9f0217cd6c325b3072fcd133518db8e6bf5b8bbd520e"
CONTRACT_REF = "sha256:453d0bb49a25d4588d4b9da8955b1f348b1df860117378ad3a61cda6aaace81a"
PRIOR_PLAN_REF = "sha256:7d323a9a920f1fe96832b5f6e631b4da257c3ce995ef433705aff95c3ed1643b"
TARGET_HEAD = "f23e2dd247e04e55574b12484a3240b1295ee5dc"
TARGET_TREE = "ac53c6a1823b9bf07f92c5afd321c3c07613a65e"
QUERY_FROM = 'buyer-country IN ({country}) AND publication-date >= 20260701 AND publication-date <= 20260731 SORT BY publication-number ASC'
QUERY_TO = 'buyer-country IN ({country}) AND publication-date >= 20260701 AND publication-date <= 20260731 SORT BY publication-number'


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
    manifest = load(MANIFEST)
    contract = load(CONTRACT)
    prior = load(PRIOR_PLAN)

    assert digest(MANIFEST) == MANIFEST_REF
    assert digest(CONTRACT) == CONTRACT_REF
    assert digest(PRIOR_PLAN) == PRIOR_PLAN_REF

    assert manifest["schema_version"] == "axignal.o01-campaign-authority-manifest/v0.2"
    assert manifest["task_id"] == "AX-GE2E-G7-O01-B-R1"
    assert manifest["campaign_id"] == "AX-LIB-O01-TED-QALAG-ML-CONTROLS-v0.2"
    assert manifest["target"] == {
        "head_sha": TARGET_HEAD,
        "git_tree_sha": TARGET_TREE,
    }
    scope = manifest["authorised_scope"]
    assert scope["execution_contract_sha256"] == CONTRACT_REF
    assert (ROOT / scope["execution_contract_path"]).resolve() == CONTRACT.resolve()
    assert scope["private_campaign_only"] is True
    assert scope["public_claim_contribution"] is False

    remediation = manifest["remediation_evidence"]
    assert remediation["prior_plan_sha256"] == PRIOR_PLAN_REF
    assert remediation["prior_artifact_digest"] == "sha256:6a3d55557d16459e546839a6170db02e618b3a4c31cfadf6761a0d2885dab47f"
    assert remediation["prior_result_member_sha256"] == "sha256:0d5c88da9f48371a754d58486ef4a738be67a8c76fcae953d6055767b91475df"
    assert remediation["prior_output"] == "O01_QUALITY_COVERAGE_LAG_FAIL"
    assert remediation["failure_class"] == "VERSIONED_QUERY_CONTRACT_DEFECT"
    assert remediation["fabricated_evidence"] == 0
    assert remediation["raw_plaintext_uploaded"] is False

    decision = manifest["decision_contract"]
    assert decision["required_authorities"] == ["LEGAL", "PRIVACY_DATA_RIGHTS"]
    assert decision["required_fields"] == [
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
    assert decision["signature_scheme"] == "github-identity-v1"
    evidence_expiry = instant(manifest["official_evidence"]["evidence_expires_at"])
    decision_expiry = instant(decision["decision_max_expires_at"])
    artifact_expiry = instant(manifest["official_evidence"]["artifact_expires_at"])
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
    assert contract["task_id"] == "AX-GE2E-G7-O01-C-R1"
    assert contract["frozen_before_execution"] is True
    assert contract["campaign_id"] == "AX-LIB-O01-TED-QALAG-ML-CONTROLS-v0.2"

    remediation_contract = contract["remediation_of"]
    delta = remediation_contract["permitted_delta"]
    assert delta["field"] == "sampling.query_contract"
    assert delta["from"] == QUERY_FROM
    assert delta["to"] == QUERY_TO
    assert remediation_contract["all_other_experimental_parameters_unchanged"] is True
    assert prior["sampling"]["query_contract"] == QUERY_FROM
    assert contract["sampling"]["query_contract"] == QUERY_TO

    # Compare every frozen experimental surface except the sole query string.
    prior_sampling = dict(prior["sampling"])
    prior_sampling["query_contract"] = QUERY_TO
    assert contract["sampling"] == prior_sampling
    assert contract["measurement_window"] == prior["measurement_window"]
    assert contract["source"]["source_id"] == prior["source"]["source_id"]
    assert contract["source"]["source_state"] == prior["source"]["source_state"]
    assert contract["source"]["endpoint"] == prior["source"]["endpoint"]
    assert contract["source"]["allowed_hosts"] == prior["source"]["allowed_hosts"]
    assert contract["source"]["scope"] == prior["source"]["scope"]
    assert contract["source"]["authentication"] == prior["source"]["authentication"]
    assert contract["fields"] == prior["fields"]
    assert contract["quality_metrics"] == prior["quality_metrics"]
    assert contract["lag_metrics"] == prior["lag_metrics"]
    assert contract["thresholds"] == prior["thresholds"]
    for key in (
        "raw_responses",
        "plaintext_raw_location",
        "plaintext_raw_uploaded",
        "contact_values_persisted",
        "recipient_certificate_path",
        "recipient_certificate_sha256_fingerprint",
        "artifact_retention_days",
    ):
        assert contract["retention"][key] == prior["retention"][key]
    assert contract["non_authorisations"] == prior["non_authorisations"]
    assert contract["controls"]["kill_switch"]["required"] is True
    assert contract["controls"]["rollback"]["required"] is True

    print(json.dumps({
        "status": "PASS",
        "output": "O01_CAMPAIGN_AUTHORITY_V0_2_CONTRACT_PASS",
        "manifest_reference": MANIFEST_REF,
        "execution_contract_sha256": CONTRACT_REF,
        "target_head_sha": TARGET_HEAD,
        "target_git_tree_sha": TARGET_TREE,
        "prior_plan_sha256": PRIOR_PLAN_REF,
        "only_permitted_delta": True,
        "automatic_human_signature": False,
        "automatic_human_approval": False,
        "campaign_authorised": False,
        "source_state": "CANDIDATE",
        "public_launch": "NO_GO",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
