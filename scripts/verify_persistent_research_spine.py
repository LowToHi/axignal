from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from pathlib import Path
from uuid import UUID

import psycopg
from fastapi.testclient import TestClient
from psycopg.errors import InsufficientPrivilege, RaiseException

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "apps" / "api" / "tests" / "fixtures" / "world_bank_rus_inflation.json"
DATABASE_URL = os.environ.get(
    "AXIGNAL_DATABASE_URL",
    "postgresql://axignal:axignal@127.0.0.1:5432/axignal",
)
VALKEY_URL = os.environ.get("AXIGNAL_VALKEY_URL", "redis://127.0.0.1:6379/0")
TENANT_A = UUID("11111111-1111-4111-8111-111111111111")
TENANT_B = UUID("22222222-2222-4222-8222-222222222222")

os.environ["AXIGNAL_DATABASE_URL"] = DATABASE_URL
os.environ["AXIGNAL_VALKEY_URL"] = VALKEY_URL
os.environ["AXIGNAL_PERSISTENT_RESEARCH_ENABLED"] = "true"
os.environ["AXIGNAL_LIVE_SOURCES_ENABLED"] = "false"
os.environ["AXIGNAL_WORLD_BANK_FIXTURE_PATH"] = str(FIXTURE)
os.environ["AXIGNAL_RESEARCH_QUEUE_KEY"] = "axignal:research:queue:ci"

from axignal_api.application import app  # noqa: E402
from axignal_api.queue import OutboxPublisher, ValkeyResearchQueue  # noqa: E402
from axignal_api.repository import ResearchRepository  # noqa: E402
from axignal_api.settings import Settings  # noqa: E402
from axignal_api.worker import build_runtime  # noqa: E402


def assert_database_contract() -> None:
    with psycopg.connect(DATABASE_URL) as connection, connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name IN ('axignal_global', 'tenant_private', 'intent_intelligence')
            ORDER BY schema_name
            """
        )
        assert [row[0] for row in cursor.fetchall()] == [
            "axignal_global",
            "intent_intelligence",
            "tenant_private",
        ]
        cursor.execute(
            """
            SELECT source_id, admission_state, rights_status, kill_switch
            FROM axignal_global.sources
            ORDER BY source_id
            """
        )
        sources = {row[0]: row[1:] for row in cursor.fetchall()}
        assert sources["world-bank-wdi"] == (
            "ADMITTED",
            "COMMERCIAL_REUSE_WITH_ATTRIBUTION",
            False,
        )
        assert sources["bank-of-russia-statistics"] == (
            "QUARANTINED",
            "RIGHTS_PENDING",
            True,
        )
        cursor.execute(
            """
            SELECT relrowsecurity, relforcerowsecurity
            FROM pg_class
            WHERE oid = 'tenant_private.research_runs'::regclass
            """
        )
        assert cursor.fetchone() == (True, True)


def assert_ledger_is_protected(canonical_claim_id: UUID) -> None:
    try:
        with psycopg.connect(DATABASE_URL) as connection, connection.cursor() as cursor:
            cursor.execute("SET LOCAL ROLE axignal_worker")
            cursor.execute(
                """
                UPDATE axignal_global.canonical_claims
                SET statement = 'worker tamper attempt'
                WHERE canonical_claim_id = %s
                """,
                (canonical_claim_id,),
            )
    except InsufficientPrivilege:
        pass
    else:
        raise AssertionError("Worker unexpectedly received canonical Claim Ledger UPDATE access")

    try:
        with psycopg.connect(DATABASE_URL) as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE axignal_global.canonical_claims
                SET statement = 'owner tamper attempt'
                WHERE canonical_claim_id = %s
                """,
                (canonical_claim_id,),
            )
    except RaiseException as exc:
        assert "append-only" in str(exc)
    else:
        raise AssertionError("Canonical Claim Ledger trigger accepted an in-place mutation")


