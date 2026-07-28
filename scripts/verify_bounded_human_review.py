from __future__ import annotations

import json
from uuid import UUID

import psycopg
from fastapi.testclient import TestClient
from psycopg.errors import InsufficientPrivilege, RaiseException
from psycopg.rows import dict_row
from redis import Redis

from axignal_api.admission_queue import AdmissionOutboxPublisher, ValkeyAdmissionQueue
from axignal_api.admission_repository import AdmissionRepository
from axignal_api.admission_runtime import build_runtime as build_admission_runtime
from axignal_api.application import app
from axignal_api.identity import build_identity_assertion
from axignal_api.proposal_worker import build_runtime as build_proposal_runtime
from axignal_api.settings import Settings

TENANT = UUID("77777777-7777-4777-8777-777777777777")
OTHER_TENANT = UUID("88888888-8888-4888-8888-888888888888")
REVIEWER_SUBJECT = "usr_human_review_ci"
REVIEWER_EMAIL = "human-review-ci@example.test"
IDENTITY_SECRET = "ci-identity-assertion-secret-with-at-least-32-bytes"


def identity_headers(
    tenant_id: UUID,
    subject: str = REVIEWER_SUBJECT,
) -> dict[str, str]:
    return {
        "X-AXIGNAL-Identity-Assertion": build_identity_assertion(
            secret=IDENTITY_SECRET,
            subject=subject,
            email=REVIEWER_EMAIL,
            tenant_id=tenant_id,
        )
    }


