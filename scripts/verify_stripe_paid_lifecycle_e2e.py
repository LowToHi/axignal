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
from urllib.parse import parse_qs
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

    def _send(self, status_code: int, payload: dict[str, Any]) -> None:
        encoded = json.dumps(payload, separators=(",", ":")).encode()
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _form(self) -> dict[str, list[str]]:
        size = int(self.headers.get("Content-Length", "0"))
        return parse_qs(self.rfile.read(size).decode(), keep_blank_values=True)

    def do_GET(self) -> None:  # noqa: N802
        self.state.calls.append({"method": "GET", "path": self.path})
        if self.path == "/v1/account":
            self._send(200, {"id": EXPECTED_AXIGNAL_STRIPE_ACCOUNT_ID, "livemode": False})
            return
        self._send(404, {"error": {"message": "not found"}})

    def do_POST(self) -> None:  # noqa: N802
        form = self._form()
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
            session_id = f"cs_test_axignal_{self.state.checkout_counter}"
            self._send(
                200,
                {
                    "id": session_id,
                    "object": "checkout.session",
                    "livemode": False,
                    "url": f"https://checkout.stripe.test/c/pay/{session_id}",
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


def _configure(dsn: str, api_base: str) -> None:
    os.environ.update(
        {
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
            "AXIGNAL_STRIPE_CHECKOUT_CANCEL_URL": (
                "https://app.axignal.test/billing/cancel"
            ),
            "AXIGNAL_IDENTITY_ASSERTION_SECRET": IDENTITY_SECRET,
            "AXIGNAL_CAPABILITY_TOKEN_SECRET": CAPABILITY_SECRET,
            "AXIGNAL_TRIAL_RUNTIME_ENABLED": "true",
            "AXIGNAL_END_USER_AI_ENABLED": "true",
        }
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
        payload=payload, secret=WEBHOOK_SECRET, timestamp=int(time.time())
    )
    return client.post(
        "/v1/billing/stripe/webhook",
        content=payload,
        headers={"Stripe-Signature": signature, "Content-Type": "application/json"},
    )


def _subscription(
    selection_id: UUID,
    subscription_id: str,
    item_id: str,
    price_id: str,
    created_at: datetime,
    *,
    status: str = "active",
    cancel_at_period_end: bool = False,
) -> dict[str, Any]:
    return {
        "id": subscription_id,
        "object": "subscription",
        "status": status,
        "customer": f"cus_{subscription_id}",
        "metadata": {"axignal_selection_id": str(selection_id)},
        "items": {"data": [{"id": item_id, "price": {"id": price_id}}]},
        "current_period_end": int((created_at + timedelta(days=30)).timestamp()),
        "cancel_at_period_end": cancel_at_period_end,
    }


def _checkout(
    client: TestClient,
    state: StripeSandboxState,
    tenant_id: UUID,
    suffix: str,
) -> UUID:
    response = client.post(
        "/v1/billing/checkout-sessions",
        headers=_headers(tenant_id, f"usr_paid_{suffix}"),
        json={
            "operation_id": f"op_explicit_professional_{suffix}",
            "plan_code": "PROFESSIONAL_MONTHLY",
            "confirm_paid_selection": True,
        },
    )
    assert response.status_code == 201, response.text
    selection_id = UUID(response.json()["selection_id"])
    checkout_calls = [
        call for call in state.calls if call["path"] == "/v1/checkout/sessions"
    ]
    form = checkout_calls[-1]["form"]
    assert "trial_period_days" not in " ".join(form)
    assert form["mode"] == ["subscription"]
    assert form["client_reference_id"] == [str(selection_id)]
    assert checkout_calls[-1]["idempotency_key"]
    return selection_id


def _activate_paid(
    client: TestClient,
    selection_id: UUID,
    suffix: str,
    created_at: datetime,
) -> tuple[bytes, bytes]:
    checkout_payload = _event(
        f"evt_checkout_completed_{suffix}",
        "checkout.session.completed",
        created_at,
        {
            "id": f"cs_test_axignal_{1 if suffix == 'a' else 2}",
            "object": "checkout.session",
            "client_reference_id": str(selection_id),
            "customer": f"cus_sub_test_{suffix}",
            "subscription": f"sub_test_{suffix}",
            "metadata": {"axignal_selection_id": str(selection_id)},
        },
    )
    subscription_payload = _event(
        f"evt_subscription_created_{suffix}",
        "customer.subscription.created",
        created_at + timedelta(minutes=1),
        _subscription(
            selection_id,
            f"sub_test_{suffix}",
            f"si_test_{suffix}",
            PROFESSIONAL_PRICE,
            created_at,
        ),
    )
    assert _post_event(client, checkout_payload).status_code == 200
    response = _post_event(client, subscription_payload)
    assert response.status_code == 200, response.text
    return checkout_payload, subscription_payload


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


def _reservation_state(dsn: str, reservation_id: UUID) -> str:
    with psycopg.connect(dsn) as connection, connection.cursor() as cursor:
        cursor.execute(
            "SELECT state FROM tenant_private.ai_token_reservations WHERE reservation_id = %s",
            (reservation_id,),
        )
        row = cursor.fetchone()
        assert row is not None
        return str(row[0])


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

        selection_a = _checkout(client, state, TENANT_A, "a")
        _, created_a = _activate_paid(
            client, selection_a, "a", START + timedelta(days=8, minutes=1)
        )
        duplicate = _post_event(client, created_a)
        assert duplicate.status_code == 200
        assert duplicate.json()["disposition"] == "DUPLICATE"

        conflicting = _event(
            "evt_subscription_created_a",
            "customer.subscription.created",
            START + timedelta(days=8, minutes=2),
            _subscription(
                selection_a,
                "sub_test_a",
                "si_test_a",
                TEAM_PRICE,
                START + timedelta(days=8),
            ),
        )
        assert _post_event(client, conflicting).status_code == 409

        paid = entitlements.usage(tenant_id=TENANT_A)
        assert paid is not None
        assert paid["entitlement_kind"] == "PAID_MONTHLY"
        assert paid["plan_code"] == "PROFESSIONAL_MONTHLY"
        assert paid["unlimited_ai_tokens"] is True
        assert paid["token_budget_total"] is None
        reservation_a = entitlements.reserve(
            tenant_id=TENANT_A,
            operation_id="op_paid_high_usage_before_cancel",
            capability="ASSEMBLE_EVIDENCE_LINKED_DOSSIER",
            requested_tokens=2_000_000,
            actor_subject="usr_paid_a",
            now=START + timedelta(days=8, minutes=3),
        )

        upgrade = client.post(
            "/v1/billing/subscription/upgrade",
            headers=_headers(TENANT_A, "usr_paid_a"),
            json={
                "operation_id": "op_upgrade_team_a",
                "target_plan_code": "TEAM_MONTHLY",
                "billing_effect": "IMMEDIATE_WITHOUT_PRORATION",
                "confirm_upgrade": True,
            },
        )
        assert upgrade.status_code == 200, upgrade.text
        upgrade_call = next(
            call
            for call in state.calls
            if call["path"] == "/v1/subscriptions/sub_test_a"
            and call["method"] == "POST"
            and "items[0][price]" in call["form"]
        )
        assert upgrade_call["form"]["items[0][price]"] == [TEAM_PRICE]
        assert upgrade_call["form"]["proration_behavior"] == ["none"]
        upgraded = _event(
            "evt_subscription_upgraded_a",
            "customer.subscription.updated",
            START + timedelta(days=8, minutes=4),
            _subscription(
                selection_a,
                "sub_test_a",
                "si_test_a",
                TEAM_PRICE,
                START + timedelta(days=8),
            ),
        )
        assert _post_event(client, upgraded).status_code == 200
        assert entitlements.usage(tenant_id=TENANT_A)["plan_code"] == "TEAM_MONTHLY"  # type: ignore[index]

        period_end = client.post(
            "/v1/billing/subscription/cancel",
            headers=_headers(TENANT_A, "usr_paid_a"),
            json={
                "operation_id": "op_cancel_period_end_a",
                "cancel_at_period_end": True,
                "confirm_cancellation": True,
            },
        )
        assert period_end.status_code == 200, period_end.text
        period_end_event = _event(
            "evt_cancel_period_end_a",
            "customer.subscription.updated",
            START + timedelta(days=8, minutes=5),
            _subscription(
                selection_a,
                "sub_test_a",
                "si_test_a",
                TEAM_PRICE,
                START + timedelta(days=8),
                cancel_at_period_end=True,
            ),
        )
        assert _post_event(client, period_end_event).status_code == 200
        assert billing.current_selection(tenant_id=TENANT_A)["state"] == (  # type: ignore[index]
            "CANCEL_AT_PERIOD_END"
        )
        assert entitlements.usage(tenant_id=TENANT_A)["state"] == "ACTIVE"  # type: ignore[index]

        cancel_now = client.post(
            "/v1/billing/subscription/cancel",
            headers=_headers(TENANT_A, "usr_paid_a"),
            json={
                "operation_id": "op_cancel_immediate_a",
                "cancel_at_period_end": False,
                "confirm_cancellation": True,
            },
        )
        assert cancel_now.status_code == 200, cancel_now.text
        deleted = _event(
            "evt_subscription_deleted_a",
            "customer.subscription.deleted",
            START + timedelta(days=8, minutes=6),
            _subscription(
                selection_a,
                "sub_test_a",
                "si_test_a",
                TEAM_PRICE,
                START + timedelta(days=8),
                status="canceled",
            ),
        )
        assert _post_event(client, deleted).status_code == 200
        assert entitlements.usage(tenant_id=TENANT_A)["state"] == "CANCELLED"  # type: ignore[index]
        assert _reservation_state(dsn, reservation_a["reservation_id"]) == "RELEASED"

        stale = _event(
            "evt_stale_reactivation_a",
            "customer.subscription.updated",
            START + timedelta(days=8, minutes=4, seconds=30),
            _subscription(
                selection_a,
                "sub_test_a",
                "si_test_a",
                TEAM_PRICE,
                START + timedelta(days=8),
            ),
        )
        stale_response = _post_event(client, stale)
        assert stale_response.status_code == 200
        assert stale_response.json()["disposition"] == "STALE"
        assert entitlements.usage(tenant_id=TENANT_A)["state"] == "CANCELLED"  # type: ignore[index]

        selection_b = _checkout(client, state, TENANT_B, "b")
        _activate_paid(client, selection_b, "b", START + timedelta(days=9))
        reservation_b = entitlements.reserve(
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
        assert _reservation_state(dsn, reservation_b["reservation_id"]) == "RELEASED"

        _assert_append_only(dsn, TENANT_A)
        provider_deletes = [call for call in state.calls if call["method"] == "DELETE"]
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
            "ledger_entries": len(billing.ledger(tenant_id=TENANT_A)),
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
