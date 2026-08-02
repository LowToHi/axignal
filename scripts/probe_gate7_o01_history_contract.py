from __future__ import annotations

import argparse
import hashlib
import json
import ssl
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any
from urllib.parse import urlparse

import xlrd

from axignal_api.o01_history_frequency_lag import fetch_official
from axignal_api.o01_official_baseline import (
    PinnedHTTPSConnection,
    resolve_public_addresses,
    select_address,
    validate_official_url,
)
from axignal_api.o01_quality_http import NetworkBudget

OLE2_MAGIC = bytes.fromhex("d0cf11e0a1b11ae1")
CALENDAR_TEMPLATE = (
    "https://ted.europa.eu/en/release-calendar/-/download/file/XLS/{year}"
)
SEARCH_ENDPOINT = "https://api.ted.europa.eu/v3/notices/search"
ALLOWED_HOSTS = frozenset({"api.ted.europa.eu", "ted.europa.eu"})


def sha256_prefixed(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _cell_summary(cell: xlrd.sheet.Cell, *, datemode: int) -> dict[str, Any] | None:
    if cell.ctype in {xlrd.XL_CELL_EMPTY, xlrd.XL_CELL_BLANK}:
        return None
    summary: dict[str, Any] = {"ctype": int(cell.ctype)}
    if cell.ctype == xlrd.XL_CELL_DATE:
        summary["date"] = xlrd.xldate_as_datetime(cell.value, datemode).isoformat()
        summary["serial"] = cell.value
    elif cell.ctype == xlrd.XL_CELL_NUMBER:
        summary["number"] = cell.value
    elif cell.ctype == xlrd.XL_CELL_BOOLEAN:
        summary["boolean"] = bool(cell.value)
    elif cell.ctype == xlrd.XL_CELL_ERROR:
        summary["error_code"] = int(cell.value)
    else:
        summary["text"] = str(cell.value)[:160]
    return summary


def inspect_workbook(body: bytes, *, year: int) -> dict[str, Any]:
    if not body.startswith(OLE2_MAGIC):
        raise RuntimeError(f"Calendar {year} is not OLE2")
    workbook = xlrd.open_workbook(
        file_contents=body,
        formatting_info=False,
        on_demand=True,
    )
    sheets: list[dict[str, Any]] = []
    all_dates: list[str] = []
    try:
        for sheet in workbook.sheets():
            rows: list[dict[str, Any]] = []
            for row_index in range(sheet.nrows):
                cells: list[dict[str, Any]] = []
                for column_index, cell in enumerate(sheet.row(row_index)):
                    summary = _cell_summary(cell, datemode=workbook.datemode)
                    if summary is None:
                        continue
                    if "date" in summary:
                        all_dates.append(summary["date"])
                    cells.append({"column": column_index, **summary})
                if cells:
                    rows.append({"row": row_index, "cells": cells})
            sheets.append(
                {
                    "name": sheet.name,
                    "nrows": sheet.nrows,
                    "ncols": sheet.ncols,
                    "non_empty_rows": rows,
                }
            )
    finally:
        workbook.release_resources()
    return {
        "year_url_parameter": year,
        "format": "XLS_OLE2",
        "magic_hex": body[:8].hex(),
        "body_sha256": sha256_prefixed(body),
        "body_bytes": len(body),
        "body_retained": False,
        "sheet_count": len(sheets),
        "sheets": sheets,
        "date_cell_count": len(all_dates),
        "date_cells": sorted(set(all_dates)),
    }


def _safe_error(value: Any) -> Any:
    if isinstance(value, dict):
        allowed = {
            "code",
            "error",
            "errors",
            "field",
            "location",
            "message",
            "reason",
            "status",
            "title",
            "type",
        }
        return {
            str(key): _safe_error(item)
            for key, item in value.items()
            if str(key).casefold() in allowed
        }
    if isinstance(value, list):
        return [_safe_error(item) for item in value[:20]]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value if not isinstance(value, str) else value[:1000]
    return str(value)[:1000]


def probe_search(
    *,
    query: str,
    pagination_mode: str,
    budget: NetworkBudget,
) -> dict[str, Any]:
    parsed = validate_official_url(SEARCH_ENDPOINT, allowed_hosts=ALLOWED_HOSTS)
    host = parsed.hostname or ""
    port = parsed.port or 443
    addresses = resolve_public_addresses(host, port)
    selected = select_address(addresses)
    payload = {
        "query": query,
        "fields": ["publication-number", "publication-date"],
        "page": 1,
        "limit": 1,
        "scope": "ALL",
        "checkQuerySyntax": False,
        "paginationMode": pagination_mode,
    }
    encoded = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    budget.consume()
    connection = PinnedHTTPSConnection(
        host=host,
        port=port,
        selected_address=selected,
        timeout=30,
        context=ssl.create_default_context(),
    )
    started_at = datetime.now(UTC)
    started_clock = perf_counter()
    try:
        connection.request(
            "POST",
            parsed.path,
            body=encoded,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Content-Length": str(len(encoded)),
                "User-Agent": "AXIGNAL-O01-E-Diagnostic/1.0",
                "Connection": "close",
            },
        )
        response = connection.getresponse()
        body = response.read(2_097_153)
        if len(body) > 2_097_152:
            raise RuntimeError("Search diagnostic response exceeded 2 MiB")
        completed_at = datetime.now(UTC)
        try:
            decoded = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            decoded = None
        result: dict[str, Any] = {
            "query": query,
            "pagination_mode": pagination_mode,
            "http_status": response.status,
            "response_sha256": sha256_prefixed(body),
            "response_bytes": len(body),
            "started_at": _iso(started_at),
            "completed_at": _iso(completed_at),
            "duration_seconds": max(0.0, perf_counter() - started_clock),
            "resolved_addresses": list(addresses),
            "selected_address": selected,
            "raw_response_retained": False,
        }
        if response.status == 200 and isinstance(decoded, dict):
            notices = decoded.get("notices") or decoded.get("results") or []
            first = notices[0] if isinstance(notices, list) and notices else None
            result.update(
                {
                    "success": True,
                    "total": decoded.get("totalNoticeCount", decoded.get("total")),
                    "iteration_token_present": bool(
                        decoded.get("iterationNextToken")
                        or decoded.get("iterationToken")
                    ),
                    "first_notice": first if isinstance(first, dict) else None,
                }
            )
        else:
            result.update(
                {
                    "success": False,
                    "sanitised_error": _safe_error(decoded),
                    "body_text_prefix": (
                        body.decode("utf-8", errors="replace")[:1000]
                        if decoded is None
                        else None
                    ),
                }
            )
        return result
    finally:
        connection.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    budget = NetworkBudget(6)

    calendars: list[dict[str, Any]] = []
    for year in (2025, 2026):
        body, metadata, started_at, completed_at = fetch_official(
            url=CALENDAR_TEMPLATE.format(year=year),
            allowed_hosts=ALLOWED_HOSTS,
            timeout_seconds=30,
            max_response_bytes=2_097_152,
            budget=budget,
        )
        calendars.append(
            {
                **inspect_workbook(body, year=year),
                "request_started_at": _iso(started_at),
                "request_completed_at": _iso(completed_at),
                "http_metadata": metadata,
            }
        )
        del body

    probes = [
        probe_search(
            query=(
                "publication-date >= 20260701 AND publication-date <= 20260731 "
                "SORT BY publication-number ASC"
            ),
            pagination_mode="PAGE_NUMBER",
            budget=budget,
        ),
        probe_search(
            query=(
                "publication-date >= 20150101 AND publication-date <= 20260802 "
                "SORT BY publication-number ASC"
            ),
            pagination_mode="PAGE_NUMBER",
            budget=budget,
        ),
        probe_search(
            query=(
                "publication-date >= 20150101 AND publication-date <= 20260802 "
                "SORT BY publication-number ASC"
            ),
            pagination_mode="ITERATION",
            budget=budget,
        ),
        probe_search(
            query=(
                "publication-date >= 20160101 AND publication-date <= 20161231 "
                "SORT BY publication-number ASC"
            ),
            pagination_mode="ITERATION",
            budget=budget,
        ),
    ]
    result = {
        "schema_version": "axignal.o01-history-contract-diagnostic/v0.1",
        "status": "PASS",
        "output": "O01_HISTORY_CONTRACT_DIAGNOSTIC_COMPLETE",
        "network_requests_used": budget.used,
        "network_requests_maximum": budget.maximum,
        "calendars": calendars,
        "search_probes": probes,
        "raw_calendar_bodies_retained": False,
        "raw_search_responses_retained": False,
        "claim_contribution": False,
        "gate7_closed": False,
        "public_launch": "NO_GO",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
