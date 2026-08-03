from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from fastapi import HTTPException

from axignal_api import billing_reconciliation_routes as routes
from axignal_api.billing_config import EXPECTED_AXIGNAL_STRIPE_ACCOUNT_ID
from axignal_api.identity import AuthenticatedIdentity

TENANT_ID = UUID("11111111-1111-4111-8111-111111111111")
SELECTION_ID = UUID("22222222-2222-4222-8222-222222222222")
PERIOD_END = datetime(2026, 9, 1, tzinfo=UTC)


def _configure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AXIGNAL_BILLING_DATABASE_URL", "postgresql://test/axignal")
    monkeypatch.setenv("AXIGNAL_BILLING_RUNTIME_ENABLED", "true")
    monkeypatch.setenv("AXIGNAL_STRIPE_CHECKOUT_ENABLED", "true")
    monkeypatch.setenv("AXIGNAL_STRIPE_LIFECYCLE_ENABLED", "true")
    monkeypatch.setenv("AXIGNAL_BILLING_PROVIDER", "test")
    monkeypatch.setenv("AXIGNAL_ENVIRONMENT", "test")
    monkeypatch.setenv("AXIGNAL_TEST_RUNTIME_ENABLED", "true")
    monkeypatch.setenv("AXIGNAL_STRIPE_ACCOUNT_ID", EXPECTED_AXIGNAL_STRIPE_ACCOUNT_ID)
    monkeypatch.setenv("AXIGNAL_TEST_CHECKOUT_BASE_URL", "http://localhost/test-checkout")
    monkeypatch.setenv(
        "AXIGNAL_STRIPE_PRICE_PROFESSIONAL_MONTHLY",
        "price_test_professional_monthly",
    )
    monkeypatch.setenv("AXIGNAL_STRIPE_PRICE_TEAM_MONTHLY", "price_test_team_monthly")


def _identity(subject: str = "usr_owner") -> AuthenticatedIdentity:
    now = datetime.now(UTC)
    return AuthenticatedIdentity(
        subject=subject,
        email=f"{subject}@example.test",
        tenant_id=TENANT_ID,
        issued_at=now,
        expires_at=now + timedelta(minutes=1),
    )


class FakeBillingRepository:
    applied: list[dict] = []

    def __init__(self, dsn: str) -> None:
        assert dsn == "postgresql://test/axignal"
        self.reads = 0

    def current_selection(self, *, tenant_id: UUID) -> dict:
        assert tenant_id == TENANT_ID
        self.reads += 1
        return {
            "selection_id": SELECTION_ID,
            "tenant_id": TENANT_ID,
            "selected_by": "usr_owner",
            "plan_code": "PROFESSIONAL_MONTHLY",
            "state": "ACTIVE" if self.reads > 1 else "SUSPENDED",
            "stripe_checkout_session_id": "cs_test_axignal",
            "stripe_customer_id": "cus_test_axignal",
            "stripe_subscription_id": "sub_test_axignal",
            "stripe_subscription_item_id": "si_test_axignal",
            "stripe_price_id": "price_test_professional_monthly",
            "current_period_end": PERIOD_END,
            "cancel_at_period_end": False,
            "last_provider_event_created_at": datetime(2026, 8, 1, tzinfo=UTC),
        }

    def apply_stripe_event(self, **kwargs) -> dict:
        self.applied.append(kwargs)
        return {"disposition": "APPLIED", "state": "ACTIVE"}


class FakeSeatRepository:
    def __init__(self, dsn: str) -> None:
        assert dsn == "postgresql://test/axignal"

    def summary(self, *, tenant_id: UUID) -> dict:
        assert tenant_id == TENANT_ID
        return {
            "seat_entitlement": {"seat_capacity": 3},
            "occupied_seats": 1,
            "available_seats": 2,
        }


def test_reconciliation_repairs_from_provider_snapshot_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure(monkeypatch)
    FakeBillingRepository.applied = []
    monkeypatch.setattr(routes, "BillingRepository", FakeBillingRepository)
    monkeypatch.setattr(routes, "SeatRepository", FakeSeatRepository)

    result = routes.reconcile_subscription(_identity())

    assert result.result == "REPAIRED"
    assert result.drift_fields == ["state"]
    assert result.local_state == "ACTIVE"
    assert result.provider_state == "ACTIVE"
    assert result.seat_capacity == 3
    assert result.occupied_seats == 1
    assert result.available_seats == 2
    assert result.browser_entitlement_authority is False
    assert len(FakeBillingRepository.applied) == 1
    applied = FakeBillingRepository.applied[0]
    assert applied["selection_id"] == SELECTION_ID
    assert applied["plan_code"] == "PROFESSIONAL_MONTHLY"
    assert applied["subscription_status"] == "active"
    assert applied["actor_subject"] == "stripe-reconciliation"
    assert applied["payload_digest"] == result.snapshot_digest


def test_reconciliation_rejects_unrelated_subject_without_admin_role(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure(monkeypatch)
    monkeypatch.setattr(routes, "BillingRepository", FakeBillingRepository)
    monkeypatch.setattr(routes, "SeatRepository", FakeSeatRepository)

    with pytest.raises(HTTPException) as exc_info:
        routes.reconcile_subscription(_identity("usr_unrelated"))

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Billing administration role required"
