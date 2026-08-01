from __future__ import annotations

import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / (
    "data/acceptance/campaigns/"
    "AX-LIB-O01-quality-lag-multilingual-controls.v0.1.json"
)

EXPECTED_LANGUAGES = {"en", "es", "fr", "de", "pt", "it"}
EXPECTED_STAGES = {
    "source_ingestion",
    "personal_data_filtering",
    "language_detection",
    "normalisation_or_translation",
    "indexing",
    "search_and_retrieval",
    "accessible_presentation",
    "source_citation",
}
EXPECTED_QUALITY_METRICS = {
    "required_field_completeness",
    "identifier_validity",
    "notice_type_fidelity",
    "buyer_legal_entity_fidelity",
    "cpv_fidelity",
    "nuts_fidelity",
    "date_and_deadline_fidelity",
    "amount_currency_and_unit_fidelity",
    "duplicate_rate_before_canonicalisation",
    "duplicate_rate_after_canonicalisation",
    "false_merge_rate",
    "false_split_rate",
    "source_citation_fidelity",
    "invalid_or_rejected_record_rate",
}
EXPECTED_LAG_METRICS = {
    "source_to_retrieval_seconds",
    "retrieval_latency_seconds",
    "retrieval_to_normalisation_seconds",
    "normalisation_to_index_seconds",
    "index_to_presentation_seconds",
    "publication_to_presentation_seconds",
    "p50_seconds",
    "p95_seconds",
    "max_seconds",
    "declared_vs_observed_update_frequency",
}
EXPECTED_TIMESTAMPS = {
    "source_publication_at",
    "source_updated_at_when_present",
    "retrieval_started_at",
    "retrieval_completed_at",
    "normalised_at",
    "indexed_at",
    "presented_at",
}
REQUIRED_APPROVAL_FIELDS = {
    "authority",
    "decision",
    "scope",
    "manifest_digest",
    "head_sha",
    "timestamp",
    "expiry",
    "conditions",
    "signature",
}


