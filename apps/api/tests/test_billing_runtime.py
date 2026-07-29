from __future__ import annotations

import json
import time
from uuid import UUID

from fastapi.testclient import TestClient

from axignal_api.application import app
from axignal_api.billing_config import (
    EXPECTED_AXIGNAL_STRIPE_ACCOUNT_ID,
    BillingSettings,
)
from axignal_api.identity import build_identity_assertion
from axignal_api.stripe_signature import (
    build_test_stripe_signature,
    verify_stripe_signature,
)

TENANT_ID = UUID("11111111-1111-4111-8111-111111111111")
OTHER_TENANT_ID = UUID("22222222-2222-4222-8222-222222222222")
IDENTITY_SECRET = "test-billing-identity-secret-with-at-least-32-bytes"
WEBHOOK_SECRET = "whsec_test_billing_signature_secret"


def identity_headers() -> dict[str, str]:
    return {
        "X-AXIGNAL-Identity-Assertion": build_identity_assertion(
            secret=IDENTITY_SECRET,
            subject="usr_billing_test",
            email="billing@example.test",
            tenant_id=TENANT_ID,
        )
    }


def test_billing_runtime_is_disabled_and_sandbox_only_by_default(monkeypatch) -> None:
    for name in (
        "AXIGNAL_BILLING_DATABASE_URL",
        "AXIGNAL_DATABASE_URL",
        "AXIGNAL_BILLING_RUNTIME_ENABLED",
        "AXIGNAL_STRIPE_CHECKOUT_ENABLED",
        "AXIGNAL_STRIPE_WEBHOOKS_ENABLED",
        "AXIGNAL_STRIPE_LIFECYCLE_ENABLED",
        "AXIGNAL_STRIPE_SANDBOX_ONLY",
        "AXIGNAL_STRIPE_SECRET_KEY",
    ):
        monkeypatch.delenv(name, raising=False)
    settings = BillingSettings.from_env()
    assert settings.database_url is None
    assert settings.billing_runtime_enabled is False
    assert settings.stripe_checkout_enabled is False
    assert settings.stripe_webhooks_enabled is False
    assert settings.stripe_lifecycle_enabled is False
    assert settings.stripe_sandbox_only is True


def test_checkout_rejects_wrong_account_and_live_secret(monkeypatch) -> None:
    monkeypatch.setenv("AXIGNAL_DATABASE_URL", "postgresql://example.invalid/axignal")
    monkeypatch.setenv("AXIGNAL_BILLING_RUNTIME_ENABLED", "true")
    monkeypatch.setenv("AXIGNAL_STRIPE_CHECKOUT_ENABLED", "true")
    monkeypatch.setenv("AXIGNAL_STRIPE_ACCOUNT_ID", "acct_wrong")
    monkeypatch.setenv("AXIGNAL_STRIPE_SECRET_KEY", "sk_live_forbidden")
    settings = BillingSettings.from_env()
    try:
        settings.require_checkout()
    except RuntimeError as exc:
        assert "account mismatch" in str(exc)
    else:
        raise AssertionError("Wrong Stripe account was accepted")

    monkeypatch.setenv("AXIGNAL_STRIPE_ACCOUNT_ID", EXPECTED_AXIGNAL_STRIPE_ACCOUNT_ID)
    settings = BillingSettings.from_env()
    try:
        settings.require_checkout()
    except RuntimeError as exc:
        assert "live Stripe secret" in str(exc)
    else:
        raise AssertionError("Live Stripe secret was accepted")


