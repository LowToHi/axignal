from __future__ import annotations

from datetime import UTC, datetime

import pytest

from axignal_api.o01_official_baseline import (
    BaselineError,
    TermsChangeClass,
    calculate_evidence_expiry,
    classify_terms_change,
    decode_visible_text,
    normalise_text,
    validate_official_url,
    validate_resolved_addresses,
)

ALLOWED_HOSTS = frozenset(
    {
        "ted.europa.eu",
        "docs.ted.europa.eu",
        "eur-lex.europa.eu",
    }
)


def test_official_url_requires_https_allowlist_and_default_port() -> None:
    parsed = validate_official_url(
        "https://docs.ted.europa.eu/api/latest/search.html",
        allowed_hosts=ALLOWED_HOSTS,
    )
    assert parsed.hostname == "docs.ted.europa.eu"

    invalid_urls = (
        "http://docs.ted.europa.eu/api/latest/search.html",
        "https://user:secret@docs.ted.europa.eu/api/latest/search.html",
        "https://docs.ted.europa.eu:8443/api/latest/search.html",
        "https://example.com/api/latest/search.html",
    )
    for value in invalid_urls:
        with pytest.raises(BaselineError):
            validate_official_url(value, allowed_hosts=ALLOWED_HOSTS)


def test_resolved_addresses_reject_private_or_mixed_dns_answers() -> None:
    assert validate_resolved_addresses(["93.184.216.34"]) == ("93.184.216.34",)
    with pytest.raises(BaselineError):
        validate_resolved_addresses(["127.0.0.1"])
    with pytest.raises(BaselineError):
        validate_resolved_addresses(["93.184.216.34", "10.0.0.8"])


def test_normalisation_is_stable_and_ignores_script_content() -> None:
    body = b"""
    <html><body><h1>Commercial or non-commercial purposes</h1>
    <script>private marker</script><p>Acknowledge the source.</p></body></html>
    """
    text = decode_visible_text(body, "text/html; charset=utf-8")
    assert "commercial or non commercial purposes" in text
    assert "acknowledge the source" in text
    assert "private marker" not in text
    assert normalise_text("Commercial—OR non-commercial") == (
        "commercial or non commercial"
    )


def test_first_observation_establishes_baseline() -> None:
    current = {
        "ted": {"content_sha256": "sha256:" + "a" * 64},
        "eurlex": {"content_sha256": "sha256:" + "b" * 64},
    }
    assert (
        classify_terms_change(current, None)
        is TermsChangeClass.BASELINE_ESTABLISHED
    )
    assert (
        classify_terms_change(current, dict(current))
        is TermsChangeClass.NO_MATERIAL_CHANGE
    )
    changed = dict(current)
    changed["ted"] = {"content_sha256": "sha256:" + "c" * 64}
    assert (
        classify_terms_change(changed, current)
        is TermsChangeClass.MATERIAL_TERMS_CHANGE
    )


def test_evidence_expiry_is_bounded_by_artifact_retention() -> None:
    observed_at = datetime(2026, 8, 2, 12, 0, tzinfo=UTC)
    expiry = calculate_evidence_expiry(
        observed_at=observed_at,
        evidence_freshness_days=30,
        artifact_retention_days=30,
        artifact_safety_margin_days=3,
    )
    assert expiry == datetime(2026, 8, 29, 12, 0, tzinfo=UTC)
