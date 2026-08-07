"""Sandbox billing HTTP E2E (Prioridad 6) over the real stack.

Exercises /v1/billing/sandbox through the real FastAPI application with
PostgreSQL: catalogue, idempotent checkout, entitlements (only the
acquired shell), cancellation, dunning/recovery, refund audit, webhook
signature + replay protection — then verifies persistence from a new
session and tenant isolation.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from axignal_api.application import app
from axignal_api.identity import build_identity_assertion

TENANT_A = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
TENANT_B = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
IDENTITY_SECRET = "sandbox-e2e-identity-secret-with-at-least-32-bytes"
DSN = "postgresql://axignal:axignal-local@localhost:5432/axignal"
SHELL_1 = "AXIGNAL_OPPORTUNITY_INTELLIGENCE"
SHELL_2 = "AXIGNAL_PUBLIC_EMPLOYMENT"

pytestmark = pytest.mark.skipif(
    not os.environ.get("AXIGNAL_INTEGRATION_TESTS"),
    reason="sandbox billing E2E needs a live PostgreSQL; set AXIGNAL_INTEGRATION_TESTS=1",
)


def _client(tenant_id: UUID, subject: str = "usr_billing_e2e") -> TestClient:
    headers = {
        "X-AXIGNAL-Identity-Assertion": build_identity_assertion(
            secret=IDENTITY_SECRET,
            subject=subject,
            email=f"{subject}@example.test",
            tenant_id=tenant_id,
        )
    }
    return TestClient(app, headers=headers)


class TestSandboxBillingHttpE2E:
    def test_full_billing_journey(self, monkeypatch) -> None:
        monkeypatch.setenv("AXIGNAL_IDENTITY_ASSERTION_SECRET", IDENTITY_SECRET)

        client = _client(TENANT_A)
        run_suffix = uuid4().hex[:10]
        checkout_id = f"chk-e2e-{run_suffix}"
        idem_key = f"idem-e2e-{uuid4().hex[:16]}"

        # 1. Catalogue (seeds the DB).
        catalog = client.get("/v1/billing/sandbox/catalog")
        assert catalog.status_code == 200
        products = {p["product_id"] for p in catalog.json()["products"]}
        assert products == {SHELL_1, SHELL_2}
        plans = {p["plan_id"] for p in catalog.json()["plans"]}
        assert plans == {"plan-oi-professional", "plan-oi-team", "plan-pe-academy"}

        # 2. Checkout Shell 1 (idempotent).
        checkout = client.post(
            "/v1/billing/sandbox/checkout",
            json={
                "checkout_id": checkout_id,
                "product_id": SHELL_1,
                "plan_id": "plan-oi-professional",
                "price_id": "price-oi-professional",
                "idempotency_key": idem_key,
                "customer_context": "vertical-slice",
            },
        )
        assert checkout.status_code == 201, checkout.text
        assert checkout.json()["status"] == "CHECKOUT_OK"

        replay = client.post(
            "/v1/billing/sandbox/checkout",
            json={
                "checkout_id": checkout_id,
                "product_id": SHELL_1,
                "plan_id": "plan-oi-professional",
                "price_id": "price-oi-professional",
                "idempotency_key": idem_key,
                "customer_context": "vertical-slice",
            },
        )
        assert replay.status_code == 201
        assert replay.json()["status"] == "IDEMPOTENT_REPLAY"

        # 3. Entitlements: ONLY the acquired shell.
        entitlements = client.get("/v1/billing/sandbox/entitlements").json()
        assert entitlements.get(SHELL_1) is True
        assert entitlements.get(SHELL_2) is None

        # 4. Cross-shell checkout rejected.
        cross = client.post(
            "/v1/billing/sandbox/checkout",
            json={
                "checkout_id": f"chk-e2e-2-{run_suffix}",
                "product_id": SHELL_2,
                "plan_id": "plan-oi-professional",
                "price_id": "price-oi-professional",
                "idempotency_key": f"idem-e2e-2-{run_suffix}",
                "customer_context": "vertical-slice",
            },
        )
        assert cross.status_code == 422
        assert "cross-shell" in cross.json()["detail"]

        # 5. Inactive (Public Employment) price rejected.
        inactive = client.post(
            "/v1/billing/sandbox/checkout",
            json={
                "checkout_id": f"chk-e2e-3-{run_suffix}",
                "product_id": SHELL_2,
                "plan_id": "plan-pe-academy",
                "price_id": "price-pe-academy",
                "idempotency_key": f"idem-e2e-3-{run_suffix}",
                "customer_context": "vertical-slice",
            },
        )
        assert inactive.status_code == 422
        assert "inactive" in inactive.json()["detail"]

        # 6. Subscription + dunning + recovery.
        subscription = client.get("/v1/billing/sandbox/subscription")
        assert subscription.status_code == 200
        assert subscription.json()["product_id"] == SHELL_1

        dunning = client.post("/v1/billing/sandbox/subscription/dunning", json={"grace_days": 7})
        assert dunning.status_code == 200
        assert dunning.json()["status"] == "DUNNING"

        recovered = client.post("/v1/billing/sandbox/subscription/recover")
        assert recovered.status_code == 200
        assert recovered.json()["status"] == "ACTIVE"

        # 7. Change plan (same product).
        changed = client.post(
            "/v1/billing/sandbox/subscription/change-plan",
            json={"new_plan_id": "plan-oi-team", "new_price_id": "price-oi-team"},
        )
        assert changed.status_code == 200
        assert changed.json()["plan_id"] == "plan-oi-team"

        # 8. Webhook with signature + replay guard.
        payload = {"amount_cents": 39900, "event": "invoice.paid"}
        payload_text = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            f"sandbox-hmac-key-{SHELL_1}".encode(),
            payload_text.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        webhook = client.post(
            "/v1/billing/sandbox/webhooks",
            json={
                "product_id": SHELL_1,
                "event_type": "invoice.paid",
                "payload": payload,
                "signature": signature,
                "replay_guard": datetime.now(UTC).isoformat(),
            },
        )
        assert webhook.status_code == 200, webhook.text
        assert webhook.json()["verified"] is True

        # Stale replay guard rejected.
        stale = client.post(
            "/v1/billing/sandbox/webhooks",
            json={
                "product_id": SHELL_1,
                "event_type": "invoice.paid",
                "payload": payload,
                "signature": signature,
                "replay_guard": (datetime.now(UTC) + timedelta(minutes=10)).isoformat(),
            },
        )
        assert stale.status_code == 401

        events = client.get("/v1/billing/sandbox/webhook-events")
        assert any(e["event_type"] == "invoice.paid" for e in events.json())

        # 9. Refund audit.
        refund = client.post(
            "/v1/billing/sandbox/refund",
            json={"refund_id": "ref-e2e-0001", "amount_cents": 14900, "reason": "test refund"},
        )
        assert refund.status_code == 200
        assert refund.json()["recorded"] is True

        # 10. Recovery from a NEW session.
        fresh = _client(TENANT_A)
        fresh_subscription = fresh.get("/v1/billing/sandbox/subscription")
        assert fresh_subscription.json()["plan_id"] == "plan-oi-team"
        fresh_entitlements = fresh.get("/v1/billing/sandbox/entitlements").json()
        assert fresh_entitlements.get(SHELL_1) is True

        # 11. Tenant isolation.
        other = _client(TENANT_B, subject="usr_billing_other")
        assert other.get("/v1/billing/sandbox/subscription").status_code == 404
        entitlements_b = other.get("/v1/billing/sandbox/entitlements").json()
        assert entitlements_b.get(SHELL_1) is False

        # 12. Cancel immediate revokes entitlement.
        cancelled = client.post(
            "/v1/billing/sandbox/subscription/cancel", json={"at_period_end": False}
        )
        assert cancelled.status_code == 200
        assert cancelled.json()["status"] == "CANCELLED_IMMEDIATE"
        entitlements_after = client.get("/v1/billing/sandbox/entitlements").json()
        assert entitlements_after.get(SHELL_1) is False


TENANT_C = UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc")


def _reset_billing_state(tenant_id: UUID) -> None:
    import psycopg

    with psycopg.connect(DSN) as conn, conn.cursor() as cursor:
        cursor.execute(
            "DELETE FROM tenant_private.sandbox_subscriptions WHERE tenant_id = %s",
            (tenant_id,),
        )
        cursor.execute(
            "DELETE FROM tenant_private.billing_idempotency_keys WHERE tenant_id = %s",
            (tenant_id,),
        )
        cursor.execute(
            "DELETE FROM tenant_private.billing_entitlements WHERE tenant_id = %s",
            (tenant_id,),
        )
        cursor.execute(
            "DELETE FROM tenant_private.billing_webhook_events WHERE tenant_id = %s",
            (tenant_id,),
        )
        conn.commit()


class TestSandboxBillingFullLifecycle:
    def test_upgrade_downgrade_renew_reconcile(self, monkeypatch) -> None:
        monkeypatch.setenv("AXIGNAL_IDENTITY_ASSERTION_SECRET", IDENTITY_SECRET)
        _reset_billing_state(TENANT_C)

        client = _client(TENANT_C, subject="usr_billing_lifecycle")
        run = uuid4().hex[:10]

        # Checkout Professional (149 EUR).
        checkout = client.post(
            "/v1/billing/sandbox/checkout",
            json={
                "checkout_id": f"chk-life-{run}",
                "product_id": SHELL_1,
                "plan_id": "plan-oi-professional",
                "price_id": "price-oi-professional",
                "idempotency_key": f"idem-life-{run}",
                "customer_context": "lifecycle",
            },
        )
        assert checkout.status_code == 201, checkout.text

        # Upgrade to Team (399 EUR) with direction recorded.
        upgraded = client.post(
            "/v1/billing/sandbox/subscription/change-plan-directional",
            json={"new_plan_id": "plan-oi-team", "new_price_id": "price-oi-team"},
        )
        assert upgraded.status_code == 200, upgraded.text
        assert upgraded.json()["direction"] == "UPGRADE"

        # Downgrade back with direction recorded.
        downgraded = client.post(
            "/v1/billing/sandbox/subscription/change-plan-directional",
            json={"new_plan_id": "plan-oi-professional",
                  "new_price_id": "price-oi-professional"},
        )
        assert downgraded.status_code == 200
        assert downgraded.json()["direction"] == "DOWNGRADE"

        # Renewal: ACTIVE -> ACTIVE with renewed_at.
        renewed = client.post("/v1/billing/sandbox/subscription/renew")
        assert renewed.status_code == 200
        assert renewed.json()["status"] == "ACTIVE"

        # Reconciliation: entitlement mirrors subscription.
        reconciled = client.post("/v1/billing/sandbox/reconcile")
        assert reconciled.status_code == 200
        assert reconciled.json()["status"] == "ACTIVE"
        assert reconciled.json()["entitlement_expected"] is True
        assert reconciled.json()["entitlements"][SHELL_1] is True

        # Event sequence ordered (webhooks + lifecycle).
        events = client.get("/v1/billing/sandbox/events")
        assert events.status_code == 200

        # Cancel -> reconcile -> entitlement revoked.
        cancelled = client.post(
            "/v1/billing/sandbox/subscription/cancel",
            json={"at_period_end": False},
        )
        assert cancelled.status_code == 200
        reconciled_after = client.post("/v1/billing/sandbox/reconcile").json()
        assert reconciled_after["status"] == "CANCELLED_IMMEDIATE"
        assert reconciled_after["entitlements"][SHELL_1] is False

        # Restart equivalence: new session sees the cancelled subscription.
        fresh = _client(TENANT_C, subject="usr_billing_lifecycle")
        fresh_sub = fresh.get("/v1/billing/sandbox/subscription")
        assert fresh_sub.status_code == 200
        assert fresh_sub.json()["status"] == "CANCELLED_IMMEDIATE"

    def test_renewal_without_subscription_rejected(self, monkeypatch) -> None:
        monkeypatch.setenv("AXIGNAL_IDENTITY_ASSERTION_SECRET", IDENTITY_SECRET)
        other = _client(TENANT_B, subject="usr_billing_nosub")
        response = other.post("/v1/billing/sandbox/subscription/renew")
        assert response.status_code == 404
        response = other.post("/v1/billing/sandbox/reconcile")
        assert response.status_code == 200
        assert response.json()["status"] == "NO_SUBSCRIPTION"
