from __future__ import annotations

from datetime import date

import pytest

from axignal_api.o01_history_frequency_lag_v2 import (
    bounded_date_query,
    first_available_date,
    html_text,
    parse_release_calendar,
    percentile,
)
from axignal_api.o01_quality_common import O01QualityCampaignError


def test_parse_release_calendar_accepts_semicolon_csv() -> None:
    text = "Issue;Publication date\nS 001/2025;02/01/2025\nS 002/2025;03/01/2025\n"
    releases = parse_release_calendar(text, expected_year=2025)
    assert [(item.issue, item.publication_date) for item in releases] == [
        (1, date(2025, 1, 2)),
        (2, date(2025, 1, 3)),
    ]
    assert releases[0].package_id == "202500001"


def test_parse_release_calendar_rejects_empty_or_wrong_year() -> None:
    with pytest.raises(O01QualityCampaignError):
        parse_release_calendar(
            "Issue;Publication date\nS 001/2024;02/01/2024\n",
            expected_year=2025,
        )


def test_bounded_date_query_uses_proven_canonical_interval() -> None:
    assert bounded_date_query(
        date(2015, 1, 1),
        date(2016, 8, 3),
    ) == (
        "publication-date >= 20150101 AND publication-date <= 20160803"
    )
    assert bounded_date_query(
        date(2026, 7, 31),
        date(2026, 7, 31),
        sort=True,
    ) == (
        "publication-date >= 20260731 AND publication-date <= 20260731 "
        "SORT BY publication-number ASC"
    )


def test_bounded_date_query_rejects_inverted_range() -> None:
    with pytest.raises(ValueError):
        bounded_date_query(date(2026, 8, 1), date(2026, 7, 31))


def test_first_available_date_is_exact_and_logarithmic() -> None:
    threshold = date(2016, 8, 3)
    calls: list[date] = []

    def count(candidate: date) -> int:
        calls.append(candidate)
        return 1 if candidate >= threshold else 0

    observed = first_available_date(
        lower=date(2016, 1, 1),
        upper=date(2017, 1, 1),
        count_on_or_before=count,
    )
    assert observed == threshold
    assert len(calls) <= 12


def test_first_available_date_fails_when_upper_bound_is_empty() -> None:
    with pytest.raises(O01QualityCampaignError):
        first_available_date(
            lower=date(2016, 1, 1),
            upper=date(2017, 1, 1),
            count_on_or_before=lambda _: 0,
        )


def test_percentile_interpolates_without_rounding() -> None:
    assert percentile([1.0, 2.0, 3.0, 4.0], 0.50) == 2.5
    assert percentile([1.0, 2.0, 3.0, 4.0], 0.95) == pytest.approx(3.85)


def test_html_text_normalises_markup_and_whitespace() -> None:
    assert html_text("<p>Daily <strong>edition</strong>\nMonday</p>") == (
        "Daily edition Monday"
    )
