from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from verify_gate7_source_rights import (
    APPROVAL_PATH,
    BUNDLE_PATH,
    DOSSIER_PATH,
    LIBRARY_ID,
    MATRIX_PATH,
    ROOT,
    SNAPSHOT_PATH,
    SOURCE_ID,
    RightsVerificationError,
    evidence_by_reference,
    load_json,
    require,
    require_current_expiry,
    sha256_file,
    verify_approval_request,
    verify_bundle,
    verify_field_matrix,
    verify_no_machine_signatures,
    verify_official_snapshot,
)

ADMISSION_MANIFEST_PATH = ROOT / (
    "data/acceptance/source-admission/"
    "AX-LIB-O01-TED-source-admission-authority-manifest.v0.2.json"
)
ADMISSION_CONTRACT_PATH = ROOT / (
    "data/acceptance/source-admission/"
    "AX-LIB-O01-TED-source-admission-contract.v0.2.json"
)
ADMISSION_CLOSURE_PATH = ROOT / (
    "data/acceptance/source-admission/"
    "AX-LIB-O01-TED-source-admission-closure.v0.2.json"
)
CAMPAIGN_REGISTRY_PATH = ROOT / (
    "data/acceptance/campaign-results/"
    "AX-LIB-O01-TED-QALAG-ML-CONTROLS-v0.6-r4.json"
)


def require_digest(reference: str, expected: str, label: str) -> None:
    require(reference == f"sha256:{expected}", f"{label} digest mismatch")


def verify_admission_assets(
    manifest: dict[str, Any],
    contract: dict[str, Any],
    closure: dict[str, Any],
    registry: dict[str, Any],
) -> None:
    require(
        manifest["schema_version"]
        == "axignal.o01-source-admission-authority-manifest/v0.2",
        "Unexpected source-admission manifest schema",
    )
    require(
        contract["schema_version"] == "axignal.o01-ted-source-admission-contract/v0.2",
        "Unexpected source-admission contract schema",
    )
    require(
        closure["schema_version"] == "axignal.o01-ted-source-admission-closure/v0.2",
        "Unexpected source-admission closure schema",
    )
    require(
        registry["schema_version"] == "axignal.o01-campaign-result-registry/v0.6-r4",
        "Unexpected campaign registry schema",
    )

    require_digest(
        manifest["contract_sha256"],
        sha256_file(ADMISSION_CONTRACT_PATH),
        "Admission contract",
    )
    require_digest(
        manifest["campaign_registry_sha256"],
        sha256_file(CAMPAIGN_REGISTRY_PATH),
        "Campaign registry",
    )
    manifest_reference = f"sha256:{sha256_file(ADMISSION_MANIFEST_PATH)}"
    require(
        closure["evidence"]["manifest_reference"] == manifest_reference,
        "Admission closure manifest reference mismatch",
    )
    require(
        closure["evidence"]["contract_sha256"] == manifest["contract_sha256"],
        "Admission closure contract reference mismatch",
    )
    require(
        closure["evidence"]["campaign_registry_sha256"]
        == manifest["campaign_registry_sha256"],
        "Admission closure registry reference mismatch",
    )

    require(closure["status"] == "PASS", "Admission closure is not PASS")
    require(
        closure["output"] == "O01_TED_SOURCE_ADMISSION_PASS",
        "Admission closure output mismatch",
    )
    require(closure["phase_closed"] is True, "Admission phase is not closed")
    require(closure["decision"] == "ADMIT", "Admission decision mismatch")
    require(closure["source_state"] == "PRODUCT_ADMITTED", "TED is not admitted")
    require(closure["product_admitted"] is True, "Product admission is false")

    authorities = closure["authority"]["authorities"]
    require(
        set(authorities) == set(manifest["authorities"]),
        "Admission authority set mismatch",
    )
    require(
        all(item["status"] == "APPROVED_CURRENT" for item in authorities.values()),
        "One or more admission authorities are not current",
    )
    for field in (
        "head_match",
        "manifest_match",
        "scope_match",
        "issue_match",
        "signatures_human",
        "expiry_within_evidence",
    ):
        require(closure["authority"][field] is True, f"Admission {field} failed")
    require_current_expiry(
        closure["authority"]["effective_expiry"],
        "Source admission authority",
    )

    boundary = closure["permanent_boundary"]
    require(boundary["bounded_product_use_authorised"] is True, "Product use blocked")
    require(boundary["bounded_claim_contribution"] is False, "Claims enabled")
    require(boundary["o01_canonical_state"] == "IN_REVIEW", "O01 was accepted")
    require(boundary["o01_claim_decision"] == "PENDING", "O01 claim was approved")
    require(boundary["gate7_closed"] is False, "Gate 7 was closed")
    require(boundary["global_coverage_claim_authorised"] is False, "Global claim enabled")
    require(boundary["public_launch"] == "NO_GO", "Public launch enabled")
    for field in (
        "public_redistribution_authorised",
        "contact_marketing_authorised",
        "model_training_authorised",
        "bid_submission_authorised",
        "external_notification_delivery_authorised",
    ):
        require(boundary[field] is False, f"Forbidden authority enabled: {field}")

    require(registry["status"] == "PASS", "Campaign registry is not PASS")
    require(
        registry["output"] == "O01_QUALITY_COVERAGE_LAG_PASS",
        "Campaign registry output mismatch",
    )
    require(registry["measurement"]["sample_count"] == 180, "Sample drift")
    require(
        len(registry["measurement"]["countries"]) == 12,
        "Country coverage drift",
    )
    require(
        sorted(registry["measurement"]["languages"])
        == ["de", "en", "es", "fr", "it", "pt"],
        "Language coverage drift",
    )
    require(
        registry["measurement"]["history_probe"]["status"] == "UNAVAILABLE",
        "Historical-depth limitation was hidden",
    )
    require(
        registry["measurement"]["provider_frequency"]["claim_authorised"] is False,
        "Provider-frequency claim was enabled",
    )
    require(
        registry["measurement"]["truncation_risk"]["present"] is True,
        "Truncation limitation was hidden",
    )


