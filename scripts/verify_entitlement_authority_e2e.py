from __future__ import annotations

import argparse
import json
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

import psycopg
from psycopg import sql

from axignal_api.entitlement_repository import EntitlementRepository

TENANT_ID = UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc")
START = datetime(2026, 7, 29, 19, 0, tzinfo=UTC)
OPERATION_ID = "op_concurrent_idempotent_authority"
CAPABILITY = "READ_RESEARCH_RUN_PROGRESS"


def _clean(dsn: str) -> None:
    with psycopg.connect(dsn) as connection, connection.cursor() as cursor:
        cursor.execute(
            "DELETE FROM tenant_private.entitlement_events WHERE tenant_id = %s",
            (TENANT_ID,),
        )
        cursor.execute(
            "DELETE FROM tenant_private.ai_token_reservations WHERE tenant_id = %s",
            (TENANT_ID,),
        )
        cursor.execute(
            "DELETE FROM tenant_private.organisation_entitlements WHERE tenant_id = %s",
            (TENANT_ID,),
        )


def _as_role(dsn: str, role: str, statement: str, parameters: tuple[object, ...]) -> None:
    with psycopg.connect(dsn) as connection, connection.cursor() as cursor:
        cursor.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(role)))
        cursor.execute(
            "SELECT set_config('app.tenant_id', %s, true)",
            (str(TENANT_ID),),
        )
        cursor.execute(statement, parameters)


def _expect_permission_denied(function) -> str:
    try:
        function()
    except psycopg.errors.InsufficientPrivilege as exc:
        return str(exc)
    raise AssertionError("Expected PostgreSQL permission denial")


def _assert_direct_table_mutation_blocked(dsn: str) -> None:
    _expect_permission_denied(
        lambda: _as_role(
            dsn,
            "axignal_app",
            """
            UPDATE tenant_private.organisation_entitlements
            SET state = 'CANCELLED'
            WHERE tenant_id = %s
            """,
            (TENANT_ID,),
        )
    )
    _expect_permission_denied(
        lambda: _as_role(
            dsn,
            "axignal_app",
            """
            INSERT INTO tenant_private.entitlement_events (
              tenant_id, event_type, actor_subject, payload
            ) VALUES (%s, 'FORGED_EVENT', 'forged', '{}'::jsonb)
            """,
            (TENANT_ID,),
        )
    )
    _expect_permission_denied(
        lambda: _as_role(
            dsn,
            "axignal_app",
            "DELETE FROM tenant_private.ai_token_reservations WHERE tenant_id = %s",
            (TENANT_ID,),
        )
    )


def _assert_non_app_cannot_execute_mutator(dsn: str) -> None:
    _expect_permission_denied(
        lambda: _as_role(
            dsn,
            "axignal_proposal_worker",
            "SELECT * FROM tenant_private.activate_controlled_trial(%s, %s)",
            ("unauthorised-worker", START),
        )
    )


def _concurrent_idempotent_reservation(
    repository: EntitlementRepository,
) -> tuple[UUID, int]:
    def reserve() -> dict[str, object]:
        return repository.reserve(
            tenant_id=TENANT_ID,
            operation_id=OPERATION_ID,
            capability=CAPABILITY,
            requested_tokens=100_000,
            actor_subject="usr_authority_e2e",
            now=START + timedelta(minutes=1),
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = [future.result() for future in (executor.submit(reserve), executor.submit(reserve))]
    reservation_ids = {UUID(str(result["reservation_id"])) for result in results}
    if len(reservation_ids) != 1:
        raise AssertionError(f"Concurrent retry created multiple reservations: {reservation_ids}")
    reservation_id = next(iter(reservation_ids))
    usage = repository.usage(tenant_id=TENANT_ID)
    if usage is None:
        raise AssertionError("Entitlement usage disappeared")
    reserved = int(usage["token_budget_reserved"])
    if reserved != 100_000:
        raise AssertionError(f"Concurrent retry reserved {reserved} tokens instead of 100000")
    return reservation_id, reserved


def run(dsn: str) -> dict[str, object]:
    _clean(dsn)
    repository = EntitlementRepository(dsn)
    entitlement = repository.activate_trial(
        tenant_id=TENANT_ID,
        actor_subject="usr_authority_e2e",
        now=START,
    )
    if entitlement["state"] != "ACTIVE":
        raise AssertionError("Security-definer activation did not return ACTIVE entitlement")

    _assert_direct_table_mutation_blocked(dsn)
    _assert_non_app_cannot_execute_mutator(dsn)
    reservation_id, reserved = _concurrent_idempotent_reservation(repository)
    repository.release(
        tenant_id=TENANT_ID,
        reservation_id=reservation_id,
        actor_subject="usr_authority_e2e",
        now=START + timedelta(minutes=2),
    )
    usage = repository.usage(tenant_id=TENANT_ID)
    if usage is None or usage["token_budget_reserved"] != 0:
        raise AssertionError("Reservation release left authority-test residue")

    return {
        "schema": "axignal.entitlement-authority-e2e.v0.1",
        "status": "PASS",
        "security_definer_functions_operational": True,
        "direct_app_update_blocked": True,
        "direct_app_insert_blocked": True,
        "direct_app_delete_blocked": True,
        "non_app_function_execution_blocked": True,
        "concurrent_same_operation_calls": 2,
        "concurrent_reservation_ids": 1,
        "tokens_reserved_once": reserved,
        "release_residue_tokens": 0,
        "stripe_calls": 0,
        "model_calls": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/entitlement-authority-e2e.json"),
    )
    args = parser.parse_args()
    dsn = os.environ.get("AXIGNAL_DATABASE_URL")
    if not dsn:
        raise SystemExit("AXIGNAL_DATABASE_URL is required")
    result = run(dsn)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
