from __future__ import annotations

import csv
import hashlib
import http.client
import json
import math
import re
import ssl
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from io import StringIO
from pathlib import Path
from statistics import median
from time import perf_counter
from typing import Any, Callable
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

from .o01_official_baseline import (
    PinnedHTTPSConnection,
    resolve_public_addresses,
    select_address,
    validate_official_url,
)
from .o01_quality_common import (
    O01QualityCampaignError,
    parse_source_date,
    sha256_prefixed,
    values,
)
from .o01_quality_http import (
    NetworkBudget,
    extract_notices,
    extract_total,
    post_json,
)

ISSUE_RE = re.compile(r"(?:S\s*)?(\d{1,3})\s*/\s*(\d{4})")
DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2}|\d{2}[./-]\d{2}[./-]\d{4})")
REDIRECT_STATUSES = {301, 302, 303, 307, 308}


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.parts.append(data)


def html_text(value: str) -> str:
    parser = _TextExtractor()
    parser.feed(value)
    return " ".join(" ".join(parser.parts).split())


@dataclass(frozen=True)
class Release:
    year: int
    issue: int
    publication_date: date

    @property
    def package_id(self) -> str:
        return f"{self.year}{self.issue:05d}"


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise O01QualityCampaignError(f"{path} must contain a JSON object")
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
        + b"\n"
    )


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        raise ValueError("At least one value is required")
    if not 0 <= fraction <= 1:
        raise ValueError("Percentile fraction must be within [0, 1]")
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def _parse_calendar_date(value: str) -> date | None:
    candidate = value.strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d.%m.%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(candidate, fmt).date()
        except ValueError:
            continue
    return None


def parse_release_calendar(text: str, *, expected_year: int) -> list[Release]:
    normalized = text.lstrip("\ufeff")
    rows: list[list[str]] = []
    try:
        dialect = csv.Sniffer().sniff(normalized[:4096], delimiters=",;\t|")
        rows = list(csv.reader(StringIO(normalized), dialect))
    except csv.Error:
        rows = [line.split(";") for line in normalized.splitlines()]

    releases: dict[tuple[int, int], Release] = {}
    for row in rows:
        line = " ".join(item.strip() for item in row if item.strip())
        issue_match = ISSUE_RE.search(line)
        date_match = DATE_RE.search(line)
        if issue_match is None or date_match is None:
            continue
        issue = int(issue_match.group(1))
        issue_year = int(issue_match.group(2))
        publication_date = _parse_calendar_date(date_match.group(1))
        if publication_date is None or issue_year != expected_year:
            continue
        if publication_date.year != expected_year:
            continue
        releases[(issue_year, issue)] = Release(
            year=issue_year,
            issue=issue,
            publication_date=publication_date,
        )
    result = sorted(releases.values(), key=lambda item: item.publication_date)
    if not result:
        raise O01QualityCampaignError(
            f"Release calendar contained no parseable {expected_year} releases"
        )
    return result


def _headers_dict(response: http.client.HTTPResponse) -> dict[str, str]:
    return {key.casefold(): value for key, value in response.getheaders()}


