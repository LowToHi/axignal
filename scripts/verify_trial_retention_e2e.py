from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import psycopg
from psycopg import sql
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from axignal_api.entitlement_repository import EntitlementRepository
from axignal_api.retention_repository import RetentionRepository

TENANT_A = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
TENANT_B = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
START = datetime(2026, 7, 29, 20, 0, tzinfo=UTC)


def _set_role(cursor: psycopg.Cursor[dict[str, object]], role: str) -> None:
    cursor.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(role)))


def _set_tenant(cursor: psycopg.Cursor[dict[str, object]], tenant_id: UUID) -> None:
    cursor.execute("SELECT set_config('app.tenant_id', %s, true)", (str(tenant_id),))


def _clean(dsn: str, tenant_ids: tuple[UUID, ...]) -> None:
    with psycopg.connect(dsn, row_factory=dict_row) as connection, connection.cursor() as cursor:
        cursor.execute("SELECT set_config('app.retention_purge', '1', true)")
        for tenant_id in tenant_ids:
            cursor.execute(
                "DELETE FROM tenant_private.human_review_events WHERE tenant_id = %s",
                (tenant_id,),
            )
            cursor.execute(
                "DELETE FROM tenant_private.human_review_cases WHERE tenant_id = %s",
                (tenant_id,),
            )
            cursor.execute(
                "UPDATE tenant_private.research_runs SET admission_handoff_id = NULL, dossier_id = NULL WHERE tenant_id = %s",
                (tenant_id,),
            )
            cursor.execute(
                "DELETE FROM axignal_global.admission_decisions WHERE admission_handoff_id IN (SELECT admission_handoff_id FROM axignal_global.admission_handoffs WHERE tenant_id = %s)",
                (tenant_id,),
            )
            cursor.execute(
                "DELETE FROM axignal_global.admission_handoffs WHERE tenant_id = %s",
                (tenant_id,),
            )
            cursor.execute(
                "DELETE FROM tenant_private.dossiers WHERE tenant_id = %s",
                (tenant_id,),
            )
            cursor.execute(
                "DELETE FROM tenant_private.research_evidence_links WHERE tenant_id = %s",
                (tenant_id,),
            )
            cursor.execute(
                "DELETE FROM tenant_private.knowledge_items WHERE tenant_id = %s",
                (tenant_id,),
            )
            cursor.execute(
                "DELETE FROM intent_intelligence.intent_events WHERE tenant_id = %s",
                (tenant_id,),
            )
            cursor.execute(
                "DELETE FROM tenant_private.research_runs WHERE tenant_id = %s",
                (tenant_id,),
            )
            cursor.execute(
                "DELETE FROM tenant_private.workspace_lifecycle_events WHERE tenant_id = %s",
                (tenant_id,),
            )
            cursor.execute(
                "DELETE FROM tenant_private.entitlement_events WHERE tenant_id = %s",
                (tenant_id,),
            )
            cursor.execute(
                "DELETE FROM tenant_private.ai_token_reservations WHERE tenant_id = %s",
                (tenant_id,),
            )
            cursor.execute(
                "DELETE FROM tenant_private.organisation_entitlements WHERE tenant_id = %s",
                (tenant_id,),
            )
            cursor.execute(
                "DELETE FROM tenant_private.workspace_lifecycle WHERE tenant_id = %s",
                (tenant_id,),
            )
            tenant_hash = _tenant_hash(cursor, tenant_id)
            cursor.execute(
                "DELETE FROM axignal_global.deletion_tombstones WHERE tenant_hash = %s",
                (tenant_hash,),
            )


def _tenant_hash(cursor: psycopg.Cursor[dict[str, object]], tenant_id: UUID) -> str:
    cursor.execute(
        "SELECT 'sha256:' || encode(digest(%s, 'sha256'), 'hex') AS tenant_hash",
        (str(tenant_id),),
    )
    row = cursor.fetchone()
    assert row is not None
    return str(row["tenant_hash"])


