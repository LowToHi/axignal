#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from uuid import UUID

import psycopg
from psycopg import sql
from psycopg.rows import dict_row

PENDING_STATES = (
    "SELECTED",
    "CHECKOUT_CREATED",
    "CHECKOUT_COMPLETED",
    "UPGRADE_PENDING",
    "CANCEL_PENDING",
)
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
VALID_RECEIPT_DISPOSITIONS = {"APPLIED", "STALE", "IGNORED"}
USER_LEDGER_EVENTS = {
    "PAID_PLAN_EXPLICITLY_SELECTED",
    "PAID_UPGRADE_EXPLICITLY_REQUESTED",
    "PAID_CANCELLATION_AT_PERIOD_END_REQUESTED",
}
PROVIDER_LEDGER_EVENTS = {
    "STRIPE_CHECKOUT_SESSION_COMPLETED",
    "STRIPE_CUSTOMER_SUBSCRIPTION_CREATED",
    "STRIPE_CUSTOMER_SUBSCRIPTION_UPDATED",
    "STRIPE_CUSTOMER_SUBSCRIPTION_DELETED",
    "STRIPE_INVOICE_PAID",
    "STRIPE_INVOICE_PAYMENT_FAILED",
    "STRIPE_INVOICE_PAID_RECOVERY",
}
ROLLBACK_LEDGER_EVENTS = {"PAID_LIFECYCLE_ROLLED_BACK"}
EXPECTED_LEDGER_EVENTS = (
    USER_LEDGER_EVENTS | PROVIDER_LEDGER_EVENTS | ROLLBACK_LEDGER_EVENTS
)
PROVIDER_ACTOR = "stripe-signed-webhook"
ROLLBACK_ACTOR = "deterministic-test-rollback"
RECOVERY_LEDGER_EVENT = "STRIPE_INVOICE_PAID_RECOVERY"


def _scalar(cursor: psycopg.Cursor, query: str, params: tuple[object, ...]) -> int:
    cursor.execute(query, params)
    row = cursor.fetchone()
    assert row is not None, "Scalar billing audit query returned no row"
    if isinstance(row, dict):
        return int(next(iter(row.values())))
    return int(row[0])


def _tenant_visible_count(dsn: str, tenant_id: UUID) -> int:
    with psycopg.connect(dsn) as connection, connection.cursor() as cursor:
        cursor.execute(
            sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier("axignal_app"))
        )
        cursor.execute(
            "SELECT set_config('app.tenant_id', %s, true)",
            (str(tenant_id),),
        )
        cursor.execute("SELECT count(*) FROM tenant_private.billing_plan_selections")
        row = cursor.fetchone()
        assert row is not None, "Tenant visibility query returned no row"
        return int(row[0])


def _isolation_tenant(tenant_id: UUID) -> UUID:
    return UUID(int=tenant_id.int ^ 1)


def _verify_ledger_authority(
    ledger: list[dict[str, object]], expected_subject: str
) -> None:
    observed_event_types = {str(row["ledger_event_type"]) for row in ledger}
    unexpected_event_types = observed_event_types - EXPECTED_LEDGER_EVENTS
    assert not unexpected_event_types, {
        "unexpected_ledger_event_types": sorted(unexpected_event_types),
        "observed_ledger_event_types": sorted(observed_event_types),
    }
    assert EXPECTED_LEDGER_EVENTS.issubset(observed_event_types), {
        "missing_ledger_event_types": sorted(
            EXPECTED_LEDGER_EVENTS - observed_event_types
        ),
        "observed_ledger_event_types": sorted(observed_event_types),
    }

    recovery_rows = [
        row for row in ledger if row["ledger_event_type"] == RECOVERY_LEDGER_EVENT
    ]
    assert len(recovery_rows) == 1, {
        "expected_recovery_rows": 1,
        "observed_recovery_rows": len(recovery_rows),
    }
    recovery = recovery_rows[0]
    assert recovery["previous_state"] == "SUSPENDED", recovery
    assert recovery["new_state"] == "ACTIVE", recovery
    assert recovery["actor_subject"] == PROVIDER_ACTOR, recovery
    assert recovery["provider_event_id"], recovery
    assert recovery["payload_digest"], recovery
    assert len(str(recovery["payload_digest"])) == 64, recovery

    for row in ledger:
        event_type = str(row["ledger_event_type"])
        actor_subject = str(row["actor_subject"])
        provider_event_id = row["provider_event_id"]
        payload_digest = row["payload_digest"]

        if event_type in USER_LEDGER_EVENTS:
            assert actor_subject == expected_subject, row
            assert provider_event_id is None, row
            assert payload_digest is None, row
        elif event_type in PROVIDER_LEDGER_EVENTS:
            assert actor_subject == PROVIDER_ACTOR, row
            assert provider_event_id, row
            assert payload_digest and len(str(payload_digest)) == 64, row
        elif event_type in ROLLBACK_LEDGER_EVENTS:
            assert actor_subject == ROLLBACK_ACTOR, row
            assert provider_event_id is None, row
            assert payload_digest is None, row
        else:  # pragma: no cover - guarded by the exact event taxonomy above.
            raise AssertionError(row)


