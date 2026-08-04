from __future__ import annotations

import argparse
import json
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import UUID

import psycopg
from psycopg import sql
from psycopg.rows import dict_row

from axignal_api.entitlement_repository import EntitlementRepository
from trial_grant_fixture import ensure_active_trial_grant

TENANT_A = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
TENANT_B = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
START = datetime(2026, 7, 29, 18, 0, tzinfo=UTC)
CAPABILITY = "EXPLAIN_CLAIMS_AND_EVIDENCE"


def _clean(dsn: str) -> None:
    with psycopg.connect(dsn) as connection, connection.cursor() as cursor:
        cursor.execute(
            "DELETE FROM tenant_private.entitlement_events WHERE tenant_id = ANY(%s)",
            ([TENANT_A, TENANT_B],),
        )
        cursor.execute(
            "DELETE FROM tenant_private.ai_token_reservations WHERE tenant_id = ANY(%s)",
            ([TENANT_A, TENANT_B],),
        )
        cursor.execute(
            "DELETE FROM tenant_private.organisation_entitlements WHERE tenant_id = ANY(%s)",
            ([TENANT_A, TENANT_B],),
        )


def _expect_failure(function, marker: str) -> str:
    try:
        function()
    except Exception as exc:
        message = str(exc)
        if marker not in message:
            raise AssertionError(f"Expected {marker!r}, received {message!r}") from exc
        return message
    raise AssertionError(f"Expected failure containing {marker!r}")


def _reserve_concurrently(repository: EntitlementRepository) -> tuple[dict[str, Any], str]:
    def reserve(operation_id: str) -> dict[str, Any]:
        return repository.reserve(
            tenant_id=TENANT_A,
            operation_id=operation_id,
            capability=CAPABILITY,
            requested_tokens=600_000,
            actor_subject="usr_e2e",
            now=START + timedelta(minutes=1),
        )

    successes: list[dict[str, Any]] = []
    failures: list[str] = []
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(reserve, "op_concurrent_alpha"),
            executor.submit(reserve, "op_concurrent_bravo"),
        ]
        for future in futures:
            try:
                successes.append(future.result())
            except Exception as exc:
                failures.append(str(exc))
    if len(successes) != 1 or len(failures) != 1:
        raise AssertionError(
            f"Concurrent gate expected one success and one failure: "
            f"successes={len(successes)} failures={len(failures)}"
        )
    if "trial_token_budget_exhausted" not in failures[0]:
        raise AssertionError(f"Unexpected concurrent failure: {failures[0]}")
    return successes[0], failures[0]


def _assert_cross_tenant_hidden(dsn: str, reservation_id: UUID) -> None:
    with (
        psycopg.connect(dsn, row_factory=dict_row) as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute(
            sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier("axignal_app"))
        )
        cursor.execute(
            "SELECT set_config('app.tenant_id', %s, true)",
            (str(TENANT_B),),
        )
        cursor.execute(
            """
            SELECT reservation_id
            FROM tenant_private.ai_token_reservations
            WHERE reservation_id = %s
            """,
            (reservation_id,),
        )
        if cursor.fetchone() is not None:
            raise AssertionError("Cross-tenant reservation became visible")


def _grant_paid_entitlement(dsn: str) -> None:
    with psycopg.connect(dsn) as connection, connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO tenant_private.organisation_entitlements (
              tenant_id, entitlement_kind, plan_code, state, policy_version,
              starts_at, expires_at, unlimited_ai_tokens, token_budget_total,
              activated_by
            ) VALUES (
              %s, 'PAID_MONTHLY', 'PROFESSIONAL_MONTHLY', 'ACTIVE',
              'ai-assistance-policy@0.1.0', %s, NULL, true, NULL,
              'test-billing-adapter'
            )
            """,
            (TENANT_B, START + timedelta(days=8)),
        )


def _assert_events_append_only(dsn: str) -> None:
    def mutate() -> None:
        with psycopg.connect(dsn) as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE tenant_private.entitlement_events
                SET event_type = 'MUTATED'
                WHERE tenant_id = %s
                """,
                (TENANT_A,),
            )

    _expect_failure(mutate, "append-only")


