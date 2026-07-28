from __future__ import annotations

import json
from uuid import UUID

import psycopg
from fastapi.testclient import TestClient
from psycopg.errors import InsufficientPrivilege
from psycopg.rows import dict_row

from axignal_api.admission_queue import (
    AdmissionOutboxPublisher,
    AdmissionReviewJob,
    ValkeyAdmissionQueue,
)
from axignal_api.admission_repository import AdmissionRepository
from axignal_api.admission_runtime import build_runtime as build_admission_runtime
from axignal_api.application import app
from axignal_api.identity import build_identity_assertion
from axignal_api.proposal_worker import build_runtime as build_proposal_runtime
from axignal_api.settings import Settings

TENANT = UUID("55555555-5555-4555-8555-555555555555")
OTHER_TENANT = UUID("66666666-6666-4666-8666-666666666666")
IDENTITY_SECRET = "ci-identity-assertion-secret-with-at-least-32-bytes"


def identity_headers(tenant_id: UUID) -> dict[str, str]:
    return {
        "X-AXIGNAL-Identity-Assertion": build_identity_assertion(
            secret=IDENTITY_SECRET,
            subject=f"usr_{tenant_id.hex[:12]}",
            email=f"{tenant_id.hex[:12]}@example.test",
            tenant_id=tenant_id,
        )
    }


