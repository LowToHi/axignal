from datetime import UTC, datetime, timedelta

from axignal_api.organic_policy import (
    IndexabilityCandidate,
    evaluate_indexability,
)

NOW = datetime(2026, 7, 31, 18, 0, tzinfo=UTC)


def candidate(**overrides: object) -> IndexabilityCandidate:
    values: dict[str, object] = {
        "page_kind": "TENDER_HUB",
        "active_opportunity_count": 28,
        "unique_buyer_count": 9,
        "demand_score": 0.82,
        "data_quality_score": 0.91,
        "uniqueness_score": 0.78,
        "source_coverage_score": 0.86,
        "content_depth_score": 0.88,
        "freshness_at": NOW - timedelta(hours=2),
        "is_synthetic": False,
    }
    values.update(overrides)
    return IndexabilityCandidate(**values)  # type: ignore[arg-type]


def test_high_quality_candidate_is_indexable() -> None:
    result = evaluate_indexability(candidate(), now=NOW)
    assert result.decision == "INDEX"
    assert result.reason_codes == ()
    assert result.score == 0.85


def test_stale_candidate_is_held() -> None:
    result = evaluate_indexability(
        candidate(freshness_at=NOW - timedelta(hours=49)),
        now=NOW,
    )
    assert result.decision == "HOLD"
    assert "STALE_DATA" in result.reason_codes


def test_synthetic_candidate_is_noindex() -> None:
    result = evaluate_indexability(candidate(is_synthetic=True), now=NOW)
    assert result.decision == "NOINDEX"
    assert "SYNTHETIC_DATA" in result.reason_codes


def test_inventory_and_quality_fail_closed() -> None:
    result = evaluate_indexability(
        candidate(
            active_opportunity_count=2,
            unique_buyer_count=1,
            data_quality_score=0.5,
            source_coverage_score=0.4,
        ),
        now=NOW,
    )
    assert result.decision == "NOINDEX"
    assert set(result.reason_codes) >= {
        "INSUFFICIENT_INVENTORY",
        "INSUFFICIENT_BUYER_DIVERSITY",
        "LOW_DATA_QUALITY",
        "LOW_SOURCE_COVERAGE",
    }
