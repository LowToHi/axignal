from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INVENTORY = ROOT / (
    "data/acceptance/source-inventory/"
    "AX-LIB-F01-eu-countries-territories-candidate.v0.1.json"
)
DEFAULT_DOSSIER = ROOT / "data/acceptance/library-coverage/AX-LIB-F01.json"


class ContractError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"{path} must contain a JSON object")
    return value


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(inventory_path: Path, dossier_path: Path) -> dict[str, Any]:
    inventory = load_json(inventory_path)
    dossier = load_json(dossier_path)

    require(
        inventory["schema_version"] == "axignal.source-candidate-inventory/v0.1",
        "Unexpected inventory schema",
    )
    require(inventory["task_id"] == "AX-GE2E-G7-F01-A", "Unexpected task")
    require(inventory["library_id"] == "AX-LIB-F01", "Unexpected library")
    require(
        inventory["source_id"] == "src_eu_vocab_countries_territories",
        "Unexpected candidate source",
    )
    require(inventory["source_state"] == "CANDIDATE", "Source was promoted")
    require(
        inventory["authority"]
        == {
            "data_owner": "Eurostat",
            "data_steward": "Publications Office of the European Union",
            "corporate_reference_asset": True,
            "endorsed_by": (
                "European Commission Information Management Steering Board"
            ),
            "applicable_since": "2023-09-15",
        },
        "Candidate authority drift",
    )

    identifiers = inventory["identifiers"]
    require(
        identifiers["dataset_uri"]
        == "http://publications.europa.eu/resource/dataset/country",
        "Dataset URI drift",
    )
    require(
        identifiers["authority_graph_uri"]
        == "http://publications.europa.eu/resource/authority/country",
        "Authority graph drift",
    )
    require(
        identifiers["sparql_endpoint"]
        == "https://publications.europa.eu/webapi/rdf/sparql",
        "SPARQL endpoint drift",
    )
    require(
        all(value.startswith("https://") or value.startswith("http://") for value in identifiers.values()),
        "Candidate identifiers must be absolute URLs",
    )

    publication = inventory["observed_publication"]
    require(publication["catalogue_version"] == "20260318-0", "Version drift")
    require(publication["entry_count_declared"] == 375, "Entry declaration drift")
    require(publication["historical_versions_listed"] is True, "History hidden")
    require(publication["regular_updates_foreseen"] is True, "Update declaration drift")

    scope = inventory["semantic_scope"]
    require(scope["current_and_deprecated_countries_and_territories"] is True, "Core scope missing")
    require(scope["disputed_territories"] is True, "Disputed entities hidden")
    require(scope["marine_areas"] is True, "Marine entities hidden")
    require(scope["geographical_aggregations"] is False, "Aggregations falsely claimed")
    require(scope["map_geometry"] is False, "Map geometry falsely claimed")

    language_scope = inventory["language_scope"]
    require(
        language_scope["required_axignal_languages"]
        == ["en", "es", "fr", "de", "pt", "it"],
        "Required language set drift",
    )
    require(language_scope["journeys_verified"] is False, "Journeys falsely verified")

    rights = inventory["rights"]
    require(rights["status"] == "REVIEW_REQUIRED", "Rights falsely approved")
    require(rights["specific_dataset_reuse_confirmed"] is False, "Reuse falsely confirmed")
    require(rights["redistribution_confirmed"] is False, "Redistribution falsely confirmed")
    require(rights["derived_data_confirmed"] is False, "Derived rights falsely confirmed")
    require(rights["retention_confirmed"] is False, "Retention falsely confirmed")
    require(rights["third_party_standard_components_present"] is True, "Third-party standards hidden")

    admission = inventory["admission"]
    require(
        admission
        == {
            "product_admitted": False,
            "active": False,
            "claim_contribution": False,
            "global_geography_claim": False,
            "multilingual_claim": False,
            "canonical_library_state": "BLOCKED",
            "claim_decision": "DENIED",
            "gate7_decision": "IN_PROGRESS",
            "public_launch": "NO_GO",
        },
        "Candidate admission boundary drift",
    )

    require(dossier["library_id"] == "AX-LIB-F01", "Dossier library drift")
    require(dossier["canonical_state"] == "BLOCKED", "F01 was accepted")
    require(dossier["countries_covered"] == [], "Coverage was asserted")
    require(dossier["sources"]["active"] == [], "Candidate was activated")
    require(dossier["sources"]["suspended"] == [], "Unexpected suspended source")
    require(len(dossier["sources"]["candidate"]) == 1, "Candidate cardinality drift")
    candidate = dossier["sources"]["candidate"][0]
    require(candidate["source_id"] == inventory["source_id"], "Candidate link drift")
    require(candidate["state"] == "CANDIDATE", "Dossier candidate state drift")
    require(candidate["product_admitted"] is False, "Dossier source admitted")
    require(candidate["claim_contribution"] is False, "Dossier claim enabled")
    require(dossier["rights"]["status"] == "REVIEW_REQUIRED", "Dossier rights drift")
    require(dossier["claim_decision"] == "DENIED", "F01 claim enabled")
    require(dossier["kill_switch"]["tested"] is False, "Kill switch falsely tested")
    require(dossier["rollback"]["tested"] is False, "Rollback falsely tested")
    require(
        all(item["ingestion"] == "MISSING" for item in dossier["languages"]),
        "Language journey falsely completed",
    )

    return {
        "status": "PASS",
        "output": "F01_EU_VOCAB_CANDIDATE_INVENTORY_PASS",
        "library_id": "AX-LIB-F01",
        "source_id": inventory["source_id"],
        "source_state": "CANDIDATE",
        "inventory_sha256": f"sha256:{digest(inventory_path)}",
        "dossier_sha256": f"sha256:{digest(dossier_path)}",
        "product_admitted": False,
        "canonical_library_state": "BLOCKED",
        "claim_decision": "DENIED",
        "gate7_decision": "IN_PROGRESS",
        "public_launch": "NO_GO",
        "next_required_transition": inventory["next_required_transition"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY)
    parser.add_argument("--dossier", type=Path, default=DEFAULT_DOSSIER)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = verify(args.inventory.resolve(), args.dossier.resolve())
    except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True))
        return 1
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
