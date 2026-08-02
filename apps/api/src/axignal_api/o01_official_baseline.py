from __future__ import annotations

import hashlib
import http.client
import ipaddress
import json
import re
import socket
import ssl
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import SplitResult, urljoin, urlsplit


class BaselineError(RuntimeError):
    """Raised when an official online baseline cannot be materialised safely."""


class TermsChangeClass(StrEnum):
    BASELINE_ESTABLISHED = "BASELINE_ESTABLISHED"
    NO_MATERIAL_CHANGE = "NO_MATERIAL_CHANGE"
    MATERIAL_TERMS_CHANGE = "MATERIAL_TERMS_CHANGE"


@dataclass(frozen=True)
class RetrievalPolicy:
    allowed_hosts: frozenset[str]
    max_redirects: int
    max_response_bytes: int
    timeout_seconds: float
    allowed_content_types: frozenset[str]
    challenge_markers: tuple[str, ...]


@dataclass(frozen=True)
class RetrievedDocument:
    document_id: str
    publisher: str
    requested_url: str
    final_url: str
    status: str
    http_status: int
    content_type: str
    observed_at: str
    content_sha256: str
    normalized_text_bytes: int
    critical_anchors_expected: int
    critical_anchors_present: int
    resolved_addresses: tuple[str, ...]
    selected_address: str
    etag: str | None
    last_modified: str | None
    normalized_text: str


class VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._ignored_depth = 0
        self.parts: list[str] = []

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        del attrs
        if tag.casefold() in {"script", "style", "noscript", "svg", "template"}:
            self._ignored_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.casefold() in {"script", "style", "noscript", "svg", "template"}:
            self._ignored_depth = max(0, self._ignored_depth - 1)

    def handle_data(self, data: str) -> None:
        if self._ignored_depth == 0 and data.strip():
            self.parts.append(data)


class PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(
        self,
        *,
        host: str,
        port: int,
        selected_address: str,
        timeout: float,
        context: ssl.SSLContext,
    ) -> None:
        super().__init__(host=host, port=port, timeout=timeout, context=context)
        self._selected_address = selected_address

    def connect(self) -> None:
        raw_socket = socket.create_connection(
            (self._selected_address, self.port),
            self.timeout,
            self.source_address,
        )
        if self._tunnel_host:
            self.sock = raw_socket
            self._tunnel()
            if self.sock is None:
                raise BaselineError("HTTPS tunnel did not produce a socket")
            raw_socket = self.sock
        self.sock = self._context.wrap_socket(raw_socket, server_hostname=self.host)


def canonical_bytes(value: dict[str, Any]) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return f"sha256:{hashlib.sha256(value).hexdigest()}"


def normalise_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    normalized = normalized.replace("’", "'").replace("–", "-").replace("—", "-")
    normalized = re.sub(r"[^\w]+", " ", normalized, flags=re.UNICODE)
    return " ".join(normalized.split())


def decode_visible_text(body: bytes, content_type_header: str) -> str:
    encoding = "utf-8"
    match = re.search(
        r"charset=([^;\s]+)",
        content_type_header,
        flags=re.IGNORECASE,
    )
    if match:
        encoding = match.group(1).strip('"\'')
    decoded = body.decode(encoding, errors="replace")
    media_type = content_type_header.split(";", 1)[0].strip().casefold()
    if media_type in {
        "text/html",
        "application/xhtml+xml",
        "application/xml",
        "text/xml",
    }:
        parser = VisibleTextParser()
        parser.feed(decoded)
        decoded = " ".join(parser.parts)
    return normalise_text(decoded)


def validate_official_url(url: str, *, allowed_hosts: frozenset[str]) -> SplitResult:
    parsed = urlsplit(url)
    host = (parsed.hostname or "").casefold()
    if parsed.scheme.casefold() != "https":
        raise BaselineError("Official retrieval requires HTTPS")
    if parsed.username is not None or parsed.password is not None:
        raise BaselineError("URL credentials are forbidden")
    if host not in allowed_hosts:
        raise BaselineError("Official URL host is outside the allowlist")
    if parsed.port not in {None, 443}:
        raise BaselineError("Official URL uses a forbidden port")
    if not parsed.path.startswith("/"):
        raise BaselineError("Official URL path is invalid")
    return parsed


def validate_resolved_addresses(addresses: Iterable[str]) -> tuple[str, ...]:
    unique = tuple(sorted(set(addresses)))
    if not unique:
        raise BaselineError("Official host resolved to no addresses")
    for value in unique:
        address = ipaddress.ip_address(value)
        if not address.is_global:
            raise BaselineError("Official host resolved to a non-global address")
    return unique


def resolve_public_addresses(host: str, port: int = 443) -> tuple[str, ...]:
    try:
        answers = socket.getaddrinfo(
            host,
            port,
            family=socket.AF_UNSPEC,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP,
        )
    except socket.gaierror as exc:
        raise BaselineError("Official host DNS resolution failed") from exc
    return validate_resolved_addresses(item[4][0] for item in answers)


def select_address(addresses: tuple[str, ...]) -> str:
    ipv4 = [value for value in addresses if ipaddress.ip_address(value).version == 4]
    return ipv4[0] if ipv4 else addresses[0]


def _request_target(parsed: SplitResult) -> str:
    return parsed.path + (f"?{parsed.query}" if parsed.query else "")


def _content_type(response: http.client.HTTPResponse) -> str:
    return response.getheader("Content-Type", "application/octet-stream")


def _media_type(content_type_header: str) -> str:
    return content_type_header.split(";", 1)[0].strip().casefold()


