from __future__ import annotations

import http.client
import ssl
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from time import perf_counter
from typing import Any
from urllib.parse import urljoin

from .o01_history_frequency_lag import html_text
from .o01_official_baseline import (
    PinnedHTTPSConnection,
    resolve_public_addresses,
    select_address,
    validate_official_url,
)
from .o01_quality_common import O01QualityCampaignError, sha256_prefixed
from .o01_quality_http import (
    NetworkBudget,
    effective_request_delay,
    rate_limit_wait_seconds,
    retry_after_seconds,
)

REDIRECT_STATUSES = frozenset({301, 302, 303, 307, 308})
DEFAULT_RETRYABLE_STATUSES = frozenset({202, 429, 500, 502, 503, 504})


@dataclass(frozen=True)
class OfficialResponse:
    body: bytes
    metadata: dict[str, Any]
    started_at: datetime
    completed_at: datetime


class OfficialSourceFetchError(O01QualityCampaignError):
    def __init__(self, message: str, attempts: list[dict[str, Any]]) -> None:
        super().__init__(message)
        self.attempts = attempts


def _headers(response: http.client.HTTPResponse) -> dict[str, str]:
    return {key.casefold(): value for key, value in response.getheaders()}


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def request_official_document_once(
    *,
    url: str,
    allowed_hosts: frozenset[str],
    timeout_seconds: float,
    max_response_bytes: int,
    budget: NetworkBudget,
    maximum_redirects: int = 4,
) -> OfficialResponse:
    current_url = url
    redirect_chain: list[dict[str, Any]] = []
    initial_started_at: datetime | None = None

    for redirect_index in range(maximum_redirects + 1):
        parsed = validate_official_url(current_url, allowed_hosts=allowed_hosts)
        host = parsed.hostname or ""
        port = parsed.port or 443
        path = parsed.path + (f"?{parsed.query}" if parsed.query else "")
        budget.consume()
        addresses = resolve_public_addresses(host, port)
        selected_address = select_address(addresses)
        started_at = datetime.now(UTC)
        if initial_started_at is None:
            initial_started_at = started_at
        started_clock = perf_counter()
        connection = PinnedHTTPSConnection(
            host=host,
            port=port,
            selected_address=selected_address,
            timeout=timeout_seconds,
            context=ssl.create_default_context(),
        )
        try:
            connection.request(
                "GET",
                path,
                headers={
                    "Accept": (
                        "text/html,application/xhtml+xml,application/xml;q=0.9,"
                        "text/plain;q=0.8,*/*;q=0.1"
                    ),
                    "Accept-Encoding": "identity",
                    "Accept-Language": "en",
                    "Cache-Control": "no-cache",
                    "Connection": "close",
                    "User-Agent": "AXIGNAL-O01-E-Evidence/2.0",
                },
            )
            response = connection.getresponse()
            headers = _headers(response)
            body = response.read(max_response_bytes + 1)
            completed_at = datetime.now(UTC)
            if len(body) > max_response_bytes:
                raise O01QualityCampaignError(
                    "Official endpoint response exceeded frozen byte limit"
                )
            metadata = {
                "requested_url": url,
                "final_url": current_url,
                "http_status": response.status,
                "content_type": headers.get("content-type"),
                "content_length": headers.get("content-length"),
                "date": headers.get("date"),
                "etag": headers.get("etag"),
                "last_modified": headers.get("last-modified"),
                "retry_after": headers.get("retry-after"),
                "resolved_addresses": list(addresses),
                "selected_address": selected_address,
                "redirects_followed": redirect_index,
                "redirect_chain": list(redirect_chain),
                "duration_seconds": max(0.0, perf_counter() - started_clock),
                "response_bytes": len(body),
                "response_sha256": sha256_prefixed(body),
                "response_body_persisted": False,
            }
            if response.status in REDIRECT_STATUSES:
                location = headers.get("location")
                if not location:
                    raise O01QualityCampaignError(
                        f"Redirect {response.status} omitted Location for {current_url}"
                    )
                redirect_chain.append(
                    {
                        "url": current_url,
                        "http_status": response.status,
                        "location": location,
                        "response_sha256": metadata["response_sha256"],
                        "response_bytes": len(body),
                    }
                )
                current_url = urljoin(current_url, location)
                continue
            return OfficialResponse(
                body=body,
                metadata=metadata,
                started_at=initial_started_at,
                completed_at=completed_at,
            )
        finally:
            connection.close()

    raise O01QualityCampaignError(
        f"Official endpoint exceeded redirect budget for {url}"
    )