def verify_admitted_dossier(
    dossier: dict[str, Any],
    closure: dict[str, Any],
) -> dict[str, Any]:
    require(dossier["canonical_state"] == "IN_REVIEW", "O01 is not in review")
    require(dossier["claim_decision"] == "PENDING", "O01 claim decision drift")
    require(dossier["sources"]["candidate"] == [], "TED remains duplicated as candidate")
    require(dossier["sources"]["suspended"] == [], "Unexpected suspended source")
    require(len(dossier["sources"]["active"]) == 1, "Unexpected active source count")

    source = dossier["sources"]["active"][0]
    require(source["source_id"] == SOURCE_ID, "Dossier source mismatch")
    require(source["state"] == "PRODUCT_ADMITTED", "Dossier did not admit TED")
    require(source["contributes_to_public_claim"] is False, "TED contributes to claims")
    require(
        set(source["admission"].values()) == {"PASS"},
        "One or more source-admission dimensions are not PASS",
    )
    require_current_expiry(source["rights_expiry"], "TED source rights")
    require(dossier["rights"]["status"] == "PASS", "Dossier rights are not PASS")
    require(dossier["quality"]["status"] == "PASS", "Dossier quality is not PASS")
    require(dossier["historical_depth"]["status"] == "MISSING", "History was invented")
    require(dossier["update_frequency"]["status"] == "MISSING", "Frequency was invented")
    require(dossier["lag"]["status"] == "MISSING", "Publication lag was invented")
    require(dossier["reviews"] == [], "Conditional source reviews became library reviews")
    require(dossier["kill_switch"]["implemented"] is True, "Kill switch missing")
    require(dossier["kill_switch"]["tested"] is True, "Kill switch untested")
    require(dossier["rollback"]["implemented"] is True, "Rollback missing")
    require(dossier["rollback"]["tested"] is True, "Rollback untested")
    require(len(dossier["countries_covered"]) == 12, "Dossier country count drift")
    require(
        all(
            journey["ingestion"] == "PASS"
            and journey["normalisation"] == "PASS"
            and journey["search"] == "PASS"
            and journey["presentation"] == "PASS"
            for journey in dossier["languages"]
        ),
        "One or more multilingual journeys are not PASS",
    )

    references = evidence_by_reference(source["evidence"])
    local_evidence = {
        str(BUNDLE_PATH.relative_to(ROOT)): sha256_file(BUNDLE_PATH),
        str(SNAPSHOT_PATH.relative_to(ROOT)): sha256_file(SNAPSHOT_PATH),
        str(MATRIX_PATH.relative_to(ROOT)): sha256_file(MATRIX_PATH),
        str(CAMPAIGN_REGISTRY_PATH.relative_to(ROOT)): sha256_file(
            CAMPAIGN_REGISTRY_PATH
        ),
    }
    for reference, digest in local_evidence.items():
        require(reference in references, f"Dossier missing evidence: {reference}")
        require(
            references[reference]["sha256"] == digest,
            f"Dossier evidence digest mismatch: {reference}",
        )

    approval_reference = (
        f"github-actions:artifact:{closure['evidence']['admission_artifact_id']}/result.json"
    )
    require(approval_reference in references, "Dossier missing admission result")
    require(
        references[approval_reference]["sha256"]
        == closure["evidence"]["admission_result_sha256"].removeprefix("sha256:"),
        "Dossier admission-result digest mismatch",
    )
    return source