def fetch_official_document(
    document: dict[str, Any],
    *,
    policy: RetrievalPolicy,
    observed_at: datetime,
) -> RetrievedDocument:
    document_id = str(document["document_id"])
    publisher = str(document["publisher"])
    requested_url = str(document["url"])
    current_url = requested_url
    expected_anchors = tuple(
        normalise_text(str(item)) for item in document["critical_anchors"]
    )
    allowed_content_types = frozenset(
        str(item).casefold()
        for item in document.get("content_types", policy.allowed_content_types)
    )

    for redirect_count in range(policy.max_redirects + 1):
        parsed = validate_official_url(current_url, allowed_hosts=policy.allowed_hosts)
        host = parsed.hostname or ""
        addresses = resolve_public_addresses(host, parsed.port or 443)
        selected_address = select_address(addresses)
        context = ssl.create_default_context()
        connection = PinnedHTTPSConnection(
            host=host,
            port=parsed.port or 443,
            selected_address=selected_address,
            timeout=policy.timeout_seconds,
            context=context,
        )
        try:
            connection.request(
                "GET",
                _request_target(parsed),
                headers={
                    "Accept": (
                        "text/html,application/xhtml+xml,text/plain;q=0.8,*/*;q=0.1"
                    ),
                    "Accept-Encoding": "identity",
                    "Accept-Language": "en",
                    "Cache-Control": "no-cache",
                    "Connection": "close",
                    "User-Agent": (
                        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                        "Chrome/150 Safari/537.36 AXIGNAL-O01-Baseline/1.0"
                    ),
                },
            )
            response = connection.getresponse()
            if response.status in {301, 302, 303, 307, 308}:
                location = response.getheader("Location")
                response.read(1024)
                if location is None:
                    raise BaselineError("Official redirect omitted Location")
                if redirect_count >= policy.max_redirects:
                    raise BaselineError("Official redirect limit exceeded")
                current_url = urljoin(current_url, location)
                continue
            if response.status != 200:
                response.read(1024)
                raise BaselineError(f"Official source returned HTTP {response.status}")

            content_type_header = _content_type(response)
            media_type = _media_type(content_type_header)
            if media_type not in allowed_content_types:
                response.read(1024)
                raise BaselineError("Official source returned a forbidden content type")
            body = response.read(policy.max_response_bytes + 1)
            if len(body) > policy.max_response_bytes:
                raise BaselineError("Official source exceeded the response-size limit")
            normalized_text = decode_visible_text(body, content_type_header)
            if not normalized_text:
                raise BaselineError("Official source normalized to empty content")
            for marker in policy.challenge_markers:
                if normalise_text(marker) in normalized_text:
                    raise BaselineError("Official source returned an automation challenge")
            missing = tuple(
                anchor for anchor in expected_anchors if anchor not in normalized_text
            )
            if missing:
                raise BaselineError(
                    f"Official source failed {len(missing)} critical legal anchors"
                )
            normalized_bytes = normalized_text.encode("utf-8")
            return RetrievedDocument(
                document_id=document_id,
                publisher=publisher,
                requested_url=requested_url,
                final_url=current_url,
                status="PASS",
                http_status=response.status,
                content_type=content_type_header,
                observed_at=(
                    observed_at.astimezone(UTC).isoformat().replace("+00:00", "Z")
                ),
                content_sha256=sha256_bytes(normalized_bytes),
                normalized_text_bytes=len(normalized_bytes),
                critical_anchors_expected=len(expected_anchors),
                critical_anchors_present=len(expected_anchors),
                resolved_addresses=addresses,
                selected_address=selected_address,
                etag=response.getheader("ETag"),
                last_modified=response.getheader("Last-Modified"),
                normalized_text=normalized_text,
            )
        except (OSError, TimeoutError, ssl.SSLError, http.client.HTTPException) as exc:
            raise BaselineError(
                f"Official retrieval failed for {document_id}: {type(exc).__name__}"
            ) from exc
        finally:
            connection.close()
    raise BaselineError("Official redirect loop exhausted")


def classify_terms_change(
    current_documents: dict[str, dict[str, Any]],
    previous_documents: dict[str, dict[str, Any]] | None,
) -> TermsChangeClass:
    if previous_documents is None:
        return TermsChangeClass.BASELINE_ESTABLISHED
    current_ids = set(current_documents)
    previous_ids = set(previous_documents)
    if current_ids != previous_ids:
        return TermsChangeClass.MATERIAL_TERMS_CHANGE
    for document_id in sorted(current_ids):
        if current_documents[document_id].get(
            "content_sha256"
        ) != previous_documents[document_id].get("content_sha256"):
            return TermsChangeClass.MATERIAL_TERMS_CHANGE
    return TermsChangeClass.NO_MATERIAL_CHANGE


def calculate_evidence_expiry(
    *,
    observed_at: datetime,
    evidence_freshness_days: int,
    artifact_retention_days: int,
    artifact_safety_margin_days: int,
) -> datetime:
    if observed_at.tzinfo is None:
        raise BaselineError("Observation time requires a timezone")
    if artifact_safety_margin_days < 1:
        raise BaselineError("Artifact safety margin must be positive")
    usable_artifact_days = artifact_retention_days - artifact_safety_margin_days
    if usable_artifact_days <= 0:
        raise BaselineError("Artifact retention does not exceed its safety margin")
    validity_days = min(evidence_freshness_days, usable_artifact_days)
    return observed_at.astimezone(UTC) + timedelta(days=validity_days)


def load_previous_baseline(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.is_file():
        return None
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise BaselineError("Previous baseline must be a JSON object")
    return value