def fetch_official_document_with_retry(
    *,
    url: str,
    allowed_hosts: frozenset[str],
    timeout_seconds: float,
    max_response_bytes: int,
    budget: NetworkBudget,
    maximum_attempts: int,
    minimum_delay_seconds: float,
    retryable_statuses: frozenset[int] = DEFAULT_RETRYABLE_STATUSES,
    fetch_once: Callable[..., OfficialResponse] = request_official_document_once,
    sleeper: Callable[[float], None] = time.sleep,
) -> tuple[OfficialResponse, list[dict[str, Any]]]:
    if maximum_attempts < 1:
        raise ValueError("At least one official-source attempt is required")
    attempts: list[dict[str, Any]] = []
    last_network_error: Exception | None = None

    for attempt_number in range(1, maximum_attempts + 1):
        try:
            response = fetch_once(
                url=url,
                allowed_hosts=allowed_hosts,
                timeout_seconds=timeout_seconds,
                max_response_bytes=max_response_bytes,
                budget=budget,
            )
        except (
            OSError,
            TimeoutError,
            ssl.SSLError,
            http.client.HTTPException,
        ) as exc:
            last_network_error = exc
            attempts.append(
                {
                    "attempt": attempt_number,
                    "url": url,
                    "outcome": "NETWORK_ERROR",
                    "error_type": type(exc).__name__,
                    "response_body_persisted": False,
                }
            )
            if attempt_number < maximum_attempts:
                sleeper(
                    max(
                        effective_request_delay(minimum_delay_seconds),
                        float(attempt_number),
                    )
                )
                continue
            break

        status = int(response.metadata["http_status"])
        attempt_record = {
            "attempt": attempt_number,
            "url": url,
            "final_url": response.metadata["final_url"],
            "http_status": status,
            "content_type": response.metadata.get("content_type"),
            "retry_after": response.metadata.get("retry_after"),
            "response_bytes": response.metadata["response_bytes"],
            "response_sha256": response.metadata["response_sha256"],
            "started_at": _iso(response.started_at),
            "completed_at": _iso(response.completed_at),
            "duration_seconds": response.metadata["duration_seconds"],
            "resolved_addresses": response.metadata["resolved_addresses"],
            "selected_address": response.metadata["selected_address"],
            "redirects_followed": response.metadata["redirects_followed"],
            "response_body_persisted": False,
            "accepted": status == 200,
        }
        attempts.append(attempt_record)
        if status == 200:
            return response, attempts
        if status not in retryable_statuses or attempt_number >= maximum_attempts:
            raise OfficialSourceFetchError(
                f"Official source {url} returned final HTTP {status}",
                attempts,
            )

        if status == 429:
            wait_seconds = rate_limit_wait_seconds(
                response.metadata.get("retry_after"),
                minimum_delay_seconds=minimum_delay_seconds,
                now=response.completed_at,
            )
        else:
            declared = retry_after_seconds(
                response.metadata.get("retry_after"),
                now=response.completed_at,
            )
            wait_seconds = max(
                effective_request_delay(minimum_delay_seconds),
                declared or 0.0,
            )
        attempt_record["retry_wait_seconds"] = wait_seconds
        sleeper(wait_seconds)

    raise OfficialSourceFetchError(
        "Official source network request failed after "
        f"{maximum_attempts} attempts for {url}: "
        f"{type(last_network_error).__name__ if last_network_error else 'unknown'}",
        attempts,
    )


def observe_official_source_with_retry(
    *,
    url: str,
    anchors: list[str],
    allowed_hosts: frozenset[str],
    timeout_seconds: float,
    max_response_bytes: int,
    budget: NetworkBudget,
    maximum_attempts: int,
    minimum_delay_seconds: float,
    retryable_statuses: frozenset[int],
    fetch_once: Callable[..., OfficialResponse] = request_official_document_once,
    sleeper: Callable[[float], None] = time.sleep,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    response, attempts = fetch_official_document_with_retry(
        url=url,
        allowed_hosts=allowed_hosts,
        timeout_seconds=timeout_seconds,
        max_response_bytes=max_response_bytes,
        budget=budget,
        maximum_attempts=maximum_attempts,
        minimum_delay_seconds=minimum_delay_seconds,
        retryable_statuses=retryable_statuses,
        fetch_once=fetch_once,
        sleeper=sleeper,
    )
    normalized = html_text(response.body.decode("utf-8", errors="replace"))
    missing = [anchor for anchor in anchors if anchor not in normalized]
    if missing:
        raise OfficialSourceFetchError(
            f"Official source anchors missing for {url}: {missing}",
            attempts,
        )
    observation = {
        "url": url,
        "status": "PASS",
        "anchors_expected": anchors,
        "anchors_present": anchors,
        "body_sha256": response.metadata["response_sha256"],
        "body_bytes": response.metadata["response_bytes"],
        "body_persisted": False,
        "observed_at": _iso(response.completed_at),
        "request_started_at": _iso(response.started_at),
        "metadata": response.metadata,
        "attempt_count": len(attempts),
    }
    return observation, attempts
