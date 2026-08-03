#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from uuid import UUID

import psycopg
from psycopg.rows import dict_row

EXPECTED_PROVIDER_EVENTS = {
    "checkout.session.completed",
    "customer.subscription.created",
    "customer.subscription.updated",
    "customer.subscription.deleted",
    "invoice.paid",
    "invoice.payment_failed",
}
EXPECTED_LEDGER_EVENTS = {
    "PAID_PLAN_EXPLICITLY_SELECTED",
    "PAID_UPGRADE_EXPLICITLY_REQUESTED",
    "PAID_CANCELLATION_AT_PERIOD_END_REQUESTED",
    "STRIPE_CHECKOUT_SESSION_COMPLETED",
    "STRIPE_CUSTOMER_SUBSCRIPTION_CREATED",
    "STRIPE_CUSTOMER_SUBSCRIPTION_UPDATED",
    "STRIPE_CUSTOMER_SUBSCRIPTION_DELETED",
    "STRIPE_INVOICE_PAID",
    "STRIPE_INVOICE_PAID_RECOVERY",
    "STRIPE_INVOICE_PAYMENT_FAILED",
    "PAID_LIFECYCLE_ROLLED_BACK",
}
EXPECTED_STATES = {
    "SELECTED",
    "CHECKOUT_CREATED",
    "CHECKOUT_COMPLETED",
    "ACTIVE",
    "SUSPENDED",
    "UPGRADE_PENDING",
    "CANCEL_PENDING",
    "CANCEL_AT_PERIOD_END",
    "CANCELLED",
    "ROLLED_BACK",
}
PROVIDER_ACTORS = {"stripe-signed-webhook", "stripe-reconciliation"}


def _one(cursor: psycopg.Cursor, query: str, params: tuple[object, ...]) -> dict:
    cursor.execute(query, params)
    rows = list(cursor.fetchall())
    assert len(rows) == 1, {"query": query, "row_count": len(rows)}
    return rows[0]


