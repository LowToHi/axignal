from __future__ import annotations

import json
from uuid import UUID

import psycopg
from fastapi.testclient import TestClient
from psycopg.errors import InsufficientPrivilege
from psycopg.rows import dict_row

from axignal_api.application import app
from axignal_api.identity import build_identity_assertion
from axignal_api.proposal_queue import DocumentProposalBudget, DocumentProposalJob
from axignal_api.proposal_worker import build_runtime
from axignal_api.settings import Settings

TENANT_A = UUID("33333333-3333-4333-8333-333333333333")
TENANT_B = UUID("44444444-4444-4444-8444-444444444444")
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


def verify_database_authority(admin_dsn: str, proposal_dsn: str) -> None:
    with (
        psycopg.connect(admin_dsn, row_factory=dict_row) as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute(
            """
            SELECT
              has_table_privilege(
                'axignal_proposal_worker',
                'axignal_global.canonical_claims',
                'INSERT'
              ) AS canonical_insert,
              has_table_privilege(
                'axignal_proposal_worker',
                'axignal_global.claim_state_events',
                'INSERT'
              ) AS event_insert,
              has_table_privilege(
                'axignal_proposal_worker',
                'axignal_global.candidate_claims',
                'INSERT'
              ) AS candidate_insert
            """
        )
        privileges = cursor.fetchone()
        assert privileges == {
            "canonical_insert": False,
            "event_insert": False,
            "candidate_insert": True,
        }

    with psycopg.connect(proposal_dsn) as connection, connection.cursor() as cursor:
        try:
            cursor.execute(
                """
                INSERT INTO axignal_global.canonical_claims (
                  fingerprint, subject_id, predicate, object_value, statement,
                  evidence_ids, observed_at, epistemic_class, admitted_by,
                  admission_batch_id
                ) VALUES (
                  %s, 'forbidden_subject', 'forbidden_predicate', '{}'::jsonb,
                  'This write must never succeed.', ARRAY[gen_random_uuid()], now(),
                  'OBSERVED_FACT', 'DETERMINISTIC_RUNTIME', gen_random_uuid()
                )
                """,
                ("sha256:" + ("0" * 64),),
            )
        except InsufficientPrivilege:
            connection.rollback()
        else:
            raise AssertionError(
                "Dedicated proposal credential unexpectedly wrote a canonical claim"
            )


def count_persistent_artifacts(dsn: str, run_id: UUID) -> dict[str, int]:
    with (
        psycopg.connect(dsn, row_factory=dict_row) as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute(
            """
            SELECT
              (
                SELECT count(*)
                FROM axignal_global.document_fragments fragments
                JOIN axignal_global.source_objects objects
                  ON objects.source_object_id = fragments.source_object_id
                WHERE objects.raw_payload ->> 'document_id' = 'doc_world_bank_rer41'
              ) AS fragments,
              (
                SELECT count(*)
                FROM tenant_private.research_evidence_links
                WHERE research_run_id = %s
              ) AS evidence,
              (
                SELECT cardinality(candidate_claim_ids)
                FROM tenant_private.research_runs
                WHERE research_run_id = %s
              ) AS candidates,
              (
                SELECT count(*)
                FROM axignal_global.admission_handoffs
                WHERE research_run_id = %s
              ) AS handoffs,
              (
                SELECT cardinality(canonical_claim_ids)
                FROM tenant_private.research_runs
                WHERE research_run_id = %s
              ) AS canonical
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
    assert settings.database_url is not None
    assert settings.proposal_database_url is not None

    verify_database_authority(
        settings.database_url,
        settings.proposal_database_url,
    )

    client = TestClient(app)
    response = client.post(
        "/v1/research-runs/document-proposals",
        headers=identity_headers(TENANT_A),
        json={
            "context_id": "ctx_moscow_real_estate_v01",
            "opportunity_id": "opp_moscow_ramenki",
            "question": (
                "Extrae afirmaciones económicas trazables, evidencia adversa y límites "
                "sobre la aplicabilidad del informe a la oportunidad de Moscú."
            ),
        },
    )
    assert response.status_code == 202, response.text
    accepted = response.json()
    run_id = UUID(accepted["research_run_id"])
    assert accepted["job_kind"] == "DOCUMENT_PROPOSAL"
    assert accepted["document_id"] == "doc_world_bank_rer41"

    worker = build_runtime(settings)
    assert worker.run_once(timeout_seconds=1) is True

    view_response = client.get(
        f"/v1/research-runs/{run_id}",
        headers=identity_headers(TENANT_A),
    )
    assert view_response.status_code == 200, view_response.text
    view = view_response.json()
    assert view["state"] == "COMPLETED_PROVISIONAL"
    assert len(view["evidence"]) == 2
    assert len(view["candidate_claims"]) == 2
    assert view["canonical_claims"] == []
    assert view["dossier"]["status"] == "TRACEABLE_PROVISIONAL"
    assert all(item["producer_type"] == "LOCAL_MODEL" for item in view["candidate_claims"])
    assert all(item["state"] == "ADMISSION_QUEUED" for item in view["candidate_claims"])

    cross_tenant = client.get(
        f"/v1/research-runs/{run_id}",
        headers=identity_headers(TENANT_B),
    )
    assert cross_tenant.status_code == 404

    before = count_persistent_artifacts(settings.database_url, run_id)
    assert before == {
        "fragments": 2,
        "evidence": 2,
        "candidates": 2,
        "handoffs": 1,
        "canonical": 0,
    }

    duplicate = DocumentProposalJob(
        tenant_id=TENANT_A,
        research_run_id=run_id,
        source_id="world-bank-rer41",
        document_id="doc_world_bank_rer41",
        pipeline_version="local-document-proposal-pipeline@0.1.0",
        budget=DocumentProposalBudget(),
    )
    worker.queue.enqueue(duplicate)
    assert worker.run_once(timeout_seconds=1) is True
    after = count_persistent_artifacts(settings.database_url, run_id)
    assert after == before

    with (
        psycopg.connect(settings.database_url, row_factory=dict_row) as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute(
            """
            SELECT state, package_hash, package
            FROM axignal_global.admission_handoffs
            WHERE research_run_id = %s
            """,
            (run_id,),
        )
        handoff = cursor.fetchone()
        assert handoff is not None
        assert handoff["state"] == "PENDING"
        assert handoff["package_hash"].startswith("sha256:")
        assert handoff["package"]["canonical_claim_ids"] == []
        assert len(handoff["package"]["candidate_claims"]) == 2
        assert len(handoff["package"]["evidence"]) == 2

    output = {
        "research_run_id": str(run_id),
        "state": view["state"],
        "document_id": accepted["document_id"],
        "fragments": after["fragments"],
        "evidence_objects": after["evidence"],
        "candidate_claims": after["candidates"],
        "admission_handoffs": after["handoffs"],
        "canonical_claims": after["canonical"],
        "dossier_status": view["dossier"]["status"],
        "proposal_worker_canonical_insert": False,
        "cross_tenant_read": "DENIED",
        "idempotent_replay": True,
        "handoff_state": "PENDING",
    }
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
