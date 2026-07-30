from __future__ import annotations

from uuid import UUID

from fastapi.testclient import TestClient

from axignal_api.application import app
from axignal_api.billing_config import EXPECTED_AXIGNAL_STRIPE_ACCOUNT_ID
from axignal_api.identity import build_identity_assertion

TENANT_ID = UUID("44444444-4444-4444-8444-444444444444")
IDENTITY_SECRET = "test-route-identity-secret-with-at-least-32-bytes"


def _headers() -> dict[str, str]:
    return {
        "X-AXIGNAL-Identity-Assertion": build_identity_assertion(
            secret=IDENTITY_SECRET,
            subject="usr_billing_route_test",
            email="billing-route@example.test",
            tenant_id=TENANT_ID,
        )
    }


def test_deterministic_provider_route_requires_identity(monkeypatch) -> None:
    monkeypatch.setenv("AXIGNAL_IDENTITY_ASSERTION_SECRET", IDENTITY_SECRET)
    response = TestClient(app).post(
        "/v1/billing/test/provider-event",
        json={"action": "COMPLETE_CHECKOUT"},
    )
    assert response.status_code == 401


def test_deterministic_provider_route_fails_closed_in_production(monkeypatch) -> None:
    monkeypatch.setenv("AXIGNAL_IDENTITY_ASSERTION_SECRET", IDENTITY_SECRET)
    monkeypatch.setenv("AXIGNAL_BILLING_DATABASE_URL", "postgresql://example.invalid/axignal")
    monkeypatch.setenv("AXIGNAL_BILLING_RUNTIME_ENABLED", "true")
    monkeypatch.setenv("AXIGNAL_STRIPE_WEBHOOKS_ENABLED", "true")
    monkeypatch.setenv("AXIGNAL_BILLING_PROVIDER", "test")
    monkeypatch.setenv("AXIGNAL_ENVIRONMENT", "production")
    monkeypatch.setenv("AXIGNAL_TEST_RUNTIME_ENABLED", "true")
    monkeypatch.setenv("AXIGNAL_STRIPE_ACCOUNT_ID", EXPECTED_AXIGNAL_STRIPE_ACCOUNT_ID)
    monkeypatch.setenv("AXIGNAL_STRIPE_WEBHOOK_SECRET", "whsec_test_route")
    monkeypatch.setenv(
        "AXIGNAL_TEST_CHECKOUT_BASE_URL",
        "http://127.0.0.1:3000/billing/test-checkout",
    )
    response = TestClient(app).post(
        "/v1/billing/test/provider-event",
        headers=_headers(),
        json={"action": "COMPLETE_CHECKOUT"},
    )
    assert response.status_code == 503
    assert "isolated test runtime" in response.json()["detail"]


def test_deterministic_provider_route_rejects_unknown_action(monkeypatch) -> None:
    monkeypatch.setenv("AXIGNAL_IDENTITY_ASSERTION_SECRET", IDENTITY_SECRET)
    response = TestClient(app).post(
        "/v1/billing/test/provider-event",
        headers=_headers(),
        json={"action": "ACTIVATE_ENTITLEMENT_DIRECTLY"},
    )
    assert response.status_code == 422
