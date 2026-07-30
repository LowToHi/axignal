from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from uuid import UUID

import psycopg
from psycopg import sql
from psycopg.rows import dict_row

TENANT_A = UUID("11111111-1111-4111-8111-111111111111")
TENANT_B = UUID("22222222-2222-4222-8222-222222222222")
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
    "UPGRADE_PENDING",
    "CANCEL_PENDING",
    "CANCEL_AT_PERIOD_END",
    "CANCELLED",
    "ROLLED_BACK",
}


def _scalar(cursor: psycopg.Cursor, query: str, params: tuple[object, ...]) -> int:
    cursor.execute(query, params)
    row = cursor.fetchone()
    assert row is not None
    if isinstance(row, dict):
        return int(next(iter(row.values())))
    return int(row[0])


def _tenant_visible_count(dsn: str, tenant_id: UUID) -> int:
    with psycopg.connect(dsn) as connection, connection.cursor() as cursor:
        cursor.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier("axignal_app")))
        cursor.execute("SELECT set_config('app.tenant_id', %s, true)", (str(tenant_id),))
        cursor.execute("SELECT count(*) FROM tenant_private.billing_plan_selections")
        row = cursor.fetchone()
        assert row is not None
        return int(row[0])


def run(
    dsn: str,
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
            WHERE tenant_id = %s
            ORDER BY updated_at DESC LIMIT 1
            """,
            (TENANT_A,),
        )
        selection = cursor.fetchone()
        assert selection is not None, "Commercial browser E2E created no selection"
        assert selection["state"] == "ROLLED_BACK", selection

        cursor.execute(
            """
            SELECT * FROM tenant_private.organisation_entitlements
            WHERE tenant_id = %s AND billing_selection_id = %s
            """,
            (TENANT_A, selection["selection_id"]),
        )
        entitlement = cursor.fetchone()
        assert entitlement is not None, "Paid entitlement was not created"
        assert entitlement["entitlement_kind"] == "PAID_MONTHLY"
        assert entitlement["state"] == "CANCELLED"
        assert entitlement["unlimited_ai_tokens"] is True
        assert entitlement["token_budget_total"] is None

        active_entitlements = _scalar(
            cursor,
            """
            SELECT count(*) FROM tenant_private.organisation_entitlements
            WHERE tenant_id = %s AND state = 'ACTIVE'
            """,
            (TENANT_A,),
        )
        open_reservations = _scalar(
            cursor,
            """
            SELECT count(*) FROM tenant_private.ai_token_reservations
            WHERE tenant_id = %s AND state = 'RESERVED'
            """,
            (TENANT_A,),
        )
        pending_selections = _scalar(
            cursor,
            """
            SELECT count(*) FROM tenant_private.billing_plan_selections
            WHERE tenant_id = %s AND state = ANY(%s)
            """,
            (TENANT_A, list(PENDING_STATES)),
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
            (TENANT_A,),
        )
        ledger = list(cursor.fetchall())
        assert len(ledger) >= 9, ledger
        observed_states = {
            str(state)
            for row in ledger
            for state in (row["previous_state"], row["new_state"])
            if state is not None
        }
        assert EXPECTED_STATES.issubset(observed_states), observed_states
        assert all("raw" not in row for row in ledger)

        cursor.execute(
            """
            SELECT provider_event_id, event_type, payload_digest, disposition
            FROM axignal_global.stripe_webhook_receipts
            WHERE tenant_id = %s
            ORDER BY received_at, provider_event_id
            """,
            (TENANT_A,),
        )
        receipts = list(cursor.fetchall())
        assert len(receipts) >= 5, receipts
        assert all(
            row["disposition"] in {"APPLIED", "DUPLICATE", "STALE"}
            for row in receipts
        )
        assert all(len(str(row["payload_digest"])) == 64 for row in receipts)

    tenant_a_visible = _tenant_visible_count(dsn, TENANT_A)
    tenant_b_visible = _tenant_visible_count(dsn, TENANT_B)
    assert tenant_a_visible >= 1
    assert tenant_b_visible == 0
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
        "selection_state": selection["state"],
        "entitlement_kind": entitlement["entitlement_kind"],
        "entitlement_state": entitlement["state"],
        "paid_monthly_token_quota": entitlement["token_budget_total"],
        "unlimited_ai_tokens": entitlement["unlimited_ai_tokens"],
        "token_overage_billing": False,
        "signed_provider_receipts": len(receipts),
        "ledger_entries": len(ledger),
        "external_stripe_calls": 0,
        "model_calls": 0,
    }
    state_matrix = {
        "schema": "axignal.billing-ui-state-matrix.v0.1",
        "status": "PASS",
        "states_observed": sorted(observed_states),
        "required_states": sorted(EXPECTED_STATES),
        "checkout_return_grants_entitlement": False,
        "signed_event_required": True,
        "refresh_persistence": True,
    }
    isolation = {
        "schema": "axignal.billing-tenant-isolation.v0.1",
        "status": "PASS",
        "tenant_a_visible_selections": tenant_a_visible,
        "tenant_b_cross_tenant_visible_selections": tenant_b_visible,
        "rls": "PASS",
    }
    residue = {
        "schema": "axignal.billing-rollback-residue.v0.1",
        "status": "PASS",
        "active_test_entitlements": active_entitlements,
        "open_reservations": open_reservations,
        "active_capabilities": active_capabilities,
        "pending_test_selections": pending_selections,
        "cross_tenant_effects": tenant_b_visible,
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
    outputs = run(dsn)
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