def clear_runtime_state(settings: Settings) -> None:
    assert settings.valkey_url is not None
    Redis.from_url(settings.valkey_url).flushdb()
    assert settings.database_url is not None
    with psycopg.connect(settings.database_url) as connection, connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE axignal_global.proposal_outbox_events
            SET status = 'PUBLISHED', published_at = now()
            WHERE status = 'PENDING'
            """
        )
        cursor.execute(
            """
            UPDATE axignal_global.admission_outbox_events
            SET status = 'PUBLISHED', published_at = now()
            WHERE status = 'PENDING'
            """
        )


def create_reviewable_run(client: TestClient, settings: Settings) -> UUID:
    response = client.post(
        "/v1/research-runs/document-proposals",
        headers=identity_headers(TENANT),
        json={
            "context_id": "ctx_moscow_real_estate_v01",
            "opportunity_id": "opp_moscow_ramenki",
            "question": (
                "Extrae hechos económicos explícitos y límites de aplicabilidad del informe."
            ),
        },
    )
    assert response.status_code == 202, response.text
    run_id = UUID(response.json()["research_run_id"])

    proposal_runtime = build_proposal_runtime(settings)
    assert proposal_runtime.run_once(timeout_seconds=1) is True

    assert settings.database_url is not None
    assert settings.admission_database_url is not None
    assert settings.valkey_url is not None
    admission_repository = AdmissionRepository(
        app_dsn=settings.database_url,
        admission_dsn=settings.admission_database_url,
    )
    admission_queue = ValkeyAdmissionQueue(
        settings.valkey_url,
        queue_key=settings.admission_queue_key,
    )
    publisher = AdmissionOutboxPublisher(admission_repository, admission_queue)
    assert publisher.publish_pending(limit=100) >= 1
    admission_runtime = build_admission_runtime(settings)
    assert admission_runtime.run_once(timeout_seconds=1) is True
    return run_id


def list_cases(client: TestClient, run_id: UUID, tenant_id: UUID = TENANT) -> list[dict]:
    response = client.get(
        f"/v1/human-review-cases?research_run_id={run_id}",
        headers=identity_headers(tenant_id),
    )
    assert response.status_code == 200, response.text
    return response.json()["cases"]


def database_counts(dsn: str, run_id: UUID) -> dict[str, int]:
    with (
        psycopg.connect(dsn, row_factory=dict_row) as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute(
            """
            SELECT
              (
                SELECT count(*)
                FROM tenant_private.human_review_cases
                WHERE research_run_id = %s
              ) AS cases,
              (
                SELECT count(*)
                FROM tenant_private.human_review_events AS event
                JOIN tenant_private.human_review_cases AS review_case
                  USING (human_review_case_id)
                WHERE review_case.research_run_id = %s
              ) AS events,
              (
                SELECT cardinality(canonical_claim_ids)
                FROM tenant_private.research_runs
                WHERE research_run_id = %s
              ) AS canonical_claims,
              (
                SELECT jsonb_array_length(human_review_context)
                FROM tenant_private.dossiers
                WHERE research_run_id = %s
              ) AS dossier_context
            """,
            (run_id, run_id, run_id, run_id),
        )
        row = cursor.fetchone()
        assert row is not None
        return {key: int(value or 0) for key, value in row.items()}


def verify_reviewer_authority(admin_dsn: str, reviewer_dsn: str) -> None:
    with (
        psycopg.connect(admin_dsn, row_factory=dict_row) as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute(
            """
            SELECT
              has_table_privilege(
                'axignal_human_reviewer_login',
                'axignal_global.canonical_claims',
                'INSERT'
              ) AS canonical_insert,
              has_table_privilege(
                'axignal_human_reviewer_login',
                'axignal_global.evidence_objects',
                'UPDATE'
              ) AS evidence_update,
              has_table_privilege(
                'axignal_human_reviewer_login',
                'axignal_global.admission_decisions',
                'UPDATE'
              ) AS decision_update,
              has_function_privilege(
                'axignal_human_reviewer_login',
                'tenant_private.resolve_human_review_case(uuid,text,text,text,text,text)',
                'EXECUTE'
              ) AS review_execute
            """
        )
        assert cursor.fetchone() == {
            "canonical_insert": False,
            "evidence_update": False,
            "decision_update": False,
            "review_execute": True,
        }

    forbidden_statements = (
        "INSERT INTO axignal_global.canonical_claims DEFAULT VALUES",
        "UPDATE axignal_global.evidence_objects SET title = title WHERE false",
        "UPDATE axignal_global.admission_decisions SET outcome = outcome WHERE false",
    )
    for statement in forbidden_statements:
        with psycopg.connect(reviewer_dsn) as connection, connection.cursor() as cursor:
            try:
                cursor.execute(statement)
            except InsufficientPrivilege:
                connection.rollback()
            else:
                raise AssertionError(f"Reviewer credential unexpectedly executed: {statement}")


def verify_append_only(admin_dsn: str, case_id: UUID) -> None:
    with psycopg.connect(admin_dsn) as connection, connection.cursor() as cursor:
        try:
            cursor.execute(
                """
                UPDATE tenant_private.human_review_events
                SET reason_code = reason_code
                WHERE human_review_case_id = %s
                """,
                (case_id,),
            )
        except RaiseException as exc:
            assert "AXIGNAL_HUMAN_REVIEW_EVENTS_APPEND_ONLY" in str(exc)
            connection.rollback()
        else:
            raise AssertionError("Human-review events were mutable")


def verify_atomic_failpoint(
    admin_dsn: str,
    reviewer_dsn: str,
    client: TestClient,
    settings: Settings,
) -> None:
    run_id = create_reviewable_run(client, settings)
    review_case = list_cases(client, run_id)[0]
    case_id = UUID(review_case["human_review_case_id"])
    with psycopg.connect(reviewer_dsn) as connection, connection.cursor() as cursor:
        cursor.execute(
            "SELECT set_config('app.tenant_id', %s, false)",
            (str(TENANT),),
        )
        cursor.execute(
            "SELECT set_config('axignal.test_fail_after_case_update', 'on', false)"
        )
        try:
            cursor.execute(
                """
                SELECT tenant_private.resolve_human_review_case(
                  %s, %s, %s, 'REJECT_PROPOSAL', 'TEST_ROLLBACK', NULL
                )
                """,
                (case_id, REVIEWER_SUBJECT, REVIEWER_EMAIL),
            )
        except RaiseException as exc:
            assert "TEST_FAILPOINT_AFTER_HUMAN_REVIEW_CASE_UPDATE" in str(exc)
            connection.rollback()
        else:
            raise AssertionError("Human-review failpoint did not abort the transaction")

    with (
        psycopg.connect(admin_dsn, row_factory=dict_row) as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute(
            """
            SELECT state, resolution,
              (SELECT count(*) FROM tenant_private.human_review_events
               WHERE human_review_case_id = %s) AS events
            FROM tenant_private.human_review_cases
            WHERE human_review_case_id = %s
            """,
            (case_id, case_id),
        )
        assert cursor.fetchone() == {
            "state": "OPEN",
            "resolution": None,
            "events": 1,
        }


def main() -> int:
    settings = Settings.from_env()
    settings.require_persistent_research()
    settings.require_document_proposal_worker()
    settings.require_admission_runtime()
    settings.require_human_review()
    assert settings.database_url is not None
    assert settings.human_review_database_url is not None

    clear_runtime_state(settings)
    verify_reviewer_authority(
        settings.database_url,
        settings.human_review_database_url,
    )
    client = TestClient(app)

    run_id = create_reviewable_run(client, settings)
    run_response = client.get(
        f"/v1/research-runs/{run_id}",
        headers=identity_headers(TENANT),
    )
    assert run_response.status_code == 200, run_response.text
    run_view = run_response.json()
    states = {item["kind"]: item["state"] for item in run_view["candidate_claims"]}
    assert states == {"FACT": "ADMITTED", "LIMITATION": "HUMAN_REVIEW_REQUIRED"}

    cases = list_cases(client, run_id)
    assert len(cases) == 1
    review_case = cases[0]
    assert review_case["case_type"] == "HUMAN_REVIEW_REQUIRED"
    assert review_case["state"] == "OPEN"
    assert review_case["deterministic_decision"]["outcome"] == "HUMAN_REVIEW_REQUIRED"
    assert review_case["candidate_claim"]["producer_type"] == "LOCAL_MODEL"
    assert review_case["candidate_claim"]["canonical_claim_id"] is None
    case_id = UUID(review_case["human_review_case_id"])

    before = database_counts(settings.database_url, run_id)
    assert before == {
        "cases": 1,
        "events": 1,
        "canonical_claims": 1,
        "dossier_context": 0,
    }

    action_payload = {
        "action": "ACCEPT_AS_CONTEXT",
        "reason_code": "LIMITATION_CONFIRMED",
        "note": "The national report is valid context but not local-market evidence.",
    }
    resolved_response = client.post(
        f"/v1/human-review-cases/{case_id}/actions",
        headers=identity_headers(TENANT),
        json=action_payload,
    )
    assert resolved_response.status_code == 200, resolved_response.text
    resolved = resolved_response.json()
    assert resolved["state"] == "RESOLVED"
    assert resolved["resolution"] == "ACCEPT_AS_CONTEXT"
    assert resolved["assigned_reviewer_subject"] == REVIEWER_SUBJECT
    assert len(resolved["events"]) == 5
    assert resolved["candidate_claim"]["canonical_claim_id"] is None

    after = database_counts(settings.database_url, run_id)
    assert after == {
        "cases": 1,
        "events": 5,
        "canonical_claims": 1,
        "dossier_context": 1,
    }

    replay_response = client.post(
        f"/v1/human-review-cases/{case_id}/actions",
        headers=identity_headers(TENANT),
        json=action_payload,
    )
    assert replay_response.status_code == 200, replay_response.text
    assert database_counts(settings.database_url, run_id) == after

    cross_tenant = list_cases(client, run_id, OTHER_TENANT)
    assert cross_tenant == []
    denied = client.get(
        f"/v1/human-review-cases?research_run_id={run_id}",
        headers=identity_headers(TENANT, subject="usr_not_a_reviewer"),
    )
    assert denied.status_code == 403
    verify_append_only(settings.database_url, case_id)

    blocked_run = create_reviewable_run(client, settings)
    blocked_case = list_cases(client, blocked_run)[0]
    with psycopg.connect(settings.database_url) as connection, connection.cursor() as cursor:
        cursor.execute(
            "UPDATE axignal_global.sources SET kill_switch = true "
            "WHERE source_id = 'world-bank-rer41'"
        )
    blocked_response = client.post(
        f"/v1/human-review-cases/{blocked_case['human_review_case_id']}/actions",
        headers=identity_headers(TENANT),
        json=action_payload,
    )
    assert blocked_response.status_code == 409, blocked_response.text
    with psycopg.connect(settings.database_url) as connection, connection.cursor() as cursor:
        cursor.execute(
            "UPDATE axignal_global.sources SET kill_switch = false "
            "WHERE source_id = 'world-bank-rer41'"
        )

    verify_atomic_failpoint(
        settings.database_url,
        settings.human_review_database_url,
        client,
        settings,
    )

    output = {
        "research_run_id": str(run_id),
        "human_review_cases": after["cases"],
        "review_events": after["events"],
        "accepted_as_context": after["dossier_context"],
        "canonical_claims_created_by_reviewer": 0,
        "deterministic_decisions_modified": 0,
        "evidence_objects_modified": 0,
        "reviewer_identity_recorded": True,
        "append_only_history": True,
        "idempotent_replay": True,
        "cross_tenant_access": "DENIED",
        "kill_switch_bypass": "BLOCKED",
        "partial_transactions": 0,
    }
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
