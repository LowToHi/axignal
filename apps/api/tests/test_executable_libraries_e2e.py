"""Prioridad 4 — O02-O09 executable vertical slices over PostgreSQL.

For each library O02..O09:

    fixture versionada -> ingestion -> Evidence Objects -> Candidate Claims
    -> canonical claims -> library object persistido -> API query ->
    coverage disclosure -> reinicio (nueva sesión) -> recuperación ->
    aislamiento tenant -> idempotencia.

Run: AXIGNAL_INTEGRATION_TESTS=1 pytest apps/api/tests/test_executable_libraries_e2e.py
"""

from __future__ import annotations

import os
from pathlib import Path
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from axignal_api.application import app
from axignal_api.identity import build_identity_assertion

TENANT_A = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
TENANT_B = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
IDENTITY_SECRET = "local-dev-identity-assertion-secret-32-bytes"
DSN = "postgresql://axignal:axignal-local@localhost:5432/axignal"
FIXTURES = Path(__file__).parent / "fixtures"

pytestmark = pytest.mark.skipif(
    not os.environ.get("AXIGNAL_INTEGRATION_TESTS"),
    reason="executable libraries E2E needs a live PostgreSQL",
)


@pytest.fixture(autouse=True)
def _set_dsn(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AXIGNAL_DATABASE_URL", DSN)
    monkeypatch.setenv(
        "AXIGNAL_IDENTITY_ASSERTION_SECRET", IDENTITY_SECRET
    )


def _client(tenant_id: UUID, subject: str = "usr_exec_lib") -> TestClient:
    return TestClient(
        app,
        headers={
            "X-AXIGNAL-Identity-Assertion": build_identity_assertion(
                secret=IDENTITY_SECRET,
                subject=subject,
                email=f"{subject}@example.test",
                tenant_id=tenant_id,
            )
        },
    )


LIBRARIES = {
    "O02": ("src_cordis_grants_v1", 2),
    "O03": ("src_eurlex_regulation_v1", 2),
    "O04": ("src_o04_o09_fixture_v1", 1),
    "O05": ("src_o04_o09_fixture_v1", 1),
    "O06": ("src_o04_o09_fixture_v1", 1),
    "O07": ("src_o04_o09_fixture_v1", 1),
    "O08": ("src_o04_o09_fixture_v1", 1),
    "O09": ("src_o04_o09_fixture_v1", 1),
}


class TestExecutableLibraries:
    def test_all_libraries_executable(self) -> None:
        client = _client(TENANT_A)
        for library_id, (source_id, expected_items) in LIBRARIES.items():
            # 1. Ingest the versioned fixture.
            response = client.post(
                "/v1/opportunities/executable-libraries/ingest",
                json={"library_id": library_id, "source_id": source_id},
            )
            assert response.status_code == 201, (library_id, response.text)
            result = response.json()
            assert result["items"] == expected_items, (library_id, result)
            assert result["evidence_ids"], library_id
            assert result["candidate_claim_ids"], library_id
            assert result["canonical_claim_ids"], library_id
            assert result["content_hash"]

            # 2. Query via API (persisted).
            listed = client.get(
                f"/v1/opportunities/executable-libraries/{library_id}"
            )
            assert listed.status_code == 200, library_id
            objects = listed.json()
            assert objects, library_id
            assert objects[0]["content_hash"] == result["content_hash"], library_id

            # 3. Coverage disclosure.
            coverage = client.get(
                f"/v1/opportunities/executable-libraries/{library_id}/coverage"
            )
            assert coverage.status_code == 200, library_id
            disclosure = coverage.json()
            assert disclosure["scope_id"] == f"library:{library_id}"
            assert "BLOCKED_EXTERNAL" in disclosure["completeness_note"]
            assert disclosure["claims_global_coverage"] is False

            # 4. Idempotency: re-ingest does not duplicate.
            again = client.post(
                "/v1/opportunities/executable-libraries/ingest",
                json={"library_id": library_id, "source_id": source_id},
            )
            assert again.status_code == 201
            assert again.json()["content_hash"] == result["content_hash"]
            still = client.get(
                f"/v1/opportunities/executable-libraries/{library_id}"
            ).json()
            assert len(still) == len(objects), library_id

    def test_restart_recovery_and_tenant_isolation(self) -> None:
        # New client == new session (restart equivalence).
        fresh = _client(TENANT_A, subject="usr_exec_lib_2")
        for library_id, _ in LIBRARIES.items():
            objects = fresh.get(
                f"/v1/opportunities/executable-libraries/{library_id}"
            ).json()
            assert objects, library_id

        # Tenant isolation: B sees nothing.
        other = _client(TENANT_B, subject="usr_exec_lib_b")
        for library_id, _ in LIBRARIES.items():
            assert other.get(
                f"/v1/opportunities/executable-libraries/{library_id}"
            ).json() == []

    def test_evidence_and_canonical_claims_persisted(self) -> None:
        import psycopg
        from psycopg.rows import dict_row

        with psycopg.connect(DSN, row_factory=dict_row) as conn, conn.cursor() as cursor:
            cursor.execute(
                "SELECT count(*) AS n FROM axignal_global.evidence_objects "
                "WHERE subject_id LIKE 'O02_%'"
            )
            assert cursor.fetchone()["n"] > 0, "no O02 evidence"
            cursor.execute(
                "SELECT count(*) AS n FROM axignal_global.canonical_claims "
                "WHERE subject_id LIKE 'O03_%'"
            )
            assert cursor.fetchone()["n"] > 0, "no O03 canonical claims"
            cursor.execute(
                "SELECT count(*) AS n FROM tenant_private.library_objects "
                "WHERE tenant_id = %s",
                (TENANT_A,),
            )
            assert cursor.fetchone()["n"] >= 8, "not all library objects persisted"
