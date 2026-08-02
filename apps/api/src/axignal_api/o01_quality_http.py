from __future__ import annotations

import http.client
import json
import ssl
import time
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

from .o01_official_baseline import (
    PinnedHTTPSConnection,
    resolve_public_addresses,
    select_address,
    validate_official_url,
)
from .o01_quality_common import (
    O01QualityCampaignError,
    canonical_json_bytes,
    sha256_prefixed,
)

OPERATIONAL_REQUEST_FLOOR_SECONDS = 2.0
RATE_LIMIT_FALLBACK_SECONDS = 10.0
MAXIMUM_RATE_LIMIT_WAIT_SECONDS = 120.0


class NetworkBudget:
    def __init__(self, maximum: int) -> None:
        self.maximum = maximum
        self.used = 0

    def consume(self) -> None:
        if self.used >= self.maximum:
            raise O01QualityCampaignError("Frozen network request budget exceeded")
        self.used += 1


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
        + b"\n"
    )


def effective_request_delay(minimum_delay_seconds: float) -> float:
    if minimum_delay_seconds < 0:
        raise ValueError("Minimum delay cannot be negative")
    return max(minimum_delay_seconds, OPERATIONAL_REQUEST_FLOOR_SECONDS)


def retry_after_seconds(
    value: str | None,
    *,
    now: datetime | None = None,
) -> float | None:
    if value is None:
        return None
    candidate = value.strip()
    if not candidate:
        return None
    if candidate.isdigit():
        seconds = float(candidate)
    else:
        try:
            retry_at = parsedate_to_datetime(candidate)
        except (TypeError, ValueError, OverflowError):
            return None
        if retry_at.tzinfo is None:
            retry_at = retry_at.replace(tzinfo=UTC)
        reference = now or datetime.now(UTC)
        seconds = max(
            0.0,
            (
                retry_at.astimezone(UTC) - reference.astimezone(UTC)
            ).total_seconds(),
        )
    return min(seconds, MAXIMUM_RATE_LIMIT_WAIT_SECONDS)


def rate_limit_wait_seconds(
    retry_after: str | None,
    *,
    minimum_delay_seconds: float,
    now: datetime | None = None,
) -> float:
    declared = retry_after_seconds(retry_after, now=now)
    fallback_or_declared = (
        declared if declared is not None else RATE_LIMIT_FALLBACK_SECONDS
    )
    return max(
        effective_request_delay(minimum_delay_seconds),
        fallback_or_declared,
    )


def ensure_authority(plan: dict[str, Any], authority_envelope: dict[str, Any]) -> None:
    expected = plan["authority"]
    if authority_envelope.get("output") != "O01_CAMPAIGN_AUTHORISED":
        raise O01QualityCampaignError("O01-B authority envelope is not authorised")
    if authority_envelope.get("head_sha") != expected["target_head_sha"]:
        raise O01QualityCampaignError("O01-B target head mismatch")
    if authority_envelope.get("manifest_reference") != expected["manifest_reference"]:
        raise O01QualityCampaignError("O01-B manifest mismatch")
    expiry = datetime.fromisoformat(
        str(authority_envelope["effective_expiry"]).replace("Z", "+00:00")
    )
    if expiry.tzinfo is None or datetime.now(UTC) >= expiry.astimezone(UTC):
        raise O01QualityCampaignError("O01-B authority is expired")


def extract_notices(response: dict[str, Any]) -> list[dict[str, Any]]:
    notices = response.get("notices")
    if not isinstance(notices, list):
        raise O01QualityCampaignError("TED response omitted notices array")
    return [item for item in notices if isinstance(item, dict)]


def extract_total(response: dict[str, Any]) -> int | None:
    for key in (
        "totalNoticeCount",
        "totalNotices",
        "totalCount",
        "total",
        "count",
    ):
        value = response.get(key)
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
    return None


