from __future__ import annotations

import json
import os
from hashlib import sha256
from pathlib import Path
from uuid import UUID, uuid4

import psycopg
from psycopg.errors import InsufficientPrivilege

from axignal_api.connectors.ted_xml import SOURCE_ID, TEDXMLConnector
from axignal_api.procurement_admission_runtime import ProcurementAdmissionRuntime
from axignal_api.procurement_persistent_types import sanitise_retrieved_lifecycle
from axignal_api.procurement_queue import (
    ProcurementAdmissionOutboxPublisher,
    ProcurementRetrievalOutboxPublisher,
    ValkeyProcurementAdmissionQueue,
    ValkeyProcurementRetrievalQueue,
)
from axignal_api.procurement_repository import (
    ProcurementAdmissionRepository,
    ProcurementAppRepository,
    ProcurementRetrievalRepository,
)
from axignal_api.procurement_retrieval_runtime import ProcurementRetrievalRuntime
from axignal_api.repository import ResearchRepository

OUTPUT = Path("ted-persistent-source-evidence.json")
PUBLICATION_NUMBERS = (
    "10000001-2026",
    "10000002-2026",
    "10000003-2026",
    "10000004-2026",
)


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def scalar(dsn: str, statement: str, params: tuple[object, ...] = ()) -> object:
    with psycopg.connect(dsn) as connection, connection.cursor() as cursor:
        cursor.execute(statement, params)
        row = cursor.fetchone()
        if row is None:
            raise RuntimeError("Expected scalar query result")
        return row[0]


def counts(dsn: str) -> dict[str, int]:
    tables = {
        "source_objects": "axignal_global.source_objects",
        "notice_versions": "axignal_global.procurement_notice_versions",
        "evidence_objects": "axignal_global.evidence_objects",
        "candidate_claims": "axignal_global.candidate_claims",
        "admission_handoffs": "axignal_global.admission_handoffs",
        "admission_batches": "axignal_global.admission_batches",
        "admission_decisions": "axignal_global.admission_decisions",
        "canonical_claims": "axignal_global.canonical_claims",
        "claim_state_events": "axignal_global.claim_state_events",
    }
    return {
        key: int(scalar(dsn, f"SELECT count(*) FROM {table}"))
        for key, table in tables.items()
    }


def create_run(
    app_repository: ProcurementAppRepository,
    *,
    tenant_id: UUID,
    suffix: str,
) -> UUID:
    return app_repository.create_run(
        tenant_id=tenant_id,
        context_id=f"ctx_ted_{suffix}_0001",
        opportunity_id=f"opp_ted_{suffix}",
        question="Reconstruct the bounded official TED procurement lifecycle.",
        publication_numbers=PUBLICATION_NUMBERS,
    )


