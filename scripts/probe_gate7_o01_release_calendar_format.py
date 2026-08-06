from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from axignal_api.o01_history_frequency_lag import fetch_official
from axignal_api.o01_quality_http import NetworkBudget

ALLOWED_HOSTS = frozenset({"ted.europa.eu"})
YEARS = (2025, 2026)
URL_TEMPLATE = (
    "https://ted.europa.eu/en/release-calendar/-/download/file/XLS/{year}"
)
OLE_MAGIC = bytes.fromhex("d0cf11e0a1b11ae1")
ZIP_MAGIC = b"PK\x03\x04"


def classify_calendar(body: bytes, content_type: str | None) -> dict[str, Any]:
    prefix = body[:16]
    normalized_type = (content_type or "").casefold()
    is_zip = body.startswith(ZIP_MAGIC)
    is_ole = body.startswith(OLE_MAGIC)
    is_xml = body.lstrip().startswith((b"<?xml", b"<Workbook"))
    is_html = "text/html" in normalized_type or body.lstrip().lower().startswith(
        (b"<!doctype html", b"<html")
    )
    format_name = (
        "XLSX_ZIP"
        if is_zip
        else "XLS_OLE2"
        if is_ole
        else "SPREADSHEET_XML"
        if is_xml
        else "HTML"
        if is_html
        else "UNKNOWN"
    )
    return {
        "format": format_name,
        "content_type": content_type,
        "response_bytes": len(body),
        "first_16_bytes_hex": prefix.hex(),
        "is_zip": is_zip,
        "is_ole2": is_ole,
        "is_spreadsheet_xml": is_xml,
        "is_html": is_html,
        "raw_body_retained": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    budget = NetworkBudget(2)
    observations: list[dict[str, Any]] = []
    for year in YEARS:
        body, metadata, started_at, completed_at = fetch_official(
            url=URL_TEMPLATE.format(year=year),
            allowed_hosts=ALLOWED_HOSTS,
            timeout_seconds=30,
            max_response_bytes=2_097_152,
            budget=budget,
        )
        observations.append(
            {
                "year": year,
                "url": URL_TEMPLATE.format(year=year),
                "request_started_at": started_at.isoformat().replace("+00:00", "Z"),
                "request_completed_at": completed_at.isoformat().replace(
                    "+00:00", "Z"
                ),
                "response_sha256": metadata["response_sha256"],
                "metadata": metadata,
                **classify_calendar(body, metadata.get("content_type")),
            }
        )
    result = {
        "schema_version": "axignal.o01-release-calendar-format-probe/v0.1",
        "status": "PASS",
        "output": "O01_RELEASE_CALENDAR_FORMAT_IDENTIFIED",
        "network_requests_used": budget.used,
        "network_requests_maximum": budget.maximum,
        "observations": observations,
        "raw_body_retained": False,
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
