from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from axignal_api.o01_official_source_retry import (
    OfficialResponse,
    OfficialSourceFetchError,
    fetch_official_document_with_retry,
    observe_official_source_with_retry,
)
from axignal_api.o01_quality_http import NetworkBudget

URL = "https://ted.europa.eu/en/help/search-browse"


def _response(
    status: int,
    body: bytes,
    *,
    retry_after: str | None = None,
) -> OfficialResponse:
    started = datetime(2026, 8, 2, 20, 0, tzinfo=UTC)
    completed = started + timedelta(milliseconds=100)
    return OfficialResponse(
        body=body,
        metadata={
            "requested_url": URL,
            "final_url": URL,
            "http_status": status,
            "content_type": "text/html; charset=utf-8",
            "content_length": str(len(body)),
            "date": "Sun, 02 Aug 2026 20:00:00 GMT",
            "etag": None,
            "last_modified": None,
            "retry_after": retry_after,
            "resolved_addresses": ["192.0.2.10"],
            "selected_address": "192.0.2.10",
            "redirects_followed": 0,
            "redirect_chain": [],
            "duration_seconds": 0.1,
            "response_bytes": len(body),
            "response_sha256": (
                "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
                if not body
                else "sha256:fixture"
            ),
            "response_body_persisted": False,
        },
        started_at=started,
        completed_at=completed,
    )


def _sequence(*responses: OfficialResponse):
    queue = list(responses)

    def fetch_once(**_: Any) -> OfficialResponse:
        return queue.pop(0)

    return fetch_once


def test_http_202_then_200_is_accepted_only_after_second_attempt() -> None:
    waits: list[float] = []
    result, attempts = fetch_official_document_with_retry(
        url=URL,
        allowed_hosts=frozenset({"ted.europa.eu"}),
        timeout_seconds=30,
        max_response_bytes=1_000_000,
        budget=NetworkBudget(2),
        maximum_attempts=2,
        minimum_delay_seconds=0.25,
        fetch_once=_sequence(
            _response(202, b""),
            _response(200, b"<html>All notices last 10 years from today</html>"),
        ),
        sleeper=waits.append,
    )
    assert result.metadata["http_status"] == 200
    assert [item["http_status"] for item in attempts] == [202, 200]
    assert attempts[0]["accepted"] is False
    assert attempts[1]["accepted"] is True
    assert attempts[0]["retry_wait_seconds"] == 2.0
    assert waits == [2.0]


def test_two_http_202_responses_fail_closed_with_url_and_ledger() -> None:
    with pytest.raises(OfficialSourceFetchError) as raised:
        fetch_official_document_with_retry(
            url=URL,
            allowed_hosts=frozenset({"ted.europa.eu"}),
            timeout_seconds=30,
            max_response_bytes=1_000_000,
            budget=NetworkBudget(2),
            maximum_attempts=2,
            minimum_delay_seconds=0.25,
            fetch_once=_sequence(_response(202, b""), _response(202, b"")),
            sleeper=lambda _: None,
        )
    assert URL in str(raised.value)
    assert [item["http_status"] for item in raised.value.attempts] == [202, 202]
    assert all(item["accepted"] is False for item in raised.value.attempts)


def test_retry_after_is_respected_for_http_202() -> None:
    waits: list[float] = []
    fetch_official_document_with_retry(
        url=URL,
        allowed_hosts=frozenset({"ted.europa.eu"}),
        timeout_seconds=30,
        max_response_bytes=1_000_000,
        budget=NetworkBudget(2),
        maximum_attempts=2,
        minimum_delay_seconds=0.25,
        fetch_once=_sequence(
            _response(202, b"", retry_after="7"),
            _response(200, b"ok"),
        ),
        sleeper=waits.append,
    )
    assert waits == [7.0]


def test_missing_anchors_fail_without_persisting_body() -> None:
    with pytest.raises(OfficialSourceFetchError) as raised:
        observe_official_source_with_retry(
            url=URL,
            anchors=["All notices", "last 10 years from today"],
            allowed_hosts=frozenset({"ted.europa.eu"}),
            timeout_seconds=30,
            max_response_bytes=1_000_000,
            budget=NetworkBudget(2),
            maximum_attempts=2,
            minimum_delay_seconds=0.25,
            retryable_statuses=frozenset({202}),
            fetch_once=_sequence(_response(200, b"<html>changed page</html>")),
            sleeper=lambda _: None,
        )
    assert "anchors missing" in str(raised.value)
    assert raised.value.attempts[0]["response_body_persisted"] is False


def test_attempt_ledger_is_json_serialisable_and_contains_no_body() -> None:
    _, attempts = fetch_official_document_with_retry(
        url=URL,
        allowed_hosts=frozenset({"ted.europa.eu"}),
        timeout_seconds=30,
        max_response_bytes=1_000_000,
        budget=NetworkBudget(1),
        maximum_attempts=1,
        minimum_delay_seconds=0.25,
        fetch_once=_sequence(_response(200, b"sensitive body")),
        sleeper=lambda _: None,
    )
    encoded = json.dumps(attempts)
    assert "sensitive body" not in encoded
    assert "response_body_persisted" in encoded