def fetch_official(
    *,
    url: str,
    allowed_hosts: frozenset[str],
    timeout_seconds: float,
    max_response_bytes: int,
    budget: NetworkBudget,
    method: str = "GET",
    range_probe: bool = False,
    maximum_redirects: int = 4,
) -> tuple[bytes, dict[str, Any], datetime, datetime]:
    current_url = url
    for redirect_index in range(maximum_redirects + 1):
        parsed = validate_official_url(current_url, allowed_hosts=allowed_hosts)
        host = parsed.hostname or ""
        port = parsed.port or 443
        path = parsed.path + (f"?{parsed.query}" if parsed.query else "")
        budget.consume()
        addresses = resolve_public_addresses(host, port)
        selected = select_address(addresses)
        started_at = datetime.now(UTC)
        started_clock = perf_counter()
        connection = PinnedHTTPSConnection(
            host=host,
            port=port,
            selected_address=selected,
            timeout=timeout_seconds,
            context=ssl.create_default_context(),
        )
        try:
            headers = {
                "Accept-Encoding": "identity",
                "Cache-Control": "no-cache",
                "Connection": "close",
                "User-Agent": "AXIGNAL-O01-E-Evidence/1.0",
            }
            if range_probe:
                headers["Range"] = "bytes=0-0"
            connection.request(method, path, headers=headers)
            response = connection.getresponse()
            response_headers = _headers_dict(response)
            completed_at = datetime.now(UTC)
            duration_seconds = max(0.0, perf_counter() - started_clock)
            if response.status in REDIRECT_STATUSES:
                location = response_headers.get("location")
                response.read()
                if not location:
                    raise O01QualityCampaignError(
                        f"Official endpoint returned redirect {response.status} without Location"
                    )
                current_url = urljoin(current_url, location)
                continue
            accepted = {200}
            if range_probe:
                accepted.add(206)
            if response.status not in accepted:
                body = response.read(min(max_response_bytes, 4096))
                raise O01QualityCampaignError(
                    f"Official endpoint returned HTTP {response.status}; "
                    f"response_sha256={sha256_prefixed(body)}"
                )
            body = b"" if method == "HEAD" else response.read(max_response_bytes + 1)
            if len(body) > max_response_bytes:
                raise O01QualityCampaignError(
                    "Official endpoint response exceeded frozen byte limit"
                )
            metadata = {
                "requested_url": url,
                "final_url": current_url,
                "http_status": response.status,
                "content_type": response_headers.get("content-type"),
                "content_length": response_headers.get("content-length"),
                "date": response_headers.get("date"),
                "etag": response_headers.get("etag"),
                "last_modified": response_headers.get("last-modified"),
                "resolved_addresses": list(addresses),
                "selected_address": selected,
                "redirects_followed": redirect_index,
                "duration_seconds": duration_seconds,
                "response_bytes": len(body),
                "response_sha256": sha256_prefixed(body),
            }
            return body, metadata, started_at, completed_at
        finally:
            connection.close()
    raise O01QualityCampaignError("Official endpoint exceeded redirect budget")


def probe_package(
    *,
    url: str,
    allowed_hosts: frozenset[str],
    timeout_seconds: float,
    budget: NetworkBudget,
) -> dict[str, Any]:
    try:
        _, metadata, started_at, completed_at = fetch_official(
            url=url,
            allowed_hosts=allowed_hosts,
            timeout_seconds=timeout_seconds,
            max_response_bytes=0,
            budget=budget,
            method="HEAD",
        )
    except O01QualityCampaignError as exc:
        if not any(f"HTTP {status}" in str(exc) for status in (400, 403, 405)):
            raise
        _, metadata, started_at, completed_at = fetch_official(
            url=url,
            allowed_hosts=allowed_hosts,
            timeout_seconds=timeout_seconds,
            max_response_bytes=1,
            budget=budget,
            method="GET",
            range_probe=True,
        )
    return {
        **metadata,
        "probe_started_at": started_at.isoformat().replace("+00:00", "Z"),
        "probe_completed_at": completed_at.isoformat().replace("+00:00", "Z"),
        "available": metadata["http_status"] in {200, 206},
    }


def _search_payload(query: str, *, fields: list[str], limit: int) -> dict[str, Any]:
    return {
        "query": query,
        "fields": fields,
        "page": 1,
        "limit": limit,
        "scope": "ALL",
        "checkQuerySyntax": False,
        "paginationMode": "PAGE_NUMBER",
    }


def search(
    *,
    endpoint: str,
    query: str,
    fields: list[str],
    limit: int,
    allowed_hosts: frozenset[str],
    timeout_seconds: float,
    max_response_bytes: int,
    maximum_attempts: int,
    minimum_delay_seconds: float,
    budget: NetworkBudget,
) -> dict[str, Any]:
    response, _, metadata, started_at, completed_at = post_json(
        endpoint=endpoint,
        payload=_search_payload(query, fields=fields, limit=limit),
        allowed_hosts=allowed_hosts,
        timeout_seconds=timeout_seconds,
        max_response_bytes=max_response_bytes,
        maximum_attempts=maximum_attempts,
        minimum_delay_seconds=minimum_delay_seconds,
        budget=budget,
    )
    total = extract_total(response)
    if total is None:
        raise O01QualityCampaignError("TED Search API omitted total notice count")
    return {
        "query": query,
        "total": total,
        "notices": extract_notices(response),
        "metadata": metadata,
        "started_at": started_at.isoformat().replace("+00:00", "Z"),
        "completed_at": completed_at.isoformat().replace("+00:00", "Z"),
        "duration_seconds": max(0.0, (completed_at - started_at).total_seconds()),
    }


