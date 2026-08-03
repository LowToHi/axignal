from __future__ import annotations

import argparse
import hashlib
import json
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

import psycopg
from psycopg.rows import dict_row

EXPECTED_SOURCE = "src_ted_search_api_v3"
REQUIRED_AUDIT_EVENTS = {
    "WORKSPACE_CREATED",
    "DOCUMENT_CREATED",
    "EXPORT_CREATED",
}


def _one(
    cursor: psycopg.Cursor[dict[str, Any]],
    query: str,
    params: tuple[Any, ...],
) -> dict[str, Any]:
    cursor.execute(query, params)
    row = cursor.fetchone()
    if row is None:
        raise AssertionError(
            f"Required row missing for query: {query.strip()[:100]}"
        )
    return row


def verify(*, dsn: str, subject: str) -> dict[str, Any]:
    with (
        psycopg.connect(dsn, row_factory=dict_row) as connection,
        connection.cursor() as cursor,
    ):
        identity = _one(
            cursor,
            """
            SELECT u.user_id, u.subject, u.email_normalized, uo.tenant_id
            FROM identity_private.users u
            JOIN identity_private.user_organisations uo ON uo.user_id = u.user_id
            WHERE u.subject = %s AND u.status = 'ACTIVE' AND uo.state = 'ACTIVE'
            ORDER BY (uo.relationship = 'OWNER') DESC, uo.created_at
            LIMIT 1
            """,
            (subject,),
        )
        tenant_id = UUID(str(identity["tenant_id"]))

        session = _one(
            cursor,
            """
            SELECT session_id, auth_method, assurance_level, state,
                   idle_expires_at, absolute_expires_at
            FROM identity_private.identity_sessions
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (identity["user_id"],),
        )
        assert session["state"] == "ACTIVE", session
        assert session["auth_method"] == "PASSKEY", session
        assert session["assurance_level"] == "AAL2", session
        cursor.execute(
            """
            SELECT to_regprocedure(
              'identity_private.revoke_identity_session(text,text,timestamptz)'
            ) AS fn
            """
        )
        assert cursor.fetchone()["fn"] is not None

        selection = _one(
            cursor,
            """
            SELECT plan_code, state, selected_by
            FROM tenant_private.billing_plan_selections
            WHERE tenant_id = %s
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (tenant_id,),
        )
        assert selection["plan_code"] == "PROFESSIONAL_MONTHLY", selection
        assert selection["state"] == "ACTIVE", selection
        assert selection["selected_by"] == subject, selection

        entitlement = _one(
            cursor,
            """
            SELECT entitlement_kind, plan_code, state
            FROM tenant_private.organisation_entitlements
            WHERE tenant_id = %s
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (tenant_id,),
        )
        assert entitlement == {
            "entitlement_kind": "PAID_MONTHLY",
            "plan_code": "PROFESSIONAL_MONTHLY",
            "state": "ACTIVE",
        }, entitlement

        seat = _one(
            cursor,
            """
            SELECT plan_code, state, seat_capacity
            FROM tenant_private.organisation_seat_entitlements
            WHERE tenant_id = %s
            """,
            (tenant_id,),
        )
        assert seat == {
            "plan_code": "PROFESSIONAL_MONTHLY",
            "state": "ACTIVE",
            "seat_capacity": 3,
        }, seat

        membership = _one(
            cursor,
            """
            SELECT m.membership_id, m.status,
                   array_agg(rb.role_id ORDER BY rb.role_id)
                     FILTER (WHERE rb.state = 'ACTIVE') AS roles
            FROM tenant_private.organisation_memberships m
            LEFT JOIN tenant_private.membership_role_bindings rb
              ON rb.tenant_id = m.tenant_id AND rb.membership_id = m.membership_id
            WHERE m.tenant_id = %s AND m.principal_id = %s
            GROUP BY m.membership_id
            """,
            (tenant_id, subject),
        )
        assert membership["status"] == "ACTIVE", membership
        assert "ORG_OWNER" in (membership["roles"] or []), membership

        run = _one(
            cursor,
            """
            SELECT research_run_id, context_id, opportunity_id, question, state,
                   source_plan, actual_usage, evidence_ids, candidate_claim_ids,
                   canonical_claim_ids, dossier_id, admission_batch_id
            FROM tenant_private.research_runs
            WHERE tenant_id = %s
              AND state IN ('COMPLETED', 'COMPLETED_PROVISIONAL')
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (tenant_id,),
        )
        assert run["dossier_id"] is not None, run
        assert run["admission_batch_id"] is not None, run
        assert len(run["evidence_ids"] or []) > 0, run
        assert len(run["candidate_claim_ids"] or []) > 0, run
        assert len(run["canonical_claim_ids"] or []) > 0, run
        assert len(run["candidate_claim_ids"]) == len(
            run["canonical_claim_ids"]
        ), run
        assert run["actual_usage"]["api_requests"] == 1, run
        assert run["actual_usage"]["model_calls"] == 0, run
        assert any(
            isinstance(item, dict) and item.get("source_id") == EXPECTED_SOURCE
            for item in run["source_plan"]
        ), run

        cursor.execute(
            """
            SELECT count(*) AS count
            FROM axignal_global.evidence_objects
            WHERE evidence_id = ANY(%s) AND source_id = %s
            """,
            (run["evidence_ids"], EXPECTED_SOURCE),
        )
        assert cursor.fetchone()["count"] == len(run["evidence_ids"])

        cursor.execute(
            """
            SELECT count(*) AS count
            FROM axignal_global.candidate_claims
            WHERE candidate_claim_id = ANY(%s) AND state = 'ADMITTED'
            """,
            (run["candidate_claim_ids"],),
        )
        assert cursor.fetchone()["count"] == len(run["candidate_claim_ids"])
        cursor.execute(
            """
            SELECT count(*) AS count
            FROM axignal_global.canonical_claims
            WHERE canonical_claim_id = ANY(%s) AND state = 'ADMITTED'
            """,
            (run["canonical_claim_ids"],),
        )
        assert cursor.fetchone()["count"] == len(run["canonical_claim_ids"])

        dossier = _one(
            cursor,
            """
            SELECT dossier_id, status, title, summary, sections, attribution
            FROM tenant_private.dossiers
            WHERE tenant_id = %s AND dossier_id = %s
            """,
            (tenant_id, run["dossier_id"]),
        )
        assert dossier["status"] == "TRACEABLE_WITH_ADMITTED_FACTS", dossier
        assert dossier["sections"], dossier
        assert dossier["attribution"]["source_id"] == EXPECTED_SOURCE, dossier

        workspace = _one(
            cursor,
            """
            SELECT workspace_id, research_run_id, owner_subject, state, revision
            FROM tenant_private.subscriber_workspaces
            WHERE tenant_id = %s
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (tenant_id,),
        )
        assert workspace["research_run_id"] == run["research_run_id"], workspace
        assert workspace["owner_subject"] == subject, workspace
        assert workspace["state"] == "ACTIVE", workspace

        document = _one(
            cursor,
            """
            SELECT document_id, workspace_id, title, body, version, status,
                   created_by, updated_by
            FROM tenant_private.subscriber_workspace_documents
            WHERE tenant_id = %s AND workspace_id = %s
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (tenant_id, workspace["workspace_id"]),
        )
        assert document["title"] == "Pursuit note", document
        assert document["version"] == 1, document
        assert document["created_by"] == subject == document["updated_by"], document

        export = _one(
            cursor,
            """
            SELECT export_id, workspace_id, document_id, format, filename,
                   content, content_hash, created_by
            FROM tenant_private.subscriber_workspace_exports
            WHERE tenant_id = %s AND workspace_id = %s
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (tenant_id, workspace["workspace_id"]),
        )
        assert export["document_id"] == document["document_id"], export
        assert export["format"] == "MARKDOWN", export
        assert export["created_by"] == subject, export
        digest = hashlib.sha256(export["content"].encode("utf-8")).hexdigest()
        expected_hash = f"sha256:{digest}"
        assert export["content_hash"] == expected_hash, export
        assert "Pursuit note" in export["content"], export
        assert EXPECTED_SOURCE in export["content"], export

        cursor.execute(
            """
            SELECT event_type
            FROM tenant_private.subscriber_workspace_audit_events
            WHERE tenant_id = %s AND workspace_id = %s
            """,
            (tenant_id, workspace["workspace_id"]),
        )
        audit_events = {row["event_type"] for row in cursor.fetchall()}
        assert REQUIRED_AUDIT_EVENTS.issubset(audit_events), audit_events

        cursor.execute(
            """
            SELECT count(*) AS count
            FROM tenant_private.subscriber_workspaces w
            LEFT JOIN tenant_private.subscriber_workspace_documents d
              ON d.tenant_id = w.tenant_id AND d.workspace_id = w.workspace_id
            LEFT JOIN tenant_private.subscriber_workspace_exports e
              ON e.tenant_id = w.tenant_id AND e.workspace_id = w.workspace_id
            WHERE w.tenant_id = %s
              AND (
                w.title ILIKE '%%axfx_%%'
                OR coalesce(d.title, '') ILIKE '%%axfx_%%'
                OR coalesce(d.body, '') ILIKE '%%axfx_%%'
                OR coalesce(e.content, '') ILIKE '%%axfx_%%'
              )
            """,
            (tenant_id,),
        )
        assert cursor.fetchone()["count"] == 0

        other_tenant = uuid5(NAMESPACE_URL, f"axignal-e2e-2:{tenant_id}")
        if other_tenant == tenant_id:
            raise AssertionError("Deterministic foreign tenant collided")
        with connection.transaction():
            cursor.execute("SET LOCAL ROLE axignal_app")
            cursor.execute(
                "SELECT set_config('app.tenant_id', %s, true)",
                (str(other_tenant),),
            )
            for table in (
                "subscriber_workspaces",
                "subscriber_workspace_documents",
                "subscriber_workspace_exports",
                "subscriber_workspace_audit_events",
            ):
                cursor.execute(
                    f"SELECT count(*) AS count FROM tenant_private.{table}"
                )
                assert cursor.fetchone()["count"] == 0, table

        audit_immutable = False
        with connection.transaction():
            cursor.execute("SET LOCAL ROLE axignal_app")
            cursor.execute(
                "SELECT set_config('app.tenant_id', %s, true)",
                (str(tenant_id),),
            )
            cursor.execute("SAVEPOINT audit_mutation_probe")
            try:
                cursor.execute(
                    """
                    UPDATE tenant_private.subscriber_workspace_audit_events
                    SET event_type = 'WORKSPACE_OPENED'
                    WHERE audit_event_id = (
                      SELECT audit_event_id
                      FROM tenant_private.subscriber_workspace_audit_events
                      WHERE tenant_id = %s
                      LIMIT 1
                    )
                    """,
                    (tenant_id,),
                )
            except psycopg.Error as exc:
                audit_immutable = (
                    exc.sqlstate == "42501"
                    or "append-only" in str(exc).lower()
                )
                cursor.execute("ROLLBACK TO SAVEPOINT audit_mutation_probe")
                if not audit_immutable:
                    raise AssertionError(
                        "Subscriber audit mutation failed for an unexpected reason"
                    ) from exc
            else:
                raise AssertionError(
                    "Subscriber audit mutation unexpectedly succeeded"
                )
        assert audit_immutable

    return {
        "status": "PASS",
        "subject": subject,
        "tenant_id": str(tenant_id),
        "session_id": str(session["session_id"]),
        "research_run_id": str(run["research_run_id"]),
        "dossier_id": str(dossier["dossier_id"]),
        "workspace_id": str(workspace["workspace_id"]),
        "document_id": str(document["document_id"]),
        "export_id": str(export["export_id"]),
        "export_hash": export["content_hash"],
        "evidence_count": len(run["evidence_ids"]),
        "candidate_claim_count": len(run["candidate_claim_ids"]),
        "canonical_claim_count": len(run["canonical_claim_ids"]),
        "audit_events": sorted(audit_events),
        "cross_tenant_visible_rows": 0,
        "fixture_identifiers": 0,
        "audit_append_only": True,
        "session_revocation_function": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dsn", required=True)
    parser.add_argument("--subject", required=True)
    args = parser.parse_args()
    result = verify(dsn=args.dsn, subject=args.subject)
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    print("AX_E2E_HAPPY_PATH_NO_FIXTURES_PASS")


if __name__ == "__main__":
    main()
