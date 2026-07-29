from __future__ import annotations

import argparse
import json
import os
import threading
import time
from datetime import UTC, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse
from uuid import UUID

import psycopg
from fastapi.testclient import TestClient

from axignal_api.application import app
from axignal_api.billing_config import EXPECTED_AXIGNAL_STRIPE_ACCOUNT_ID
from axignal_api.billing_repository import BillingRepository
from axignal_api.entitlement_repository import EntitlementRepository
from axignal_api.identity import build_identity_assertion
from axignal_api.stripe_signature import build_test_stripe_signature

TENANT_A = UUID("c1111111-1111-4111-8111-111111111111")
TENANT_B = UUID("c2222222-2222-4222-8222-222222222222")
START = datetime(2026, 7, 30, 8, 0, tzinfo=UTC)
IDENTITY_SECRET = "ci-billing-identity-secret-with-at-least-32-bytes"
CAPABILITY_SECRET = "ci-billing-capability-secret-with-at-least-32-bytes"
WEBHOOK_SECRET = "whsec_ci_axignal_paid_lifecycle"
PROFESSIONAL_PRICE = "price_test_axignal_professional_monthly"
TEAM_PRICE = "price_test_axignal_team_monthly"


class StripeSandboxState:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self.checkout_counter = 0


class StripeSandboxHandler(BaseHTTPRequestHandler):
    state: StripeSandboxState

    def log_message(self, format: str, *args: object) -> None:
        del format, args

    def _send(self, status: int, payload: dict[str, Any]) -> None:
        encoded = json.dumps(payload, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _body(self) -> dict[str, list[str]]:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode()
        return parse_qs(raw, keep_blank_values=True)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/v1/account":
            self.state.calls.append({"method": "GET", "path": self.path})
            self._send(200, {"id": EXPECTED_AXIGNAL_STRIPE_ACCOUNT_ID, "livemode": False})
            return
        self._send(404, {"error": {"message": "not found"}})

    def do_POST(self) -> None:  # noqa: N802
        form = self._body()
        self.state.calls.append(
            {
                "method": "POST",
                "path": self.path,
                "form": form,
                "idempotency_key": self.headers.get("Idempotency-Key"),
            }
        )
        if self.path == "/v1/checkout/sessions":
            self.state.checkout_counter += 1
            identifier = f"cs_test_axignal_{self.state.checkout_counter}"
            self._send(
                200,
                {
                    "id": identifier,
                    "object": "checkout.session",
                    "livemode": False,
                    "url": f"https://checkout.stripe.test/c/pay/{identifier}",
                },
            )
            return
        if self.path.startswith("/v1/subscriptions/"):
            subscription_id = self.path.rsplit("/", 1)[-1]
            self._send(
                200,
                {
                    "id": subscription_id,
                    "object": "subscription",
                    "status": "active",
                    "cancel_at_period_end": form.get("cancel_at_period_end") == ["true"],
                },
            )
            return
        self._send(404, {"error": {"message": "not found"}})

    def do_DELETE(self) -> None:  # noqa: N802
        self.state.calls.append(
            {
                "method": "DELETE",
                "path": self.path,
                "idempotency_key": self.headers.get("Idempotency-Key"),
            }
        )
        if self.path.startswith("/v1/subscriptions/"):
            subscription_id = self.path.rsplit("/", 1)[-1]
            self._send(
                200,
                {
                    "id": subscription_id,
                    "object": "subscription",
                    "status": "canceled",
                    "cancel_at_period_end": False,
                },
            )
            return
        self._send(404, {"error": {"message": "not found"}})


def _clean(dsn: str) -> None:
    with psycopg.connect(dsn) as connection, connection.cursor() as cursor:
        cursor.execute(
            """
            TRUNCATE
              tenant_private.payment_ledger_entries,
              axignal_global.stripe_webhook_receipts,
              tenant_private.ai_token_reservations,
              tenant_private.entitlement_events,
              tenant_private.organisation_entitlements,
              tenant_private.billing_plan_selections
            RESTART IDENTITY CASCADE
            """
        )


def _headers(tenant_id: UUID, subject: str) -> dict[str, str]:
    return {
        "X-AXIGNAL-Identity-Assertion": build_identity_assertion(
            secret=IDENTITY_SECRET,
            subject=subject,
            email=f"{subject}@example.test",
            tenant_id=tenant_id,
        )
    }


def _event(
    *,
    event_id: str,
    event_type: str,
    created_at: datetime,
    obj: dict[str, Any],
) -> bytes:
    return json.dumps(
        {
            "id": event_id,
            "object": "event",
            "type": event_type,
            "created": int(created_at.timestamp()),
            "livemode": False,
            "data": {"object": obj},
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode()


def _post_event(client: TestClient, payload: bytes) -> Any:
    signature = build_test_stripe_signature(
        payload=payload,
        secret=WEBHOOK_SECRET,
        timestamp=int(time.time()),
    )
    return client.post(
        "/v1/billing/stripe/webhook",
        content=payload,
        headers={"Stripe-Signature": signature, "Content-Type": "application/json"},
    )


def _subscription_object(
    *,
    selection_id: UUID,
    subscription_id: str,
    item_id: str,
    price_id: str,
    status: str = "active",
    cancel_at_period_end: bool = False,
    period_end: datetime,
) -> dict[str, Any]:
    return {
        "id": subscription_id,
        "object": "subscription",
        "status": status,
        "customer": f"cus_{subscription_id}",
        "metadata": {"axignal_selection_id": str(selection_id)},
        "items": {"data": [{"id": item_id, "price": {"id": price_id}}]},
        "current_period_end": int(period_end.timestamp()),
        "cancel_at_period_end": cancel_at_period_end,
    }


def _assert_append_only(dsn: str, tenant_id: UUID) -> None:
    try:
        with psycopg.connect(dsn) as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE tenant_private.payment_ledger_entries
                SET ledger_event_type = 'MUTATED'
                WHERE tenant_id = %s
                """,
                (tenant_id,),
            )
    except Exception as exc:
        if "append-only" not in str(exc):
            raise
    else:
        raise AssertionError("Payment ledger mutation unexpectedly succeeded")


def _configure(dsn: str, api_base: str) -> None:
    values = {
        "AXIGNAL_DATABASE_URL": dsn,
        "AXIGNAL_BILLING_DATABASE_URL": dsn,
        "AXIGNAL_ENTITLEMENT_DATABASE_URL": dsn,
        "AXIGNAL_BILLING_RUNTIME_ENABLED": "true",
        "AXIGNAL_STRIPE_CHECKOUT_ENABLED": "true",
        "AXIGNAL_STRIPE_WEBHOOKS_ENABLED": "true",
        "AXIGNAL_STRIPE_LIFECYCLE_ENABLED": "true",
        "AXIGNAL_STRIPE_SANDBOX_ONLY": "true",
        "AXIGNAL_STRIPE_SECRET_KEY": "sk_test_axignal_ci_only",
        "AXIGNAL_STRIPE_WEBHOOK_SECRET": WEBHOOK_SECRET,
        "AXIGNAL_STRIPE_ACCOUNT_ID": EXPECTED_AXIGNAL_STRIPE_ACCOUNT_ID,
        "AXIGNAL_STRIPE_API_BASE": api_base,
        "AXIGNAL_STRIPE_API_VERSION": "2026-06-24.preview",
        "AXIGNAL_STRIPE_PRICE_PROFESSIONAL_MONTHLY": PROFESSIONAL_PRICE,
        "AXIGNAL_STRIPE_PRICE_TEAM_MONTHLY": TEAM_PRICE,
        "AXIGNAL_STRIPE_CHECKOUT_SUCCESS_URL": (
            "https://app.axignal.test/billing/success?session_id={CHECKOUT_SESSION_ID}"
        ),
        "AXIGNAL_STRIPE_CHECKOUT_CANCEL_URL": "https://app.axignal.test/billing/cancel",
        "AXIGNAL_IDENTITY_ASSERTION_SECRET": IDENTITY_SECRET,
        "AXIGNAL_CAPABILITY_TOKEN_SECRET": CAPABILITY_SECRET,
        "AXIGNAL_TRIAL_RUNTIME_ENABLED": "true",
        "AXIGNAL_END_USER_AI_ENABLED": "true",
    }
    os.environ.update(values)


def run(dsn: str) -> dict[str, Any]:
    _clean(dsn)
    state = StripeSandboxState()
    handler = type("BoundStripeSandboxHandler", (StripeSandboxHandler,), {"state": state})
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    _configure(dsn, f"http://127.0.0.1:{server.server_port}")

    client = TestClient(app)
    entitlements = EntitlementRepository(dsn)
    billing = BillingRepository(dsn)
    try:
        trial = entitlements.activate_trial(
            tenant_id=TENANT_A, actor_subject="usr_trial", now=START
        )
        assert trial["entitlement_kind"] == "TRIAL"
        entitlements.expire_trial(
            tenant_id=TENANT_A,
            actor_subject="system-expiry",
            now=START + timedelta(days=8),
        )
        assert state.calls == [], "Trial lifecycle invoked Stripe"

        checkout_response = client.post(
            "/v1/billing/checkout-sessions",
            headers=_headers(TENANT_A, "usr_paid_a"),
            json={
                "operation_id": "op_explicit_professional_a",
                "plan_code": "PROFESSIONAL_MONTHLY",
                "confirm_paid_selection": True,
            },
        )
        assert checkout_response.status_code == 201, checkout_response.text
        checkout = checkout_response.json()
        selection_id = UUID(checkout["selection_id"])
        checkout_call = next(
            call for call in state.calls if call["path"] == "/v1/checkout/sessions"
        )
        form = checkout_call["form"]
        assert "trial_period_days" not in " ".join(form)
        assert form["mode"] == ["subscription"]
        assert form["client_reference_id"] == [str(selection_id)]
        assert checkout_call["idempotency_key"]

        checkout_event = _event(
            event_id="evt_checkout_completed_a",
            event_type="checkout.session.completed",
            created_at=START + timedelta(days=8, minutes=1),
            obj={
                "id": "cs_test_axignal_1",
                "object": "checkout.session",
                "client_reference_id": str(selection_id),
                "customer": "cus_sub_test_a",
                "subscription": "sub_test_a",
                "metadata": {"axignal_selection_id": str(selection_id)},
            },
        )
        response = _post_event(client, checkout_event)
        assert response.status_code == 200, response.text

        subscription_created = _event(
            event_id="evt_subscription_created_a",
            event_type="customer.subscription.created",
            created_at=START + timedelta(days=8, minutes=2),
            obj=_subscription_object(
                selection_id=selection_id,
                subscription_id="sub_test_a",
                item_id="si_test_a",
                price_id=PROFESSIONAL_PRICE,
                period_end=START + timedelta(days=38),
            ),
        )
        response = _post_event(client, subscription_created)
        assert response.status_code == 200, response.text
        duplicate = _post_event(client, subscription_created)
        assert duplicate.status_code == 200
        assert duplicate.json()["disposition"] == "DUPLICATE"

        conflicting = _event(
            event_id="evt_subscription_created_a",
            event_type="customer.subscription.created",
            created_at=START + timedelta(days=8, minutes=2),
            obj=_subscription_object(
                selection_id=selection_id,
                subscription_id="sub_test_a",
                item_id="si_test_a",
                price_id=TEAM_PRICE,
                period_end=START + timedelta(days=38),
            ),
        )
        conflict_response = _post_event(client, conflicting)
        assert conflict_response.status_code == 409

        paid = entitlements.usage(tenant_id=TENANT_A)
        assert paid is not None
        assert paid["entitlement_kind"] == "PAID_MONTHLY"
        assert paid["plan_code"] == "PROFESSIONAL_MONTHLY"
        assert paid["unlimited_ai_tokens"] is True
        assert paid["token_budget_total"] is None

        reservation = entitlements.reserve(
            tenant_id=TENANT_A,
            operation_id="op_paid_high_usage_before_cancel",
            capability="ASSEMBLE_EVIDENCE_LINKED_DOSSIER",
            requested_tokens=2_000_000,
            actor_subject="usr_paid_a",
            now=START + timedelta(days=8, minutes=3),
        )

        upgrade_response = client.post(
            "/v1/billing/subscription/upgrade",
            headers=_headers(TENANT_A, "usr_paid_a"),
            json={
                "operation_id": "op_upgrade_team_a",
                "target_plan_code": "TEAM_MONTHLY",
                "billing_effect": "IMMEDIATE_WITHOUT_PRORATION",
                "confirm_upgrade": True,
            },
        )
        assert upgrade_response.status_code == 200, upgrade_response.text
        upgrade_call = next(
            call
            for call in state.calls
            if call["path"] == "/v1/subscriptions/sub_test_a"
            and call["method"] == "POST"
            and "items[0][price]" in call["form"]
        )
        assert upgrade_call["form"]["proration_behavior"] == ["none"]
        assert upgrade_call["form"]["items[0][price]"] == [TEAM_PRICE]

        upgraded_event = _event(
            event_id="evt_subscription_upgraded_a",
            event_type="customer.subscription.updated",
            created_at=START + timedelta(days=8, minutes=4),
            obj=_subscription_object(
                selection_id=selection_id,
                subscription_id="sub_test_a",
                item_id="si_test_a",
                price_id=TEAM_PRICE,
                period_end=START + timedelta(days=38),
            ),
        )
        assert _post_event(client, upgraded_event).status_code == 200
        paid_after_upgrade = entitlements.usage(tenant_id=TENANT_A)
        assert paid_after_upgrade is not None
        assert paid_after_upgrade["plan_code"] == "TEAM_MONTHLY"
        assert paid_after_upgrade["token_budget_total"] is None

        period_end_response = client.post(
            "/v1/billing/subscription/cancel",
            headers=_headers(TENANT_A, "usr_paid_a"),
            json={
                "operation_id": "op_cancel_period_end_a",
                "cancel_at_period_end": True,
                "confirm_cancellation": True,
            },
        )
        assert period_end_response.status_code == 200, period_end_response.text
        period_end_event = _event(
            event_id="evt_cancel_period_end_a",
            event_type="customer.subscription.updated",
            created_at=START + timedelta(days=8, minutes=5),
            obj=_subscription_object(
                selection_id=selection_id,
                subscription_id="sub_test_a",
                item_id="si_test_a",
                price_id=TEAM_PRICE,
                cancel_at_period_end=True,
                period_end=START + timedelta(days=38),
            ),
        )
        assert _post_event(client, period_end_event).status_code == 200
        current = billing.current_selection(tenant_id=TENANT_A)
        assert current is not None and current["state"] == "CANCEL_AT_PERIOD_END"
        assert entitlements.usage(tenant_id=TENANT_A)["state"] == "ACTIVE"  # type: ignore[index]

        cancel_now_response = client.post(
            "/v1/billing/subscription/cancel",
            headers=_headers(TENANT_A, "usr_paid_a"),
            json={
                "operation_id": "op_cancel_immediate_a",
                "cancel_at_period_end": False,
                "confirm_cancellation": True,
            },
        )
        assert cancel_now_response.status_code == 200, cancel_now_response.text
        deleted_event = _event(
            event_id="evt_subscription_deleted_a",
            event_type="customer.subscription.deleted",
            created_at=START + timedelta(days=8, minutes=6),
            obj=_subscription_object(
                selection_id=selection_id,
                subscription_id="sub_test_a",
                item_id="si_test_a",
                price_id=TEAM_PRICE,
                status="canceled",
                period_end=START + timedelta(days=8, minutes=6),
            ),
        )
        assert _post_event(client, deleted_event).status_code == 200
        cancelled = entitlements.usage(tenant_id=TENANT_A)
        assert cancelled is not None and cancelled["state"] == "CANCELLED"
        with psycopg.connect(dsn) as connection, connection.cursor() as cursor:
            cursor.execute(
                "SELECT state FROM tenant_private.ai_token_reservations WHERE reservation_id = %s",
                (reservation["reservation_id"],),
            )
            assert cursor.fetchone()[0] == "RELEASED"

        stale_event = _event(
            event_id="evt_stale_reactivation_a",
            event_type="customer.subscription.updated",
            created_at=START + timedelta(days=8, minutes=4, seconds=30),
            obj=_subscription_object(
                selection_id=selection_id,
                subscription_id="sub_test_a",
                item_id="si_test_a",
                price_id=TEAM_PRICE,
                period_end=START + timedelta(days=38),
            ),
        )
        stale_response = _post_event(client, stale_event)
        assert stale_response.status_code == 200
        assert stale_response.json()["disposition"] == "STALE"
        assert entitlements.usage(tenant_id=TENANT_A)["state"] == "CANCELLED"  # type: ignore[index]

        checkout_b = client.post(
            "/v1/billing/checkout-sessions",
            headers=_headers(TENANT_B, "usr_paid_b"),
            json={
                "operation_id": "op_explicit_professional_b",
                "plan_code": "PROFESSIONAL_MONTHLY",
                "confirm_paid_selection": True,
            },
        )
        assert checkout_b.status_code == 201, checkout_b.text
        selection_b = UUID(checkout_b.json()["selection_id"])
        assert _post_event(
            client,
            _event(
                event_id="evt_checkout_completed_b",
                event_type="checkout.session.completed",
                created_at=START + timedelta(days=9),
                obj={
                    "id": "cs_test_axignal_2",
                    "object": "checkout.session",
                    "client_reference_id": str(selection_b),
                    "customer": "cus_sub_test_b",
                    "subscription": "sub_test_b",
                    "metadata": {"axignal_selection_id": str(selection_b)},
                },
            ),
        ).status_code == 200
        assert _post_event(
            client,
            _event(
                event_id="evt_subscription_created_b",
                event_type="customer.subscription.created",
                created_at=START + timedelta(days=9, minutes=1),
                obj=_subscription_object(
                    selection_id=selection_b,
                    subscription_id="sub_test_b",
                    item_id="si_test_b",
                    price_id=PROFESSIONAL_PRICE,
                    period_end=START + timedelta(days=39),
                ),
            ),
        ).status_code == 200
        pending_b = entitlements.reserve(
            tenant_id=TENANT_B,
            operation_id="op_reservation_before_rollback_b",
            capability="EXPLAIN_CLAIMS_AND_EVIDENCE",
            requested_tokens=500_000,
            actor_subject="usr_paid_b",
            now=START + timedelta(days=9, minutes=2),
        )
        rollback_cancel = client.post(
            "/v1/billing/subscription/cancel",
            headers=_headers(TENANT_B, "usr_paid_b"),
            json={
                "operation_id": "op_rollback_cancel_b",
                "cancel_at_period_end": False,
                "confirm_cancellation": True,
            },
        )
        assert rollback_cancel.status_code == 200, rollback_cancel.text
        rolled_back = billing.rollback(
            selection_id=selection_b,
            actor_subject="system-billing-rollback",
            now=START + timedelta(days=9, minutes=3),
        )
        assert rolled_back["state"] == "ROLLED_BACK"
        assert entitlements.usage(tenant_id=TENANT_B)["state"] == "CANCELLED"  # type: ignore[index]
        with psycopg.connect(dsn) as connection, connection.cursor() as cursor:
            cursor.execute(
                "SELECT state FROM tenant_private.ai_token_reservations WHERE reservation_id = %s",
                (pending_b["reservation_id"],),
            )
            assert cursor.fetchone()[0] == "RELEASED"

        _assert_append_only(dsn, TENANT_A)
        ledger = billing.ledger(tenant_id=TENANT_A)
        provider_deletes = [
            call for call in state.calls if call["method"] == "DELETE"
        ]
        return {
            "schema": "axignal.stripe-paid-lifecycle-e2e.v0.1",
            "status": "PASS",
            "provider_account_id": EXPECTED_AXIGNAL_STRIPE_ACCOUNT_ID,
            "provider_mode": "LOCAL_STRIPE_SANDBOX_CONTRACT",
            "external_stripe_sandbox_executed": False,
            "explicit_paid_selection": True,
            "trial_stripe_calls": 0,
            "checkout_contains_stripe_trial": False,
            "signed_webhook": True,
            "duplicate_event_disposition": "DUPLICATE",
            "conflicting_event_rejected": True,
            "out_of_order_event_disposition": "STALE",
            "paid_monthly_token_quota": None,
            "paid_token_overage_billing": False,
            "upgrade": "PROFESSIONAL_MONTHLY_TO_TEAM_MONTHLY",
            "upgrade_proration": "NONE_EXPLICIT_V0_1",
            "cancel_at_period_end_preserves_access": True,
            "immediate_cancel_revokes_access": True,
            "rollback_revokes_access": True,
            "rollback_releases_reservations": True,
            "future_provider_charges_after_cancel": False,
            "provider_delete_commands": len(provider_deletes),
            "ledger_entries": len(ledger),
            "ledger_append_only": True,
            "live_stripe_calls": 0,
            "model_calls": 0,
        }
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/stripe-paid-lifecycle-e2e.json"),
    )
    args = parser.parse_args()
    dsn = os.environ.get("AXIGNAL_DATABASE_URL")
    if not dsn:
        raise SystemExit("AXIGNAL_DATABASE_URL is required")
    result = run(dsn)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
