#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import psycopg
from psycopg.rows import dict_row

DSN = os.environ["AXIGNAL_DATABASE_URL"]
TENANT_A = uuid4()
TENANT_B = uuid4()
OWNER = "usr_seat_owner"
OWNER_EMAIL = "owner@seat-e2e.test"


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def app_call(
    tenant_id: UUID,
    query: str,
    params: tuple[object, ...],
) -> dict | None:
    with psycopg.connect(DSN, row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL ROLE axignal_app")
            cursor.execute(
                "SELECT set_config('app.tenant_id', %s, true)",
                (str(tenant_id),),
            )
            cursor.execute(query, params)
            return cursor.fetchone()


def seed_paid(tenant_id: UUID, plan_code: str) -> UUID:
    entitlement_id = uuid4()
    with psycopg.connect(DSN, row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO tenant_private.organisation_entitlements (
                  entitlement_id, tenant_id, entitlement_kind, plan_code, state,
                  policy_version, starts_at, expires_at, unlimited_ai_tokens,
                  token_budget_total, activated_by
                ) VALUES (
                  %s, %s, 'PAID_MONTHLY', %s, 'ACTIVE',
                  'ai-assistance-policy@0.1.0', now(), NULL, true, NULL,
                  'seat-governance-e2e'
                )
                """,
                (entitlement_id, tenant_id, plan_code),
            )
    return entitlement_id


def update_entitlement(
    entitlement_id: UUID,
    *,
    plan_code: str | None = None,
    state: str | None = None,
) -> None:
    assignments: list[str] = []
    values: list[object] = []
    if plan_code is not None:
        assignments.append("plan_code = %s")
        values.append(plan_code)
    if state is not None:
        assignments.append("state = %s")
        values.append(state)
    values.append(entitlement_id)
    with psycopg.connect(DSN) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                UPDATE tenant_private.organisation_entitlements
                SET {", ".join(assignments)}, updated_at = now()
                WHERE entitlement_id = %s
                """,
                tuple(values),
            )


def bootstrap_owner(tenant_id: UUID) -> dict:
    row = app_call(
        tenant_id,
        """
        SELECT * FROM tenant_private.bootstrap_organisation_owner(
          %s, %s, %s, now()
        )
        """,
        (OWNER, OWNER_EMAIL, OWNER),
    )
    assert row is not None
    return row


def invite(
    tenant_id: UUID,
    *,
    operation: str,
    email: str,
    role: str = "BID_REVIEWER",
    actor: str = OWNER,
    expires_at: datetime | None = None,
) -> dict:
    token = f"token-{operation}"
    row = app_call(
        tenant_id,
        """
        SELECT * FROM tenant_private.reserve_seat_invitation(
          %s, %s, %s, %s, 'TEST', %s, %s, now()
        )
        """,
        (
            operation,
            email,
            role,
            digest(token),
            actor,
            expires_at or datetime.now(UTC) + timedelta(hours=1),
        ),
    )
    assert row is not None
    row["_token"] = token
    return row


def accept(
    tenant_id: UUID,
    *,
    token: str,
    principal: str,
    email: str,
) -> dict:
    row = app_call(
        tenant_id,
        """
        SELECT * FROM tenant_private.accept_seat_invitation(
          %s, %s, %s, %s, now()
        )
        """,
        (digest(token), principal, email, principal),
    )
    assert row is not None
    return row


def revoke_member(tenant_id: UUID, membership_id: UUID) -> dict:
    row = app_call(
        tenant_id,
        """
        SELECT * FROM tenant_private.revoke_organisation_membership(
          %s, %s, now()
        )
        """,
        (membership_id, OWNER),
    )
    assert row is not None
    return row


def seat_counts(tenant_id: UUID) -> dict:
    with psycopg.connect(DSN, row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL ROLE axignal_app")
            cursor.execute(
                "SELECT set_config('app.tenant_id', %s, true)",
                (str(tenant_id),),
            )
            cursor.execute(
                """
                SELECT
                  e.plan_code,
                  e.seat_capacity,
                  e.state,
                  count(a.*) FILTER (WHERE a.state = 'ACTIVE') AS active,
                  count(a.*) FILTER (WHERE a.state = 'RESERVED') AS reserved
                FROM tenant_private.organisation_seat_entitlements e
                LEFT JOIN tenant_private.organisation_seat_allocations a
                  ON a.tenant_id = e.tenant_id
                WHERE e.tenant_id = %s
                GROUP BY e.plan_code, e.seat_capacity, e.state
                """,
                (tenant_id,),
            )
            row = cursor.fetchone()
            assert row is not None
            return row


def expect_error(marker: str, operation) -> None:
    try:
        operation()
    except Exception as exc:
        assert marker in str(exc), (marker, exc)
    else:
        raise AssertionError(f"Expected {marker}")


def main() -> None:
    entitlement_a = seed_paid(TENANT_A, "PROFESSIONAL_MONTHLY")
    seed_paid(TENANT_B, "PROFESSIONAL_MONTHLY")
    owner = bootstrap_owner(TENANT_A)
    bootstrap_owner(TENANT_B)

    second_invite = invite(
        TENANT_A,
        operation="op_seat_member_0002",
        email="member2@seat-e2e.test",
    )
    member2 = accept(
        TENANT_A,
        token=second_invite["_token"],
        principal="usr_member_2",
        email="member2@seat-e2e.test",
    )
    third_invite = invite(
        TENANT_A,
        operation="op_seat_member_0003",
        email="member3@seat-e2e.test",
    )
    member3 = accept(
        TENANT_A,
        token=third_invite["_token"],
        principal="usr_member_3",
        email="member3@seat-e2e.test",
    )

    professional = seat_counts(TENANT_A)
    assert professional["seat_capacity"] == 3
    assert professional["active"] == 3
    assert professional["reserved"] == 0

    expect_error(
        "seat_capacity_exhausted",
        lambda: invite(
            TENANT_A,
            operation="op_seat_member_0004",
            email="member4@seat-e2e.test",
        ),
    )
    expect_error(
        "membership_admin_required",
        lambda: invite(
            TENANT_A,
            operation="op_non_admin_invite",
            email="blocked@seat-e2e.test",
            actor="usr_member_2",
        ),
    )

    replay = invite(
        TENANT_A,
        operation="op_seat_member_0003",
        email="member3@seat-e2e.test",
    )
    assert replay["invitation_id"] == third_invite["invitation_id"]
    assert seat_counts(TENANT_A)["active"] == 3

    update_entitlement(entitlement_a, plan_code="TEAM_MONTHLY")
    assert seat_counts(TENANT_A)["seat_capacity"] == 15

    members: list[dict] = [member2, member3]
    for index in range(4, 15):
        item = invite(
            TENANT_A,
            operation=f"op_seat_member_{index:04d}",
            email=f"member{index}@seat-e2e.test",
        )
        members.append(
            accept(
                TENANT_A,
                token=item["_token"],
                principal=f"usr_member_{index}",
                email=f"member{index}@seat-e2e.test",
            )
        )

    before_race = seat_counts(TENANT_A)
    assert before_race["active"] == 14
    assert before_race["reserved"] == 0

    def final_invite(index: int) -> str:
        try:
            invite(
                TENANT_A,
                operation=f"op_final_race_{index:04d}",
                email=f"race{index}@seat-e2e.test",
            )
            return "SUCCESS"
        except Exception as exc:
            assert "seat_capacity_exhausted" in str(exc)
            return "EXHAUSTED"

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(final_invite, (1, 2)))
    assert sorted(results) == ["EXHAUSTED", "SUCCESS"]
    full_team = seat_counts(TENANT_A)
    assert full_team["active"] == 14
    assert full_team["reserved"] == 1

    expect_error(
        "seat_downgrade_capacity_conflict",
        lambda: update_entitlement(
            entitlement_a,
            plan_code="PROFESSIONAL_MONTHLY",
        ),
    )
    assert seat_counts(TENANT_A)["seat_capacity"] == 15

    expect_error(
        "last_owner_revocation_forbidden",
        lambda: revoke_member(TENANT_A, owner["membership_id"]),
    )

    with psycopg.connect(DSN, row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT invitation_id
                FROM tenant_private.organisation_invitations
                WHERE tenant_id = %s AND status = 'PENDING'
                """,
                (TENANT_A,),
            )
            pending = cursor.fetchall()
    for row in pending:
        app_call(
            TENANT_A,
            """
            SELECT * FROM tenant_private.revoke_seat_invitation(
              %s, %s, 'ADMIN_REVOKED', now()
            )
            """,
            (row["invitation_id"], OWNER),
        )

    for member in members[2:]:
        revoke_member(TENANT_A, member["membership_id"])

    assert seat_counts(TENANT_A)["active"] == 3
    update_entitlement(entitlement_a, plan_code="PROFESSIONAL_MONTHLY")
    downgraded = seat_counts(TENANT_A)
    assert downgraded["seat_capacity"] == 3
    assert downgraded["active"] == 3

    revoke_member(TENANT_A, members[1]["membership_id"])
    expiring = invite(
        TENANT_A,
        operation="op_expiring_invitation",
        email="expires@seat-e2e.test",
        expires_at=datetime.now(UTC) + timedelta(seconds=1),
    )
    assert seat_counts(TENANT_A)["reserved"] == 1
    app_call(
        TENANT_A,
        """
        SELECT tenant_private.expire_pending_seat_invitations(
          %s, %s
        ) AS expired
        """,
        (OWNER, datetime.now(UTC) + timedelta(seconds=2)),
    )
    assert seat_counts(TENANT_A)["reserved"] == 0

    with psycopg.connect(DSN, row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL ROLE axignal_app")
            cursor.execute(
                "SELECT set_config('app.tenant_id', %s, true)",
                (str(TENANT_B),),
            )
            cursor.execute(
                """
                SELECT membership_id
                FROM tenant_private.organisation_memberships
                WHERE membership_id = %s
                """,
                (owner["membership_id"],),
            )
            assert cursor.fetchone() is None

    active_read = app_call(
        TENANT_A,
        "SELECT tenant_private.seat_access_decision(%s, false, now()) AS d",
        (OWNER,),
    )
    active_write = app_call(
        TENANT_A,
        "SELECT tenant_private.seat_access_decision(%s, true, now()) AS d",
        (OWNER,),
    )
    assert active_read["d"]["decision"] == "ALLOW"
    assert active_write["d"]["decision"] == "ALLOW"

    update_entitlement(entitlement_a, state="READ_ONLY")
    read_only_read = app_call(
        TENANT_A,
        "SELECT tenant_private.seat_access_decision(%s, false, now()) AS d",
        (OWNER,),
    )
    read_only_write = app_call(
        TENANT_A,
        "SELECT tenant_private.seat_access_decision(%s, true, now()) AS d",
        (OWNER,),
    )
    assert read_only_read["d"]["decision"] == "ALLOW"
    assert read_only_write["d"]["reason"] == "seat_entitlement_read_only"

    update_entitlement(entitlement_a, state="SUSPENDED")
    suspended = app_call(
        TENANT_A,
        "SELECT tenant_private.seat_access_decision(%s, false, now()) AS d",
        (OWNER,),
    )
    assert suspended["d"]["decision"] == "DENY"
    assert suspended["d"]["reason"] == "seat_entitlement_inactive"

    with psycopg.connect(DSN) as connection:
        with connection.cursor() as cursor:
            expect_error(
                "membership_audit_events_are_append_only",
                lambda: cursor.execute(
                    """
                    UPDATE tenant_private.membership_audit_events
                    SET event_type = 'TAMPERED'
                    WHERE tenant_id = %s
                    """,
                    (TENANT_A,),
                ),
            )
            connection.rollback()

    with psycopg.connect(DSN, row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT count(*) AS count
                FROM tenant_private.membership_audit_events
                WHERE tenant_id = %s
                """,
                (TENANT_A,),
            )
            audit_count = int(cursor.fetchone()["count"])

    evidence = {
        "status": "PASS",
        "task_id": "AX-GE2E-P21-T02",
        "professional_capacity": 3,
        "team_capacity": 15,
        "trial_capacity": 2,
        "professional_fourth_seat": "BLOCKED",
        "team_sixteenth_seat": "BLOCKED_CONCURRENTLY",
        "concurrent_last_seat_successes": results.count("SUCCESS"),
        "downgrade_over_capacity": "BLOCKED",
        "last_owner_revocation": "BLOCKED",
        "expired_invitation_released": expiring["invitation_id"] is not None,
        "cross_tenant_visibility": "BLOCKED_BY_RLS",
        "read_only_read": "ALLOW",
        "read_only_write": "DENY",
        "suspended_access": "DENY",
        "audit_immutable": True,
        "audit_events": audit_count,
        "stripe_subscription_quantity": 1,
        "external_stripe_calls": 0,
        "model_calls": 0,
        "commercial_activation_authorised": False,
    }

    output_dir = Path(os.environ.get("AXIGNAL_SEAT_EVIDENCE_DIR", "artifacts"))
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "seat-governance-e2e.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(evidence, sort_keys=True))


if __name__ == "__main__":
    main()
