from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from statistics import median
from typing import Any
from zoneinfo import ZoneInfo

import xlrd

from . import o01_history_frequency_lag as legacy
from .o01_history_frequency_lag_v3 import OLE2_MAGIC, _cell_date
from .o01_quality_common import O01QualityCampaignError
from .o01_quality_http import NetworkBudget


def bounded_date_query(lower: date, upper: date) -> str:
    if lower > upper:
        raise ValueError("Publication-date lower bound exceeds upper bound")
    return (
        f"publication-date >= {lower:%Y%m%d} "
        f"AND publication-date <= {upper:%Y%m%d}"
    )


def parse_release_calendar_xls(
    body: bytes,
    *,
    expected_year: int,
) -> list[legacy.Release]:
    if not body.startswith(OLE2_MAGIC):
        raise O01QualityCampaignError(
            "Release calendar does not match the observed OLE2 signature"
        )
    try:
        workbook = xlrd.open_workbook(
            file_contents=body,
            formatting_info=False,
            on_demand=True,
        )
    except xlrd.XLRDError as exc:
        raise O01QualityCampaignError(
            f"Release calendar is not a readable BIFF8 workbook: {exc}"
        ) from exc

    releases: dict[tuple[int, int], legacy.Release] = {}
    try:
        for sheet in workbook.sheets():
            for row_index in range(sheet.nrows):
                cells = sheet.row(row_index)
                issue: int | None = None
                publication_date: date | None = None
                for column_index, cell in enumerate(cells):
                    if (
                        column_index == 0
                        and cell.ctype == xlrd.XL_CELL_NUMBER
                        and float(cell.value).is_integer()
                    ):
                        candidate_issue = int(cell.value)
                        if 1 <= candidate_issue <= 400:
                            issue = candidate_issue
                    candidate_date = _cell_date(
                        cell,
                        datemode=workbook.datemode,
                    )
                    if candidate_date is not None:
                        publication_date = candidate_date
                if (
                    issue is None
                    or publication_date is None
                    or publication_date.year != expected_year
                ):
                    continue
                releases[(expected_year, issue)] = legacy.Release(
                    year=expected_year,
                    issue=issue,
                    publication_date=publication_date,
                )
    finally:
        workbook.release_resources()

    result = sorted(releases.values(), key=lambda item: item.publication_date)
    if not result:
        raise O01QualityCampaignError(
            f"BIFF8 release calendar contained no parseable {expected_year} editions"
        )
    issues = [item.issue for item in result]
    if issues != list(range(1, len(issues) + 1)):
        raise O01QualityCampaignError(
            "Release calendar OJ S issue sequence is not contiguous from 1"
        )
    return result


def _search_interval(
    plan: dict[str, Any],
    lower: date,
    upper: date,
    *,
    budget: NetworkBudget,
) -> dict[str, Any]:
    return legacy._run_search(
        plan,
        bounded_date_query(lower, upper),
        budget=budget,
    )


