from __future__ import annotations

from datetime import UTC, datetime, timedelta

from axignal_api.o01_quality_common import PageObservation
from axignal_api.o01_quality_stage_timing import (
    index_and_enqueue,
    lag_report,
    stage_timings,
)


def source_record() -> dict[str, object]:
    return {
        "publication-number": "000001-2026",
        "publication-date": "2026-07-15",
        "notice-identifier": ["notice-000001-2026"],
        "notice-version": ["01"],
        "notice-type": ["cn-standard"],
        "form-type": ["competition"],
        "notice-title": {"eng": ["Public software services"]},
        "buyer-name": {"eng": ["Example public authority"]},
        "buyer-country": ["ESP"],
        "procedure-type": ["open"],
        "contract-nature": ["services"],
        "classification-cpv": ["48000000"],
        "place-of-performance-country-proc": ["ESP"],
        "place-of-performance-subdiv-proc": ["ES1"],
        "deadline": ["2026-09-01T12:00:00Z"],
        "estimated-value-proc": ["100000.00"],
        "estimated-value-cur-proc": ["EUR"],
        "identifier-lot": ["LOT-1"],
    }


def test_stage_duration_excludes_batch_queue_wait() -> None:
    retrieval_completed = datetime.now(UTC) - timedelta(seconds=125)
    observation = PageObservation(
        country="ESP",
        page=1,
        query="frozen",
        retrieval_started_at=retrieval_completed - timedelta(milliseconds=250),
        retrieval_completed_at=retrieval_completed,
        response_date_header=None,
        total_notice_count=1,
        returned_count=1,
    )

    normalized, acquisition, notifications = index_and_enqueue(
        [(source_record(), "ESP", observation)]
    )
    report = lag_report(normalized, acquisition_by_notice=acquisition)
    notice = normalized[0]
    timing = stage_timings()[notice.publication_number]

    assert report["metrics"]["normalisation_lag"]["p95"] < 1.0
    assert report["metrics"]["indexing_lag"]["p95"] < 1.0
    assert report["metrics"]["subscriber_notification_lag"]["p95"] < 1.0
    assert (
        report["queueing_context"]["retrieval_to_normalisation_start_lag"]["p95"]
        >= 124.0
    )
    assert report["queueing_context"]["thresholded_as_normalisation_lag"] is False
    assert report["measurement_semantics"]["queue_wait_disclosed_separately"] is True
    assert timing["normalisation_seconds"] < 1.0
    assert timing["retrieval_to_normalisation_start_seconds"] >= 124.0
    assert notifications[0]["normalized_record_sha256"] == notice.normalized_record_sha256

    retrieved = datetime.fromisoformat(notice.retrieval_completed_at.replace("Z", "+00:00"))
    normalised = datetime.fromisoformat(notice.normalised_at.replace("Z", "+00:00"))
    indexed = datetime.fromisoformat(notice.indexed_at.replace("Z", "+00:00"))
    enqueued = datetime.fromisoformat(
        notice.notification_enqueued_at.replace("Z", "+00:00")
    )
    assert retrieved <= normalised <= indexed <= enqueued
