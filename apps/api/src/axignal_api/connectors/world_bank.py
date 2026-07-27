from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urlparse

import httpx

SOURCE_ID = "world-bank-wdi"
COUNTRY_CODE = "RUS"
INDICATOR_CODE = "FP.CPI.TOTL.ZG"
BASE_URL = (
    "https://api.worldbank.org/v2/country/"
    f"{COUNTRY_CODE}/indicator/{INDICATOR_CODE}"
)
ALLOWED_HOST = "api.worldbank.org"
MAX_RESPONSE_BYTES = 524_288
TIMEOUT_SECONDS = 10.0


class SourceRetrievalError(RuntimeError):
    """Raised when a source response violates the admitted connector contract."""


@dataclass(frozen=True)
class WorldBankObservation:
    source_id: str
    country_code: str
    country_name: str
    indicator_code: str
    indicator_name: str
    period: str
    value: float
    unit: str
    request_url: str
    retrieved_at: datetime
    source_updated_at: str | None
    content_hash: str
    raw_payload: Any
    retrieval_mode: str

    @property
    def retrieval_key(self) -> str:
        return (
            f"{self.source_id}:{self.country_code}:{self.indicator_code}:"
            f"{self.period}:{self.content_hash}"
        )


class WorldBankConnector:
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

    def fetch_latest_inflation(self) -> WorldBankObservation:
        if self.live_enabled:
            return self._fetch_live()
        if self.fixture_path is None:
            raise SourceRetrievalError(
                "Live retrieval is disabled and no frozen World Bank fixture was provided"
            )
        return self._from_payload(
            json.loads(self.fixture_path.read_text(encoding="utf-8")),
            request_url=self._build_request_url(),
            retrieved_at=datetime.now(UTC),
            retrieval_mode="FROZEN_FIXTURE",
        )

    def _fetch_live(self) -> WorldBankObservation:
        request_url = self._build_request_url()
        self._validate_url(request_url)
        owns_client = self.client is None
        client = self.client or httpx.Client(
            timeout=TIMEOUT_SECONDS,
            follow_redirects=False,
            headers={
                "accept": "application/json",
                "user-agent": "AXIGNAL/0.1 institutional-source-connector",
            },
        )
        try:
            response = client.get(request_url)
        except httpx.HTTPError as exc:
            raise SourceRetrievalError(f"World Bank request failed: {exc.__class__.__name__}") from exc
        finally:
            if owns_client:
                client.close()

        if response.is_redirect:
            raise SourceRetrievalError("World Bank connector refuses redirects")
        if response.status_code != 200:
            raise SourceRetrievalError(
                f"World Bank returned unexpected status {response.status_code}"
            )
        if len(response.content) > MAX_RESPONSE_BYTES:
            raise SourceRetrievalError("World Bank response exceeded the admitted size budget")
        content_type = response.headers.get("content-type", "").casefold()
        if "json" not in content_type:
            raise SourceRetrievalError("World Bank response was not JSON")
        try:
            payload = response.json()
        except ValueError as exc:
            raise SourceRetrievalError("World Bank returned invalid JSON") from exc
        return self._from_payload(
            payload,
            request_url=str(response.request.url),
            retrieved_at=datetime.now(UTC),
            retrieval_mode="LIVE_API",
        )

    @staticmethod
    def _build_request_url() -> str:
        query = urlencode(
            {
                "format": "json",
                "mrnev": "5",
                "per_page": "5",
                "source": "2",
            }
        )
        return f"{BASE_URL}?{query}"

    @staticmethod
    def _validate_url(url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme != "https":
            raise SourceRetrievalError("World Bank connector requires HTTPS")
        if parsed.hostname != ALLOWED_HOST:
            raise SourceRetrievalError("World Bank connector host is outside the allowlist")
        if parsed.username or parsed.password:
            raise SourceRetrievalError("World Bank connector URL must not contain credentials")
        if parsed.port not in {None, 443}:
            raise SourceRetrievalError("World Bank connector refuses non-standard ports")
        expected_path = f"/v2/country/{COUNTRY_CODE}/indicator/{INDICATOR_CODE}"
        if parsed.path != expected_path:
            raise SourceRetrievalError("World Bank connector path is outside the admitted dataset")

    @staticmethod
    def _from_payload(
        payload: Any,
        *,
        request_url: str,
        retrieved_at: datetime,
        retrieval_mode: str,
    ) -> WorldBankObservation:
        if not isinstance(payload, list) or len(payload) != 2:
            raise SourceRetrievalError("World Bank response shape is invalid")
        metadata, rows = payload
        if not isinstance(metadata, dict) or not isinstance(rows, list):
            raise SourceRetrievalError("World Bank response metadata or rows are invalid")

        selected: dict[str, Any] | None = None
        for row in rows:
            if not isinstance(row, dict):
                continue
            if row.get("countryiso3code") != COUNTRY_CODE:
                continue
            indicator = row.get("indicator")
            if not isinstance(indicator, dict) or indicator.get("id") != INDICATOR_CODE:
                continue
            value = row.get("value")
            if isinstance(value, int | float) and not isinstance(value, bool):
                selected = row
                break

        if selected is None:
            raise SourceRetrievalError("World Bank response has no non-empty admitted observation")

        canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        content_hash = f"sha256:{sha256(canonical.encode('utf-8')).hexdigest()}"
        indicator = selected["indicator"]
        country = selected.get("country")
        if not isinstance(country, dict):
            raise SourceRetrievalError("World Bank country metadata is missing")

        return WorldBankObservation(
            source_id=SOURCE_ID,
            country_code=COUNTRY_CODE,
            country_name=str(country.get("value") or "Russian Federation"),
            indicator_code=INDICATOR_CODE,
            indicator_name=str(indicator.get("value") or "Inflation, consumer prices (annual %)"),
            period=str(selected.get("date")),
            value=float(selected["value"]),
            unit="percent_annual",
            request_url=request_url,
            retrieved_at=retrieved_at,
            source_updated_at=(
                str(metadata["lastupdated"]) if metadata.get("lastupdated") is not None else None
            ),
            content_hash=content_hash,
            raw_payload=payload,
            retrieval_mode=retrieval_mode,
        )