def verify_database_authority(admin_dsn: str, admission_dsn: str) -> None:
    with (
        psycopg.connect(admin_dsn, row_factory=dict_row) as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute(
            """
            SELECT
              has_table_privilege(
                'axignal_admission_runtime_login',
                'axignal_global.canonical_claims',
                'INSERT'
              ) AS canonical_insert,
              has_table_privilege(
                'axignal_admission_runtime_login',
                'axignal_global.admission_decisions',
                'INSERT'
              ) AS decision_insert,
              has_table_privilege(
                'axignal_admission_runtime_login',
                'axignal_global.evidence_objects',
                'UPDATE'
              ) AS evidence_update,
              has_table_privilege(
                'axignal_admission_runtime_login',
                'axignal_global.source_objects',
                'INSERT'
              ) AS source_insert
            """
        )
        assert cursor.fetchone() == {
            "canonical_insert": True,
            "decision_insert": True,
            "evidence_update": False,
            "source_insert": False,
        }

    with psycopg.connect(admission_dsn) as connection, connection.cursor() as cursor:
        try:
            cursor.execute(
                "UPDATE axignal_global.evidence_objects SET title = title WHERE false"
            )
        except InsufficientPrivilege:
            connection.rollback()
        else:
            raise AssertionError("Admission credential unexpectedly mutated Evidence Objects")


def isolate_admission_outbox(admin_dsn: str) -> None:
    with psycopg.connect(admin_dsn) as connection, connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE axignal_global.admission_outbox_events
            SET status = 'PUBLISHED', published_at = now()
            WHERE status = 'PENDING'
            """
        )


def create_provisional_run(client: TestClient, settings: Settings) -> UUID:
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
    return run_id


def load_job(admin_dsn: str, run_id: UUID) -> AdmissionReviewJob:
    with (
        psycopg.connect(admin_dsn, row_factory=dict_row) as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute(
            """
            SELECT admission_handoff_id, tenant_id, research_run_id, package_hash
            FROM axignal_global.admission_handoffs
            WHERE research_run_id = %s
            """,
            (run_id,),
        )
        row = cursor.fetchone()
        assert row is not None
        return AdmissionReviewJob(
            admission_handoff_id=row["admission_handoff_id"],
            research_run_id=row["research_run_id"],
            tenant_id=row["tenant_id"],
            expected_package_hash=row["package_hash"],
        )


def counts(admin_dsn: str, run_id: UUID) -> dict[str, int]:
    with (
        psycopg.connect(admin_dsn, row_factory=dict_row) as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute(
            """
            SELECT
              (
                SELECT count(*) FROM axignal_global.admission_batches batch
                JOIN axignal_global.admission_decisions decision
                  ON decision.admission_batch_id = batch.admission_batch_id
                JOIN axignal_global.admission_handoffs handoff
                  ON handoff.admission_handoff_id = decision.admission_handoff_id
                WHERE handoff.research_run_id = %s
              ) AS decisions,
              (
                SELECT count(DISTINCT batch.admission_batch_id)
                FROM axignal_global.admission_batches batch
                JOIN axignal_global.admission_decisions decision
                  ON decision.admission_batch_id = batch.admission_batch_id
                JOIN axignal_global.admission_handoffs handoff
                  ON handoff.admission_handoff_id = decision.admission_handoff_id
                WHERE handoff.research_run_id = %s
              ) AS batches,
              (
                SELECT cardinality(canonical_claim_ids)
                FROM tenant_private.research_runs
                WHERE research_run_id = %s
              ) AS run_canonical,
              (
                SELECT count(*) FROM axignal_global.claim_state_events event
                JOIN axignal_global.canonical_claims claim
                  ON claim.canonical_claim_id = event.canonical_claim_id
                JOIN tenant_private.research_runs run
                  ON claim.canonical_claim_id = ANY(run.canonical_claim_ids)
                WHERE run.research_run_id = %s
              ) AS events
            """,
            (run_id, run_id, run_id, run_id),
        )
        row = cursor.fetchone()
        assert row is not None
        return {key: int(value or 0) for key, value in row.items()}


def main() -> int:
    settings = Settings.from_env()
    settings.require_persistent_research()
    settings.require_document_proposal_worker()
    settings.require_admission_runtime()
    assert settings.database_url is not None
    assert settings.admission_database_url is not None
    assert settings.valkey_url is not None

    verify_database_authority(
        settings.database_url,
        settings.admission_database_url,
    )
    isolate_admission_outbox(settings.database_url)
    client = TestClient(app)
    run_id = create_provisional_run(client, settings)
    job = load_job(settings.database_url, run_id)

    admission_repository = AdmissionRepository(
        app_dsn=settings.database_url,
        admission_dsn=settings.admission_database_url,
    )
    try:
        admission_repository.decide(job, fail_after_canonical_insert=True)
    except RuntimeError as exc:
        assert str(exc) == "TEST_FAILPOINT_AFTER_CANONICAL_INSERT"
    else:
        raise AssertionError("Admission failpoint did not abort the transaction")
    assert counts(settings.database_url, run_id) == {
        "decisions": 0,
        "batches": 0,
        "run_canonical": 0,
        "events": 0,
    }

    admission_queue = ValkeyAdmissionQueue(
        settings.valkey_url,
        queue_key=settings.admission_queue_key,
    )
    publisher = AdmissionOutboxPublisher(admission_repository, admission_queue)
    assert publisher.publish_pending(limit=100) >= 1
    runtime = build_admission_runtime(settings)
    assert runtime.run_once(timeout_seconds=1) is True

    view_response = client.get(
        f"/v1/research-runs/{run_id}",
        headers=identity_headers(TENANT),
    )
    assert view_response.status_code == 200, view_response.text
    view = view_response.json()
    assert view["state"] == "COMPLETED"
    assert len(view["canonical_claims"]) == 1
    canonical = view["canonical_claims"][0]
    assert canonical["admitted_by"] == "DETERMINISTIC_RUNTIME"
    assert canonical["predicate"] == "real_gdp_growth_annual_pct"
    assert canonical["object_value"] == {
        "value": "2.3",
        "unit": "percent_annual",
        "period": "2018",
    }
    assert view["dossier"]["status"] == "TRACEABLE_WITH_ADMITTED_FACTS"
    states = {item["kind"]: item["state"] for item in view["candidate_claims"]}
    assert states == {"FACT": "ADMITTED", "LIMITATION": "HUMAN_REVIEW_REQUIRED"}
    assert all(item["producer_type"] == "LOCAL_MODEL" for item in view["candidate_claims"])
    assert view["actual_usage"]["admission_model_calls"] == 0

    cross_tenant = client.get(
        f"/v1/research-runs/{run_id}",
        headers=identity_headers(OTHER_TENANT),
    )
    assert cross_tenant.status_code == 404

    after_success = counts(settings.database_url, run_id)
    assert after_success == {
        "decisions": 2,
        "batches": 1,
        "run_canonical": 1,
        "events": 1,
    }
    runtime.queue.enqueue(job)
    assert runtime.run_once(timeout_seconds=1) is True
    assert counts(settings.database_url, run_id) == after_success

    tampered_run = create_provisional_run(client, settings)
    tampered_job = load_job(settings.database_url, tampered_run)
    with psycopg.connect(settings.database_url) as connection, connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE axignal_global.admission_handoffs
            SET package = jsonb_set(
              package,
              '{candidate_claims,0,object_value,value}',
              to_jsonb('2.4'::text)
            )
            WHERE admission_handoff_id = %s
            """,
            (tampered_job.admission_handoff_id,),
        )
    admission_queue.enqueue(tampered_job)
    assert runtime.run_once(timeout_seconds=1) is True
    with (
        psycopg.connect(settings.database_url, row_factory=dict_row) as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute(
            "SELECT state FROM axignal_global.admission_handoffs "
            "WHERE admission_handoff_id = %s",
            (tampered_job.admission_handoff_id,),
        )
        assert cursor.fetchone()["state"] == "QUARANTINED"
        cursor.execute(
            "SELECT count(*) AS count FROM axignal_global.admission_job_failures "
            "WHERE admission_handoff_id = %s AND quarantined",
            (tampered_job.admission_handoff_id,),
        )
        assert cursor.fetchone()["count"] == 1

    blocked_run = create_provisional_run(client, settings)
    blocked_job = load_job(settings.database_url, blocked_run)
    with psycopg.connect(settings.database_url) as connection, connection.cursor() as cursor:
        cursor.execute(
            "UPDATE axignal_global.sources SET kill_switch = true "
            "WHERE source_id = 'world-bank-rer41'"
        )
    admission_queue.enqueue(blocked_job)
    assert runtime.run_once(timeout_seconds=1) is True
    with (
        psycopg.connect(settings.database_url, row_factory=dict_row) as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute(
            "SELECT state FROM axignal_global.admission_handoffs "
            "WHERE admission_handoff_id = %s",
            (blocked_job.admission_handoff_id,),
        )
        assert cursor.fetchone()["state"] == "REJECTED"
        cursor.execute(
            "SELECT cardinality(canonical_claim_ids) AS count "
            "FROM tenant_private.research_runs WHERE research_run_id = %s",
            (blocked_run,),
        )
        assert int(cursor.fetchone()["count"] or 0) == 0
        cursor.execute(
            "UPDATE axignal_global.sources SET kill_switch = false "
            "WHERE source_id = 'world-bank-rer41'"
        )

    output = {
        "research_run_id": str(run_id),
        "state": view["state"],
        "admission_batches": after_success["batches"],
        "candidate_decisions": after_success["decisions"],
        "admitted_rederived": 1,
        "human_review_required": 1,
        "canonical_claims_created": after_success["run_canonical"],
        "model_claims_directly_admitted": 0,
        "admission_model_calls": 0,
        "idempotent_replay": True,
        "partial_transactions": 0,
        "tampered_package": "QUARANTINED",
        "source_kill_switch": "BLOCKED",
        "cross_tenant_read": "DENIED",
        "admission_credential_evidence_update": False,
    }
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