def run(dsn: str) -> dict[str, Any]:
    _clean(dsn)
    repository = EntitlementRepository(dsn)

    trial_a = repository.activate_trial(
        tenant_id=TENANT_A,
        actor_subject="usr_e2e",
        now=START,
    )
    assert trial_a["entitlement_kind"] == "TRIAL"
    assert trial_a["token_budget_total"] == 1_000_000
    assert trial_a["unlimited_ai_tokens"] is False
    assert trial_a["expires_at"] - trial_a["starts_at"] == timedelta(days=7)
    ensure_active_trial_grant(dsn, tenant_id=TENANT_A, now=START)
    _expect_failure(
        lambda: repository.activate_trial(
            tenant_id=TENANT_A,
            actor_subject="usr_e2e",
            now=START + timedelta(minutes=1),
        ),
        "trial_already_activated",
    )

    first_reservation, concurrency_failure = _reserve_concurrently(repository)
    replay = repository.reserve(
        tenant_id=TENANT_A,
        operation_id=str(first_reservation["operation_id"]),
        capability=CAPABILITY,
        requested_tokens=600_000,
        actor_subject="usr_e2e",
        now=START + timedelta(minutes=2),
    )
    assert replay["reservation_id"] == first_reservation["reservation_id"]

    repository.reconcile(
        tenant_id=TENANT_A,
        reservation_id=first_reservation["reservation_id"],
        actual_tokens=550_000,
        actor_subject="usr_e2e",
        now=START + timedelta(minutes=3),
    )
    usage_after_first = repository.usage(tenant_id=TENANT_A)
    assert usage_after_first is not None
    assert usage_after_first["token_budget_available"] == 450_000

    final_reservation = repository.reserve(
        tenant_id=TENANT_A,
        operation_id="op_exhaust_remaining_budget",
        capability=CAPABILITY,
        requested_tokens=450_000,
        actor_subject="usr_e2e",
        now=START + timedelta(minutes=4),
    )
    repository.reconcile(
        tenant_id=TENANT_A,
        reservation_id=final_reservation["reservation_id"],
        actual_tokens=450_000,
        actor_subject="usr_e2e",
        now=START + timedelta(minutes=5),
    )
    exhausted_usage = repository.usage(tenant_id=TENANT_A)
    assert exhausted_usage is not None
    assert exhausted_usage["token_budget_consumed"] == 1_000_000
    assert exhausted_usage["token_budget_reserved"] == 0
    assert exhausted_usage["token_budget_available"] == 0
    _expect_failure(
        lambda: repository.reserve(
            tenant_id=TENANT_A,
            operation_id="op_after_exhaustion",
            capability=CAPABILITY,
            requested_tokens=1,
            actor_subject="usr_e2e",
            now=START + timedelta(minutes=6),
        ),
        "trial_token_budget_exhausted",
    )
    _assert_cross_tenant_hidden(dsn, first_reservation["reservation_id"])

    trial_b = repository.activate_trial(
        tenant_id=TENANT_B,
        actor_subject="usr_e2e_b",
        now=START,
    )
    ensure_active_trial_grant(dsn, tenant_id=TENANT_B, now=START)
    released = repository.reserve(
        tenant_id=TENANT_B,
        operation_id="op_release_without_usage",
        capability="READ_RESEARCH_RUN_PROGRESS",
        requested_tokens=12_345,
        actor_subject="usr_e2e_b",
        now=START + timedelta(minutes=1),
    )
    repository.release(
        tenant_id=TENANT_B,
        reservation_id=released["reservation_id"],
        actor_subject="usr_e2e_b",
        now=START + timedelta(minutes=2),
    )
    release_usage = repository.usage(tenant_id=TENANT_B)
    assert release_usage is not None
    assert release_usage["token_budget_reserved"] == 0
    assert release_usage["token_budget_consumed"] == 0

    expired = repository.expire_trial(
        tenant_id=TENANT_B,
        actor_subject="system-expiry",
        now=START + timedelta(days=8),
    )
    assert expired["state"] == "READ_ONLY"
    assert trial_b["entitlement_id"] == expired["entitlement_id"]
    _expect_failure(
        lambda: repository.reserve(
            tenant_id=TENANT_B,
            operation_id="op_after_expiry",
            capability=CAPABILITY,
            requested_tokens=100,
            actor_subject="usr_e2e_b",
            now=START + timedelta(days=8),
        ),
        "active_entitlement_required",
    )

    _grant_paid_entitlement(dsn)
    paid_usage = repository.usage(tenant_id=TENANT_B)
    assert paid_usage is not None
    assert paid_usage["entitlement_kind"] == "PAID_MONTHLY"
    assert paid_usage["unlimited_ai_tokens"] is True
    assert paid_usage["token_budget_total"] is None
    paid_reservation = repository.reserve(
        tenant_id=TENANT_B,
        operation_id="op_paid_without_monthly_quota",
        capability="ASSEMBLE_EVIDENCE_LINKED_DOSSIER",
        requested_tokens=2_000_000,
        actor_subject="usr_paid_e2e",
        now=START + timedelta(days=8, minutes=1),
    )
    repository.reconcile(
        tenant_id=TENANT_B,
        reservation_id=paid_reservation["reservation_id"],
        actual_tokens=1_800_000,
        actor_subject="usr_paid_e2e",
        now=START + timedelta(days=8, minutes=2),
    )
    paid_after = repository.usage(tenant_id=TENANT_B)
    assert paid_after is not None
    assert paid_after["token_budget_available"] is None
    assert paid_after["token_budget_consumed"] == 1_800_000

    _assert_events_append_only(dsn)

    return {
        "schema": "axignal.entitlement-runtime-e2e.v0.1",
        "status": "PASS",
        "trial_duration_days": 7,
        "trial_budget_total": 1_000_000,
        "concurrent_reservations": 2,
        "concurrent_successes": 1,
        "concurrent_failures": 1,
        "concurrency_failure": "trial_token_budget_exhausted"
        if "trial_token_budget_exhausted" in concurrency_failure
        else "unexpected",
        "trial_consumed_tokens": exhausted_usage["token_budget_consumed"],
        "trial_available_tokens": exhausted_usage["token_budget_available"],
        "release_residue_tokens": release_usage["token_budget_reserved"],
        "expired_state": expired["state"],
        "cross_tenant_visibility": "BLOCKED_BY_RLS",
        "paid_monthly_token_quota": None,
        "paid_token_overage_billing": False,
        "paid_usage_tokens": paid_after["token_budget_consumed"],
        "append_only_events": True,
        "stripe_calls": 0,
        "model_calls": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/entitlement-runtime-e2e.json"),
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
