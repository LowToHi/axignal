from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal

PageKind = Literal["TENDER_HUB", "MARKET_INTELLIGENCE", "TENDER_DETAIL"]
IndexabilityDecision = Literal["INDEX", "NOINDEX", "HOLD"]


@dataclass(frozen=True)
class IndexabilityCandidate:
    page_kind: PageKind
    active_opportunity_count: int
    unique_buyer_count: int
    demand_score: float
    data_quality_score: float
    uniqueness_score: float
    source_coverage_score: float
    content_depth_score: float
    freshness_at: datetime
    is_synthetic: bool = False


@dataclass(frozen=True)
class IndexabilityResult:
    decision: IndexabilityDecision
    reason_codes: tuple[str, ...]
    score: float
    policy_version: str = "indexability-gate@1.0.0"


MINIMUM_OPPORTUNITIES: dict[PageKind, int] = {
    "TENDER_HUB": 8,
    "MARKET_INTELLIGENCE": 12,
    "TENDER_DETAIL": 1,
}
MINIMUM_BUYERS: dict[PageKind, int] = {
    "TENDER_HUB": 3,
    "MARKET_INTELLIGENCE": 5,
    "TENDER_DETAIL": 1,
}


def evaluate_indexability(
    candidate: IndexabilityCandidate,
    *,
    now: datetime | None = None,
) -> IndexabilityResult:
    current = now or datetime.now(UTC)
    reasons: list[str] = []
    if candidate.is_synthetic:
        reasons.append("SYNTHETIC_DATA")
    if candidate.active_opportunity_count < MINIMUM_OPPORTUNITIES[candidate.page_kind]:
        reasons.append("INSUFFICIENT_INVENTORY")
    if candidate.unique_buyer_count < MINIMUM_BUYERS[candidate.page_kind]:
        reasons.append("INSUFFICIENT_BUYER_DIVERSITY")
    thresholds = (
        (candidate.demand_score, 0.55, "LOW_DEMAND"),
        (candidate.data_quality_score, 0.75, "LOW_DATA_QUALITY"),
        (candidate.uniqueness_score, 0.65, "LOW_UNIQUENESS"),
        (candidate.source_coverage_score, 0.70, "LOW_SOURCE_COVERAGE"),
        (candidate.content_depth_score, 0.70, "LOW_CONTENT_DEPTH"),
    )
    for value, threshold, reason in thresholds:
        if value < threshold:
            reasons.append(reason)
    if candidate.freshness_at < current - timedelta(hours=48):
        reasons.append("STALE_DATA")

    score = round(
        (
            candidate.demand_score
            + candidate.data_quality_score
            + candidate.uniqueness_score
            + candidate.source_coverage_score
            + candidate.content_depth_score
        )
        / 5,
        4,
    )
    if not reasons:
        decision: IndexabilityDecision = "INDEX"
    elif "STALE_DATA" in reasons and "SYNTHETIC_DATA" not in reasons:
        decision = "HOLD"
    else:
        decision = "NOINDEX"
    return IndexabilityResult(
        decision=decision,
        reason_codes=tuple(reasons),
        score=score,
    )
