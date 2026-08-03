from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from . import o01_history_frequency_lag as legacy
from . import o01_history_frequency_lag_v4 as v4
from .o01_quality_common import O01QualityCampaignError
from .o01_quality_http import NetworkBudget

DIAGNOSTIC_DIGEST = (
    "sha256:f6a7524549b8f48fdc4858a06641b5fbd94de0a61f1e1f812a8c3021b3897a1a"
)
PLAN_SCHEMA = "axignal.o01-history-frequency-lag-plan/v0.5"


def run_campaign(plan_path: Path, output_dir: Path) -> dict[str, Any]:
    plan = legacy.load_json(plan_path)
    if plan["schema_version"] != PLAN_SCHEMA:
        raise O01QualityCampaignError("Unexpected O01-E plan schema")
    if (
        plan["history_contract_diagnostic"]["artifact_digest"]
        != DIAGNOSTIC_DIGEST
    ):
        raise O01QualityCampaignError("History diagnostic authority digest mismatch")
    source = plan["source"]
    if source["state"] != "PRODUCT_ADMITTED" or source["scope"] != "ALL":
        raise O01QualityCampaignError("O01-E requires admitted TED with ALL scope")

    output_dir.mkdir(parents=True, exist_ok=True)
    network = plan["network"]
    allowed_hosts = frozenset(network["allowed_hosts"])
    budget = NetworkBudget(network["maximum_requests"])
    observed_at = datetime.now(UTC)
    execution_date = observed_at.date()

    official = [
        legacy._source_observation(
            url=item["url"],
            anchors=item["anchors"],
            allowed_hosts=allowed_hosts,
            timeout_seconds=network["timeout_seconds"],
            max_response_bytes=network["maximum_document_bytes"],
            budget=budget,
        )
        for item in plan["official_sources"]
    ]
    legacy.write_json(
        output_dir / "official-source-observations.v0.1.json",
        {
            "schema_version": "axignal.o01-official-source-observations/v0.6",
            "status": "PASS",
            "documents": official,
            "fabricated_evidence": 0,
        },
    )

    releases_by_year: dict[int, list[legacy.Release]] = {}
    calendar_observations: list[dict[str, Any]] = []
    for year in plan["release_calendar_years"]:
        calendar_url = plan["release_calendar_url_template"].format(year=year)
        body, metadata, started_at, completed_at = legacy.fetch_official(
            url=calendar_url,
            allowed_hosts=allowed_hosts,
            timeout_seconds=network["timeout_seconds"],
            max_response_bytes=network["maximum_calendar_bytes"],
            budget=budget,
        )
        releases = v4.parse_release_calendar_xls(body, expected_year=year)
        releases_by_year[year] = releases
        calendar_observations.append(
            {
                "year": year,
                "url": calendar_url,
                "format": "XLS_OLE2_BIFF8",
                "parser_contract": "NUMERIC_ISSUE_COLUMN_0_TEXT_DATE_COLUMN_1",
                "magic_hex": body[:8].hex(),
                "release_count": len(releases),
                "first_issue": releases[0].issue,
                "last_issue": releases[-1].issue,
                "first_release": releases[0].publication_date.isoformat(),
                "last_release": releases[-1].publication_date.isoformat(),
                "body_sha256": metadata["response_sha256"],
                "body_persisted": False,
                "request_started_at": legacy._iso(started_at),
                "observed_at": legacy._iso(completed_at),
                "metadata": metadata,
            }
        )
        del body
    legacy.write_json(
        output_dir / "release-calendar-observations.v0.1.json",
        {
            "schema_version": "axignal.o01-release-calendar-observations/v0.6",
            "status": "PASS",
            "parser": "xlrd==2.0.2",
            "parser_lock": plan["release_calendar_parser_lock"],
            "calendars": calendar_observations,
            "release_calendar_bodies_persisted": False,
            "fabricated_evidence": 0,
        },
    )

    all_releases = [
        item for releases in releases_by_year.values() for item in releases
    ]
    history = v4._history_report(
        plan,
        execution_date=execution_date,
        releases=all_releases,
        budget=budget,
    )
    frequency, lag = v4._frequency_and_lag(
        plan,
        execution_date=execution_date,
        releases_by_year=releases_by_year,
        budget=budget,
    )
    legacy.write_json(output_dir / "history-depth-report.v0.1.json", history)
    legacy.write_json(output_dir / "update-frequency-report.v0.1.json", frequency)
    legacy.write_json(output_dir / "publication-lag-report.v0.1.json", lag)

    checks = {
        "official_sources": all(item["status"] == "PASS" for item in official),
        "history_contract_diagnostic": (
            plan["history_contract_diagnostic"]["artifact_digest"]
            == DIAGNOSTIC_DIGEST
            and plan["history_contract_diagnostic"]["workbook_rows"] == 255
            and plan["history_contract_diagnostic"]["invalid_sort_token"] == "ASC"
            and plan["history_contract_diagnostic"]["raw_bodies_retained"] is False
        ),
        "calendar_bodies_not_persisted": all(
            item["body_persisted"] is False for item in calendar_observations
        ),
        **legacy._threshold_checks(
            plan,
            execution_date=execution_date,
            history=history,
            frequency=frequency,
            lag=lag,
            budget=budget,
        ),
    }
    passed = all(checks.values())
    result = {
        "schema_version": "axignal.o01-history-frequency-lag-result/v0.6",
        "status": "PASS" if passed else "FAIL",
        "output": (
            "O01_HISTORY_FREQUENCY_LAG_PASS"
            if passed
            else "O01_HISTORY_FREQUENCY_LAG_FAIL"
        ),
        "library_id": plan["library_id"],
        "source_id": source["source_id"],
        "observed_at": legacy._iso(observed_at),
        "evidence_expires_at": legacy._iso(
            observed_at + timedelta(days=plan["evidence_retention_days"])
        ),
        "network_requests_used": budget.used,
        "network_requests_maximum": budget.maximum,
        "checks": checks,
        "history": history,
        "frequency": frequency,
        "lag": lag,
        "decision": {
            "o01_metrics_closed": passed,
            "recommended_canonical_state": "ACCEPTED" if passed else "IN_REVIEW",
            "recommended_claim_decision": "DENIED",
            "claim_contribution": False,
            "gate7_closed": False,
            "public_launch": "NO_GO",
        },
        "history_diagnostic_artifact_digest": DIAGNOSTIC_DIGEST,
        "release_calendar_bodies_persisted": False,
        "fabricated_evidence": 0,
        "synthetic_evidence": 0,
    }
    legacy.write_json(output_dir / "final-result.v0.1.json", result)
    if not passed:
        failed = ", ".join(name for name, value in checks.items() if not value)
        raise O01QualityCampaignError(f"O01-E thresholds failed: {failed}")
    return result