def _seed_workspace(dsn: str, tenant_id: UUID, suffix: str) -> UUID:
    run_id = uuid4()
    dossier_id = uuid4()
    with psycopg.connect(dsn, row_factory=dict_row) as connection, connection.cursor() as cursor:
        _set_role(cursor, "axignal_app")
        _set_tenant(cursor, tenant_id)
        cursor.execute(
            """
            INSERT INTO tenant_private.research_runs (
              research_run_id, tenant_id, context_id, opportunity_id, question,
              state, private_knowledge_authorised, source_plan, budgets
            ) VALUES (%s, %s, %s, %s, %s, 'COMPLETED', false, %s, %s)
            """,
            (
                run_id,
                tenant_id,
                f"ctx_retention_{suffix}",
                f"opp_retention_{suffix}",
                "Verify terminal deletion without cross-tenant residue.",
                Jsonb([{"source_id": "src_ted_search_api_v3"}]),
                Jsonb({"max_model_calls": 0}),
            ),
        )
        cursor.execute(
            """
            INSERT INTO tenant_private.dossiers (
              dossier_id, tenant_id, research_run_id, status, title, summary,
              sections, attribution
            ) VALUES (%s, %s, %s, 'TRACEABLE_WITH_ADMITTED_FACTS', %s, %s, %s, %s)
            """,
            (
                dossier_id,
                tenant_id,
                run_id,
                f"Retention dossier {suffix}",
                "Tenant-private deletion fixture.",
                Jsonb([{"kind": "FACT", "value": suffix}]),
                Jsonb({"source": "TED", "synthetic": True}),
            ),
        )
        cursor.execute(
            "UPDATE tenant_private.research_runs SET dossier_id = %s WHERE research_run_id = %s",
            (dossier_id, run_id),
        )
        cursor.execute(
            """
            INSERT INTO tenant_private.knowledge_items (
              tenant_id, item_type, title, body, source_metadata, content_hash
            ) VALUES (%s, 'NOTE', %s, %s, '{}'::jsonb, %s)
            """,
            (
                tenant_id,
                f"Private note {suffix}",
                f"private-body-{suffix}",
                f"sha256:{suffix * 64}"[:71],
            ),
        )
        cursor.execute(
            """
            INSERT INTO intent_intelligence.intent_events (
              tenant_id, event_type, subject_key, payload, occurred_at, expires_at
            ) VALUES (%s, 'RETENTION_E2E', %s, %s, %s, %s)
            """,
            (
                tenant_id,
                f"subject-{suffix}",
                Jsonb({"private": suffix}),
                START,
                START + timedelta(days=30),
            ),
        )
    return run_id


def _expect_database_error(function, marker: str) -> str:
    try:
        function()
    except psycopg.Error as exc:
        message = str(exc)
        if marker not in message:
            raise AssertionError(f"Expected {marker!r}, received {message!r}") from exc
        return marker
    raise AssertionError(f"Expected PostgreSQL error containing {marker!r}")


def _attempt_new_run(dsn: str, tenant_id: UUID) -> None:
    with psycopg.connect(dsn, row_factory=dict_row) as connection, connection.cursor() as cursor:
        _set_role(cursor, "axignal_app")
        _set_tenant(cursor, tenant_id)
        cursor.execute(
            """
            INSERT INTO tenant_private.research_runs (
              tenant_id, context_id, opportunity_id, question, state,
              private_knowledge_authorised, source_plan, budgets
            ) VALUES (%s, 'ctx_blocked', 'opp_blocked', 'blocked', 'QUEUED', false, '[]'::jsonb, '{}'::jsonb)
            """,
            (tenant_id,),
        )


def _direct_app_lifecycle_mutation(dsn: str, tenant_id: UUID) -> None:
    with psycopg.connect(dsn, row_factory=dict_row) as connection, connection.cursor() as cursor:
        _set_role(cursor, "axignal_app")
        _set_tenant(cursor, tenant_id)
        cursor.execute(
            "UPDATE tenant_private.workspace_lifecycle SET state = 'ACTIVE' WHERE tenant_id = %s",
            (tenant_id,),
        )


def _app_attempts_purge(dsn: str, deletion_id: UUID) -> None:
    with psycopg.connect(dsn, row_factory=dict_row) as connection, connection.cursor() as cursor:
        _set_role(cursor, "axignal_app")
        _set_tenant(cursor, TENANT_A)
        cursor.execute(
            "SELECT * FROM tenant_private.purge_claimed_workspace(%s, 'forged-app-worker', %s)",
            (deletion_id, START + timedelta(days=8, seconds=5)),
        )


