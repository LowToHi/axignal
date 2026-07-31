from __future__ import annotations

from axignal_api.seat_config import SeatSettings
from axignal_api.seat_delivery import (
    SeatInvitationDelivery,
    create_invitation_secret,
    digest_invitation_token,
)


def test_invitation_secret_is_random_and_digestable() -> None:
    first = create_invitation_secret()
    second = create_invitation_secret()
    assert first.token != second.token
    assert len(first.digest) == 64
    assert digest_invitation_token(first.token) == first.digest


def test_test_delivery_provider_is_fail_closed_outside_test(monkeypatch) -> None:
    monkeypatch.setenv("AXIGNAL_SEAT_GOVERNANCE_ENABLED", "true")
    monkeypatch.setenv("AXIGNAL_DATABASE_URL", "postgresql://example.invalid/axignal")
    monkeypatch.setenv("AXIGNAL_SEAT_INVITATION_PROVIDER", "test")
    monkeypatch.setenv("AXIGNAL_ENVIRONMENT", "production")
    monkeypatch.setenv("AXIGNAL_TEST_RUNTIME_ENABLED", "false")
    settings = SeatSettings.from_env()
    try:
        settings.require_invitation_delivery()
    except RuntimeError as exc:
        assert "restricted to the test runtime" in str(exc)
    else:
        raise AssertionError("Test invitation delivery was accepted outside test")


def test_test_delivery_returns_token_only_in_test_runtime(monkeypatch) -> None:
    monkeypatch.setenv("AXIGNAL_SEAT_GOVERNANCE_ENABLED", "true")
    monkeypatch.setenv("AXIGNAL_DATABASE_URL", "postgresql://example.invalid/axignal")
    monkeypatch.setenv("AXIGNAL_SEAT_INVITATION_PROVIDER", "test")
    monkeypatch.setenv("AXIGNAL_ENVIRONMENT", "test")
    monkeypatch.setenv("AXIGNAL_TEST_RUNTIME_ENABLED", "true")
    settings = SeatSettings.from_env()
    receipt = SeatInvitationDelivery(settings).deliver(
        recipient_email="member@example.test",
        token="opaque-test-token",
        inviter_email="owner@example.test",
        expires_at_iso="2026-08-01T00:00:00+00:00",
    )
    assert receipt.provider == "TEST"
    assert receipt.delivered is True
    assert receipt.test_acceptance_token == "opaque-test-token"