def main() -> int:
    app_dsn = require_env("AXIGNAL_DATABASE_URL")
    worker_dsn = require_env("AXIGNAL_TED_DATABASE_URL")
    admission_dsn = require_env("AXIGNAL_TED_ADMISSION_DATABASE_URL")
    valkey_url = require_env("AXIGNAL_VALKEY_URL")
    manifest_path = Path(require_env("AXIGNAL_TED_FIXTURE_MANIFEST_PATH")).resolve()
    retrieval_key = os.environ.get(
        "AXIGNAL_TED_RETRIEVAL_QUEUE_KEY",
        "axignal:procurement:retrieval:queue:v1",
    )
    admission_key = os.environ.get(
        "AXIGNAL_TED_ADMISSION_QUEUE_KEY",
        "axignal:procurement:admission:queue:v1",
    )

    app_repository = ProcurementAppRepository(app_dsn)
    retrieval_repository = ProcurementRetrievalRepository(worker_dsn)
    admission_repository = ProcurementAdmissionRepository(admission_dsn)
    retrieval_queue = ValkeyProcurementRetrievalQueue(valkey_url, queue_key=retrieval_key)
    admission_queue = ValkeyProcurementAdmissionQueue(valkey_url, queue_key=admission_key)
    retrieval_queue.purge_for_test()
    admission_queue.purge_for_test()
    connector = TEDXMLConnector(
        live_enabled=False,
        fixture_manifest_path=manifest_path,
    )
    retrieval_publisher = ProcurementRetrievalOutboxPublisher(
        app_repository,
        retrieval_queue,
    )
    worker_publisher = ProcurementRetrievalOutboxPublisher(
        retrieval_repository,
        retrieval_queue,
    )
    admission_publisher = ProcurementAdmissionOutboxPublisher(
        admission_repository,
        admission_queue,
    )
    retrieval_runtime = ProcurementRetrievalRuntime(
        repository=retrieval_repository,
        queue=retrieval_queue,
        connector=connector,
    )
    admission_runtime = ProcurementAdmissionRuntime(
        repository=admission_repository,
        queue=admission_queue,
        connector=connector,
    )

    tenant_id = UUID("11111111-1111-4111-8111-111111111111")
    run_id = create_run(app_repository, tenant_id=tenant_id, suffix="primary")
    assert retrieval_publisher.publish_pending(limit=100) >= 1
    assert retrieval_runtime.run_once(timeout_seconds=1) is True
    assert admission_publisher.publish_pending(limit=100) >= 1
    assert admission_runtime.run_once(timeout_seconds=1) is True

    view_repository = ResearchRepository(app_dsn)
    view = view_repository.get_run_view(tenant_id=tenant_id, run_id=run_id)
    assert view is not None
    assert view["state"] == "COMPLETED"
    assert view["source_plan"][0]["source_id"] == SOURCE_ID
    assert view["evidence"]
    assert view["candidate_claims"]
    assert view["canonical_claims"]
    assert view["dossier"]["status"] == "TRACEABLE_WITH_ADMITTED_FACTS"
    assert view_repository.get_run_view(tenant_id=uuid4(), run_id=run_id) is None

    source = scalar(
        app_dsn,
        "SELECT row_to_json(s) FROM axignal_global.sources s WHERE source_id = %s",
        (SOURCE_ID,),
    )
    assert source["admission_state"] == "ADMITTED"
    assert source["kill_switch"] is False
    assert source["config"]["rights_scope"] == "DERIVED_NON_PERSONAL_ONLY"
    assert source["config"]["raw_xml_persistence"] is False
    assert source["config"]["personal_values_persistence"] is False

    raw_xml_rows = int(
        scalar(
            app_dsn,
            """
            SELECT count(*) FROM axignal_global.procurement_notice_versions
            WHERE raw_xml_persisted OR sanitised_payload::text LIKE '%<Contract%'
            """,
        )
    )
    personal_value_rows = int(
        scalar(
            app_dsn,
            """
            SELECT count(*)
            FROM axignal_global.evidence_objects
            WHERE source_id = %s AND (
              payload::text ~* 'electronicmail|telephone|firstname|familyname|@'
              OR predicate ~* 'contact|email|phone|telephone|person'
            )
            """,
            (SOURCE_ID,),
        )
    )
    excluded_identity_rows = int(
        scalar(
            app_dsn,
            """
            SELECT count(*) FROM axignal_global.candidate_claims
            WHERE producer_id = 'ted-eforms-parser' AND predicate IN (
              'procurement_buyer_official_name',
              'procurement_buyer_identifier',
              'procurement_winner_official_name',
              'procurement_winner_organisation_ref',
              'procurement_contract_identifier'
            )
            """,
        )
    )
    assert raw_xml_rows == 0
    assert personal_value_rows == 0
    assert excluded_identity_rows == 0

    with psycopg.connect(worker_dsn) as connection, connection.cursor() as cursor:
        try:
            cursor.execute("INSERT INTO axignal_global.canonical_claims DEFAULT VALUES")
        except InsufficientPrivilege:
            connection.rollback()
            worker_canonical_insert = False
        else:
            connection.rollback()
            worker_canonical_insert = True
    assert worker_canonical_insert is False

    with psycopg.connect(admission_dsn) as connection, connection.cursor() as cursor:
        try:
            cursor.execute(
                "UPDATE axignal_global.evidence_objects SET provisional = false WHERE false"
            )
        except InsufficientPrivilege:
            connection.rollback()
            admission_evidence_update = False
        else:
            connection.rollback()
            admission_evidence_update = True
    assert admission_evidence_update is False

    primary_handoff_id = UUID(
        str(
            scalar(
                app_dsn,
                "SELECT admission_handoff_id FROM tenant_private.research_runs "
                "WHERE research_run_id = %s",
                (run_id,),
            )
        )
    )
    primary_package_hash = str(
        scalar(
            app_dsn,
            "SELECT package_hash FROM axignal_global.admission_handoffs "
            "WHERE admission_handoff_id = %s",
            (primary_handoff_id,),
        )
    )
    primary_admission_job_payload = {
        "schema_version": 1,
        "job_kind": "PROCUREMENT_ADMISSION_REVIEW",
        "tenant_id": str(tenant_id),
        "research_run_id": str(run_id),
        "admission_handoff_id": str(primary_handoff_id),
        "expected_package_hash": primary_package_hash,
        "publication_numbers": list(PUBLICATION_NUMBERS),
        "policy_version": "ted-procurement-observed@1.0.0",
    }
    from axignal_api.procurement_queue import ProcurementAdmissionJob

    replay = admission_repository.decide(
        job=ProcurementAdmissionJob.from_payload(primary_admission_job_payload),
        connector=connector,
    )
    assert replay.idempotent_replay is True

    retrieved = tuple(connector.fetch(item) for item in PUBLICATION_NUMBERS)
    lifecycle = sanitise_retrieved_lifecycle(retrieved)
    retrieval_before = counts(app_dsn)
    rollback_run = create_run(app_repository, tenant_id=tenant_id, suffix="rollback_retrieval")
    assert worker_publisher.publish_pending(limit=100) >= 1
    rollback_job = retrieval_queue.dequeue(timeout_seconds=1)
    assert rollback_job is not None and rollback_job.research_run_id == rollback_run
    rollback_source = retrieval_repository.load_source()
    assert rollback_source is not None
    retrieval_repository.transition(rollback_job, "RETRIEVING")
    retrieval_repository.transition(rollback_job, "DOCUMENT_PARSING")
    retrieval_repository.transition(rollback_job, "EVIDENCE_BINDING")
    try:
        retrieval_repository.persist_lifecycle(
            job=rollback_job,
            lifecycle=lifecycle,
            source=rollback_source,
            fail_after_first_evidence=True,
        )
    except RuntimeError as exc:
        assert str(exc) == "TEST_FAILPOINT_AFTER_FIRST_TED_EVIDENCE"
    else:
        raise AssertionError("TED retrieval rollback failpoint did not fire")
    retrieval_after = counts(app_dsn)
    for key in (
        "source_objects",
        "notice_versions",
        "evidence_objects",
        "candidate_claims",
        "admission_handoffs",
    ):
        assert retrieval_after[key] == retrieval_before[key]

    admission_rollback_run = create_run(
        app_repository,
        tenant_id=tenant_id,
        suffix="rollback_admission",
    )
    assert worker_publisher.publish_pending(limit=100) >= 1
    assert retrieval_runtime.run_once(timeout_seconds=1) is True
    assert admission_publisher.publish_pending(limit=100) >= 1
    admission_rollback_job = admission_queue.dequeue(timeout_seconds=1)
    assert admission_rollback_job is not None
    assert admission_rollback_job.research_run_id == admission_rollback_run
    admission_before = counts(app_dsn)
    try:
        admission_repository.decide(
            job=admission_rollback_job,
            connector=connector,
            fail_after_first_canonical=True,
        )
    except RuntimeError as exc:
        assert str(exc) == "TEST_FAILPOINT_AFTER_FIRST_TED_CANONICAL"
    else:
        raise AssertionError("TED admission rollback failpoint did not fire")
    admission_after = counts(app_dsn)
    for key in (
        "admission_batches",
        "admission_decisions",
        "canonical_claims",
        "claim_state_events",
    ):
        assert admission_after[key] == admission_before[key]
    assert (
        scalar(
            app_dsn,
            "SELECT state FROM axignal_global.admission_handoffs WHERE admission_handoff_id = %s",
            (admission_rollback_job.admission_handoff_id,),
        )
        == "PENDING"
    )
    recovered = admission_repository.decide(
        job=admission_rollback_job,
        connector=connector,
    )
    assert recovered.canonical_claim_ids

    with psycopg.connect(app_dsn) as connection, connection.cursor() as cursor:
        cursor.execute(
            "UPDATE axignal_global.sources SET kill_switch = true WHERE source_id = %s",
            (SOURCE_ID,),
        )
    kill_run = create_run(app_repository, tenant_id=tenant_id, suffix="kill_switch")
    assert worker_publisher.publish_pending(limit=100) >= 1
    assert retrieval_runtime.run_once(timeout_seconds=1) is True
    assert scalar(
        app_dsn,
        "SELECT state FROM tenant_private.research_runs WHERE research_run_id = %s",
        (kill_run,),
    ) == "QUARANTINED"
    assert scalar(
        app_dsn,
        "SELECT admission_handoff_id FROM tenant_private.research_runs WHERE research_run_id = %s",
        (kill_run,),
    ) is None
    with psycopg.connect(app_dsn) as connection, connection.cursor() as cursor:
        cursor.execute(
            "UPDATE axignal_global.sources SET kill_switch = false WHERE source_id = %s",
            (SOURCE_ID,),
        )

    final_counts = counts(app_dsn)
    evidence = {
        "source_id": SOURCE_ID,
        "source_product_admitted": True,
        "source_kill_switch_restored_off": True,
        "rights_scope": "DERIVED_NON_PERSONAL_ONLY",
        "publication_count_per_run": len(PUBLICATION_NUMBERS),
        "primary_run_state": view["state"],
        "primary_evidence_count": len(view["evidence"]),
        "primary_candidate_claim_count": len(view["candidate_claims"]),
        "primary_canonical_claim_count": len(view["canonical_claims"]),
        "dossier_status": view["dossier"]["status"],
        "raw_xml_persisted_rows": raw_xml_rows,
        "personal_value_rows": personal_value_rows,
        "excluded_identity_candidate_rows": excluded_identity_rows,
        "worker_canonical_insert": worker_canonical_insert,
        "admission_evidence_update": admission_evidence_update,
        "idempotent_admission_replay": replay.idempotent_replay,
        "retrieval_rollback_residue": {
            key: retrieval_after[key] - retrieval_before[key]
            for key in (
                "source_objects",
                "notice_versions",
                "evidence_objects",
                "candidate_claims",
                "admission_handoffs",
            )
        },
        "admission_rollback_residue": {
            key: admission_after[key] - admission_before[key]
            for key in (
                "admission_batches",
                "admission_decisions",
                "canonical_claims",
                "claim_state_events",
            )
        },
        "kill_switch_blocked_run": True,
        "cross_tenant_read": "DENIED",
        "model_calls": 0,
        "final_counts": final_counts,
        "primary_run_fingerprint": "sha256:"
        + sha256(str(run_id).encode("utf-8")).hexdigest(),
    }
    OUTPUT.write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