def _history_report(
    plan: dict[str, Any],
    *,
    execution_date: date,
    releases: list[legacy.Release],
    budget: NetworkBudget,
) -> dict[str, Any]:
    history = plan["history"]
    lower = date(execution_date.year - history["search_years"], 1, 1)
    cache: dict[date, int] = {}
    observations: list[dict[str, Any]] = []

    def count_on_or_before(candidate: date) -> int:
        if candidate not in cache:
            observed = _search_interval(
                plan,
                lower,
                candidate,
                budget=budget,
            )
            cache[candidate] = observed["total"]
            observations.append(
                {
                    "lower_bound": lower.isoformat(),
                    "upper_bound": candidate.isoformat(),
                    "query": observed["query"],
                    "total": observed["total"],
                    "request": observed["metadata"],
                    "duration_seconds": observed["duration_seconds"],
                }
            )
        return cache[candidate]

    earliest = legacy.first_available_date(
        lower=lower,
        upper=execution_date,
        count_on_or_before=count_on_or_before,
    )
    before_count = count_on_or_before(earliest - timedelta(days=1))
    earliest_result = _search_interval(
        plan,
        earliest,
        earliest,
        budget=budget,
    )
    if earliest_result["total"] <= 0 or not earliest_result["notices"]:
        raise O01QualityCampaignError("Earliest TED date has no retrievable notice")
    earliest_notice = earliest_result["notices"][0]
    if legacy._notice_publication_date(earliest_notice) != earliest:
        raise O01QualityCampaignError("Earliest notice publication date mismatch")

    completed_dates = [
        item.publication_date
        for item in releases
        if item.publication_date <= execution_date
    ]
    if not completed_dates:
        raise O01QualityCampaignError("No completed release exists at execution time")
    latest = max(completed_dates)
    latest_result = _search_interval(
        plan,
        latest,
        latest,
        budget=budget,
    )
    if latest_result["total"] <= 0 or not latest_result["notices"]:
        raise O01QualityCampaignError("Latest completed edition is absent from Search API")
    latest_notice = latest_result["notices"][0]
    if legacy._notice_publication_date(latest_notice) != latest:
        raise O01QualityCampaignError("Latest notice publication date mismatch")

    expected_start = date(
        execution_date.year - history["declared_public_years"],
        execution_date.month,
        execution_date.day,
    )
    slack_days = (earliest - expected_start).days
    return {
        "schema_version": "axignal.o01-history-depth-report/v0.4",
        "status": "PASS",
        "declared_public_years": history["declared_public_years"],
        "declared_boundary_date": expected_start.isoformat(),
        "earliest_available_date": earliest.isoformat(),
        "earliest_publication_number": legacy._notice_publication_number(
            earliest_notice
        ),
        "latest_available_date": latest.isoformat(),
        "latest_publication_number": legacy._notice_publication_number(latest_notice),
        "day_before_earliest_total": before_count,
        "boundary_slack_days": slack_days,
        "public_depth_days": (latest - earliest).days + 1,
        "full_internal_archive_claimed": False,
        "search_scope": "ALL",
        "query_contract": "CANONICAL_CLOSED_INTERVAL_WITHOUT_SORT",
        "retrieval_mode_for_characterisation": "COUNT_ONLY_LIMIT_1",
        "pagination_truncation_applies_to_count": False,
        "exhaustive_notice_ingestion_performed": False,
        "binary_search_observations": observations,
        "limitations": [
            (
                "TED public search exposes a rolling ten-year window, not the "
                "non-public internal archive."
            ),
            (
                "The campaign characterises public availability boundaries; "
                "it does not ingest every notice."
            ),
            "No ordering clause is used because order is irrelevant to counts.",
        ],
        "fabricated_evidence": 0,
    }


