from __future__ import annotations

from uuid import UUID

import pytest

from axignal_api.billing_config import (
    EXPECTED_AXIGNAL_STRIPE_ACCOUNT_ID,
    BillingSettings,
)
from axignal_api.billing_provider import (
    DeterministicTestBillingProvider,
    StripeBillingProvider,
    billing_provider,
)

SELECTION_ID = UUID("33333333-3333-4333-8333-333333333333")


def _configure_common(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AXIGNAL_BILLING_DATABASE_URL", "postgresql://test/axignal")
    monkeypatch.setenv("AXIGNAL_BILLING_RUNTIME_ENABLED", "true")
    monkeypatch.setenv("AXIGNAL_STRIPE_CHECKOUT_ENABLED", "true")
    monkeypatch.setenv("AXIGNAL_STRIPE_ACCOUNT_ID", EXPECTED_AXIGNAL_STRIPE_ACCOUNT_ID)
    monkeypatch.setenv(
        "AXIGNAL_STRIPE_PRICE_PROFESSIONAL_MONTHLY",
        "price_test_professional_monthly",
    )
    monkeypatch.setenv("AXIGNAL_STRIPE_PRICE_TEAM_MONTHLY", "price_test_team_monthly")


def test_production_defaults_to_stripe_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    _configure_common(monkeypatch)
    monkeypatch.setenv("AXIGNAL_STRIPE_SECRET_KEY", "sk_test_provider_contract")
    monkeypatch.setenv("AXIGNAL_STRIPE_API_VERSION", "2026-06-24.preview")
    monkeypatch.setenv(
        "AXIGNAL_STRIPE_CHECKOUT_SUCCESS_URL",
        "https://app.axignal.test/billing/success",
    )
    monkeypatch.setenv(
        "AXIGNAL_STRIPE_CHECKOUT_CANCEL_URL",
        "https://app.axignal.test/billing/cancel",
    )
    settings = BillingSettings.from_env()
    assert settings.billing_provider == "stripe"
    assert isinstance(billing_provider(settings), StripeBillingProvider)


@pytest.mark.parametrize(
    ("environment", "test_runtime_enabled"),
    [("production", "true"), ("test", "false"), ("staging", "false")],
)
def test_deterministic_provider_fails_closed_outside_isolated_test_runtime(
    monkeypatch: pytest.MonkeyPatch,
    environment: str,
    test_runtime_enabled: str,
) -> None:
    _configure_common(monkeypatch)
    monkeypatch.setenv("AXIGNAL_BILLING_PROVIDER", "test")
    monkeypatch.setenv("AXIGNAL_ENVIRONMENT", environment)
    monkeypatch.setenv("AXIGNAL_TEST_RUNTIME_ENABLED", test_runtime_enabled)
    monkeypatch.setenv(
        "AXIGNAL_TEST_CHECKOUT_BASE_URL",
        "http://127.0.0.1:3000/billing/test-checkout",
    )
    with pytest.raises(RuntimeError, match="isolated test runtime"):
        billing_provider(BillingSettings.from_env())


def test_deterministic_provider_returns_local_checkout_without_granting_access(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure_common(monkeypatch)
    monkeypatch.setenv("AXIGNAL_BILLING_PROVIDER", "test")
    monkeypatch.setenv("AXIGNAL_ENVIRONMENT", "test")
    monkeypatch.setenv("AXIGNAL_TEST_RUNTIME_ENABLED", "true")
    monkeypatch.setenv(
        "AXIGNAL_TEST_CHECKOUT_BASE_URL",
        "http://127.0.0.1:3000/billing/test-checkout",
    )
    provider = billing_provider(BillingSettings.from_env())
    assert isinstance(provider, DeterministicTestBillingProvider)

    checkout = provider.create_checkout_session(
        selection_id=SELECTION_ID,
        plan_code="PROFESSIONAL_MONTHLY",
        customer_email="ignored@example.test",
        operation_id="op_provider_checkout_test",
    )
    assert checkout.session_id == f"cs_test_axignal_{SELECTION_ID.hex}"
    assert checkout.price_id == "price_test_professional_monthly"
    assert "selection_id=33333333-3333-4333-8333-333333333333" in checkout.url
    assert "plan_code=PROFESSIONAL_MONTHLY" in checkout.url

    upgrade = provider.upgrade_subscription(
        subscription_id="sub_test_axignal",
        subscription_item_id="si_test_axignal",
        target_plan_code="TEAM_MONTHLY",
        operation_id="op_provider_upgrade_test",
    )
    assert upgrade.status == "pending_signed_event"

    cancellation = provider.cancel_subscription(
        subscription_id="sub_test_axignal",
        cancel_at_period_end=True,
        operation_id="op_provider_cancel_test",
    )
    assert cancellation.status == "pending_signed_event"
    assert cancellation.cancel_at_period_end is True
