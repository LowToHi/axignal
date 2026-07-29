from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from axignal_api.connectors.ted import (
    ENDPOINT,
    FIXED_FIELDS,
    FIXED_QUERY,
    LIMIT,
    TEDSearchConnector,
    TEDSourceRetrievalError,
)

FIXTURE = Path(__file__).parent / "fixtures" / "ted_search_probe.json"


def test_ted_fixture_is_parsed_hashed_and_preserves_missing_fields() -> None:
    page = TEDSearchConnector(
        live_enabled=False,
        fixture_path=FIXTURE,
    ).fetch_probe_page()

    assert page.source_id == "src_ted_search_api_v3"
    assert page.query == FIXED_QUERY
    assert page.requested_fields == FIXED_FIELDS
    assert page.total_notice_count == 8421
    assert len(page.notices) == 2
    assert page.notices[0].publication_number == "123456-2026"
    assert page.notices[0].missing_requested_fields == ()
    assert page.notices[1].missing_requested_fields == ("buyer-name",)
    assert page.notices[1].fields["buyer-name"] is None
    assert page.content_hash.startswith("sha256:")
    assert page.request_hash.startswith("sha256:")
    assert page.retrieval_mode == "FROZEN_FIXTURE"


def test_ted_probe_request_is_fixed_bounded_and_non_personal() -> None:
    body = TEDSearchConnector._build_request_body()

    assert body == {
        "query": "place-of-performance IN (ESP FRA DEU)",
        "fields": [
            "publication-number",
            "notice-title",
            "buyer-name",
            "notice-type",
        ],
        "page": 1,
        "limit": LIMIT,
        "scope": "ACTIVE",
        "checkQuerySyntax": False,
        "paginationMode": "PAGE_NUMBER",
    }
    assert all(
        token not in field.casefold()
        for field in body["fields"]
        for token in ("email", "phone", "contact", "person")
    )
    assert "iterationNextToken" not in body


def test_ted_live_connector_posts_exact_request() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["url"] = str(request.url)
        captured["body"] = json.loads(request.content)
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        return httpx.Response(
            200,
            headers={"content-type": "application/json"},
            json=payload,
            request=request,
        )

    connector = TEDSearchConnector(
        live_enabled=True,
        client=httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=False),
    )
    page = connector.fetch_probe_page()

    assert captured["method"] == "POST"
    assert captured["url"] == ENDPOINT
    assert captured["body"] == TEDSearchConnector._build_request_body()
    assert page.retrieval_mode == "LIVE_API_TECHNICAL_PROBE"


def test_ted_live_connector_refuses_redirects() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            302,
            headers={"location": "https://example.com"},
            request=request,
        )

    connector = TEDSearchConnector(
        live_enabled=True,
        client=httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=False),
    )
    with pytest.raises(TEDSourceRetrievalError, match="redirects"):
        connector.fetch_probe_page()


def test_ted_connector_rejects_duplicate_publication_numbers(tmp_path: Path) -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    payload["notices"][1]["publication-number"] = payload["notices"][0]["publication-number"]
    fixture = tmp_path / "duplicate.json"
    fixture.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(TEDSourceRetrievalError, match="duplicate publication numbers"):
        TEDSearchConnector(live_enabled=False, fixture_path=fixture).fetch_probe_page()


def test_ted_connector_rejects_invalid_publication_number(tmp_path: Path) -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    payload["notices"][0]["publication-number"] = "../../not-a-notice"
    fixture = tmp_path / "invalid.json"
    fixture.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(TEDSourceRetrievalError, match="invalid publication number"):
        TEDSearchConnector(live_enabled=False, fixture_path=fixture).fetch_probe_page()


def test_ted_connector_refuses_unapproved_endpoint_shapes() -> None:
    for url in (
        "http://api.ted.europa.eu/v3/notices/search",
        "https://example.com/v3/notices/search",
        "https://user:pass@api.ted.europa.eu/v3/notices/search",
        "https://api.ted.europa.eu:444/v3/notices/search",
        "https://api.ted.europa.eu/v3/notices/search?query=anything",
        "https://api.ted.europa.eu/v3/notices/other",
    ):
        with pytest.raises(TEDSourceRetrievalError):
            TEDSearchConnector._validate_url(url)
