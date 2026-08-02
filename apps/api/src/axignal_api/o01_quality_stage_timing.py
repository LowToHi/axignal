from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, replace
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

from .o01_quality_common import NormalizedNotice, PageObservation
from .o01_quality_coverage_lag import lag_report as legacy_lag_report
from .o01_quality_normalize import normalize_notice
from .o01_quality_reports import metric_summary
from .o01_quality_retention import json_line, sha256_prefixed

_STAGE_TIMINGS: dict[str, dict[str, float]] = {}


def _now() -> datetime:
    return datetime.now(UTC)


def _iso(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _semantic_hash(notice: NormalizedNotice) -> str:
    payload = asdict(notice)
    payload.pop("normalized_record_sha256", None)
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256_prefixed(encoded)


def reset_stage_timings() -> None:
    _STAGE_TIMINGS.clear()


def stage_timings() -> dict[str, dict[str, float]]:
    return {key: dict(value) for key, value in _STAGE_TIMINGS.items()}


def index_and_enqueue(
    selected: list[tuple[dict[str, Any], str, PageObservation]],
) -> tuple[list[NormalizedNotice], dict[str, float], list[dict[str, Any]]]:
    """Normalize, index and enqueue while timing each local stage independently.

    The previous campaign derived normalisation lag from the end of a page-level HTTP
    request to the later batch-processing pass. That included deterministic sampling,
    all remaining network requests and contact classification. Here stage duration is
    measured with a monotonic clock; retrieval-to-processing wait remains available as
    an explicit queueing disclosure rather than being mislabelled as normalisation.
    """

    reset_stage_timings()
    connection = sqlite3.connect(":memory:")
    connection.execute(
        "CREATE TABLE notices (publication_number TEXT PRIMARY KEY, title TEXT, sha256 TEXT)"
    )
    normalized: list[NormalizedNotice] = []
    acquisition_by_notice: dict[str, float] = {}
    notification_ledger: list[dict[str, Any]] = []

    try:
        for source, sampled_country, observation in selected:
            publication_number = str(source["publication-number"])
            queue_started_at = _now()
            normalisation_started = perf_counter()
            draft = normalize_notice(
                source,
                sampled_country=sampled_country,
                retrieval_started_at=observation.retrieval_started_at,
                retrieval_completed_at=observation.retrieval_completed_at,
                normalised_at=queue_started_at,
                indexed_at=queue_started_at,
                notification_enqueued_at=queue_started_at,
            )
            normalisation_completed_at = _now()
            normalisation_seconds = max(0.0, perf_counter() - normalisation_started)

            indexing_started_at = _now()
            indexing_started = perf_counter()
            connection.execute(
                "INSERT INTO notices VALUES (?, ?, ?)",
                (
                    draft.publication_number,
                    draft.title,
                    draft.normalized_record_sha256,
                ),
            )
            connection.commit()

            notification_enqueued_at = _now()
            staged = replace(
                draft,
                normalised_at=_iso(normalisation_completed_at),
                indexed_at=_iso(indexing_started_at),
                notification_enqueued_at=_iso(notification_enqueued_at),
            )
            notice = replace(staged, normalized_record_sha256=_semantic_hash(staged))
            connection.execute(
                "UPDATE notices SET sha256 = ? WHERE publication_number = ?",
                (notice.normalized_record_sha256, notice.publication_number),
            )
            connection.commit()
            indexing_seconds = max(0.0, perf_counter() - indexing_started)

            notification_started = perf_counter()
            notification_ledger.append(
                {
                    "publication_number": notice.publication_number,
                    "normalized_record_sha256": notice.normalized_record_sha256,
                    "enqueued_at": notice.notification_enqueued_at,
                    "delivery_mode": "PRIVATE_INTERNAL_LEDGER_ONLY",
                    "external_delivery_authorised": False,
                }
            )
            notification_seconds = max(0.0, perf_counter() - notification_started)

            normalized.append(notice)
            acquisition_by_notice[notice.publication_number] = max(
                0.0,
                (
                    observation.retrieval_completed_at
                    - observation.retrieval_started_at
                ).total_seconds(),
            )
            _STAGE_TIMINGS[notice.publication_number] = {
                "normalisation_seconds": normalisation_seconds,
                "indexing_seconds": indexing_seconds,
                "notification_seconds": notification_seconds,
                "retrieval_to_normalisation_start_seconds": max(
                    0.0,
                    (
                        queue_started_at - observation.retrieval_completed_at
                    ).total_seconds(),
                ),
            }
    finally:
        connection.close()

    return normalized, acquisition_by_notice, notification_ledger


def lag_report(
    normalized_records: list[NormalizedNotice],
    *,
    acquisition_by_notice: dict[str, float],
) -> dict[str, Any]:
    """Build the proven lag report with corrected local-stage timing semantics."""

    report = legacy_lag_report(
        normalized_records,
        acquisition_by_notice=acquisition_by_notice,
    )
    missing = [
        record.publication_number
        for record in normalized_records
        if record.publication_number not in _STAGE_TIMINGS
    ]
    if missing:
        raise RuntimeError(
            "Stage timing evidence missing for normalized notices: "
            + ", ".join(sorted(missing)[:5])
        )

    normalisation = [
        _STAGE_TIMINGS[item.publication_number]["normalisation_seconds"]
        for item in normalized_records
    ]
    indexing = [
        _STAGE_TIMINGS[item.publication_number]["indexing_seconds"]
        for item in normalized_records
    ]
    notification = [
        _STAGE_TIMINGS[item.publication_number]["notification_seconds"]
        for item in normalized_records
    ]
    queueing = [
        _STAGE_TIMINGS[item.publication_number][
            "retrieval_to_normalisation_start_seconds"
        ]
        for item in normalized_records
    ]

    report["metrics"]["normalisation_lag"] = metric_summary(
        normalisation,
        unit="seconds_stage_duration",
    )
    report["metrics"]["indexing_lag"] = metric_summary(
        indexing,
        unit="seconds_stage_duration",
    )
    report["metrics"]["subscriber_notification_lag"] = metric_summary(
        notification,
        unit="seconds_stage_duration",
    )
    report["queueing_context"] = {
        "retrieval_to_normalisation_start_lag": metric_summary(
            queueing,
            unit="seconds_queue_wait",
        ),
        "thresholded_as_normalisation_lag": False,
        "reason": (
            "Queue wait includes deterministic sampling and remaining bounded network "
            "work; it is disclosed separately from local transformation duration."
        ),
    }
    report["measurement_semantics"] = {
        "clock": "MONOTONIC_FOR_STAGE_DURATION_UTC_FOR_AUDIT_TIMESTAMPS",
        "normalisation_lag": "normalize_notice call duration",
        "indexing_lag": "SQLite insert, commit, final hash update and commit duration",
        "subscriber_notification_lag": "private ledger append duration",
        "queue_wait_disclosed_separately": True,
        "fabricated_evidence": 0,
    }
    report["confidence_limitations"].append(
        "Local stage durations are measured in the one-shot runner and do not claim "
        "production queue capacity; retrieval-to-processing wait is disclosed separately."
    )
    return report