def run(dsn: str, expected_subject: str) -> dict[str, object]:
    with (
        psycopg.connect(dsn, row_factory=dict_row) as connection,
        connection.cursor() as cursor,
    ):
        selection = _one(
            cursor,
            """
            SELECT *
            FROM tenant_private.billing_plan_selections
            WHERE selected_by = %s
            """,
            (expected_subject,),
        )
        tenant_id = UUID(str(selection["tenant_id"]))
        assert selection["plan_code"] == "TEAM_MONTHLY", selection
        assert selection["state"] == "ROLLED_BACK", selection
        assert selection["stripe_customer_id"], selection
        assert selection["stripe_subscription_id"], selection
        assert selection["stripe_subscription_item_id"], selection

        entitlement = _one(
            cursor,
            """
            SELECT *
            FROM tenant_private.organisation_entitlements
            WHERE tenant_id = %s AND billing_selection_id = %s
            """,
            (tenant_id, selection["selection_id"]),
        )
        assert entitlement["entitlement_kind"] == "PAID_MONTHLY", entitlement
        assert entitlement["plan_code"] == "TEAM_MONTHLY", entitlement
        assert entitlement["state"] == "CANCELLED", entitlement
        assert entitlement["activated_by"] == "stripe-signed-webhook", entitlement
        assert entitlement["unlimited_ai_tokens"] is True, entitlement
        assert entitlement["token_budget_total"] is None, entitlement

        cursor.execute(
            """
            SELECT plan_code, seat_capacity, billing_model, state
            FROM axignal_global.seat_plan_policies
            WHERE plan_code IN ('PROFESSIONAL_MONTHLY', 'TEAM_MONTHLY')
            ORDER BY plan_code
            """
        )
        policies = {row["plan_code"]: row for row in cursor.fetchall()}
        assert policies["PROFESSIONAL_MONTHLY"]["seat_capacity"] == 3, policies
        assert policies["TEAM_MONTHLY"]["seat_capacity"] == 15, policies
        assert all(row["billing_model"] == "FLAT_TIER" for row in policies.values())

        seat_entitlement = _one(
            cursor,
            """
            SELECT *
            FROM tenant_private.organisation_seat_entitlements
            WHERE tenant_id = %s
            """,
            (tenant_id,),
        )
        assert seat_entitlement["source_entitlement_id"] == entitlement["entitlement_id"]
        assert seat_entitlement["source_billing_selection_id"] == selection["selection_id"]
        assert seat_entitlement["plan_code"] == "TEAM_MONTHLY", seat_entitlement
        assert seat_entitlement["seat_capacity"] == 15, seat_entitlement
        assert seat_entitlement["state"] == "CANCELLED", seat_entitlement

        cursor.execute(
            """
            SELECT provider_event_id, event_type, disposition, payload_digest
            FROM axignal_global.stripe_webhook_receipts
            WHERE tenant_id = %s
            ORDER BY event_created_at, provider_event_id
            """,
            (tenant_id,),
        )
        receipts = list(cursor.fetchall())
        receipt_types = {row["event_type"] for row in receipts}
        dispositions = {row["disposition"] for row in receipts}
        assert EXPECTED_PROVIDER_EVENTS.issubset(receipt_types), {
            "missing": sorted(EXPECTED_PROVIDER_EVENTS - receipt_types),
            "observed": sorted(receipt_types),
        }
        assert "APPLIED" in dispositions, dispositions
        assert "STALE" in dispositions, dispositions
        assert all(len(str(row["payload_digest"])) == 64 for row in receipts)
        assert any(str(row["provider_event_id"]).startswith("reconcile_") for row in receipts)

        cursor.execute(
            """
            SELECT ledger_event_type, previous_state, new_state,
                   provider_event_id, payload_digest, actor_subject
            FROM tenant_private.payment_ledger_entries
            WHERE tenant_id = %s
            ORDER BY occurred_at, created_at, ledger_entry_id
            """,
            (tenant_id,),
        )
        ledger = list(cursor.fetchall())
        event_types = {row["ledger_event_type"] for row in ledger}
        observed_states = {
            str(state)
            for row in ledger
            for state in (row["previous_state"], row["new_state"])
            if state is not None
        }
        assert EXPECTED_LEDGER_EVENTS.issubset(event_types), {
            "missing": sorted(EXPECTED_LEDGER_EVENTS - event_types),
            "observed": sorted(event_types),
        }
        assert EXPECTED_STATES.issubset(observed_states), {
            "missing": sorted(EXPECTED_STATES - observed_states),
            "observed": sorted(observed_states),
        }

        recovery_rows = [
            row
            for row in ledger
            if row["ledger_event_type"] == "STRIPE_INVOICE_PAID_RECOVERY"
        ]
        assert len(recovery_rows) == 1, recovery_rows
        recovery = recovery_rows[0]
        assert recovery["previous_state"] == "SUSPENDED", recovery
        assert recovery["new_state"] == "ACTIVE", recovery
        assert recovery["actor_subject"] == "stripe-signed-webhook", recovery
        assert recovery["provider_event_id"], recovery
        assert len(str(recovery["payload_digest"])) == 64, recovery

        provider_rows = [
            row for row in ledger if str(row["ledger_event_type"]).startswith("STRIPE_")
        ]
        assert provider_rows, ledger
        assert all(row["actor_subject"] in PROVIDER_ACTORS for row in provider_rows)
        assert any(row["actor_subject"] == "stripe-reconciliation" for row in provider_rows)
        assert all(row["provider_event_id"] for row in provider_rows)
        assert all(len(str(row["payload_digest"])) == 64 for row in provider_rows)

        user_rows = [
            row
            for row in ledger
            if row["ledger_event_type"]
            in {
                "PAID_PLAN_EXPLICITLY_SELECTED",
                "PAID_UPGRADE_EXPLICITLY_REQUESTED",
                "PAID_CANCELLATION_AT_PERIOD_END_REQUESTED",
            }
        ]
        assert user_rows
        assert all(row["actor_subject"] == expected_subject for row in user_rows)
        assert all(row["provider_event_id"] is None for row in user_rows)

        cursor.execute(
            """
            SELECT count(*) AS count
            FROM tenant_private.organisation_entitlements
            WHERE tenant_id = %s AND state = 'ACTIVE'
            """,
            (tenant_id,),
        )
        assert cursor.fetchone()["count"] == 0

    return {
        "schema": "axignal.e2e-3-commercial-round-trip.v0.1",
        "status": "PASS",
        "output": "AX_E2E_COMMERCIAL_DETERMINISTIC_ROUND_TRIP_PASS",
        "tenant_id": str(tenant_id),
        "selection_id": str(selection["selection_id"]),
        "provider": "DETERMINISTIC_TEST_PROVIDER",
        "external_stripe_verified": False,
        "browser_entitlement_authority": False,
        "signed_receipts": len(receipts),
        "receipt_dispositions": sorted(dispositions),
        "ledger_entries": len(ledger),
        "states_observed": sorted(observed_states),
        "paid_invoice_recovery": "SUSPENDED_TO_ACTIVE_PASS",
        "professional_seat_capacity": 3,
        "team_seat_capacity": 15,
        "final_selection_state": selection["state"],
        "final_entitlement_state": entitlement["state"],
        "reconciliation": "DETERMINISTIC_REPAIR_PASS",
        "final_marker_reserved_for_external_sandbox": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/e2e-3-commercial-round-trip.json"),
    )
    args = parser.parse_args()
    dsn = os.environ.get("AXIGNAL_DATABASE_URL", "").strip()
    subject = os.environ.get("AXIGNAL_AUTH_SUBJECT", "").strip()
    if not dsn or not subject:
        raise SystemExit("AXIGNAL_DATABASE_URL and AXIGNAL_AUTH_SUBJECT are required")
    payload = run(dsn, subject)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
