from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

SOURCE_ID = "src_ted_search_api_v3"
ENDPOINT = "https://api.ted.europa.eu/v3/notices/search"
ALLOWED_HOST = "api.ted.europa.eu"
ALLOWED_PATH = "/v3/notices/search"
FIXED_QUERY = "place-of-performance IN (ESP FRA DEU)"
FIXED_FIELDS = (
    "publication-number",
    "notice-title",
    "buyer-name",
    "notice-type",
)
LIMIT = 3
MAX_RESPONSE_BYTES = 1_048_576
TIMEOUT_SECONDS = 15.0
PUBLICATION_NUMBER_PATTERN = re.compile(r"^[0-9]{1,8}-[0-9]{4}$")


class TEDSourceRetrievalError(RuntimeError):
    """Raised when TED violates the bounded technical-probe contract."""


@dataclass(frozen=True)
class TEDNoticeProjection:
    publication_number: str
    fields: dict[str, Any]


@dataclass(frozen=True)
class TEDSearchPage:
    source_id: str
    query: str
    requested_fields: tuple[str, ...]
    total_notice_count: int
    notices: tuple[TEDNoticeProjection, ...]
    iteration_next_token_present: bool
    request_url: str
    retrieved_at: datetime
    content_hash: str
    request_hash: str
    raw_payload: dict[str, Any]
    retrieval_mode: str