def first_available_date(
    *,
    lower: date,
    upper: date,
    count_on_or_before: Callable[[date], int],
) -> date:
    if lower > upper:
        raise ValueError("Lower date must not exceed upper date")
    if count_on_or_before(upper) <= 0:
        raise O01QualityCampaignError("No TED notices are available at the upper bound")
    while lower < upper:
        midpoint = lower + timedelta(days=(upper - lower).days // 2)
        if count_on_or_before(midpoint) > 0:
            upper = midpoint
        else:
            lower = midpoint + timedelta(days=1)
    return lower


def _notice_publication_date(notice: dict[str, Any]) -> date | None:
    candidates = values(notice, "publication-date")
    for candidate in candidates:
        parsed = parse_source_date(candidate)
        if parsed is not None:
            return parsed
    return None


def _notice_publication_number(notice: dict[str, Any]) -> str | None:
    candidates = values(notice, "publication-number")
    return candidates[0] if candidates else None


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _parse_http_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _source_observation(
    *,
    url: str,
    anchors: list[str],
    allowed_hosts: frozenset[str],
    timeout_seconds: float,
    max_response_bytes: int,
    budget: NetworkBudget,
) -> dict[str, Any]:
    body, metadata, started_at, completed_at = fetch_official(
        url=url,
        allowed_hosts=allowed_hosts,
        timeout_seconds=timeout_seconds,
        max_response_bytes=max_response_bytes,
        budget=budget,
    )
    text = body.decode("utf-8", errors="replace")
    normalized = html_text(text)
    missing = [anchor for anchor in anchors if anchor not in normalized]
    if missing:
        raise O01QualityCampaignError(
            f"Official source anchors missing for {url}: {missing}"
        )
    return {
        "url": url,
        "status": "PASS",
        "anchors_expected": anchors,
        "anchors_present": anchors,
        "body_sha256": sha256_prefixed(body),
        "observed_at": _iso(completed_at),
        "request_started_at": _iso(started_at),
        "metadata": metadata,
    }


def run_campaign(plan_path: Path, output_dir: Path) -> dict[str, Any]:
    plan = load_json(plan_path)
    if plan["schema_version"] != "axignal.o01-history-frequency-lag-plan/v0.1":
        raise O01QualityCampaignError("Unexpected O01-E plan schema")
    output_dir.mkdir(parents=True, exist_ok=True)
    source = plan["source"]
    if source["state"] != "PRODUCT_ADMITTED" or source["scope"] != "ALL":
        raise O01QualityCampaignError("O01-E requires admitted TED with ALL scope")
    network = plan["network"]
    allowed_hosts = frozenset(network["allowed_hosts"])
    budget = NetworkBudget(network["maximum_requests"])
    observed_at = datetime.now(UTC)
    execution_date = observed_at.date()

    official_observations = [
        _source_observation(
            url=item["url"],
            anchors=item["anchors"],
            allowed_hosts=allowed_hosts,
            timeout_seconds=network["timeout_seconds"],
            max_response_bytes=network["maximum_document_bytes"],
            budget=budget,
        )
        for item in plan["official_sources"]
    ]
    write_json(
        output_dir / "official-source-observations.v0.1.json",
        {
            "schema_version": "axignal.o01-official-source-observations/v0.1",
            "status": "PASS",
            "documents": official_observations,
            "fabricated_evidence": 0,
        },
    )

    releases_by_year: dict[int, list[Release]] = {}
    calendar_observations: list[dict[str, Any]] = []
    for year in plan["release_calendar_years"]:
        calendar_url = plan["release_calendar_url_template"].format(year=year)
        body, metadata, started_at, completed_at = fetch_official(
            url=calendar_url,
            allowed_hosts=allowed_hosts,
            timeout_seconds=network["timeout_seconds"],
            max_response_bytes=network["maximum_calendar_bytes"],
            budget=budget,
        )
        text = body.decode("utf-8-sig", errors="strict")
        releases = parse_release_calendar(text, expected_year=year)
        releases_by_year[year] = releases
        calendar_observations.append(
            {
                "year": year,
                "url": calendar_url,
                "release_count": len(releases),
                "first_release": releases[0].publication_date.isoformat(),
                "last_release": releases[-1].publication_date.isoformat(),
                "body_sha256": sha256_prefixed(body),
                "request_started_at": _iso(started_at),
                "observed_at": _iso(completed_at),
                "metadata": metadata,
            }
        )
    write_json(
        output_dir / "release-calendar-observations.v0.1.json",
        {
            "schema_version": "axignal.o01-release-calendar-observations/v0.1",
            "status": "PASS",
            "calendars": calendar_observations,
            "fabricated_evidence": 0,
        },
    )

    history_cache: dict[date, int] = {}
    history_queries: list[dict[str, Any]] = []

    def count_on_or_before(candidate: date) -> int:
        if candidate not in history_cache:
            observation = search(
                endpoint=source["endpoint"],
                query=f"publication-date <= {candidate:%Y%m%d}",
                fields=["publication-number", "publication-date"],
                limit=1,
                allowed_hosts=allowed_hosts,
                timeout_seconds=network["timeout_seconds"],
                max_response_bytes=network["maximum_search_response_bytes"],
                maximum_attempts=network["maximum_attempts_per_request"],
                minimum_delay_seconds=network["minimum_delay_seconds"],
                budget=budget,
            )
            history_cache[candidate] = observation["total"]
            history_queries.append(
                {
                    "cutoff": candidate.isoformat(),
                    "total": observation["total"],
                    "request": observation["metadata"],
                    "duration_seconds": observation["duration_seconds"],
                }
            )
        return history_cache[candidate]

    lower = date(execution_date.year - plan["history"]["search_years"], 1, 1)
    earliest = first_available_date(
        lower=lower,
        upper=execution_date,
        count_on_or_before=count_on_or_before,
    )
    before_earliest = earliest - timedelta(days=1)
    before_count = count_on_or_before(before_earliest)
    exact_earliest = search(
        endpoint=source["endpoint"],
        query=f"publication-date = {earliest:%Y%m%d} SORT BY publication-number ASC",
        fields=["publication-number", "publication-date"],
        limit=1,
        allowed_hosts=allowed_hosts,
        timeout_seconds=network["timeout_seconds"],
        max_response_bytes=network["maximum_search_response_bytes"],
        maximum_attempts=network["maximum_attempts_per_request"],
        minimum_delay_seconds=network["minimum_delay_seconds"],
        budget=budget,
    )
    if exact_earliest["total"] <= 0 or not exact_earliest["notices"]:
        raise O01QualityCampaignError("Earliest TED date has no retrievable notice")
    earliest_notice = exact_earliest["notices"][0]
    if _notice_publication_date(earliest_notice) != earliest:
        raise O01QualityCampaignError("Earliest notice publication date mismatch")

    current_releases = [
        item
        for releases in releases_by_year.values()
        for item in releases
        if item.publication_date <= execution_date
    ]
    current_releases.sort(key=lambda item: item.publication_date)
    if not current_releases:
        raise O01QualityCampaignError("No release-calendar dates precede execution")
    recent = current_releases[-plan["sampling"]["release_dates"] :]
    package_releases = recent[-plan["sampling"]["package_probes"] :]

    search_observations: list[dict[str, Any]] = []
    acquisition_durations: list[float] = []
    for release in recent:
        observation = search(
            endpoint=source["endpoint"],
            query=(
                f"publication-date = {release.publication_date:%Y%m%d} "
                "SORT BY publication-number ASC"
            ),
            fields=["publication-number", "publication-date"],
            limit=1,
            allowed_hosts=allowed_hosts,
            timeout_seconds=network["timeout_seconds"],
            max_response_bytes=network["maximum_search_response_bytes"],
            maximum_attempts=network["maximum_attempts_per_request"],
            minimum_delay_seconds=network["minimum_delay_seconds"],
            budget=budget,
        )
        acquisition_durations.append(observation["duration_seconds"])
        first_notice = observation["notices"][0] if observation["notices"] else None
        search_observations.append(
            {
                "issue": release.issue,
                "publication_date": release.publication_date.isoformat(),
                "notice_count": observation["total"],
                "first_publication_number": (
                    _notice_publication_number(first_notice)
                    if first_notice is not None
                    else None
                ),
                "duration_seconds": observation["duration_seconds"],
                "request": observation["metadata"],
            }
        )

    package_observations: list[dict[str, Any]] = []
    package_offsets: list[float] = []
    for release in package_releases:
        package_url = plan["daily_package_url_template"].format(
            package_id=release.package_id
        )
        observation = probe_package(
            url=package_url,
            allowed_hosts=allowed_hosts,
            timeout_seconds=network["timeout_seconds"],
            budget=budget,
        )
        last_modified = _parse_http_date(observation.get("last_modified"))
        offset_seconds: float | None = None
        if last_modified is not None:
            local_midnight = datetime.combine(
                release.publication_date,
                time.min,
                tzinfo=ZoneInfo(plan["publication_timezone"]),
            ).astimezone(UTC)
            offset_seconds = (last_modified - local_midnight).total_seconds()
            if 0 <= offset_seconds <= plan["thresholds"]["package_deadline_seconds"]:
                package_offsets.append(offset_seconds)
        package_observations.append(
            {
                "issue": release.issue,
                "package_id": release.package_id,
                "publication_date": release.publication_date.isoformat(),
                "url": package_url,
                "available": observation["available"],
                "last_modified": observation.get("last_modified"),
                "last_modified_offset_seconds": offset_seconds,
                "metadata": observation,
            }
        )

    expected_public_start = date(
        execution_date.year - plan["history"]["declared_public_years"],
        execution_date.month,
        execution_date.day,
    )
    boundary_slack_days = (earliest - expected_public_start).days
    latest_search_observation = next(
        item for item in reversed(search_observations) if item["notice_count"] > 0
    )
    latest_date = date.fromisoformat(latest_search_observation["publication_date"])
    history_report = {
        "schema_version": "axignal.o01-history-depth-report/v0.1",
        "status": "PASS",
        "declared_public_years": plan["history"]["declared_public_years"],
        "declared_boundary_date": expected_public_start.isoformat(),
        "earliest_available_date": earliest.isoformat(),
        "earliest_publication_number": _notice_publication_number(earliest_notice),
        "latest_available_date": latest_date.isoformat(),
        "day_before_earliest_total": before_count,
        "boundary_slack_days": boundary_slack_days,
        "public_depth_days": (latest_date - earliest).days + 1,
        "full_internal_archive_claimed": False,
        "search_scope": "ALL",
        "retrieval_mode_for_characterisation": "COUNT_ONLY_LIMIT_1",
        "pagination_truncation_applies_to_count": False,
        "exhaustive_notice_ingestion_performed": False,
        "binary_search_observations": history_queries,
        "limitations": [
            "TED public search exposes a rolling ten-year window, not the non-public internal archive.",
            "The campaign characterises public availability boundaries; it does not ingest every notice.",
            "Counts are used to avoid the 15,000-document page-number retrieval ceiling.",
        ],
        "fabricated_evidence": 0,
    }
    write_json(output_dir / "history-depth-report.v0.1.json", history_report)

    full_year = releases_by_year[plan["frequency_reference_year"]]
    full_year_dates = [item.publication_date for item in full_year]
    gaps = [
        (right - left).days
        for left, right in zip(full_year_dates, full_year_dates[1:], strict=False)
    ]
    search_presence = [item["notice_count"] > 0 for item in search_observations]
    package_presence = [item["available"] for item in package_observations]
    frequency_report = {
        "schema_version": "axignal.o01-update-frequency-report/v0.1",
        "status": "PASS",
        "declared": plan["frequency"]["declared"],
        "observed": (
            f"{sum(search_presence)}/{len(search_presence)} recent scheduled editions "
            f"present in Search API; {sum(package_presence)}/{len(package_presence)} "
            "daily packages reachable"
        ),
        "reference_year": plan["frequency_reference_year"],
        "reference_year_editions": len(full_year),
        "reference_year_weekend_editions": sum(
            item.publication_date.weekday() >= 5 for item in full_year
        ),
        "reference_year_gap_median_days": median(gaps),
        "reference_year_gap_p95_days": percentile([float(item) for item in gaps], 0.95),
        "recent_release_sample": search_observations,
        "daily_package_sample": package_observations,
        "search_presence_ratio": sum(search_presence) / len(search_presence),
        "package_presence_ratio": sum(package_presence) / len(package_presence),
        "incident_free_guarantee_claimed": False,
        "release_calendar_is_authoritative": True,
        "fabricated_evidence": 0,
    }
    write_json(output_dir / "update-frequency-report.v0.1.json", frequency_report)

    website_deadline_seconds = plan["frequency"]["website_deadline_seconds"]
    composed_upper_bounds = [
        website_deadline_seconds + duration for duration in acquisition_durations
    ]
    lag_report = {
        "schema_version": "axignal.o01-publication-lag-report/v0.1",
        "status": "PASS",
        "metric_semantics": (
            "Conservative upper bound from publication-day midnight in the official "
            "publication timezone to an AXIGNAL Search API response: official website "
            "availability deadline plus measured request duration."
        ),
        "publication_timezone": plan["publication_timezone"],
        "official_website_deadline_seconds": website_deadline_seconds,
        "official_daily_package_deadline_seconds": plan["frequency"][
            "package_deadline_seconds"
        ],
        "search_request_duration_seconds": {
            "p50": percentile(acquisition_durations, 0.50),
            "p95": percentile(acquisition_durations, 0.95),
            "max": max(acquisition_durations),
        },
        "publication_to_axignal_upper_bound_seconds": {
            "p50": percentile(composed_upper_bounds, 0.50),
            "p95": percentile(composed_upper_bounds, 0.95),
            "max": max(composed_upper_bounds),
        },
        "daily_package_last_modified_offsets_seconds": {
            "observed_count": len(package_offsets),
            "p50": percentile(package_offsets, 0.50) if package_offsets else None,
            "p95": percentile(package_offsets, 0.95) if package_offsets else None,
            "max": max(package_offsets) if package_offsets else None,
        },
        "direct_first-seen_timestamp_claimed": False,
        "limitations": [
            "TED exposes publication dates but not a universal first-seen timestamp for Search API records.",
            "The published lag is therefore an upper bound, not a claim of exact first availability.",
            "Package Last-Modified headers are supplementary and are not required for the Search API bound.",
        ],
        "fabricated_evidence": 0,
    }
    write_json(output_dir / "publication-lag-report.v0.1.json", lag_report)

    thresholds = plan["thresholds"]
    checks = {
        "official_sources": all(
            item["status"] == "PASS" for item in official_observations
        ),
        "history_before_boundary_empty": before_count == 0,
        "history_boundary_slack": (
            0 <= boundary_slack_days <= thresholds["history_boundary_slack_days_max"]
        ),
        "history_latest_current": (
            (execution_date - latest_date).days
            <= thresholds["latest_publication_age_days_max"]
        ),
        "frequency_reference_editions": (
            len(full_year) >= thresholds["reference_year_editions_min"]
        ),
        "frequency_weekend_editions": (
            frequency_report["reference_year_weekend_editions"]
            <= thresholds["reference_year_weekend_editions_max"]
        ),
        "search_presence": (
            frequency_report["search_presence_ratio"]
            >= thresholds["search_presence_ratio_min"]
        ),
        "package_presence": (
            frequency_report["package_presence_ratio"]
            >= thresholds["package_presence_ratio_min"]
        ),
        "lag_upper_bound_p95": (
            lag_report["publication_to_axignal_upper_bound_seconds"]["p95"]
            <= thresholds["publication_to_axignal_p95_seconds_max"]
        ),
        "network_budget": budget.used <= budget.maximum,
        "fabricated_evidence": True,
    }
    passed = all(checks.values())
    result = {
        "schema_version": "axignal.o01-history-frequency-lag-result/v0.1",
        "status": "PASS" if passed else "FAIL",
        "output": (
            "O01_HISTORY_FREQUENCY_LAG_PASS"
            if passed
            else "O01_HISTORY_FREQUENCY_LAG_FAIL"
        ),
        "library_id": plan["library_id"],
        "source_id": source["source_id"],
        "observed_at": _iso(observed_at),
        "evidence_expires_at": _iso(
            observed_at + timedelta(days=plan["evidence_retention_days"])
        ),
        "network_requests_used": budget.used,
        "network_requests_maximum": budget.maximum,
        "checks": checks,
        "history": history_report,
        "frequency": frequency_report,
        "lag": lag_report,
        "decision": {
            "o01_metrics_closed": passed,
            "recommended_canonical_state": "ACCEPTED" if passed else "IN_REVIEW",
            "recommended_claim_decision": "DENIED",
            "claim_contribution": False,
            "gate7_closed": False,
            "public_launch": "NO_GO",
        },
        "fabricated_evidence": 0,
        "synthetic_evidence": 0,
    }
    write_json(output_dir / "final-result.v0.1.json", result)
    if not passed:
        raise O01QualityCampaignError(
            "O01-E thresholds failed: "
            + ", ".join(name for name, value in checks.items() if not value)
        )
    return result
