from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLAN = (
    ROOT
    / "data/acceptance/campaigns/"
    "AX-LIB-O01-history-frequency-lag-plan.v0.1.json"
)
ADMISSION_CLOSURE = (
    ROOT
    / "data/acceptance/source-admission/"
    "AX-LIB-O01-TED-source-admission-closure.v0.2.json"
)
DOSSIER = ROOT / "data/acceptance/library-coverage/AX-LIB-O01.json"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SENSITIVE_RE = re.compile(
    r'"(buyer-email|buyer-tel|organisation-tel-buyer|buyer-contact-point)"\s*:'
)


class O01HistoryContractError(RuntimeError):
    """Raised when O01-E plan or retained evidence violates its contract."""


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise O01HistoryContractError(f"Required file is missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise O01HistoryContractError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise O01HistoryContractError(f"Expected JSON object in {path}")
    return value


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise O01HistoryContractError(message)


def verify_admission_baseline(plan: dict[str, Any]) -> None:
    closure = load_json(ADMISSION_CLOSURE)
    dossier = load_json(DOSSIER)
    baseline = plan["baseline"]
    require(
        baseline["exact_head_sha"]
        == "97a61f79f5c709ed25af2dcaf960236b711deb4f",
        "Unexpected O01-D baseline head",
    )
    require(
        baseline["admission_artifact_id"] == 8838855002,
        "Unexpected O01-D validation artifact",
    )
    require(
        baseline["admission_artifact_digest"]
        == "sha256:870261e24767ab170b191ee4a5e8fca27b9c406aec7113237cc41220eb80f74a",
        "Unexpected O01-D validation artifact digest",
    )
    require(closure["status"] == "PASS", "O01-D closure is not PASS")
    require(
        closure["output"] == baseline["admission_output"],
        "O01-D output mismatch",
    )
    require(closure["phase_closed"] is True, "O01-D is not closed")
    require(closure["source_state"] == "PRODUCT_ADMITTED", "TED is not admitted")
    require(closure["product_admitted"] is True, "TED admission is false")
    boundary = closure["permanent_boundary"]
    require(boundary["bounded_product_use_authorised"] is True, "Product use blocked")
    require(boundary["bounded_claim_contribution"] is False, "Claims enabled")
    require(boundary["gate7_closed"] is False, "Gate 7 unexpectedly closed")
    require(boundary["public_launch"] == "NO_GO", "Public launch enabled")

    require(dossier["canonical_state"] == "IN_REVIEW", "O01 baseline state drift")
    require(dossier["claim_decision"] == "PENDING", "O01 baseline claim drift")
    require(len(dossier["sources"]["active"]) == 1, "Unexpected source count")
    source = dossier["sources"]["active"][0]
    require(source["source_id"] == plan["source"]["source_id"], "Source mismatch")
    require(source["state"] == "PRODUCT_ADMITTED", "Source state mismatch")
    require(source["contributes_to_public_claim"] is False, "Claim contribution enabled")


def verify_plan(plan: dict[str, Any]) -> dict[str, Any]:
    require(
        plan["schema_version"] == "axignal.o01-history-frequency-lag-plan/v0.1",
        "Unexpected plan schema",
    )
    require(plan["task_id"] == "AX-GE2E-G7-O01-E", "Unexpected task id")
    require(plan["library_id"] == "AX-LIB-O01", "Unexpected library")
    require(plan["frozen_before_execution"] is True, "Plan is not frozen")
    verify_admission_baseline(plan)

    source = plan["source"]
    require(source["source_id"] == "src_ted_search_api_v3", "Unexpected source")
    require(source["state"] == "PRODUCT_ADMITTED", "Source is not admitted")
    require(source["scope"] == "ALL", "History requires ALL scope")
    require(source["authentication"] == "NONE", "Unexpected authentication")
    require(
        source["endpoint"] == "https://api.ted.europa.eu/v3/notices/search",
        "Unexpected Search API endpoint",
    )

    expected_sources = {
        "https://ted.europa.eu/en/help/search-browse",
        "https://ted.europa.eu/en/help/data-reuse",
        "https://ted.europa.eu/en/legal-notice",
        "https://docs.ted.europa.eu/api/latest/search.html",
    }
    require(
        {item["url"] for item in plan["official_sources"]} == expected_sources,
        "Official source set drift",
    )
    require(
        all(item["anchors"] for item in plan["official_sources"]),
        "Official source anchors are required",
    )
    require(plan["release_calendar_years"] == [2025, 2026], "Calendar drift")
    require(plan["frequency_reference_year"] == 2025, "Reference year drift")
    require(plan["publication_timezone"] == "Europe/Luxembourg", "Timezone drift")

    history = plan["history"]
    require(history["declared_public_years"] == 10, "Public depth drift")
    require(history["search_years"] == 11, "Search lower bound drift")
    require(history["day_before_boundary_must_be_empty"] is True, "Weak boundary")
    require(history["full_internal_archive_claimed"] is False, "Archive claim enabled")

    sampling = plan["sampling"]
    require(sampling["release_dates"] == 20, "Release sample drift")
    require(sampling["package_probes"] == 10, "Package sample drift")
    require(sampling["search_limit"] == 1, "Search limit drift")
    require(sampling["check_query_syntax"] is False, "Query syntax mode drift")
    require(sampling["raw_notice_payloads_persisted"] is False, "Raw notices enabled")
    require(sampling["daily_package_bodies_persisted"] is False, "Packages retained")

    network = plan["network"]
    require(
        set(network["allowed_hosts"])
        == {"api.ted.europa.eu", "docs.ted.europa.eu", "ted.europa.eu"},
        "Network allowlist drift",
    )
    require(network["maximum_requests"] <= 60, "Network budget exceeds 60")
    require(network["maximum_attempts_per_request"] <= 2, "Retry budget exceeds 2")
    require(network["minimum_delay_seconds"] >= 0.25, "Request delay too low")
    require(network["timeout_seconds"] <= 30, "Timeout exceeds 30 seconds")

    thresholds = plan["thresholds"]
    require(thresholds["history_boundary_slack_days_max"] <= 7, "History slack widened")
    require(thresholds["latest_publication_age_days_max"] <= 4, "Freshness age widened")
    require(thresholds["reference_year_editions_min"] >= 240, "Edition floor lowered")
    require(thresholds["reference_year_weekend_editions_max"] == 0, "Weekend drift")
    require(thresholds["search_presence_ratio_min"] == 1.0, "Search ratio lowered")
    require(thresholds["package_presence_ratio_min"] >= 0.9, "Package ratio lowered")
    require(
        thresholds["publication_to_axignal_p95_seconds_max"] <= 32430,
        "Lag threshold widened",
    )
    require(thresholds["fabricated_evidence_max"] == 0, "Fabrication allowed")
    require(thresholds["synthetic_evidence_max"] == 0, "Synthetic evidence allowed")

    expected_boundary = {
        "full_internal_archive_access": False,
        "exhaustive_notice_ingestion": False,
        "exact_first_seen_timestamp_claim": False,
        "public_claim_contribution": False,
        "global_coverage_claim": False,
        "public_redistribution": False,
        "contact_marketing": False,
        "model_training": False,
        "bid_submission": False,
        "external_notification_delivery": False,
        "gate7_closed": False,
        "public_launch": "NO_GO",
    }
    require(plan["non_authorisations"] == expected_boundary, "Boundary drift")
    require(
        plan["recommended_success_transition"]
        == {
            "o01_canonical_state": "ACCEPTED",
            "o01_claim_decision": "DENIED",
            "source_state": "PRODUCT_ADMITTED",
            "source_contributes_to_public_claim": False,
            "gate7_decision": "IN_PROGRESS",
            "public_launch": "NO_GO",
        },
        "Success transition drift",
    )
    plan_digest = sha256_file(DEFAULT_PLAN)
    require(SHA256_RE.fullmatch(plan_digest) is not None, "Invalid plan digest")
    return {
        "status": "PASS",
        "output": "O01_HISTORY_FREQUENCY_LAG_PLAN_PASS",
        "plan_sha256": f"sha256:{plan_digest}",
        "maximum_network_requests": network["maximum_requests"],
        "public_history_years": history["declared_public_years"],
        "release_sample": sampling["release_dates"],
        "package_sample": sampling["package_probes"],
        "claim_contribution": False,
        "gate7_closed": False,
        "public_launch": "NO_GO",
    }


def verify_result(result_dir: Path, plan: dict[str, Any]) -> dict[str, Any]:
    required_names = {
        "official-source-observations.v0.1.json",
        "release-calendar-observations.v0.1.json",
        "history-depth-report.v0.1.json",
        "update-frequency-report.v0.1.json",
        "publication-lag-report.v0.1.json",
        "final-result.v0.1.json",
    }
    actual_names = {path.name for path in result_dir.iterdir() if path.is_file()}
    require(required_names <= actual_names, "O01-E retained evidence is incomplete")
    require(
        not any("raw" in name.casefold() or name.endswith(".zip") for name in actual_names),
        "Raw or archive payload was retained",
    )
    for path in sorted(result_dir.iterdir()):
        if path.is_file() and path.suffix in {".json", ".jsonl", ".txt"}:
            require(not SENSITIVE_RE.search(path.read_text(encoding="utf-8")), "PII retained")

    history = load_json(result_dir / "history-depth-report.v0.1.json")
    frequency = load_json(result_dir / "update-frequency-report.v0.1.json")
    lag = load_json(result_dir / "publication-lag-report.v0.1.json")
    result = load_json(result_dir / "final-result.v0.1.json")
    thresholds = plan["thresholds"]

    require(history["status"] == "PASS", "History report failed")
    earliest = date.fromisoformat(history["earliest_available_date"])
    latest = date.fromisoformat(history["latest_available_date"])
    require(earliest <= latest, "History dates are inverted")
    require(history["day_before_earliest_total"] == 0, "History lower bound is not exact")
    require(
        0 <= history["boundary_slack_days"] <= thresholds["history_boundary_slack_days_max"],
        "History boundary slack failed",
    )
    require(history["full_internal_archive_claimed"] is False, "Internal archive claimed")
    require(history["exhaustive_notice_ingestion_performed"] is False, "Exhaustive ingest claimed")
    require(history["fabricated_evidence"] == 0, "History evidence fabricated")

    require(frequency["status"] == "PASS", "Frequency report failed")
    require(frequency["declared"] == plan["frequency"]["declared"], "Frequency drift")
    require(
        frequency["reference_year_editions"] >= thresholds["reference_year_editions_min"],
        "Insufficient calendar editions",
    )
    require(
        frequency["reference_year_weekend_editions"]
        <= thresholds["reference_year_weekend_editions_max"],
        "Unexpected weekend editions",
    )
    require(
        frequency["search_presence_ratio"] >= thresholds["search_presence_ratio_min"],
        "Search presence failed",
    )
    require(
        frequency["package_presence_ratio"] >= thresholds["package_presence_ratio_min"],
        "Package presence failed",
    )
    require(frequency["incident_free_guarantee_claimed"] is False, "Incident-free claim")
    require(frequency["fabricated_evidence"] == 0, "Frequency evidence fabricated")

    require(lag["status"] == "PASS", "Lag report failed")
    upper = lag["publication_to_axignal_upper_bound_seconds"]
    require(upper["p50"] <= upper["p95"] <= upper["max"], "Lag ordering failed")
    require(
        upper["p95"] <= thresholds["publication_to_axignal_p95_seconds_max"],
        "Lag p95 threshold failed",
    )
    require(lag["direct_first-seen_timestamp_claimed"] is False, "First-seen claim")
    require(lag["fabricated_evidence"] == 0, "Lag evidence fabricated")

    require(result["status"] == "PASS", "Final O01-E result is not PASS")
    require(
        result["output"] == "O01_HISTORY_FREQUENCY_LAG_PASS",
        "Unexpected O01-E output",
    )
    require(result["library_id"] == "AX-LIB-O01", "Result library mismatch")
    require(result["source_id"] == "src_ted_search_api_v3", "Result source mismatch")
    require(
        result["network_requests_used"] <= result["network_requests_maximum"] <= 60,
        "Network budget failed",
    )
    require(all(result["checks"].values()), "One or more O01-E checks failed")
    require(result["fabricated_evidence"] == 0, "Fabricated evidence present")
    require(result["synthetic_evidence"] == 0, "Synthetic evidence present")
    require(
        result["decision"]
        == {
            "o01_metrics_closed": True,
            "recommended_canonical_state": "ACCEPTED",
            "recommended_claim_decision": "DENIED",
            "claim_contribution": False,
            "gate7_closed": False,
            "public_launch": "NO_GO",
        },
        "O01-E decision boundary drift",
    )

    members = {
        name: f"sha256:{sha256_file(result_dir / name)}" for name in sorted(required_names)
    }
    return {
        "status": "PASS",
        "output": "O01_HISTORY_FREQUENCY_LAG_EVIDENCE_PASS",
        "plan_sha256": f"sha256:{sha256_file(DEFAULT_PLAN)}",
        "members": members,
        "earliest_available_date": history["earliest_available_date"],
        "latest_available_date": history["latest_available_date"],
        "declared_frequency": frequency["declared"],
        "observed_frequency": frequency["observed"],
        "publication_lag_p50_seconds": round(upper["p50"]),
        "publication_lag_p95_seconds": round(upper["p95"]),
        "publication_lag_max_seconds": round(upper["max"]),
        "recommended_canonical_state": "ACCEPTED",
        "recommended_claim_decision": "DENIED",
        "claim_contribution": False,
        "gate7_closed": False,
        "public_launch": "NO_GO",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--result-dir", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--require-pass", action="store_true")
    args = parser.parse_args()
    global DEFAULT_PLAN
    DEFAULT_PLAN = args.plan.resolve()

    try:
        plan = load_json(DEFAULT_PLAN)
        result = verify_plan(plan)
        if args.result_dir is not None:
            result = verify_result(args.result_dir, plan)
    except (KeyError, OSError, TypeError, ValueError, O01HistoryContractError) as exc:
        failure = {"status": "FAIL", "error": str(exc)}
        print(json.dumps(failure, sort_keys=True))
        return 1

    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    if args.require_pass and result["status"] != "PASS":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