class CampaignContractError(RuntimeError):
    """Raised when the O01 campaign contract ceases to be fail-closed."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CampaignContractError(message)


def load_contract() -> dict[str, Any]:
    require(CONTRACT_PATH.is_file(), "O01 campaign contract is missing")
    payload = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    require(isinstance(payload, dict), "O01 campaign contract must be an object")
    return payload


def require_current_expiry(value: str) -> None:
    expiry = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(expiry.tzinfo is not None, "Campaign expiry must include a timezone")
    require(expiry > datetime.now(UTC), "Campaign contract evidence is expired")


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


def verify_authority(contract: dict[str, Any]) -> None:
    authority = contract["approval_input"]
    expected = {
        "evidence_head_sha": "e423ea55dd282eb7d337c002806faba150330a56",
        "evidence_tree": "f7e6a9813e565a84b5dca8c0508a6d18e4257d40",
        "workflow_run": 30712199578,
        "artifact_id": 8822228662,
        "artifact_digest": (
            "sha256:402fba527b0eeb7c6e58330644e6f1fcefcd6b31b4d7de004ea0578f9e7c7d65"
        ),
        "gate7_report_sha256": (
            "1ec13c712475d2e95205c628baa2e5d4499aa9a6e06f20177d3a6d8d482d2a2e"
        ),
        "approval_manifest_digest": (
            "sha256:b6063d529c11cf23312f9d04e516530b2b6d162a375fc502ba277b8f45d186fe"
        ),
    }
    for key, value in expected.items():
        require(authority[key] == value, f"Campaign authority drift: {key}")


def verify_entry_gate(contract: dict[str, Any]) -> None:
    gate = contract["entry_gate"]
    require(contract["campaign_status"] == "BLOCKED", "Campaign was unblocked")
    require(contract["approvals"] == [], "Campaign contains unverified approvals")
    require(gate["execution_authorised"] is False, "External execution was authorised")
    require(
        gate["status"] == "BLOCKED_BY_TYPED_HUMAN_APPROVALS",
        "Campaign entry gate advanced",
    )
    require(
        set(gate["required_authorities"]) == {"LEGAL", "PRIVACY_DATA_RIGHTS"},
        "Campaign authority set mismatch",
    )
    require(gate["required_decision"] == "APPROVE", "Unsafe approval decision")
    require(
        set(gate["required_fields"]) == REQUIRED_APPROVAL_FIELDS,
        "Typed approval fields are incomplete",
    )
    require(
        gate["approval_survives_head_change"] is False,
        "Campaign approval incorrectly survives head changes",
    )


def verify_controls(contract: dict[str, Any]) -> None:
    controls = contract["controls"]
    require(controls["external_request_budget"] == 0, "External requests are enabled")
    for key in (
        "attachment_retrieval",
        "contact_field_persistence",
        "model_training",
        "natural_person_persistence",
        "public_api_redistribution",
        "raw_payload_persistence",
        "source_text_republication",
        "third_party_content_persistence",
    ):
        require(controls[key] == "DENIED", f"Unsafe campaign control: {key}")
    require(
        controls["personal_data_filter"] == "REQUIRED_BEFORE_PERSISTENCE",
        "Personal-data filtering is not mandatory",
    )

    permitted = set(contract["permitted_field_classes"])
    prohibited = set(contract["prohibited_field_classes"])
    require(permitted, "Permitted field scope is empty")
    require(prohibited, "Prohibited field scope is empty")
    require(permitted.isdisjoint(prohibited), "Field scopes overlap")


def verify_sampling_is_frozen_closed(contract: dict[str, Any]) -> None:
    sampling = contract["sampling_manifest"]
    require(sampling["status"] == "MISSING", "Sampling manifest advanced")
    require(sampling["countries_or_jurisdictions"] == [], "Countries were selected")
    require(sampling["cpv_strata"] == [], "CPV strata were selected")
    require(sampling["notice_types"] == [], "Notice types were selected")
    require(sampling["query_definitions"] == [], "Queries were selected")
    for key in (
        "campaign_expiry",
        "deterministic_seed",
        "measurement_window",
        "pagination_and_truncation_limits",
        "parser_normaliser_index_presenter_versions",
        "rate_limit_and_retry_policy",
        "replacement_rules",
        "sample_size",
    ):
        require(sampling[key] is None, f"Sampling field advanced before approval: {key}")


def verify_measurement_contracts(contract: dict[str, Any]) -> None:
    quality = contract["quality_contract"]
    require(quality["status"] == "MISSING", "Quality evidence was fabricated")
    require(
        set(quality["metrics"]) == EXPECTED_QUALITY_METRICS,
        "Quality metric contract drift",
    )

    lag = contract["lag_contract"]
    require(lag["status"] == "MISSING", "Lag evidence was fabricated")
    require(set(lag["metrics"]) == EXPECTED_LAG_METRICS, "Lag metric contract drift")
    require(
        set(lag["required_timestamps"]) == EXPECTED_TIMESTAMPS,
        "Lag timestamp contract drift",
    )


def verify_languages(contract: dict[str, Any]) -> None:
    journeys = contract["multilingual_journeys"]
    require(
        {journey["language"] for journey in journeys} == EXPECTED_LANGUAGES,
        "Required language set drift",
    )
    require(len(journeys) == len(EXPECTED_LANGUAGES), "Duplicate language journey")
    for journey in journeys:
        require(journey["status"] == "MISSING", "Language evidence was fabricated")
        require(
            set(journey["required_stages"]) == EXPECTED_STAGES,
            f"Journey stage drift: {journey['language']}",
        )


def verify_rehearsals_and_claims(contract: dict[str, Any]) -> None:
    require(
        contract["kill_switch_rehearsal"]["status"] == "NOT_EXECUTED",
        "Kill switch rehearsal was fabricated",
    )
    require(
        contract["rollback_rehearsal"]["status"] == "NOT_EXECUTED",
        "Rollback rehearsal was fabricated",
    )
    claims = contract["claim_effect"]
    require(all(value is False for value in claims.values()), "A claim was enabled")
    require(contract["source_state"] == "CANDIDATE", "TED source was activated")
    require(contract["synthetic_data"]["present"] is False, "Synthetic data appeared")
    require(
        contract["synthetic_data"]["contributes_to_claim"] is False,
        "Synthetic data contributes to a claim",
    )
    require(len(contract["stop_conditions"]) >= 10, "Stop-condition contract is incomplete")
    require(len(contract["required_outputs"]) >= 9, "Campaign output contract is incomplete")


def verify() -> dict[str, Any]:
    contract = load_contract()
    require(
        contract["schema_version"] == "axignal.o01-evidence-campaign-contract/v0.1",
        "Unexpected campaign schema",
    )
    require(contract["gate_id"] == "PUBLIC-LAUNCH-GATE-7", "Campaign gate mismatch")
    require(contract["library_id"] == "AX-LIB-O01", "Campaign library mismatch")
    require(contract["source_id"] == "src_ted_search_api_v3", "Campaign source mismatch")
    require_current_expiry(contract["expires_at"])

    verify_authority(contract)
    verify_entry_gate(contract)
    verify_controls(contract)
    verify_sampling_is_frozen_closed(contract)
    verify_measurement_contracts(contract)
    verify_languages(contract)
    verify_rehearsals_and_claims(contract)

    for location, value in iter_signatures(contract):
        require(value in (None, ""), f"Unexpected signature at {location}")

    return {
        "status": "PASS",
        "campaign_id": contract["campaign_id"],
        "contract_head_sha": os.environ.get("AXIGNAL_EXACT_SHA", "UNBOUND"),
        "contract_sha256": hashlib.sha256(CONTRACT_PATH.read_bytes()).hexdigest(),
        "campaign_status": "BLOCKED",
        "execution_authorised": False,
        "external_request_budget": 0,
        "source_state": "CANDIDATE",
        "required_authorities": ["LEGAL", "PRIVACY_DATA_RIGHTS"],
        "languages": sorted(EXPECTED_LANGUAGES),
        "quality_metrics": len(EXPECTED_QUALITY_METRICS),
        "lag_metrics": len(EXPECTED_LAG_METRICS),
        "kill_switch_rehearsal": "NOT_EXECUTED",
        "rollback_rehearsal": "NOT_EXECUTED",
        "claim_contribution": False,
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
        CampaignContractError,
    ) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