def verify() -> dict[str, Any]:
    snapshot = load_json(SNAPSHOT_PATH)
    matrix = load_json(MATRIX_PATH)
    approval = load_json(APPROVAL_PATH)
    bundle = load_json(BUNDLE_PATH)
    dossier = load_json(DOSSIER_PATH)
    manifest = load_json(ADMISSION_MANIFEST_PATH)
    contract = load_json(ADMISSION_CONTRACT_PATH)
    closure = load_json(ADMISSION_CLOSURE_PATH)
    registry = load_json(CAMPAIGN_REGISTRY_PATH)

    documents = verify_official_snapshot(snapshot)
    fields = verify_field_matrix(matrix)
    verify_approval_request(approval)
    historical_source = verify_bundle(bundle)
    verify_admission_assets(manifest, contract, closure, registry)
    admitted_source = verify_admitted_dossier(dossier, closure)
    verify_no_machine_signatures(
        {
            "snapshot": snapshot,
            "matrix": matrix,
            "approval": approval,
            "bundle": bundle,
            "dossier": dossier,
            "manifest": manifest,
            "closure": closure,
        }
    )

    return {
        "status": "PASS",
        "output": "O01_SOURCE_RIGHTS_ADMISSION_RECONCILIATION_PASS",
        "library_id": LIBRARY_ID,
        "source_id": SOURCE_ID,
        "historical_source_state": historical_source["state"],
        "source_state": admitted_source["state"],
        "legal_admission": admitted_source["admission"]["legal"],
        "rights_admission": admitted_source["admission"]["rights"],
        "privacy_data_rights_approval": "PASS",
        "human_authority": admitted_source["admission"]["human_authority"],
        "bounded_product_use_authorised": True,
        "claim_contribution": False,
        "o01_canonical_state": dossier["canonical_state"],
        "o01_claim_decision": dossier["claim_decision"],
        "historical_depth": dossier["historical_depth"]["status"],
        "update_frequency": dossier["update_frequency"]["status"],
        "publication_lag": dossier["lag"]["status"],
        "field_classes_checked": len(fields),
        "official_sources_checked": len(documents),
        "controls": {
            "personal_data_blocked": True,
            "third_party_content_blocked": True,
            "protected_marks_blocked": True,
            "raw_payload_storage_denied": True,
            "public_api_redistribution_denied": True,
            "model_training_denied": True,
            "kill_switch_tested": True,
            "rollback_tested": True,
            "global_coverage_claim_authorised": False,
            "gate7_closed": False,
            "public_launch": "NO_GO",
        },
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
        RightsVerificationError,
    ) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
