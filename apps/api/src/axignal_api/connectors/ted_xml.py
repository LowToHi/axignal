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
DOWNLOAD_HOST = "ted.europa.eu"
DOWNLOAD_PATH_PREFIX = "/en/notice/"
PUBLICATION_NUMBER_PATTERN = re.compile(r"^[0-9]{1,8}-[0-9]{4}$")
MAX_XML_BYTES = 2_097_152
TIMEOUT_SECONDS = 20.0


class TEDXMLRetrievalError(RuntimeError):
    """Raised when an official TED XML retrieval violates the admitted profile."""


@dataclass(frozen=True)
class TEDXMLNotice:
    publication_number: str
    request_url: str
    retrieved_at: datetime
    raw_xml: bytes
    content_hash: str
    retrieval_mode: str


class TEDXMLConnector:
    """Bounded direct-link connector for official TED XML notices.

    Callers provide publication numbers, never arbitrary URLs. Raw XML is returned only
    in memory and must not be persisted by downstream code.
    """

    def __init__(
        self,
        *,
        live_enabled: bool,
        fixture_manifest_path: Path | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.live_enabled = live_enabled
        self.fixture_manifest_path = fixture_manifest_path
        self.client = client

    def fetch(self, publication_number: str) -> TEDXMLNotice:
        self.validate_publication_number(publication_number)
        if self.live_enabled:
            return self._fetch_live(publication_number)
        return self._fetch_fixture(publication_number)

    @staticmethod
    def validate_publication_number(publication_number: str) -> None:
        if not PUBLICATION_NUMBER_PATTERN.fullmatch(publication_number):
            raise TEDXMLRetrievalError("TED publication number is invalid")

    @classmethod
    def direct_xml_url(cls, publication_number: str) -> str:
        cls.validate_publication_number(publication_number)
        url = f"https://{DOWNLOAD_HOST}/en/notice/{publication_number}/xml"
        cls._validate_url(url, publication_number=publication_number)
        return url

    def _fetch_fixture(self, publication_number: str) -> TEDXMLNotice:
        manifest_path = self.fixture_manifest_path
        if manifest_path is None:
            raise TEDXMLRetrievalError(
                "Live TED retrieval is disabled and no fixture manifest was provided"
            )
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise TEDXMLRetrievalError("TED fixture manifest is unreadable or invalid") from exc
        if not isinstance(manifest, dict):
            raise TEDXMLRetrievalError("TED fixture manifest must be an object")
        relative = manifest.get(publication_number)
        if not isinstance(relative, str) or not relative:
            raise TEDXMLRetrievalError("TED fixture manifest has no requested publication")
        fixture_path = (manifest_path.parent / relative).resolve()
        try:
            fixture_path.relative_to(manifest_path.parent.resolve())
        except ValueError as exc:
            raise TEDXMLRetrievalError("TED fixture path escapes its manifest directory") from exc
        try:
            raw_xml = fixture_path.read_bytes()
        except OSError as exc:
            raise TEDXMLRetrievalError("TED XML fixture is unreadable") from exc
        self._validate_xml_bytes(raw_xml)
        return TEDXMLNotice(
            publication_number=publication_number,
            request_url=self.direct_xml_url(publication_number),
            retrieved_at=datetime.now(UTC),
            raw_xml=raw_xml,
            content_hash=f"sha256:{sha256(raw_xml).hexdigest()}",
            retrieval_mode="FROZEN_FIXTURE",
        )

    def _fetch_live(self, publication_number: str) -> TEDXMLNotice:
        url = self.direct_xml_url(publication_number)
        owns_client = self.client is None
        client = self.client or httpx.Client(
            timeout=TIMEOUT_SECONDS,
            follow_redirects=False,
            headers={
                "accept": "application/xml,text/xml",
                "user-agent": "AXIGNAL/0.1 TED-non-personal-runtime",
            },
        )
        try:
            response = client.get(url)
        except httpx.HTTPError as exc:
            raise TEDXMLRetrievalError(
                f"TED XML request failed: {exc.__class__.__name__}"
            ) from exc
        finally:
            if owns_client:
                client.close()
        if response.is_redirect:
            raise TEDXMLRetrievalError("TED XML connector refuses redirects")
        if response.status_code != 200:
            raise TEDXMLRetrievalError(
                f"TED XML endpoint returned unexpected status {response.status_code}"
            )
        content_type = response.headers.get("content-type", "").casefold()
        if not any(token in content_type for token in ("xml", "octet-stream")):
            raise TEDXMLRetrievalError("TED XML response has an unexpected content type")
        raw_xml = bytes(response.content)
        self._validate_xml_bytes(raw_xml)
        self._validate_url(str(response.request.url), publication_number=publication_number)
        return TEDXMLNotice(
            publication_number=publication_number,
            request_url=str(response.request.url),
            retrieved_at=datetime.now(UTC),
            raw_xml=raw_xml,
            content_hash=f"sha256:{sha256(raw_xml).hexdigest()}",
            retrieval_mode="LIVE_DIRECT_XML",
        )

    @staticmethod
    def _validate_xml_bytes(raw_xml: bytes) -> None:
        if not raw_xml:
            raise TEDXMLRetrievalError("TED XML response is empty")
        if len(raw_xml) > MAX_XML_BYTES:
            raise TEDXMLRetrievalError("TED XML response exceeded the size budget")
        lowered = raw_xml[:4096].lower()
        if b"<!doctype" in lowered or b"<!entity" in lowered:
            raise TEDXMLRetrievalError("DTD and entity declarations are prohibited")
        if not raw_xml.lstrip().startswith(b"<"):
            raise TEDXMLRetrievalError("TED XML response does not begin with XML content")

    @staticmethod
    def _validate_url(url: str, *, publication_number: str) -> None:
        parsed = urlparse(url)
        expected_path = f"{DOWNLOAD_PATH_PREFIX}{publication_number}/xml"
        if parsed.scheme != "https" or parsed.hostname != DOWNLOAD_HOST:
            raise TEDXMLRetrievalError("TED XML URL is outside the admitted host")
        if parsed.port not in {None, 443} or parsed.username or parsed.password:
            raise TEDXMLRetrievalError("TED XML URL contains a prohibited authority component")
        if parsed.path != expected_path or parsed.query or parsed.fragment:
            raise TEDXMLRetrievalError("TED XML URL is outside the admitted path")


def fixture_manifest_payload(mapping: dict[str, str]) -> dict[str, Any]:
    """Return a normalised manifest payload for deterministic tooling."""

    for publication_number, relative_path in mapping.items():
        TEDXMLConnector.validate_publication_number(publication_number)
        if not relative_path or Path(relative_path).is_absolute():
            raise TEDXMLRetrievalError("Fixture manifest paths must be non-empty and relative")
    return dict(sorted(mapping.items()))
