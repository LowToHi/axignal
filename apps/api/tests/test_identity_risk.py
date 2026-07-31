from __future__ import annotations

import pytest

from axignal_api.identity_config import IdentityRuntimeSettings
from axignal_api.identity_delivery import verify_bot_token
from axignal_api.identity_risk import (
    domain_is_disposable,
    email_identity_key,
    network_prefix,
    risk_subjects,
)

PEPPER = "p" * 48


def test_gmail_aliases_resolve_to_one_strong_identity() -> None:
    assert email_identity_key("First.Last+sales@gmail.com") == "firstlast@gmail.com"
    assert email_identity_key("firstlast@googlemail.com") == "firstlast@gmail.com"


def test_weak_network_signal_uses_bounded_prefix() -> None:
    assert network_prefix("203.0.113.42") == "203.0.113.0/24"
    assert network_prefix("2001:db8:abcd:1234::7") == "2001:db8:abcd:1200::/56"
    assert network_prefix("invalid") == "unknown"


def test_risk_subjects_do_not_store_raw_values() -> None:
    subjects = risk_subjects(
        email="buyer@example.test",
        installation_id="installation_identifier_123456",
        network="203.0.113.42",
        pepper=PEPPER,
    )
    assert subjects["email_normalized"] == "buyer@example.test"
    assert len(subjects["email_identity_hmac"]) == 64
    assert "buyer" not in subjects["email_identity_hmac"]
    assert "203.0.113" not in subjects["network_hmac"]


def test_disposable_domain_is_only_a_risk_signal() -> None:
    assert domain_is_disposable("person@yopmail.com") is True
    assert domain_is_disposable("person@example.com") is False


def _settings(**overrides: object) -> IdentityRuntimeSettings:
    values: dict[str, object] = {
        "enabled": True,
        "database_url": "postgresql://example",
        "environment": "test",
        "test_runtime_enabled": True,
        "public_app_url": "http://127.0.0.1:18080",
        "rp_id": "127.0.0.1",
        "rp_name": "AXIGNAL",
        "expected_origin": "http://127.0.0.1:18080",
        "identity_pepper": PEPPER,
        "session_idle_seconds": 3600,
        "session_absolute_seconds": 86400,
        "session_touch_interval_seconds": 300,
        "challenge_ttl_seconds": 600,
        "email_provider": "test",
        "bot_provider": "test",
        "turnstile_secret": None,
        "smtp_host": None,
        "smtp_port": 587,
        "smtp_username": None,
        "smtp_password": None,
        "smtp_from": None,
        "smtp_starttls": True,
        "trusted_proxy_headers": False,
        "trial_full_token_budget": 1_000_000,
        "trial_restricted_token_budget": 250_000,
        "trial_full_cost_budget_microunits": 5_000_000,
        "trial_restricted_cost_budget_microunits": 1_000_000,
    }
    values.update(overrides)
    return IdentityRuntimeSettings(**values)  # type: ignore[arg-type]


def test_identity_runtime_requires_exact_trial_budget() -> None:
    with pytest.raises(RuntimeError, match="1,000,000"):
        _settings(trial_full_token_budget=999_999).require_runtime()


def test_test_providers_are_confined_to_test_runtime() -> None:
    settings = _settings(environment="production")
    with pytest.raises(RuntimeError, match="restricted to the test runtime"):
        settings.require_email_delivery()
    with pytest.raises(RuntimeError, match="restricted to the test runtime"):
        settings.require_bot_verification()


def test_test_bot_token_is_server_verified() -> None:
    settings = _settings()
    verify_bot_token(
        settings=settings,
        token="axignal-test-bot-pass",
        remote_ip="127.0.0.1",
    )
    with pytest.raises(RuntimeError, match="bot_verification_failed"):
        verify_bot_token(settings=settings, token="wrong", remote_ip="127.0.0.1")