def _counts(dsn: str, tenant_id: UUID) -> dict[str, int]:
    queries = {
        "research_runs": "tenant_private.research_runs",
        "dossiers": "tenant_private.dossiers",
        "knowledge_items": "tenant_private.knowledge_items",
        "intent_events": "intent_intelligence.intent_events",
        "human_review_cases": "tenant_private.human_review_cases",
        "human_review_events": "tenant_private.human_review_events",
        "entitlements": "tenant_private.organisation_entitlements",
        "reservations": "tenant_private.ai_token_reservations",
        "entitlement_events": "tenant_private.entitlement_events",
        "lifecycle": "tenant_private.workspace_lifecycle",
        "lifecycle_events": "tenant_private.workspace_lifecycle_events",
        "scheduled_jobs": "axignal_global.scheduled_jobs",
    }
    result: dict[str, int] = {}
    with psycopg.connect(dsn, row_factory=dict_row) as connection, connection.cursor() as cursor:
        for name, table in queries.items():
            cursor.execute(
                sql.SQL("SELECT count(*) AS count FROM {} WHERE tenant_id = %s").format(
                    sql.SQL(table)
                ),
                (tenant_id,),
            )
            row = cursor.fetchone()
            result[name] = int(row["count"] if row is not None else -1)
    return result


def _simulate_restore_residue(dsn: str, tenant_id: UUID) -> None:
    run_id = uuid4()
    with psycopg.connect(dsn, row_factory=dict_row) as connection, connection.cursor() as cursor:
        cursor.execute("ALTER TABLE tenant_private.research_runs DISABLE TRIGGER USER")
        cursor.execute(
            """
            INSERT INTO tenant_private.research_runs (
              research_run_id, tenant_id, context_id, opportunity_id, question,
              state, private_knowledge_authorised, source_plan, budgets
            ) VALUES (%s, %s, 'ctx_restored', 'opp_restored', 'restored residue',
              'FAILED', false, '[]'::jsonb, '{}'::jsonb)
            """,
            (run_id, tenant_id),
        )
        cursor.execute("ALTER TABLE tenant_private.research_runs ENABLE TRIGGER USER")
        cursor.execute(
            """
            INSERT INTO tenant_private.knowledge_items (
              tenant_id, item_type, title, body, source_metadata, content_hash
            ) VALUES (%s, 'NOTE', 'Restored residue', 'must be repurged', '{}'::jsonb, %s)
            """,
            (tenant_id, "sha256:" + "f" * 64),
        )