class TEDSearchConnector:
    """Fixed-profile, non-personal TED Search API technical probe.

    The connector deliberately does not accept arbitrary expert-search strings or
    arbitrary return fields. Promotion beyond this profile requires a new source
    and query contract.
    """

    def __init__(
        self,
        *,
        live_enabled: bool,
        fixture_path: Path | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.live_enabled = live_enabled
        self.fixture_path = fixture_path
        self.client = client

    def fetch_probe_page(self) -> TEDSearchPage:
        request_body = self._build_request_body()
        if self.live_enabled:
            return self._fetch_live(request_body)
        if self.fixture_path is None:
            raise TEDSourceRetrievalError(
                "Live TED retrieval is disabled and no frozen fixture was provided"
            )
        try:
            payload = json.loads(self.fixture_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise TEDSourceRetrievalError("Frozen TED fixture is unreadable or invalid") from exc
        return self._from_payload(
            payload,
            request_body=request_body,
            request_url=ENDPOINT,
            retrieved_at=datetime.now(UTC),
            retrieval_mode="FROZEN_FIXTURE",
        )

    def _fetch_live(self, request_body: dict[str, Any]) -> TEDSearchPage:
        self._validate_url(ENDPOINT)
        owns_client = self.client is None
        client = self.client or httpx.Client(
            timeout=TIMEOUT_SECONDS,
            follow_redirects=False,
            headers={
                "accept": "application/json",
                "content-type": "application/json",
                "user-agent": "AXIGNAL/0.1 TED-technical-probe",
            },
        )
        try:
            response = client.post(ENDPOINT, json=request_body)
        except httpx.HTTPError as exc:
            error_name = exc.__class__.__name__
            raise TEDSourceRetrievalError(f"TED Search API request failed: {error_name}") from exc
        finally:
            if owns_client:
                client.close()

        if response.is_redirect:
            raise TEDSourceRetrievalError("TED connector refuses redirects")
        if response.status_code != 200:
            raise TEDSourceRetrievalError(
                f"TED Search API returned unexpected status {response.status_code}"
            )
        if len(response.content) > MAX_RESPONSE_BYTES:
            raise TEDSourceRetrievalError("TED Search API response exceeded the probe size budget")
        content_type = response.headers.get("content-type", "").casefold()
        if "json" not in content_type:
            raise TEDSourceRetrievalError("TED Search API response was not JSON")
        try:
            payload = response.json()
        except ValueError as exc:
            raise TEDSourceRetrievalError("TED Search API returned invalid JSON") from exc
        return self._from_payload(
            payload,
            request_body=request_body,
            request_url=str(response.request.url),
            retrieved_at=datetime.now(UTC),
            retrieval_mode="LIVE_API_TECHNICAL_PROBE",
        )

    @staticmethod
    def _build_request_body() -> dict[str, Any]:
        return {
            "query": FIXED_QUERY,
            "fields": list(FIXED_FIELDS),
            "page": 1,
            "limit": LIMIT,
            "scope": "ACTIVE",
            "checkQuerySyntax": False,
            "paginationMode": "PAGE_NUMBER",
        }

    @staticmethod
    def _validate_url(url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme != "https":
            raise TEDSourceRetrievalError("TED connector requires HTTPS")
        if parsed.hostname != ALLOWED_HOST:
            raise TEDSourceRetrievalError("TED connector host is outside the allowlist")
        if parsed.username or parsed.password:
            raise TEDSourceRetrievalError("TED connector URL must not contain credentials")
        if parsed.port not in {None, 443}:
            raise TEDSourceRetrievalError("TED connector refuses non-standard ports")
        if parsed.path != ALLOWED_PATH or parsed.query or parsed.fragment:
            raise TEDSourceRetrievalError("TED connector URL is outside the admitted endpoint")

    @classmethod
    def _from_payload(
        cls,
        payload: Any,
        *,
        request_body: dict[str, Any],
        request_url: str,
        retrieved_at: datetime,
        retrieval_mode: str,
    ) -> TEDSearchPage:
        if not isinstance(payload, dict):
            raise TEDSourceRetrievalError("TED Search API response root is not an object")
        total_notice_count = payload.get("totalNoticeCount")
        notices = payload.get("notices")
        if not isinstance(total_notice_count, int) or isinstance(total_notice_count, bool):
            raise TEDSourceRetrievalError("TED totalNoticeCount is missing or invalid")
        if total_notice_count < 0:
            raise TEDSourceRetrievalError("TED totalNoticeCount cannot be negative")
        if not isinstance(notices, list):
            raise TEDSourceRetrievalError("TED notices list is missing or invalid")
        if not notices:
            raise TEDSourceRetrievalError("TED technical probe returned no notices")
        if len(notices) > LIMIT:
            raise TEDSourceRetrievalError("TED returned more notices than requested")

        projections: list[TEDNoticeProjection] = []
        seen_publication_numbers: set[str] = set()
        for item in notices:
            if not isinstance(item, dict):
                raise TEDSourceRetrievalError("TED notice projection is not an object")
            publication_number = item.get("publication-number")
            if not isinstance(publication_number, str) or not PUBLICATION_NUMBER_PATTERN.fullmatch(
                publication_number
            ):
                raise TEDSourceRetrievalError("TED notice has an invalid publication number")
            if publication_number in seen_publication_numbers:
                raise TEDSourceRetrievalError("TED response contains duplicate publication numbers")
            seen_publication_numbers.add(publication_number)
            for field in FIXED_FIELDS:
                if field not in item:
                    raise TEDSourceRetrievalError(
                        f"TED notice projection omitted requested field {field}"
                    )
            projections.append(
                TEDNoticeProjection(
                    publication_number=publication_number,
                    fields={field: item[field] for field in FIXED_FIELDS},
                )
            )

        request_json = json.dumps(
            request_body,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        payload_json = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return TEDSearchPage(
            source_id=SOURCE_ID,
            query=FIXED_QUERY,
            requested_fields=FIXED_FIELDS,
            total_notice_count=total_notice_count,
            notices=tuple(projections),
            iteration_next_token_present=bool(payload.get("iterationNextToken")),
            request_url=request_url,
            retrieved_at=retrieved_at,
            content_hash=f"sha256:{sha256(payload_json.encode('utf-8')).hexdigest()}",
            request_hash=f"sha256:{sha256(request_json.encode('utf-8')).hexdigest()}",
            raw_payload=payload,
            retrieval_mode=retrieval_mode,
        )
