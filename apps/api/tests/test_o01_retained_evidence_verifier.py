from __future__ import annotations

import json
from pathlib import Path

import pytest

from verify_gate7_o01_retained_evidence_v8 import (
    VerificationError,
    verify_calendars,
    verify_query,
)


def _plan() -> dict:
    return {
        "expected_measurement": {
            "calendar_years": {
                "2025": {
                    "release_count": 252,
                    "first_issue": 1,
                    "last_issue": 252,
                    "first_release": "2025-01-02",
                    "last_release": "2025-12-31",
                },
                "2026": {
                    "release_count": 254,
                    "first_issue": 1,
                    "last_issue": 254,
                    "first_release": "2026-01-02",
                    "last_release": "2026-12-31",
                },
            }
        }
    }


def _calendar(year: int, count: int) -> dict:
    return {
        "year": year,
        "format": "XLS_OLE2_BIFF8",
        "magic_hex": "d0cf11e0a1b11ae1",
        "body_persisted": False,
        "release_count": count,
        "first_issue": 1,
        "last_issue": count,
        "first_release": f"{year}-01-02",
        "last_release": f"{year}-12-31",
        "metadata": {
            "http_status": 200,
            "response_bytes": 20992,
        },
    }


def _write_calendar_document(tmp_path: Path, calendars: list[dict]) -> None:
    document = {
        "schema_version": "axignal.o01-release-calendar-observations/v0.6",
        "status": "PASS",
        "parser": "xlrd==2.0.2",
        "parser_lock": "requirements/o01-xls.lock",
        "release_calendar_bodies_persisted": False,
        "fabricated_evidence": 0,
        "calendars": calendars,
    }
    (tmp_path / "release-calendar-observations.v0.1.json").write_text(
        json.dumps(document),
        encoding="utf-8",
    )


def test_completed_and_planned_calendar_counts_pass_without_255_rule(
    tmp_path: Path,
) -> None:
    _write_calendar_document(
        tmp_path,
        [_calendar(2025, 252), _calendar(2026, 254)],
    )
    calendars = verify_calendars(_plan(), tmp_path)
    assert calendars[2025]["release_count"] == 252
    assert calendars[2026]["release_count"] == 254


def test_non_contiguous_issue_sequence_fails(tmp_path: Path) -> None:
    broken = _calendar(2025, 252)
    broken["last_issue"] = 251
    _write_calendar_document(
        tmp_path,
        [broken, _calendar(2026, 254)],
    )
    with pytest.raises(VerificationError, match="Last issue drift: 2025"):
        verify_calendars(_plan(), tmp_path)


def test_wrong_observed_count_fails_instead_of_being_normalised(
    tmp_path: Path,
) -> None:
    _write_calendar_document(
        tmp_path,
        [_calendar(2025, 255), _calendar(2026, 254)],
    )
    with pytest.raises(VerificationError, match="Count drift: 2025"):
        verify_calendars(_plan(), tmp_path)


def test_canonical_closed_query_passes() -> None:
    verify_query("publication-date >= 20150101 AND publication-date <= 20160802")


def test_sort_clause_is_rejected() -> None:
    with pytest.raises(VerificationError, match="Forbidden SORT clause"):
        verify_query(
            "publication-date >= 20150101 AND publication-date <= 20160802 "
            "SORT BY publication-number"
        )
