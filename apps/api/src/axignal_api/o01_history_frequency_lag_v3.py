from __future__ import annotations

import re
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

from . import o01_history_frequency_lag as legacy
from . import o01_history_frequency_lag_v2 as v2
from .o01_quality_common import O01QualityCampaignError
from .o01_quality_http import NetworkBudget

OLE2_MAGIC = bytes.fromhex("d0cf11e0a1b11ae1")
ISSUE_RE = re.compile(r"(?:S\s*)?(\d{1,3})\s*/\s*(\d{4})")


def _cell_date(cell: Any, *, datemode: int) -> date | None:
    import xlrd

    if cell.ctype == xlrd.XL_CELL_DATE:
        return xlrd.xldate_as_datetime(cell.value, datemode).date()
    if cell.ctype == xlrd.XL_CELL_TEXT:
        text = str(cell.value).strip()
        match = legacy.DATE_RE.search(text)
        if match is not None:
            return legacy._parse_calendar_date(match.group(1))
    return None


def parse_release_calendar_xls(body: bytes, *, expected_year: int) -> list[legacy.Release]:
    if not body.startswith(OLE2_MAGIC):
        raise O01QualityCampaignError(
            "Release calendar does not match the observed OLE2 signature"
        )
    try:
        import xlrd
    except ImportError as exc:
        raise O01QualityCampaignError(
            "The frozen O01-E XLS parser dependency is unavailable"
        ) from exc

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
                issue_year: int | None = None
                publication_date: date | None = None
                for cell in cells:
                    if cell.ctype == xlrd.XL_CELL_TEXT:
                        issue_match = ISSUE_RE.search(str(cell.value))
                        if issue_match is not None:
                            issue = int(issue_match.group(1))
                            issue_year = int(issue_match.group(2))
                    candidate = _cell_date(cell, datemode=workbook.datemode)
                    if candidate is not None:
                        publication_date = candidate
                if (
                    issue is None
                    or issue_year != expected_year
                    or publication_date is None
                    or publication_date.year != expected_year
                ):
                    continue
                releases[(issue_year, issue)] = legacy.Release(
                    year=issue_year,
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
    issue_numbers = [item.issue for item in result]
    if len(issue_numbers) != len(set(issue_numbers)):
        raise O01QualityCampaignError("Release calendar contains duplicate OJ S issues")
    return result


def run_campaign(plan_path: Path, output_dir: Path) -> dict[str, Any]:
    plan = legacy.load_json(plan_path)
    if plan["schema_version"] != "axignal.o01-history-frequency-lag-plan/v0.2":
        raise O01QualityCampaignError("Unexpected O01-E plan schema")
    source = plan["source"]
    if source["state"] != "PRODUCT_ADMITTED" or source["scope"] != "ALL":
        raise O01QualityCampaignError("O01-E requires admitted TED with ALL scope")
    if plan["release_calendar_format"] != "XLS_OLE2_BIFF8":
        raise O01QualityCampaignError("Unexpected release-calendar format contract")

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
            "schema_version": "axignal.o01-official-source-observations/v0.3",
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
            "schema_version": "axignal.o01-release-calendar-observations/v0.3",
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
    history = v2._history_report(
        plan,
        execution_date=execution_date,
        releases=all_releases,
        budget=budget,
    )
    frequency, lag = v2._frequency_and_lag(
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
        "calendar_format_probe": (
            plan["calendar_format_probe"]["format"] == "XLS_OLE2"
            and plan["calendar_format_probe"]["magic_hex"] == OLE2_MAGIC.hex()
            and plan["calendar_format_probe"]["raw_body_retained"] is False
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
        "schema_version": "axignal.o01-history-frequency-lag-result/v0.3",
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