def post_json(
    *,
    endpoint: str,
    payload: dict[str, Any],
    allowed_hosts: frozenset[str],
    timeout_seconds: float,
    max_response_bytes: int,
    maximum_attempts: int,
    minimum_delay_seconds: float,
    budget: NetworkBudget,
) -> tuple[dict[str, Any], bytes, dict[str, Any], datetime, datetime]:
    parsed = validate_official_url(endpoint, allowed_hosts=allowed_hosts)
    host = parsed.hostname or ""
    path = parsed.path + (f"?{parsed.query}" if parsed.query else "")
    body = canonical_json_bytes(payload)
    last_error: Exception | None = None
    operational_delay = effective_request_delay(minimum_delay_seconds)
    for attempt in range(1, maximum_attempts + 1):
        budget.consume()
        addresses = resolve_public_addresses(host, parsed.port or 443)
        selected_address = select_address(addresses)
        started_at = datetime.now(UTC)
        connection = PinnedHTTPSConnection(
            host=host,
            port=parsed.port or 443,
            selected_address=selected_address,
            timeout=timeout_seconds,
            context=ssl.create_default_context(),
        )
        try:
            connection.request(
                "POST",
                path,
                body=body,
                headers={
                    "Accept": "application/json",
                    "Accept-Encoding": "identity",
                    "Cache-Control": "no-cache",
                    "Connection": "close",
                    "Content-Type": "application/json",
                    "User-Agent": "AXIGNAL-O01-C-Evidence/1.0",
                },
            )
            response = connection.getresponse()
            response_body = response.read(max_response_bytes + 1)
            completed_at = datetime.now(UTC)
            if len(response_body) > max_response_bytes:
                raise O01QualityCampaignError("TED response exceeded frozen byte limit")
            if response.status == 429:
                last_error = O01QualityCampaignError("TED transient HTTP status 429")
                if attempt < maximum_attempts:
                    wait_seconds = rate_limit_wait_seconds(
                        response.getheader("Retry-After"),
                        minimum_delay_seconds=minimum_delay_seconds,
                        now=completed_at,
                    )
                    time.sleep(wait_seconds)
                    continue
            elif 500 <= response.status <= 599:
                last_error = O01QualityCampaignError(
                    f"TED transient HTTP status {response.status}"
                )
                if attempt < maximum_attempts:
                    time.sleep(max(operational_delay, float(attempt)))
                    continue
            if response.status != 200:
                raise O01QualityCampaignError(
                    "TED returned HTTP "
                    f"{response.status}; response_sha256="
                    f"{sha256_prefixed(response_body)}"
                )
            content_type = response.getheader("Content-Type", "")
            if "json" not in content_type.casefold():
                raise O01QualityCampaignError("TED response was not JSON")
            try:
                value = json.loads(response_body)
            except json.JSONDecodeError as exc:
                raise O01QualityCampaignError("TED response JSON is invalid") from exc
            if not isinstance(value, dict):
                raise O01QualityCampaignError("TED response root is not an object")
            metadata = {
                "http_status": response.status,
                "content_type": content_type,
                "date": response.getheader("Date"),
                "etag": response.getheader("ETag"),
                "last_modified": response.getheader("Last-Modified"),
                "resolved_addresses": list(addresses),
                "selected_address": selected_address,
                "attempt": attempt,
                "request_body_sha256": sha256_prefixed(body),
                "response_body_sha256": sha256_prefixed(response_body),
                "response_bytes": len(response_body),
                "operational_delay_seconds": operational_delay,
            }
            time.sleep(operational_delay)
            return value, response_body, metadata, started_at, completed_at
        except (
            OSError,
            TimeoutError,
            ssl.SSLError,
            http.client.HTTPException,
        ) as exc:
            last_error = exc
            if attempt < maximum_attempts:
                time.sleep(max(operational_delay, float(attempt)))
                continue
        finally:
            connection.close()
    raise O01QualityCampaignError(
        f"TED request failed after {maximum_attempts} attempts: "
        f"{type(last_error).__name__}"
    )


def request_payload(
    *,
    query: str,
    fields: list[str],
    page: int,
    plan: dict[str, Any],
) -> dict[str, Any]:
    sampling = plan["sampling"]
    return {
        "query": query,
        "fields": fields,
        "page": page,
        "limit": sampling["page_size"],
        "scope": plan["source"]["scope"],
        "checkQuerySyntax": sampling["check_query_syntax"],
        "paginationMode": sampling["pagination_mode"],
    }
