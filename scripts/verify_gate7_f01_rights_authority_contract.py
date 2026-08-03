from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from axignal_api.f01_rights_authority import (
    LEGAL_REQUIRED_ASSERTIONS,
    PRIVACY_REQUIRED_ASSERTIONS,
    REQUIRED_AUTHORITIES,
    REQUIRED_DECISION_FIELDS,
)

BASELINE_SHA256 = (
    "sha256:29abbb31ecbfc040438c02f107362303d2eacd677cce5867d06e548228941edb"
)
TECHNICAL_HEAD = "db7758a2e250a80ba992b2ff28b0574b01393c82"
TECHNICAL_TREE = "f631a3efdc0199a1468bd96e3a2947ec7e32c3ec"


class ContractError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def sha256_file(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def verify(
    manifest_path: Path,
    baseline_contract_path: Path,
    dossier_path: Path,
) -> dict[str, Any]:
    manifest = load_json(manifest_path)
    baseline_contract = load_json(baseline_contract_path)
    dossier = load_json(dossier_path)

    require(
        manifest["schema_version"]
        == "axignal.f01-rights-authority-manifest/v0.1",
        "Manifest schema drift",
    )
    require(manifest["task_id"] == "AX-GE2E-G7-F01-B", "Task drift")
    require(manifest["library_id"] == "AX-LIB-F01", "Library drift")
    require(
        manifest["source_id"] == "src_eu_vocab_countries_territories",
        "Source drift",
    )

    target = manifest["target"]
    require(target["head_sha"] == TECHNICAL_HEAD, "Technical head drift")
    require(target["git_tree_sha"] == TECHNICAL_TREE, "Technical tree drift")
    require(
        target["baseline_contract_path"] == str(baseline_contract_path),
        "Baseline contract path drift",
    )
    require(
        target["baseline_contract_sha256"]
        == sha256_file(baseline_contract_path)
        == BASELINE_SHA256,
        "Baseline contract digest drift",
    )
    require(
        baseline_contract["official_publication"]["expected_latest_version"]
        == "20260617-0",
        "Official publication version drift",
    )

    evidence = manifest["official_evidence"]
    require(evidence["workflow_run_id"] == 30777549236, "Workflow run drift")
    require(evidence["artifact_id"] == 8842563273, "Artifact ID drift")
    require(
        evidence["artifact_digest"]
        == "sha256:16a21241a43a0f6d4e7994179723110d7b227d719264d1dd8cdbb02608389e74",
        "Artifact digest drift",
    )
    require(
        evidence["baseline_file_digest"]
        == "sha256:67e4e7c4d18261fbd087427b4a1a6f179ed5b32a29956a2c8637f566fff744b9",
        "Baseline file digest drift",
    )
    require(
        evidence["baseline_payload_digest"]
        == "sha256:190d3a1c61b14b6b4600d99ad45519a68a86c79c77aa22ef088efc2655b3f6a4",
        "Baseline payload digest drift",
    )
    require(
        evidence["result_digest"]
        == "sha256:f172dc2a0adae2aec479deaf00df19da4ebb68d7162746cf19e86f9c5c54f6ba",
        "Result digest drift",
    )
    require(
        evidence["artifact_expires_at"] == "2026-09-02T01:44:49Z",
        "Artifact expiry drift",
    )
    require(
        evidence["evidence_expires_at"] == "2026-08-31T23:59:59Z",
        "Evidence expiry drift",
    )
    require(
        evidence["count_reconciliation"]
        == {
            "canonical_concepts": 345,
            "catalogue_non_retired_entries": 375,
            "category_xml_records": 378,
            "non_retired_duplicate_record_surplus": 33,
            "non_retired_unique_authority_codes": 342,
            "rdf_concept_schemes_including_root": 11,
            "rdf_sparql_exact_parity": True,
            "retired_entries": 3,
            "sparql_concepts": 345,
        },
        "Count reconciliation drift",
    )

    scope = manifest["authorised_scope"]
    require(scope["private_campaign_only"] is True, "Private scope disabled")
    require(scope["request_budget"] == 6, "Request budget drift")
    require(scope["retention_days"] == 30, "Retention budget drift")
    require(scope["paid_budget_eur"] == 0, "Paid budget drift")
    require(
        scope["source_state_during_campaign"] == "CANDIDATE",
        "Source state drift",
    )
    for field in (
        "product_admission",
        "active_source",
        "public_claim_contribution",
        "public_redistribution",
        "model_training_or_fine_tuning",
        "profiling_or_marketing",
    ):
        require(scope[field] is False, f"Forbidden scope enabled: {field}")

    require(
        manifest["legal_required_assertions"] == LEGAL_REQUIRED_ASSERTIONS,
        "Legal assertion contract drift",
    )
    require(
        manifest["privacy_required_assertions"] == PRIVACY_REQUIRED_ASSERTIONS,
        "Privacy assertion contract drift",
    )

    decision = manifest["decision_contract"]
    require(
        set(decision["required_authorities"]) == REQUIRED_AUTHORITIES,
        "Required authorities drift",
    )
    require(
        set(decision["required_fields"]) == REQUIRED_DECISION_FIELDS,
        "Required decision fields drift",
    )
    require(
        decision["admitted_decisions"]
        == ["APPROVE", "APPROVE_WITH_CONDITIONS", "REJECT"],
        "Admitted decisions drift",
    )
    require(
        decision["authorising_decisions"]
        == ["APPROVE", "APPROVE_WITH_CONDITIONS"],
        "Authorising decisions drift",
    )
    require(
        decision["signature_scheme"] == "github-identity-v1",
        "Signature scheme drift",
    )
    for field in (
        "comment_author_must_be_human",
        "technical_head_match_required",
        "manifest_match_required",
        "assertions_exact_match_required",
        "expiry_strictly_before_evidence",
    ):
        require(decision[field] is True, f"Decision check disabled: {field}")
    require(
        decision["decision_max_expires_at"] == "2026-08-30T23:59:59Z",
        "Decision maximum expiry drift",
    )
    require(
        not any(manifest["binding"].values()),
        "An authority binding survives invalidation",
    )

    state = manifest["required_state_until_both_authorities_pass"]
    require(state["technical_baseline"] == "PRESENT", "Technical baseline hidden")
    require(state["campaign_authorised"] is False, "Campaign pre-authorised")
    require(state["product_admitted"] is False, "Product pre-admitted")
    require(state["active_source"] is False, "Source pre-activated")
    require(state["f01_state"] == "BLOCKED", "F01 unblocked early")
    require(state["claim_decision"] == "DENIED", "Claims enabled early")
    require(state["gate7"] == "IN_PROGRESS", "Gate 7 closed early")
    require(state["public_launch"] == "NO_GO", "Public launch enabled")

    require(dossier["library_id"] == "AX-LIB-F01", "Dossier library drift")
    require(dossier["canonical_state"] == "BLOCKED", "Dossier state drift")
    require(dossier["countries_covered"] == [], "Coverage claimed early")
    require(dossier["sources"]["active"] == [], "Active source exists")
    require(len(dossier["sources"]["candidate"]) == 1, "Candidate count drift")
    candidate = dossier["sources"]["candidate"][0]
    require(candidate["state"] == "CANDIDATE", "Candidate promoted")
    require(candidate["admission"]["technical"] == "PASS", "Technical evidence hidden")
    for field in ("legal", "rights", "quality", "human_authority"):
        require(candidate["admission"][field] == "MISSING", f"{field} pre-approved")
    require(candidate["rights_expiry"] is None, "Rights expiry asserted")
    require(
        candidate["contributes_to_public_claim"] is False,
        "Candidate contributes to public claim",
    )
    require(dossier["rights"]["status"] == "MISSING", "Rights pre-approved")
    require(dossier["claim_decision"] == "DENIED", "Dossier claim drift")

    return {
        "status": "PASS",
        "output": "F01_RIGHTS_AUTHORITY_CONTRACT_PASS",
        "manifest_reference": sha256_file(manifest_path),
        "technical_head_sha": target["head_sha"],
        "technical_tree_sha": target["git_tree_sha"],
        "artifact_id": evidence["artifact_id"],
        "artifact_digest": evidence["artifact_digest"],
        "legal_issue": 160,
        "privacy_data_rights_issue": 161,
        "legal": "MISSING",
        "privacy_data_rights": "MISSING",
        "campaign_authorised": False,
        "f01_state": "BLOCKED",
        "gate7": "IN_PROGRESS",
        "public_launch": "NO_GO",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path(
            "data/acceptance/approvals/"
            "AX-LIB-F01-rights-authority-manifest.v0.1.json"
        ),
    )
    parser.add_argument(
        "--baseline-contract",
        type=Path,
        default=Path(
            "data/acceptance/source-baselines/"
            "AX-LIB-F01-eu-countries-territories-baseline-contract.v0.1.json"
        ),
    )
    parser.add_argument(
        "--dossier",
        type=Path,
        default=Path("data/acceptance/library-coverage/AX-LIB-F01.json"),
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = verify(args.manifest, args.baseline_contract, args.dossier)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
