from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


class ContractError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def canonical_digest(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def verify(
    contract_path: Path,
    inventory_path: Path,
    dossier_path: Path,
) -> dict[str, Any]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    dossier = json.loads(dossier_path.read_text(encoding="utf-8"))

    require(
        contract["schema_version"]
        == "axignal.f01-official-baseline-contract/v0.1",
        "Contract schema drift",
    )
    require(contract["task_id"] == "AX-GE2E-G7-F01-B", "Task drift")
    require(contract["library_id"] == "AX-LIB-F01", "Library drift")
    require(
        contract["source_id"] == "src_eu_vocab_countries_territories",
        "Source drift",
    )
    require(contract["source_state"] == "CANDIDATE", "Source promoted early")

    lineage = contract["lineage"]
    require(
        lineage["f01_a_head_sha"]
        == "c0259cc6abdb0d43504e9891501cf00b727fdacd",
        "F01-A lineage drift",
    )
    require(
        lineage["candidate_inventory_version"]
        == inventory["observed_publication"]["catalogue_version"]
        == "20260318-0",
        "Candidate version lineage mismatch",
    )
    require(lineage["version_drift_expected"] is True, "Version drift hidden")

    publication = contract["official_publication"]
    require(
        publication["expected_latest_version"] == "20260617-0",
        "Official publication target drift",
    )
    require(publication["expected_concept_count"] == 375, "Concept count drift")
    require(
        publication["sparql_endpoint"]
        == "https://publications.europa.eu/webapi/rdf/sparql",
        "SPARQL endpoint drift",
    )
    require(
        publication["reserved_concept_uri"].endswith("/OP_DATPRO"),
        "Reserved concept exclusion missing",
    )

    access = contract["access_contract"]
    require(access["authentication"] == "NONE", "Authentication drift")
    require(access["transport"] == "HTTPS", "Insecure transport")
    require(access["methods"] == ["GET", "POST"], "Access methods drift")
    require(
        access["required_formats"]
        == ["text/csv", "application/sparql-results+json"],
        "Machine-readable format drift",
    )
    require(access["maximum_http_requests"] == 4, "Request budget drift")
    require(access["maximum_retries"] == 0, "Retries are not frozen to zero")
    require(access["concurrency"] == 1, "Concurrency budget drift")
    require(
        access["external_monetary_budget_eur"] == 0,
        "External spend must remain zero",
    )
    require(access["fail_closed"] is True, "Fail-closed disabled")

    schemes = contract["concept_schemes"]
    require(set(schemes) == {f"{value:04d}" for value in range(1, 11)}, "Scheme set drift")
    require(
        schemes["0004"] == "DISPUTED_TERRITORIES",
        "Disputed entities are not explicit",
    )
    require(
        contract["derived_bucket_precedence"]
        == [
            "HISTORICAL_OR_DEPRECATED",
            "DISPUTED_ENTITY",
            "MARINE_AREA",
            "SPECIAL_STATUS_TERRITORY",
            "TERRITORY",
            "COUNTRY_OR_CITIZENSHIP_ENTITY",
            "OTHER_GEOPOLITICAL_ENTITY",
        ],
        "Derived classification precedence drift",
    )

    rights = contract["rights_boundary"]
    for field in (
        "dataset_specific_reuse",
        "retention",
        "redistribution",
        "derived_data",
    ):
        require(
            rights[field] == "HUMAN_LEGAL_DECISION_REQUIRED",
            f"{field} was approved without Legal authority",
        )
    require(rights["iso_codes_free_use_observed"] is True, "ISO code observation hidden")
    require(
        rights["iso_publications_and_collections_redistribution"]
        == "NOT_AUTHORISED_BY_THIS_CONTRACT",
        "ISO redistribution was overclaimed",
    )
    require(rights["iso_or_other_standard_text_ingestion"] is False, "Standard text ingestion enabled")
    require(rights["model_training_or_fine_tuning"] is False, "Training enabled")

    privacy = contract["privacy_boundary"]
    require(privacy["personal_data_expected"] is False, "Personal data expectation drift")
    require(privacy["contact_values_ingested"] is False, "Contact ingestion enabled")
    require(
        privacy["human_privacy_data_rights_decision_required"] is True,
        "Privacy authority bypassed",
    )

    campaign = contract["campaign_plan"]
    require(campaign["request_budget"] == 4, "Campaign request budget drift")
    require(campaign["paid_budget_eur"] == 0, "Campaign paid budget drift")
    require(campaign["product_ingestion"] is False, "Product ingestion enabled")
    require(campaign["public_redistribution"] is False, "Redistribution enabled")
    require(campaign["public_claims"] is False, "Public claims enabled")
    require(campaign["launch_transition"] is False, "Launch transition enabled")

    state = contract["required_state"]
    require(state["product_admitted"] is False, "Product admission overclaimed")
    require(state["active_source"] is False, "Source activated early")
    require(state["f01_state"] == "BLOCKED", "F01 must remain blocked")
    require(state["claim_decision"] == "DENIED", "Claim was authorised")
    require(state["gate7"] == "IN_PROGRESS", "Gate 7 was closed early")
    require(state["public_launch"] == "NO_GO", "Public launch was authorised")

    require(dossier["canonical_state"] == "BLOCKED", "Dossier state drift")
    require(dossier["countries_covered"] == [], "Coverage was claimed early")
    require(dossier["sources"]["active"] == [], "Active source exists")
    require(
        len(dossier["sources"]["candidate"]) == 1,
        "Exactly one F01 candidate is required",
    )
    require(dossier["claim_decision"] == "DENIED", "Dossier claim drift")

    return {
        "status": "PASS",
        "output": "F01_OFFICIAL_BASELINE_CONTRACT_PASS",
        "manifest_reference": canonical_digest(contract),
        "target_publication_version": publication["expected_latest_version"],
        "expected_concept_count": publication["expected_concept_count"],
        "request_budget": access["maximum_http_requests"],
        "paid_budget_eur": access["external_monetary_budget_eur"],
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
        "--contract",
        type=Path,
        default=Path(
            "data/acceptance/source-baselines/"
            "AX-LIB-F01-eu-countries-territories-baseline-contract.v0.1.json"
        ),
    )
    parser.add_argument(
        "--inventory",
        type=Path,
        default=Path(
            "data/acceptance/source-inventory/"
            "AX-LIB-F01-eu-countries-territories-candidate.v0.1.json"
        ),
    )
    parser.add_argument(
        "--dossier",
        type=Path,
        default=Path("data/acceptance/library-coverage/AX-LIB-F01.json"),
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = verify(args.contract, args.inventory, args.dossier)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
