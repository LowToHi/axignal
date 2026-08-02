from __future__ import annotations

import math
from typing import Any

from .o01_quality_common import (
    CORE_FIELDS,
    CPV_RE,
    CURRENCY_RE,
    NUTS_RE,
    PUBLICATION_NUMBER_RE,
    NormalizedNotice,
    normalize_text,
    normalized_code,
    parse_amount,
    parse_deadline,
    publication_number,
    values,
)


def percentile(values_: list[float], percentile_: float) -> float | None:
    if not values_:
        return None
    ordered = sorted(float(item) for item in values_)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * percentile_
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def metric_summary(values_: list[float], *, unit: str) -> dict[str, Any]:
    return {
        "p50": percentile(values_, 0.50),
        "p95": percentile(values_, 0.95),
        "maximum": max(values_) if values_ else None,
        "minimum": min(values_) if values_ else None,
        "sample_count": len(values_),
        "unit": unit,
    }


def ratio(numerator: int, denominator: int) -> dict[str, Any]:
    return {
        "value": numerator / denominator if denominator else None,
        "numerator": numerator,
        "denominator": denominator,
    }


def quality_report(
    *,
    selected_source_records: list[dict[str, Any]],
    normalized_records: list[NormalizedNotice],
    all_candidate_records: list[dict[str, Any]],
    contact_classification: dict[str, Any],
) -> dict[str, Any]:
    sample_count = len(selected_source_records)
    normalized_by_id = {
        item.publication_number: item for item in normalized_records
    }

    identifier_valid = sum(
        1
        for record in selected_source_records
        if (notice_id := publication_number(record))
        and PUBLICATION_NUMBER_RE.fullmatch(notice_id)
    )
    title_present = sum(
        bool(values(record, "notice-title")) for record in selected_source_records
    )

    buyer_observed = 0
    buyer_valid = 0
    deadline_observed = 0
    deadline_valid = 0
    amount_observed = 0
    amount_valid = 0
    currency_observed = 0
    currency_valid = 0
    cpv_observed = 0
    cpv_valid = 0
    nuts_observed = 0
    nuts_valid = 0
    lots_present = 0
    missing_cells = 0

    for record in selected_source_records:
        for field in CORE_FIELDS:
            if not values(record, field):
                missing_cells += 1
        buyer_values = values(record, "buyer-name")
        buyer_observed += len(buyer_values)
        buyer_valid += sum(bool(normalize_text(item)) for item in buyer_values)

        deadline_values = values(record, "deadline")
        deadline_observed += len(deadline_values)
        deadline_valid += sum(
            parse_deadline(item) is not None for item in deadline_values
        )

        amount_values = values(record, "estimated-value-proc")
        amount_observed += len(amount_values)
        amount_valid += sum(parse_amount(item) is not None for item in amount_values)

        currency_values = values(record, "estimated-value-cur-proc")
        currency_observed += len(currency_values)
        currency_valid += sum(
            bool(CURRENCY_RE.fullmatch(normalized_code(item)))
            for item in currency_values
        )

        cpv_values = values(record, "classification-cpv")
        cpv_observed += len(cpv_values)
        cpv_valid += sum(
            bool(CPV_RE.fullmatch(normalized_code(item))) for item in cpv_values
        )

        nuts_values = values(record, "place-of-performance-subdiv-proc")
        nuts_observed += len(nuts_values)
        nuts_valid += sum(
            bool(NUTS_RE.fullmatch(normalized_code(item))) for item in nuts_values
        )

        lots_present += bool(values(record, "identifier-lot"))

    candidate_ids = [publication_number(record) for record in all_candidate_records]
    candidate_ids = [item for item in candidate_ids if item]
    duplicate_count = len(candidate_ids) - len(set(candidate_ids))
    unparseable_count = sample_count - len(normalized_records)

    return {
        "schema_version": "axignal.o01-quality-report/v0.1",
        "sample_count": sample_count,
        "normalized_count": len(normalized_records),
        "metrics": {
            "identifier_accuracy": ratio(identifier_valid, sample_count),
            "title_completeness": ratio(title_present, sample_count),
            "buyer_accuracy": ratio(buyer_valid, buyer_observed),
            "deadline_accuracy": ratio(deadline_valid, deadline_observed),
            "amount_accuracy": ratio(amount_valid, amount_observed),
            "currency_accuracy": ratio(currency_valid, currency_observed),
            "CPV_accuracy": ratio(cpv_valid, cpv_observed),
            "NUTS_accuracy": ratio(nuts_valid, nuts_observed),
            "lot_completeness": ratio(lots_present, sample_count),
            "contact_channel_classification_accuracy": contact_classification,
            "duplicate_rate": ratio(duplicate_count, len(candidate_ids)),
            "unparseable_rate": ratio(unparseable_count, sample_count),
            "missing_field_rate": ratio(
                missing_cells,
                sample_count * len(CORE_FIELDS),
            ),
        },
        "definitions": {
            "accuracy": (
                "Deterministic AXIGNAL transformation or policy-conformance fidelity "
                "against the TED Search API projected source fields; not an assertion "
                "that the publisher's underlying facts are legally or factually "
                "correct."
            ),
            "title_completeness": (
                "At least one source-projected title value is present."
            ),
            "lot_completeness": (
                "At least one source-projected identifier-lot value is present; not "
                "every notice type is expected to expose a lot."
            ),
            "contact_channel_classification_accuracy": (
                "Agreement of the frozen reference classifier with the O01 policy "
                "matrix. Raw contact values are processed ephemerally and never "
                "persisted."
            ),
        },
        "source_record_digests": sorted(
            item.source_record_sha256 for item in normalized_by_id.values()
        ),
    }