def run(dsn: str) -> dict[str, object]:
    _clean(dsn, (TENANT_A, TENANT_B))
    entitlement = EntitlementRepository(dsn)
    retention = RetentionRepository(dsn)

    entitlement.activate_trial(
        tenant_id=TENANT_A,
        actor_subject="usr_retention_a",
        now=START,
    )
    entitlement.activate_trial(
        tenant_id=TENANT_B,
        actor_subject="usr_retention_b",
        now=START,
    )
    run_a = _seed_workspace(dsn, TENANT_A, "a")
    run_b = _seed_workspace(dsn, TENANT_B, "b")
    reservation = entitlement.reserve(
        tenant_id=TENANT_A,
        operation_id="op_retention_reserved_tokens",
        capability="READ_RESEARCH_RUN_PROGRESS",
        requested_tokens=100_000,
        actor_subject="usr_retention_a",
        now=START + timedelta(minutes=1),
    )

    expired = entitlement.expire_trial(
        tenant_id=TENANT_A,
        actor_subject="retention-expiry-sweep",
        now=START + timedelta(days=8),
    )
    if expired["state"] != "READ_ONLY":
        raise AssertionError("Trial expiry did not persist READ_ONLY")
    lifecycle = retention.lifecycle(tenant_id=TENANT_A)
    if lifecycle is None or lifecycle["state"] != "READ_ONLY":
        raise AssertionError("Workspace lifecycle did not mirror READ_ONLY")

    requested = retention.request_deletion(
        tenant_id=TENANT_A,
        actor_subject="usr_retention_a",
        retention_seconds=1,
        now=START + timedelta(days=8, seconds=1),
    )
    replayed = retention.request_deletion(
        tenant_id=TENANT_A,
        actor_subject="usr_retention_a",
        retention_seconds=1,
        now=START + timedelta(days=8, seconds=1),
    )
    if requested["deletion_id"] != replayed["deletion_id"]:
        raise AssertionError("Deletion request replay changed deletion_id")
    if requested["state"] != "DELETION_REQUESTED":
        raise AssertionError("Deletion request did not enter DELETION_REQUESTED")

    _expect_database_error(
        lambda: _attempt_new_run(dsn, TENANT_A),
        "workspace_not_operational:DELETION_REQUESTED",
    )
    _expect_database_error(
        lambda: _direct_app_lifecycle_mutation(dsn, TENANT_A),
        "permission denied",
    )
    _expect_database_error(
        lambda: _app_attempts_purge(dsn, requested["deletion_id"]),
        "permission denied",
    )

    queued = retention.queue_due(now=START + timedelta(days=8, seconds=3))
    if queued != 1:
        raise AssertionError(f"Expected one queued purge, received {queued}")
    claim = retention.claim(
        worker_id="retention-e2e-worker",
        lease_seconds=60,
        now=START + timedelta(days=8, seconds=3),
    )
    if claim is None or claim["deletion_id"] != requested["deletion_id"]:
        raise AssertionError("Retention worker did not claim the requested deletion")
    tombstone = retention.purge(
        deletion_id=claim["deletion_id"],
        worker_id="retention-e2e-worker",
        now=START + timedelta(days=8, seconds=4),
    )

    tenant_a_counts = _counts(dsn, TENANT_A)
    if any(tenant_a_counts.values()):
        raise AssertionError(f"Deletion residue detected: {tenant_a_counts}")
    tenant_b_counts_before_suspension = _counts(dsn, TENANT_B)
    if tenant_b_counts_before_suspension["research_runs"] != 1:
        raise AssertionError("Cross-tenant research data was modified")
    if tenant_b_counts_before_suspension["dossiers"] != 1:
        raise AssertionError("Cross-tenant dossier was modified")

    _expect_database_error(
        lambda: entitlement.activate_trial(
            tenant_id=TENANT_A,
            actor_subject="usr_retention_a",
            now=START + timedelta(days=9),
        ),
        "workspace_terminally_deleted",
    )

    _simulate_restore_residue(dsn, TENANT_A)
    restored_counts = _counts(dsn, TENANT_A)
    if restored_counts["research_runs"] != 1 or restored_counts["knowledge_items"] != 1:
        raise AssertionError("Restore simulation did not recreate residue")
    reapplication = retention.reapply_tombstone(
        tenant_id=TENANT_A,
        now=START + timedelta(days=9, seconds=1),
    )
    post_restore_counts = _counts(dsn, TENANT_A)
    if any(post_restore_counts.values()):
        raise AssertionError(f"Tombstone reapplication left residue: {post_restore_counts}")

    suspended = retention.suspend(
        tenant_id=TENANT_B,
        reason_code="E2E_OPERATOR_SUSPENSION",
        actor_subject="operator_retention_e2e",
        now=START + timedelta(days=1),
    )
    if suspended["state"] != "SUSPENDED":
        raise AssertionError("Operator suspension did not persist SUSPENDED")
    _expect_database_error(
        lambda: _attempt_new_run(dsn, TENANT_B),
        "workspace_not_operational:SUSPENDED",
    )

    if str(reservation["state"]) != "RESERVED":
        raise AssertionError("Pre-deletion reservation fixture was not created")
    if not str(tombstone["tenant_hash"]).startswith("sha256:"):
        raise AssertionError("Tombstone did not use an irreversible tenant hash")
    if not str(tombstone["verification_digest"]).startswith("sha256:"):
        raise AssertionError("Tombstone verification digest is missing")

    return {
        "schema": "axignal.trial-retention-e2e.v0.1",
        "status": "PASS",
        "tenant_a_run_id": str(run_a),
        "tenant_b_run_id": str(run_b),
        "expired_state": "READ_ONLY",
        "deletion_request_replay": "IDEMPOTENT",
        "deletion_id": str(tombstone["deletion_id"]),
        "tenant_hash_pseudonymous": True,
        "tenant_a_post_purge_counts": tenant_a_counts,
        "tenant_b_preserved_before_suspension": tenant_b_counts_before_suspension,
        "direct_app_lifecycle_mutation": "BLOCKED",
        "direct_app_purge_execution": "BLOCKED",
        "new_execution_after_deletion_request": "BLOCKED",
        "terminal_reactivation": "BLOCKED",
        "restore_residue_created": restored_counts,
        "restore_tombstone_reapplication": reapplication,
        "post_restore_counts": post_restore_counts,
        "operator_suspension": "PASS",
        "model_calls": 0,
        "stripe_calls": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/trial-retention-e2e.json"),
    )
    args = parser.parse_args()
    dsn = os.environ.get("AXIGNAL_DATABASE_URL")
    if not dsn:
        raise SystemExit("AXIGNAL_DATABASE_URL is required")
    result = run(dsn)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
