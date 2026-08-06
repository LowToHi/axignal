from __future__ import annotations

import argparse
import json
from pathlib import Path

from verify_gate7_o01_history_frequency_lag import (
    ContractError,
    digest,
    load_json,
    require,
    verify_baseline,
    verify_result,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLAN = ROOT / (
    "data/acceptance/campaigns/"
    "AX-LIB-O01-history-frequency-lag-plan.v0.1.json"
)


def verify_plan(plan: dict, plan_path: Path) -> dict:
    require(
        plan["schema_version"] == "axignal.o01-history-frequency-lag-plan/v0.1",
        "Unexpected plan schema",
    )
    require(plan["task_id"] == "AX-GE2E-G7-O01-E", "Unexpected task id")
    require(plan["library_id"] == "AX-LIB-O01", "Unexpected library")
    require(plan["frozen_before_execution"] is True, "Plan is not frozen")
    verify_baseline(plan)

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
        "https://docs.ted.europa.eu/ODS/latest/reuse/calendar.html",
    }
    require(
        {item["url"] for item in plan["official_sources"]} == expected_sources,
        "Official source set drift",
    )
    require(all(item["anchors"] for item in plan["official_sources"]), "Missing anchors")
    require(plan["release_calendar_years"] == [2025, 2026], "Calendar years drift")
    require(plan["frequency_reference_year"] == 2025, "Reference year drift")
    require(plan["publication_timezone"] == "Europe/Luxembourg", "Timezone drift")
    require(
        plan["release_calendar_url_template"]
        == "https://ted.europa.eu/en/release-calendar/-/download/file/CSV/{year}",
        "Release calendar URL is not the canonical case-sensitive CSV contract",
    )
    require(
        plan["daily_package_url_template"]
        == "https://ted.europa.eu/packages/daily/{package_id}",
        "Daily package URL drift",
    )

    history = plan["history"]
    require(history["declared_public_years"] == 10, "Public depth drift")
    require(history["search_years"] == 11, "History lower bound drift")
    require(
        history["query_mode"]
        == "COUNT_ONLY_CANONICAL_BOUNDED_INTERVAL_BINARY_SEARCH",
        "History query mode is not canonical and bounded",
    )
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

    require(
        plan["non_authorisations"]
        == {
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
        },
        "Authority boundary drift",
    )
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
    return {
        "status": "PASS",
        "output": "O01_HISTORY_FREQUENCY_LAG_PLAN_PASS",
        "implementation": "CANONICAL_INTERVAL_REMEDIATION_V0_2",
        "plan_sha256": f"sha256:{digest(plan_path)}",
        "maximum_network_requests": network["maximum_requests"],
        "claim_contribution": False,
        "gate7_closed": False,
        "public_launch": "NO_GO",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--result-dir", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    plan_path = args.plan.resolve()
    try:
        plan = load_json(plan_path)
        result = verify_plan(plan, plan_path)
        if args.result_dir is not None:
            result = verify_result(args.result_dir, plan, plan_path)
    except (KeyError, OSError, TypeError, ValueError, ContractError) as exc:
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
