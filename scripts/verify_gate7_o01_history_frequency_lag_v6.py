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
)
from verify_gate7_o01_history_frequency_lag_v4 import (
    verify_result as verify_v4_result,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLAN = ROOT / (
    "data/acceptance/campaigns/"
    "AX-LIB-O01-history-frequency-lag-plan.v0.5.json"
)
PARSER_LOCK = ROOT / "requirements/o01-xls.lock"
PLAN_SCHEMA = "axignal.o01-history-frequency-lag-plan/v0.5"
DIAGNOSTIC_DIGEST = (
    "sha256:f6a7524549b8f48fdc4858a06641b5fbd94de0a61f1e1f812a8c3021b3897a1a"
)


def verify_plan(plan: dict, plan_path: Path) -> dict:
    require(plan["schema_version"] == PLAN_SCHEMA, "Unexpected plan schema")
    require(plan["task_id"] == "AX-GE2E-G7-O01-E", "Unexpected task id")
    require(plan["campaign_id"] == "AX-LIB-O01-TED-HISTORY-FREQUENCY-LAG-v0.5", "Unexpected campaign")
    require(plan["library_id"] == "AX-LIB-O01", "Unexpected library")
    require(plan["frozen_before_execution"] is True, "Plan is not frozen")
    verify_baseline(plan)

    probe = plan["calendar_format_probe"]
    require(
        probe
        == {
            "head_sha": "267c86bc31518dcb735d2604dedc93974cbc74f2",
            "artifact_id": 8839697337,
            "artifact_digest": (
                "sha256:5b77b1a6975443ad9f9cb2af4668821aa508a2b2d72749ff4aa546aae25016f8"
            ),
            "years": [2025, 2026],
            "format": "XLS_OLE2",
            "magic_hex": "d0cf11e0a1b11ae1",
            "raw_body_retained": False,
        },
        "Calendar format probe drift",
    )
    diagnostic = plan["history_contract_diagnostic"]
    require(
        diagnostic
        == {
            "head_sha": "6d0a5c1ade15a6a6f0f7d7345de1bbbc172e5885",
            "artifact_id": 8839903336,
            "artifact_digest": DIAGNOSTIC_DIGEST,
            "workbook_rows": 255,
            "issue_column": 0,
            "issue_cell_type": "NUMBER",
            "publication_date_column": 1,
            "publication_date_cell_type": "TEXT_ISO_DATE",
            "invalid_sort_token": "ASC",
            "raw_bodies_retained": False,
        },
        "History contract diagnostic drift",
    )

    require(PARSER_LOCK.is_file(), "Frozen XLS parser lock is missing")
    require(
        PARSER_LOCK.read_text(encoding="utf-8").strip()
        == (
            "xlrd==2.0.2 \\\n"
            "    --hash=sha256:ea762c3d29f4cca48d82df517b6d89fbce4db3107f9d78713e48cd321d5c9aa9"
        ),
        "Frozen XLS parser lock drift",
    )

    require(
        plan["source"]
        == {
            "source_id": "src_ted_search_api_v3",
            "name": "TED Search API v3.0",
            "state": "PRODUCT_ADMITTED",
            "endpoint": "https://api.ted.europa.eu/v3/notices/search",
            "scope": "ALL",
            "authentication": "NONE",
        },
        "Source contract drift",
    )
    require(
        {item["url"] for item in plan["official_sources"]}
        == {
            "https://ted.europa.eu/en/help/search-browse",
            "https://ted.europa.eu/en/help/data-reuse",
            "https://ted.europa.eu/en/legal-notice",
            "https://docs.ted.europa.eu/api/latest/search.html",
            "https://docs.ted.europa.eu/ODS/latest/reuse/calendar.html",
        },
        "Official source set drift",
    )
    require(all(item["anchors"] for item in plan["official_sources"]), "Missing anchors")

    require(plan["release_calendar_years"] == [2025, 2026], "Calendar years drift")
    require(plan["frequency_reference_year"] == 2025, "Reference year drift")
    require(plan["publication_timezone"] == "Europe/Luxembourg", "Timezone drift")
    require(
        plan["release_calendar_url_template"]
        == "https://ted.europa.eu/en/release-calendar/-/download/file/XLS/{year}",
        "Release calendar URL drift",
    )
    require(plan["release_calendar_format"] == "XLS_OLE2_BIFF8", "Format drift")
    require(
        plan["release_calendar_parser_contract"]
        == "NUMERIC_ISSUE_COLUMN_0_TEXT_ISO_DATE_COLUMN_1",
        "Parser contract drift",
    )
    require(plan["release_calendar_parser_lock"] == "requirements/o01-xls.lock", "Parser lock path drift")

    history = plan["history"]
    require(history["declared_public_years"] == 10, "Public depth drift")
    require(history["search_years"] == 11, "History lower bound drift")
    require(
        history["query_mode"]
        == "COUNT_ONLY_CANONICAL_BOUNDED_INTERVAL_WITHOUT_SORT",
        "History query mode drift",
    )
    require(history["pagination_mode"] == "PAGE_NUMBER", "Pagination drift")
    require(history["day_before_boundary_must_be_empty"] is True, "Weak boundary")
    require(history["full_internal_archive_claimed"] is False, "Archive claim enabled")

    sampling = plan["sampling"]
    require(sampling["release_dates"] == 20, "Release sample drift")
    require(sampling["package_probes"] == 10, "Package sample drift")
    require(sampling["search_limit"] == 1, "Search limit drift")
    require(sampling["search_pagination_mode"] == "PAGE_NUMBER", "Search mode drift")
    require(sampling["check_query_syntax"] is False, "Query syntax mode drift")
    require(sampling["sort_clause"] is None, "Sort clause enabled")
    require(sampling["notice_fields"] == ["publication-number", "publication-date"], "Notice field drift")
    require(sampling["raw_notice_payloads_persisted"] is False, "Raw notices enabled")
    require(sampling["release_calendar_body_persisted"] is False, "XLS retained")
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
    require(thresholds["publication_to_axignal_p95_seconds_max"] <= 32430, "Lag threshold widened")
    require(thresholds["fabricated_evidence_max"] == 0, "Fabrication allowed")
    require(thresholds["synthetic_evidence_max"] == 0, "Synthetic evidence allowed")

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
    boundary = plan["non_authorisations"]
    for key in (
        "full_internal_archive_access",
        "exhaustive_notice_ingestion",
        "exact_first_seen_timestamp_claim",
        "public_claim_contribution",
        "global_coverage_claim",
        "public_redistribution",
        "contact_marketing",
        "model_training",
        "bid_submission",
        "external_notification_delivery",
        "gate7_closed",
    ):
        require(boundary[key] is False, f"Forbidden authority enabled: {key}")
    require(boundary["public_launch"] == "NO_GO", "Launch enabled")

    return {
        "status": "PASS",
        "output": "O01_HISTORY_FREQUENCY_LAG_PLAN_PASS",
        "implementation": "NUMERIC_XLS_NO_SORT_V0_6_EFFECTIVE_AUTHORITY",
        "plan_sha256": f"sha256:{digest(plan_path)}",
        "parser_lock_sha256": f"sha256:{digest(PARSER_LOCK)}",
        "admission_artifact_id": plan["baseline"]["admission_artifact_id"],
        "calendar_probe_artifact_id": probe["artifact_id"],
        "history_diagnostic_artifact_id": diagnostic["artifact_id"],
        "history_diagnostic_artifact_digest": diagnostic["artifact_digest"],
        "maximum_network_requests": network["maximum_requests"],
        "claim_contribution": False,
        "gate7_closed": False,
        "public_launch": "NO_GO",
    }


def verify_result(result_dir: Path, plan: dict, plan_path: Path) -> dict:
    compatibility_plan = dict(plan)
    compatibility_plan["schema_version"] = "axignal.o01-history-frequency-lag-plan/v0.4"
    result = verify_v4_result(result_dir, compatibility_plan, plan_path)
    require(
        plan["history_contract_diagnostic"]["artifact_digest"] == DIAGNOSTIC_DIGEST,
        "Result consumed the wrong diagnostic authority",
    )
    final = load_json(result_dir / "final-result.v0.1.json")
    require(final["schema_version"] == "axignal.o01-history-frequency-lag-result/v0.6", "Unexpected result schema")
    require(final["history_diagnostic_artifact_digest"] == DIAGNOSTIC_DIGEST, "Result authority drift")
    return {
        **result,
        "implementation": "NUMERIC_XLS_NO_SORT_V0_6_EFFECTIVE_AUTHORITY",
        "history_diagnostic_artifact_digest": DIAGNOSTIC_DIGEST,
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