def _frequency_and_lag(
    plan: dict[str, Any],
    *,
    execution_date: date,
    releases_by_year: dict[int, list[legacy.Release]],
    budget: NetworkBudget,
) -> tuple[dict[str, Any], dict[str, Any]]:
    network = plan["network"]
    all_releases = sorted(
        (
            release
            for releases in releases_by_year.values()
            for release in releases
            if release.publication_date <= execution_date
        ),
        key=lambda item: item.publication_date,
    )
    if not all_releases:
        raise O01QualityCampaignError("No release-calendar dates precede execution")
    recent = all_releases[-plan["sampling"]["release_dates"] :]
    package_releases = recent[-plan["sampling"]["package_probes"] :]

    search_observations: list[dict[str, Any]] = []
    acquisition_durations: list[float] = []
    for release in recent:
        observed = _search_interval(
            plan,
            release.publication_date,
            release.publication_date,
            budget=budget,
        )
        acquisition_durations.append(observed["duration_seconds"])
        first_notice = observed["notices"][0] if observed["notices"] else None
        search_observations.append(
            {
                "issue": release.issue,
                "publication_date": release.publication_date.isoformat(),
                "query": observed["query"],
                "notice_count": observed["total"],
                "first_publication_number": (
                    legacy._notice_publication_number(first_notice)
                    if first_notice is not None
                    else None
                ),
                "duration_seconds": observed["duration_seconds"],
                "request": observed["metadata"],
            }
        )

    package_observations: list[dict[str, Any]] = []
    package_offsets: list[float] = []
    for release in package_releases:
        package_url = plan["daily_package_url_template"].format(
            package_id=release.package_id
        )
        observed = legacy.probe_package(
            url=package_url,
            allowed_hosts=frozenset(network["allowed_hosts"]),
            timeout_seconds=network["timeout_seconds"],
            budget=budget,
        )
        last_modified = legacy._parse_http_date(observed.get("last_modified"))
        offset_seconds: float | None = None
        if last_modified is not None:
            local_midnight = datetime.combine(
                release.publication_date,
                time.min,
                tzinfo=ZoneInfo(plan["publication_timezone"]),
            ).astimezone(UTC)
            offset_seconds = (last_modified - local_midnight).total_seconds()
            deadline = plan["thresholds"]["package_deadline_seconds"]
            if 0 <= offset_seconds <= deadline:
                package_offsets.append(offset_seconds)
        package_observations.append(
            {
                "issue": release.issue,
                "package_id": release.package_id,
                "publication_date": release.publication_date.isoformat(),
                "url": package_url,
                "available": observed["available"],
                "last_modified": observed.get("last_modified"),
                "last_modified_offset_seconds": offset_seconds,
                "metadata": observed,
            }
        )

    reference = releases_by_year[plan["frequency_reference_year"]]
    reference_dates = [item.publication_date for item in reference]
    gaps = [
        (right - left).days
        for left, right in zip(reference_dates, reference_dates[1:], strict=False)
    ]
    search_presence = [item["notice_count"] > 0 for item in search_observations]
    package_presence = [item["available"] for item in package_observations]
    frequency = {
        "schema_version": "axignal.o01-update-frequency-report/v0.4",
        "status": "PASS",
        "declared": plan["frequency"]["declared"],
        "observed": (
            f"{sum(search_presence)}/{len(search_presence)} recent scheduled "
            f"editions present in Search API; "
            f"{sum(package_presence)}/{len(package_presence)} daily packages reachable"
        ),
        "reference_year": plan["frequency_reference_year"],
        "reference_year_editions": len(reference),
        "reference_year_weekend_editions": sum(
            item.publication_date.weekday() >= 5 for item in reference
        ),
        "reference_year_gap_median_days": median(gaps),
        "reference_year_gap_p95_days": legacy.percentile(
            [float(item) for item in gaps],
            0.95,
        ),
        "recent_release_sample": search_observations,
        "daily_package_sample": package_observations,
        "search_presence_ratio": sum(search_presence) / len(search_presence),
        "package_presence_ratio": sum(package_presence) / len(package_presence),
        "incident_free_guarantee_claimed": False,
        "release_calendar_is_authoritative": True,
        "fabricated_evidence": 0,
    }

    website_deadline = plan["frequency"]["website_deadline_seconds"]
    upper_bounds = [
        website_deadline + duration for duration in acquisition_durations
    ]
    lag = {
        "schema_version": "axignal.o01-publication-lag-report/v0.4",
        "status": "PASS",
        "metric_semantics": (
            "Conservative upper bound from publication-day midnight in the "
            "official timezone to an AXIGNAL Search API response: official "
            "website availability deadline plus measured request duration."
        ),
        "publication_timezone": plan["publication_timezone"],
        "official_website_deadline_seconds": website_deadline,
        "official_daily_package_deadline_seconds": plan["frequency"][
            "package_deadline_seconds"
        ],
        "search_request_duration_seconds": {
            "p50": legacy.percentile(acquisition_durations, 0.50),
            "p95": legacy.percentile(acquisition_durations, 0.95),
            "max": max(acquisition_durations),
        },
        "publication_to_axignal_upper_bound_seconds": {
            "p50": legacy.percentile(upper_bounds, 0.50),
            "p95": legacy.percentile(upper_bounds, 0.95),
            "max": max(upper_bounds),
        },
        "daily_package_last_modified_offsets_seconds": {
            "observed_count": len(package_offsets),
            "p50": legacy.percentile(package_offsets, 0.50)
            if package_offsets
            else None,
            "p95": legacy.percentile(package_offsets, 0.95)
            if package_offsets
            else None,
            "max": max(package_offsets) if package_offsets else None,
        },
        "direct_first-seen_timestamp_claimed": False,
        "limitations": [
            (
                "TED exposes publication dates but not a universal first-seen "
                "timestamp for Search API records."
            ),
            (
                "The published lag is an upper bound, not a claim of exact "
                "first availability."
            ),
            (
                "Package Last-Modified headers are supplementary and are not "
                "required for the Search API bound."
            ),
        ],
        "fabricated_evidence": 0,
    }
    return frequency, lag


def run_campaign(plan_path: Path, output_dir: Path) -> dict[str, Any]:
    plan = legacy.load_json(plan_path)
    if plan["schema_version"] != "axignal.o01-history-frequency-lag-plan/v0.3":
        raise O01QualityCampaignError("Unexpected O01-E plan schema")
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
            "schema_version": "axignal.o01-official-source-observations/v0.4",
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
        releases = parse_release_calendar_xls(body, expected_year=year)
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
            "schema_version": "axignal.o01-release-calendar-observations/v0.4",
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
    history = _history_report(
        plan,
        execution_date=execution_date,
        releases=all_releases,
        budget=budget,
    )
    frequency, lag = _frequency_and_lag(
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
            plan["history_contract_diagnostic"]["workbook_rows"] == 255
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
        "schema_version": "axignal.o01-history-frequency-lag-result/v0.4",
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
        "release_calendar_bodies_persisted": False,
        "fabricated_evidence": 0,
        "synthetic_evidence": 0,
    }
    legacy.write_json(output_dir / "final-result.v0.1.json", result)
    if not passed:
        failed = ", ".join(name for name, value in checks.items() if not value)
        raise O01QualityCampaignError(f"O01-E thresholds failed: {failed}")
    return result