def main() -> int:
    assert_database_contract()
    settings = Settings.from_env()
    repository = ResearchRepository(DATABASE_URL)
    queue = ValkeyResearchQueue(VALKEY_URL, queue_key=settings.queue_key)
    queue.purge_for_test()

    client = TestClient(app)
    create_response = client.post(
        "/v1/research-runs",
        headers={"X-AXIGNAL-Tenant-ID": str(TENANT_A)},
        json={
            "context_id": "ctx_moscow_real_estate_v01",
            "opportunity_id": "opp_moscow_ramenki",
            "question": "Actualiza el contexto de inflación de la oportunidad.",
            "include_private_knowledge": False,
        },
    )
    assert create_response.status_code == 202, create_response.text
    accepted = create_response.json()
    run_id = UUID(accepted["research_run_id"])
    assert accepted["state"] == "QUEUED"
    assert accepted["source_ids"] == ["world-bank-wdi"]
    assert accepted["synthetic"] is False

    publisher, worker = build_runtime(settings)
    publisher.publish_pending(limit=20)
    assert worker.run_once(timeout_seconds=1) is True
    publisher.publish_pending(limit=20)

    get_response = client.get(
        f"/v1/research-runs/{run_id}",
        headers={"X-AXIGNAL-Tenant-ID": str(TENANT_A)},
    )
    assert get_response.status_code == 200, get_response.text
    result = get_response.json()
    assert result["state"] == "COMPLETED"
    assert result["synthetic"] is False
    assert result["actual_usage"]["model_calls"] == 0
    assert result["actual_usage"]["fixture_reads"] == 1
    assert len(result["evidence"]) == 1
    assert result["evidence"][0]["source_id"] == "world-bank-wdi"
    assert result["evidence"][0]["rights_status"] == ("COMMERCIAL_REUSE_WITH_ATTRIBUTION")
    assert result["evidence"][0]["numeric_value"] == "8.7"
    assert len(result["candidate_claims"]) == 1
    assert result["candidate_claims"][0]["producer_type"] == "DETERMINISTIC_PARSER"
    assert result["candidate_claims"][0]["state"] == "ADMITTED"
    assert len(result["canonical_claims"]) == 1
    canonical = result["canonical_claims"][0]
    assert canonical["state"] == "ADMITTED"
    assert canonical["admitted_by"] == "DETERMINISTIC_RUNTIME"
    assert canonical["object_value"]["indicator_code"] == "FP.CPI.TOTL.ZG"
    assert result["dossier"]["status"] == "TRACEABLE_WITH_ADMITTED_FACTS"
    assert result["dossier"]["attribution"]["license_id"] == "CC-BY-4.0"

    other_tenant_response = client.get(
        f"/v1/research-runs/{run_id}",
        headers={"X-AXIGNAL-Tenant-ID": str(TENANT_B)},
    )
    assert other_tenant_response.status_code == 404
    assert repository.debug_count_for_tenant(tenant_id=TENANT_A, table="research_runs") == 1
    assert repository.debug_count_for_tenant(tenant_id=TENANT_B, table="research_runs") == 0

    private_body = "Fixture privada: priorizar estabilidad de desplazamiento."
    repository.add_private_knowledge_fixture(
        tenant_id=TENANT_A,
        title="Preferencia privada de movilidad",
        body=private_body,
        content_hash=f"sha256:{sha256(private_body.encode()).hexdigest()}",
    )
    assert repository.debug_count_for_tenant(tenant_id=TENANT_A, table="knowledge_items") == 1
    assert repository.debug_count_for_tenant(tenant_id=TENANT_B, table="knowledge_items") == 0

    now = datetime.now(UTC)
    repository.record_intent_event(
        tenant_id=TENANT_A,
        event_type="RESEARCH_RUN_REQUESTED",
        subject_key="opp_moscow_ramenki",
        payload={"research_run_id": str(run_id)},
        occurred_at=now,
        expires_at=now + timedelta(days=30),
    )

    assert_ledger_is_protected(UUID(canonical["canonical_claim_id"]))

    # Duplicate delivery is safe and must not create a second canonical fact.
    OutboxPublisher(repository, queue).publish_pending(limit=20)
    with psycopg.connect(DATABASE_URL) as connection, connection.cursor() as cursor:
        cursor.execute("SELECT count(*) FROM axignal_global.canonical_claims")
        assert cursor.fetchone()[0] == 1
        cursor.execute("SELECT count(*) FROM axignal_global.claim_state_events")
        assert cursor.fetchone()[0] == 1
        cursor.execute(
            """
            SELECT count(*)
            FROM intent_intelligence.knowledge_tides
            WHERE research_candidate_only
            """
        )
        assert cursor.fetchone()[0] == 0

    print("PASS persistent ResearchRun, RLS, outbox, worker and deterministic admission")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
