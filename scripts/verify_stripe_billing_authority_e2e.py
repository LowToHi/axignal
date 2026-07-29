from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from uuid import UUID

import psycopg
from psycopg import sql

TENANT_ID = UUID("d1111111-1111-4111-8111-111111111111")


def _expect_failure(function, marker: str) -> str:
    try:
        function()
    except Exception as exc:
        message = str(exc)
        if marker.casefold() not in message.casefold():
            raise AssertionError(f"Expected {marker!r}, received {message!r}") from exc
        return message
    raise AssertionError(f"Expected failure containing {marker!r}")


def run(dsn: str) -> dict[str, object]:
    def app_direct_insert() -> None:
        with psycopg.connect(dsn) as connection, connection.cursor() as cursor:
            cursor.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier("axignal_app")))
            cursor.execute(
                "SELECT set_config('app.tenant_id', %s, true)", (str(TENANT_ID),)
            )
            cursor.execute(
                """
                INSERT INTO tenant_private.billing_plan_selections (
                  tenant_id, operation_id, provider_account_id, plan_code,
                  state, selected_by, selected_at
                ) VALUES (%s, 'op_forbidden_direct_insert', 'acct_forbidden',
                          'PROFESSIONAL_MONTHLY', 'ACTIVE', 'forbidden', now())
                """,
                (TENANT_ID,),
            )

    def app_direct_receipt() -> None:
        with psycopg.connect(dsn) as connection, connection.cursor() as cursor:
            cursor.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier("axignal_app")))
            cursor.execute(
                """
                INSERT INTO axignal_global.stripe_webhook_receipts (
                  provider_event_id, tenant_id, selection_id, event_type,
                  event_created_at, livemode, provider_account_id,
                  payload_digest, disposition
                ) VALUES ('evt_forbidden', %s, %s, 'invoice.paid', now(), false,
                          'acct_forbidden', repeat('0', 64), 'APPLIED')
                """,
                (TENANT_ID, TENANT_ID),
            )

    def billing_worker_direct_select() -> None:
        with psycopg.connect(dsn) as connection, connection.cursor() as cursor:
            cursor.execute(
                sql.SQL("SET LOCAL ROLE {}").format(
                    sql.Identifier("axignal_billing_worker")
                )
            )
            cursor.execute("SELECT * FROM tenant_private.organisation_entitlements")

    app_insert_error = _expect_failure(app_direct_insert, "permission denied")
    receipt_error = _expect_failure(app_direct_receipt, "permission denied")
    worker_select_error = _expect_failure(billing_worker_direct_select, "permission denied")
    return {
        "schema": "axignal.stripe-billing-authority-e2e.v0.1",
        "status": "PASS",
        "app_direct_billing_mutation": "BLOCKED",
        "app_direct_webhook_receipt": "BLOCKED",
        "billing_worker_direct_table_read": "BLOCKED",
        "app_error_class": app_insert_error.splitlines()[0],
        "receipt_error_class": receipt_error.splitlines()[0],
        "worker_error_class": worker_select_error.splitlines()[0],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/stripe-billing-authority-e2e.json"),
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
