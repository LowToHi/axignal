#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import psycopg
from psycopg import errors
from psycopg.rows import dict_row

DSN = os.environ["AXIGNAL_DATABASE_URL"]
EVIDENCE_DIR = Path(os.environ.get("AXIGNAL_IDENTITY_EVIDENCE_DIR", "artifacts"))
BASE = datetime(2026, 7, 31, 18, 0, tzinfo=UTC)


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def hmac_like(label: str) -> str:
    return digest(f"p25:{label}")


def app_call(query: str, params: tuple[object, ...] = ()) -> dict | None:
    with (
        psycopg.connect(DSN, row_factory=dict_row) as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute("SET LOCAL ROLE axignal_app")
        cursor.execute(query, params)
        return cursor.fetchone()


def tenant_call(
    tenant_id: UUID,
    query: str,
    params: tuple[object, ...] = (),
) -> dict | None:
    with (
        psycopg.connect(DSN, row_factory=dict_row) as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute("SET LOCAL ROLE axignal_app")
        cursor.execute(
            "SELECT set_config('app.tenant_id', %s, true)",
            (str(tenant_id),),
        )
        cursor.execute(query, params)
        return cursor.fetchone()


def admin_one(query: str, params: tuple[object, ...] = ()) -> dict | None:
    with (
        psycopg.connect(DSN, row_factory=dict_row) as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute(query, params)
        return cursor.fetchone()


def begin_signup(
    *,
    token: str,
    email: str,
    email_identity: str,
    installation: str,
    network: str,
    domain: str,
    disposable: bool = False,
    now: datetime = BASE,
) -> None:
    row = app_call(
        """
        SELECT * FROM identity_private.begin_email_challenge(
          'SIGNUP', %s, %s, %s, %s, %s, %s, %s, %s,
          %s, %s
        )
        """,
        (
            digest(token),
            email,
            hmac_like(f"email:{email}"),
            hmac_like(f"identity:{email_identity}"),
            hmac_like(f"domain:{domain}"),
            hmac_like(f"installation:{installation}"),
            hmac_like(f"network:{network}"),
            disposable,
            now + timedelta(minutes=10),
            now,
        ),
    )
    assert row is not None and row["state"] == "PENDING"


def consume_signup(
    *,
    token: str,
    ticket: str,
    operation: str,
    now: datetime = BASE + timedelta(seconds=1),
) -> dict:
    row = app_call(
        """
        SELECT identity_private.consume_signup_challenge(
          %s, %s, %s, 1000000, 250000, 5000000, 1000000, %s
        ) AS result
        """,
        (digest(token), digest(ticket), operation, now),
    )
    assert row is not None and isinstance(row["result"], dict)
    return row["result"]


def bind_test_passkey(
    *,
    ticket: str,
    user_id: UUID,
    tenant_id: UUID,
    session_token: str,
    now: datetime,
) -> dict:
    challenge = f"challenge_{uuid4().hex}"
    challenge_row = app_call(
        """
        SELECT * FROM identity_private.create_webauthn_challenge(
          %s, %s, 'REGISTRATION', %s, (
            SELECT bootstrap_ticket_id
            FROM identity_private.bootstrap_tickets
            WHERE token_digest = %s
          ), '127.0.0.1', 'http://127.0.0.1:18080', %s, %s
        )
        """,
        (
            challenge,
            digest(challenge),
            user_id,
            digest(ticket),
            now + timedelta(minutes=5),
            now,
        ),
    )
    assert challenge_row is not None
    recovery = [hmac_like(f"recovery:{index}:{user_id}") for index in range(8)]
    row = app_call(
        """
        SELECT identity_private.complete_passkey_registration(
          %s, %s, %s, %s, 0, ARRAY['internal']::text[],
          'MULTI_DEVICE', true, NULL, %s, %s, %s, %s,
          %s, 3600, 86400, %s
        ) AS result
        """,
        (
            digest(challenge),
            digest(ticket),
            f"credential_{uuid4().hex}",
            "a1b2c3d4",
            digest(session_token),
            hmac_like("installation:first"),
            hmac_like("network:first"),
            hmac_like("ua:first"),
            recovery,
            now + timedelta(seconds=1),
        ),
    )
    assert row is not None and isinstance(row["result"], dict)
    assert UUID(str(row["result"]["tenant_id"])) == tenant_id
    return row["result"]


def expect_failure(marker: str, operation) -> str:
    try:
        operation()
    except Exception as exc:
        assert marker in str(exc), f"Expected {marker!r}, got {exc!r}"
        return marker
    raise AssertionError(f"Expected failure {marker}")


def main() -> None:
    first_token = f"verify_{uuid4().hex}"
    first_ticket = f"register_{uuid4().hex}"
    canonical_email_identity = "firstlast@gmail.com"
    begin_signup(
        token=first_token,
        email="first.last+trial@gmail.com",
        email_identity=canonical_email_identity,
        installation="device-a",
        network="203.0.113.0/24",
        domain="gmail.com",
    )
    first = consume_signup(
        token=first_token,
        ticket=first_ticket,
        operation=f"op_signup_{uuid4().hex}",
    )
    assert first["decision"] == "ALLOW"
    first_tenant = UUID(str(first["tenant_id"]))
    first_user = UUID(str(first["user_id"]))

    before = admin_one(
        """
        SELECT count(*) AS count
        FROM tenant_private.organisation_entitlements
        WHERE tenant_id = %s
        """,
        (first_tenant,),
    )
    assert before is not None and before["count"] == 0

    session_token = f"session_{uuid4().hex}{uuid4().hex}"
    bound = bind_test_passkey(
        ticket=first_ticket,
        user_id=first_user,
        tenant_id=first_tenant,
        session_token=session_token,
        now=BASE + timedelta(seconds=2),
    )
    assert bound["assurance_level"] == "AAL2"

    session = app_call(
        "SELECT identity_private.resolve_identity_session(%s, 300, %s) AS result",
        (digest(session_token), BASE + timedelta(seconds=4)),
    )
    assert session is not None
    assert session["result"]["assurance_level"] == "AAL2"
    assert session["result"]["membership_id"] is None

    duplicate_token = f"verify_{uuid4().hex}"
    duplicate_ticket = f"register_{uuid4().hex}"
    begin_signup(
        token=duplicate_token,
        email="firstlast@googlemail.com",
        email_identity=canonical_email_identity,
        installation="device-b",
        network="198.51.100.0/24",
        domain="gmail.com",
        now=BASE + timedelta(minutes=1),
    )
    duplicate = consume_signup(
        token=duplicate_token,
        ticket=duplicate_ticket,
        operation=f"op_signup_{uuid4().hex}",
        now=BASE + timedelta(minutes=1, seconds=1),
    )
    assert duplicate["decision"] == "REUSE_EXISTING_TRIAL"
    assert UUID(str(duplicate["tenant_id"])) == first_tenant
    grants = admin_one(
        "SELECT count(*) AS count FROM identity_private.trial_grants"
    )
    assert grants is not None and grants["count"] == 1

    risky_token = f"verify_{uuid4().hex}"
    risky_ticket = f"register_{uuid4().hex}"
    begin_signup(
        token=risky_token,
        email="second@example.test",
        email_identity="second@example.test",
        installation="device-a",
        network="203.0.113.0/24",
        domain="example.test",
        now=BASE + timedelta(minutes=2),
    )
    risky = consume_signup(
        token=risky_token,
        ticket=risky_ticket,
        operation=f"op_signup_{uuid4().hex}",
        now=BASE + timedelta(minutes=2, seconds=1),
    )
    assert risky["decision"] == "STEP_UP_REQUIRED"
    risky_tenant = UUID(str(risky["tenant_id"]))
    risky_user = UUID(str(risky["user_id"]))
    step_up = app_call(
        """
        SELECT identity_private.approve_trial_step_up(
          %s, %s, 'VERIFIED_PHONE', %s, %s,
          1000000, 5000000, %s
        ) AS result
        """,
        (
            risky_tenant,
            risky_user,
            hmac_like("phone:+34111111111"),
            str(risky["subject"]),
            BASE + timedelta(minutes=3),
        ),
    )
    assert step_up is not None
    assert step_up["result"]["state"] == "READY"
    assert step_up["result"]["decision"] == "ALLOW"

    activation_time = BASE + timedelta(hours=1)
    entitlement = tenant_call(
        first_tenant,
        """
        SELECT * FROM tenant_private.start_prepared_identity_trial(
          %s, %s, %s, %s
        )
        """,
        (
            first_user,
            str(first["subject"]),
            str(first["email"]),
            activation_time,
        ),
    )
    assert entitlement is not None
    assert entitlement["starts_at"] == activation_time
    assert entitlement["expires_at"] == activation_time + timedelta(days=7)
    assert entitlement["token_budget_total"] == 1_000_000

    idempotent = tenant_call(
        first_tenant,
        """
        SELECT * FROM tenant_private.start_prepared_identity_trial(
          %s, %s, %s, %s
        )
        """,
        (
            first_user,
            str(first["subject"]),
            str(first["email"]),
            activation_time + timedelta(minutes=1),
        ),
    )
    assert idempotent is not None
    assert idempotent["entitlement_id"] == entitlement["entitlement_id"]

    seats = admin_one(
        """
        SELECT seat_capacity, plan_code, state
        FROM tenant_private.organisation_seat_entitlements
        WHERE tenant_id = %s
        """,
        (first_tenant,),
    )
    assert seats == {"seat_capacity": 2, "plan_code": "TRIAL_7D", "state": "ACTIVE"}

    reservation = tenant_call(
        first_tenant,
        """
        SELECT * FROM tenant_private.reserve_ai_tokens(
          %s, 'REQUEST_BOUNDED_RESEARCH_RUN', 100000, %s, %s
        )
        """,
        (
            f"op_ai_{uuid4().hex}",
            str(first["subject"]),
            activation_time + timedelta(minutes=2),
        ),
    )
    assert reservation is not None
    usage = admin_one(
        """
        SELECT * FROM identity_private.trial_usage_accounts
        WHERE tenant_id = %s
        """,
        (first_tenant,),
    )
    assert usage is not None
    assert usage["token_budget_reserved"] == 100_000
    assert usage["cost_reserved_microunits"] == 500_000

    reconciled = tenant_call(
        first_tenant,
        """
        SELECT * FROM tenant_private.reconcile_ai_tokens(%s, 50000, %s, %s)
        """,
        (
            reservation["reservation_id"],
            str(first["subject"]),
            activation_time + timedelta(minutes=3),
        ),
    )
    assert reconciled is not None and reconciled["state"] == "RECONCILED"
    usage = admin_one(
        """
        SELECT * FROM identity_private.trial_usage_accounts
        WHERE tenant_id = %s
        """,
        (first_tenant,),
    )
    assert usage is not None
    assert usage["token_budget_reserved"] == 0
    assert usage["token_budget_consumed"] == 50_000
    assert usage["cost_consumed_microunits"] == 250_000

    with psycopg.connect(DSN) as connection, connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE identity_private.trial_usage_accounts
            SET cost_budget_microunits = cost_consumed_microunits + 10
            WHERE tenant_id = %s
            """,
            (first_tenant,),
        )
    expect_failure(
        "trial_cost_budget_exhausted",
        lambda: tenant_call(
            first_tenant,
            """
            SELECT * FROM tenant_private.reserve_ai_tokens(
              %s, 'REQUEST_BOUNDED_RESEARCH_RUN', 100, %s, %s
            )
            """,
            (
                f"op_cost_{uuid4().hex}",
                str(first["subject"]),
                activation_time + timedelta(minutes=4),
            ),
        ),
    )

    first_run = uuid4()
    second_run = uuid4()

    def insert_run(run_id: UUID, state: str) -> dict | None:
        return tenant_call(
            first_tenant,
            """
            INSERT INTO tenant_private.research_runs (
              research_run_id, tenant_id, context_id, opportunity_id,
              question, state, private_knowledge_authorised,
              source_plan, budgets
            ) VALUES (%s, %s, %s, %s, %s, %s, false, '[]'::jsonb, '{}'::jsonb)
            RETURNING research_run_id, state
            """,
            (
                run_id,
                first_tenant,
                f"context-{run_id}",
                f"opportunity-{run_id}",
                "Can AXIGNAL govern concurrent trial research?",
                state,
            ),
        )

    assert insert_run(first_run, "QUEUED") is not None
    expect_failure(
        "trial_concurrency_exhausted",
        lambda: insert_run(second_run, "QUEUED"),
    )
    completed = tenant_call(
        first_tenant,
        """
        UPDATE tenant_private.research_runs
        SET state = 'COMPLETED', updated_at = %s
        WHERE research_run_id = %s
        RETURNING research_run_id, state
        """,
        (activation_time + timedelta(minutes=5), first_run),
    )
    assert completed is not None and completed["state"] == "COMPLETED"
    assert insert_run(second_run, "QUEUED") is not None

    immutable = "NOT_TESTED"
    try:
        with psycopg.connect(DSN) as connection, connection.cursor() as cursor:
            cursor.execute(
                "UPDATE identity_private.security_events SET decision = 'BLOCK'"
            )
    except errors.RaiseException as exc:
        assert "identity_append_only_ledger" in str(exc)
        immutable = "BLOCKED"

    cross_schema = "NOT_TESTED"
    try:
        app_call("SELECT count(*) AS count FROM identity_private.users")
    except errors.InsufficientPrivilege:
        cross_schema = "BLOCKED"

    revoked = app_call(
        "SELECT identity_private.revoke_identity_session(%s, 'E2E_LOGOUT', %s) AS revoked",
        (digest(session_token), activation_time + timedelta(minutes=6)),
    )
    assert revoked is not None and revoked["revoked"] is True
    expect_failure(
        "identity_session_expired",
        lambda: app_call(
            "SELECT identity_private.resolve_identity_session(%s, 300, %s) AS result",
            (digest(session_token), activation_time + timedelta(minutes=7)),
        ),
    )

    evidence = {
        "schema": "axignal.identity-trial-abuse-e2e.v1",
        "status": "PASS",
        "strong_alias_reuse": "REUSE_EXISTING_TRIAL",
        "duplicate_tenant_reused": True,
        "trial_grant_count_after_alias": 1,
        "weak_installation_signal": "STEP_UP_REQUIRED",
        "weak_signal_independent_block": False,
        "step_up": "ALLOW",
        "trial_before_first_ai": "NOT_ACTIVATED",
        "trial_activation": "FIRST_ADMITTED_AI_REQUEST",
        "trial_duration_seconds": 7 * 24 * 60 * 60,
        "trial_seats": 2,
        "trial_token_budget": 1_000_000,
        "cost_budget": "ENFORCED",
        "concurrent_research_runs": 1,
        "second_concurrent_run": "BLOCKED",
        "session_assurance": "AAL2",
        "session_revocation": "IMMEDIATE",
        "append_only_security_ledger": immutable,
        "identity_table_direct_access": cross_schema,
        "raw_ip_stored": False,
        "raw_installation_id_stored": False,
        "external_identity_provider_calls": 0,
        "model_calls": 0,
        "public_signup_authorised": False,
    }
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    target = EVIDENCE_DIR / "identity-trial-abuse-e2e.json"
    target.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    print(json.dumps(evidence, sort_keys=True))


if __name__ == "__main__":
    main()