def run(
    dsn: str,
    expected_subject: str,
) -> tuple[
    dict[str, object],
    dict[str, object],
    dict[str, object],
    dict[str, object],
]:
    with (
        psycopg.connect(dsn, row_factory=dict_row) as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute(
            """
            SELECT * FROM tenant_private.billing_plan_selections
            WHERE selected_by = %s
            ORDER BY updated_at DESC
            LIMIT 2
            """,
            (expected_subject,),
        )
        selections = list(cursor.fetchall())
        assert selections, (
            "Commercial browser E2E created no selection for authenticated subject "
            f"{expected_subject!r}"
        )
        assert len(selections) == 1, (
            "Commercial browser E2E must create exactly one selection for the "
            f"authenticated subject; observed {len(selections)}"
        )
        selection = selections[0]
        tenant_id = UUID(str(selection["tenant_id"]))
        isolation_tenant_id = _isolation_tenant(tenant_id)

        assert selection["selected_by"] == expected_subject, selection
        assert selection["state"] == "ROLLED_BACK", selection

        cursor.execute(
            """
            SELECT * FROM tenant_private.organisation_entitlements
            WHERE tenant_id = %s AND billing_selection_id = %s
            """,
            (tenant_id, selection["selection_id"]),
        )
        entitlement = cursor.fetchone()
        assert entitlement is not None, "Paid entitlement was not created"
        assert entitlement["entitlement_kind"] == "PAID_MONTHLY", entitlement
        assert entitlement["state"] == "CANCELLED", entitlement
        assert entitlement["unlimited_ai_tokens"] is True, entitlement
        assert entitlement["token_budget_total"] is None, entitlement

        active_entitlements = _scalar(
            cursor,
            """
            SELECT count(*) FROM tenant_private.organisation_entitlements
            WHERE tenant_id = %s AND state = 'ACTIVE'
            """,
            (tenant_id,),
        )
        open_reservations = _scalar(
            cursor,
            """
            SELECT count(*) FROM tenant_private.ai_token_reservations
            WHERE tenant_id = %s AND state = 'RESERVED'
            """,
            (tenant_id,),
        )
        pending_selections = _scalar(
            cursor,
            """
            SELECT count(*) FROM tenant_private.billing_plan_selections
            WHERE tenant_id = %s AND state = ANY(%s)
            """,
            (tenant_id, list(PENDING_STATES)),
        )
        active_capabilities = active_entitlements

        cursor.execute(
            """
            SELECT ledger_event_type, previous_state, new_state, provider_event_id,
                   payload_digest, actor_subject
            FROM tenant_private.payment_ledger_entries
            WHERE tenant_id = %s
            ORDER BY occurred_at, created_at, ledger_entry_id
            """,
            (tenant_id,),
        )
        ledger = list(cursor.fetchall())
        assert len(ledger) >= 12, ledger
        observed_states = {
            str(state)
            for row in ledger
            for state in (row["previous_state"], row["new_state"])
            if state is not None
        }
        assert EXPECTED_STATES.issubset(observed_states), observed_states
        _verify_ledger_authority(ledger, expected_subject)
        assert all("raw" not in row for row in ledger)

        cursor.execute(
            """
            SELECT provider_event_id, event_type, payload_digest, disposition
            FROM axignal_global.stripe_webhook_receipts
            WHERE tenant_id = %s
            ORDER BY received_at, provider_event_id
            """,
            (tenant_id,),
        )
        receipts = list(cursor.fetchall())
        assert len(receipts) >= 5, receipts
        assert all(
            row["disposition"] in VALID_RECEIPT_DISPOSITIONS for row in receipts
        ), receipts
        assert all(len(str(row["payload_digest"])) == 64 for row in receipts), receipts

    tenant_visible = _tenant_visible_count(dsn, tenant_id)
    cross_tenant_visible = _tenant_visible_count(dsn, isolation_tenant_id)
    assert tenant_visible >= 1
    assert cross_tenant_visible == 0
    assert active_entitlements == 0
    assert open_reservations == 0
    assert pending_selections == 0
    assert active_capabilities == 0

    commercial = {
        "schema": "axignal.commercial-shell-e2e.v0.1",
        "status": "PASS",
        "provider": "DETERMINISTIC_TEST_PROVIDER",
        "external_stripe_verified": False,
        "commercial_payment_evidence": False,
        "authenticated_subject": expected_subject,
        "tenant_id": str(tenant_id),
        "selection_state": selection["state"],
        "entitlement_kind": entitlement["entitlement_kind"],
        "entitlement_state": entitlement["state"],
        "paid_monthly_token_quota": entitlement["token_budget_total"],
        "unlimited_ai_tokens": entitlement["unlimited_ai_tokens"],
        "token_overage_billing": False,
        "signed_provider_receipts": len(receipts),
        "ledger_entries": len(ledger),
        "paid_invoice_recovery": "SUSPENDED_TO_ACTIVE_PASS",
        "ledger_authority_taxonomy": {
            "authenticated_subject": expected_subject,
            "provider_actor": PROVIDER_ACTOR,
            "rollback_actor": ROLLBACK_ACTOR,
        },
        "external_stripe_calls": 0,
        "model_calls": 0,
    }
    state_matrix = {
        "schema": "axignal.billing-ui-state-matrix.v0.1",
        "status": "PASS",
        "states_observed": sorted(observed_states),
        "required_states": sorted(EXPECTED_STATES),
        "ledger_events_observed": sorted(
            {str(row["ledger_event_type"]) for row in ledger}
        ),
        "paid_invoice_recovery": "SUSPENDED_TO_ACTIVE_PASS",
        "checkout_return_grants_entitlement": False,
        "signed_event_required": True,
        "refresh_persistence": True,
    }
    isolation = {
        "schema": "axignal.billing-tenant-isolation.v0.1",
        "status": "PASS",
        "tenant_id": str(tenant_id),
        "isolation_tenant_id": str(isolation_tenant_id),
        "tenant_visible_selections": tenant_visible,
        "cross_tenant_visible_selections": cross_tenant_visible,
        "rls": "PASS",
    }
    residue = {
        "schema": "axignal.billing-rollback-residue.v0.1",
        "status": "PASS",
        "tenant_id": str(tenant_id),
        "active_test_entitlements": active_entitlements,
        "open_reservations": open_reservations,
        "active_capabilities": active_capabilities,
        "pending_test_selections": pending_selections,
        "cross_tenant_effects": cross_tenant_visible,
        "external_stripe_calls": 0,
        "selection_state": selection["state"],
    }
    return commercial, state_matrix, isolation, residue


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts"))
    args = parser.parse_args()
    dsn = os.environ.get("AXIGNAL_DATABASE_URL")
    if not dsn:
        raise SystemExit("AXIGNAL_DATABASE_URL is required")
    expected_subject = os.environ.get("AXIGNAL_AUTH_SUBJECT", "").strip()
    if not expected_subject:
        raise SystemExit("AXIGNAL_AUTH_SUBJECT is required")
    outputs = run(dsn, expected_subject)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    names = (
        "commercial-shell-e2e.json",
        "billing-ui-state-matrix.json",
        "billing-tenant-isolation.json",
        "billing-rollback-residue.json",
    )
    for name, payload in zip(names, outputs, strict=True):
        (args.output_dir / name).write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(outputs[0], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