def test_stripe_signature_accepts_valid_and_rejects_forged_or_stale() -> None:
    payload = b'{"id":"evt_test","type":"invoice.paid"}'
    now = int(time.time())
    header = build_test_stripe_signature(
        payload=payload, secret=WEBHOOK_SECRET, timestamp=now
    )
    verified = verify_stripe_signature(
        payload=payload,
        header=header,
        secret=WEBHOOK_SECRET,
        tolerance_seconds=300,
        now=now,
    )
    assert verified.timestamp == now

    try:
        verify_stripe_signature(
            payload=payload + b" ",
            header=header,
            secret=WEBHOOK_SECRET,
            tolerance_seconds=300,
            now=now,
        )
    except ValueError as exc:
        assert str(exc) == "stripe_signature_mismatch"
    else:
        raise AssertionError("Forged Stripe payload was accepted")

    stale = build_test_stripe_signature(
        payload=payload, secret=WEBHOOK_SECRET, timestamp=now - 301
    )
    try:
        verify_stripe_signature(
            payload=payload,
            header=stale,
            secret=WEBHOOK_SECRET,
            tolerance_seconds=300,
            now=now,
        )
    except ValueError as exc:
        assert str(exc) == "stripe_signature_tolerance_exceeded"
    else:
        raise AssertionError("Stale Stripe signature was accepted")


def test_paid_selection_requires_authenticated_identity(monkeypatch) -> None:
    monkeypatch.setenv("AXIGNAL_IDENTITY_ASSERTION_SECRET", IDENTITY_SECRET)
    response = TestClient(app).post(
        "/v1/billing/checkout-sessions",
        json={
            "operation_id": "op_checkout_missing_identity",
            "plan_code": "PROFESSIONAL_MONTHLY",
            "confirm_paid_selection": True,
        },
    )
    assert response.status_code == 401


def test_paid_selection_rejects_client_tenant_injection(monkeypatch) -> None:
    monkeypatch.setenv("AXIGNAL_IDENTITY_ASSERTION_SECRET", IDENTITY_SECRET)
    response = TestClient(app).post(
        "/v1/billing/checkout-sessions",
        headers=identity_headers(),
        json={
            "operation_id": "op_checkout_tenant_injection",
            "plan_code": "PROFESSIONAL_MONTHLY",
            "confirm_paid_selection": True,
            "tenant_id": str(OTHER_TENANT_ID),
        },
    )
    assert response.status_code == 422
    locations = [tuple(item["loc"]) for item in response.json()["detail"]]
    assert ("body", "tenant_id") in locations


def test_paid_selection_fails_closed_when_runtime_disabled(monkeypatch) -> None:
    monkeypatch.setenv("AXIGNAL_IDENTITY_ASSERTION_SECRET", IDENTITY_SECRET)
    monkeypatch.setenv("AXIGNAL_BILLING_DATABASE_URL", "postgresql://example.invalid/axignal")
    monkeypatch.delenv("AXIGNAL_BILLING_RUNTIME_ENABLED", raising=False)
    response = TestClient(app).post(
        "/v1/billing/checkout-sessions",
        headers=identity_headers(),
        json={
            "operation_id": "op_checkout_runtime_disabled",
            "plan_code": "PROFESSIONAL_MONTHLY",
            "confirm_paid_selection": True,
        },
    )
    assert response.status_code == 503
    assert response.json()["detail"] == "AXIGNAL billing runtime is disabled"


def test_webhook_rejects_missing_signature_before_store_access(monkeypatch) -> None:
    monkeypatch.setenv("AXIGNAL_BILLING_DATABASE_URL", "postgresql://example.invalid/axignal")
    monkeypatch.setenv("AXIGNAL_BILLING_RUNTIME_ENABLED", "true")
    monkeypatch.setenv("AXIGNAL_STRIPE_WEBHOOKS_ENABLED", "true")
    monkeypatch.setenv("AXIGNAL_STRIPE_ACCOUNT_ID", EXPECTED_AXIGNAL_STRIPE_ACCOUNT_ID)
    monkeypatch.setenv("AXIGNAL_STRIPE_WEBHOOK_SECRET", WEBHOOK_SECRET)
    payload = json.dumps(
        {
            "id": "evt_missing_signature",
            "type": "invoice.paid",
            "created": int(time.time()),
            "livemode": False,
            "data": {"object": {}},
        }
    ).encode()
    response = TestClient(app).post(
        "/v1/billing/stripe/webhook",
        content=payload,
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid Stripe webhook"
