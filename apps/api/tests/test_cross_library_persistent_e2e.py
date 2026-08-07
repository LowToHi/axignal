"""Prioridad 5 — persistent cross-library graph E2E over PostgreSQL.

Nodes + edges + timeline + contradictions + non-canonical hypotheses +
portfolio, tenant-scoped; source quarantine; restart recovery; tenant
isolation.

Run: AXIGNAL_INTEGRATION_TESTS=1 pytest apps/api/tests/test_cross_library_persistent_e2e.py
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from axignal_api.application import app
from axignal_api.identity import build_identity_assertion

TENANT_A = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
TENANT_B = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
IDENTITY_SECRET = "local-dev-identity-assertion-secret-32-bytes"
DSN = "postgresql://axignal:axignal-local@localhost:5432/axignal"

pytestmark = pytest.mark.skipif(
    not os.environ.get("AXIGNAL_INTEGRATION_TESTS"),
    reason="cross-library E2E needs a live PostgreSQL",
)


@pytest.fixture(autouse=True)
def _set_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AXIGNAL_DATABASE_URL", DSN)
    monkeypatch.setenv("AXIGNAL_IDENTITY_ASSERTION_SECRET", IDENTITY_SECRET)


def _client(tenant_id: UUID, subject: str = "usr_xlib") -> TestClient:
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


def _reset_graph() -> None:
    import psycopg

    with psycopg.connect(DSN) as conn, conn.cursor() as cursor:
        for table in (
            "cross_library_hypotheses",
            "cross_library_contradictions",
            "cross_library_timeline",
            "cross_library_edges",
            "cross_library_nodes",
        ):
            cursor.execute(
                f"DELETE FROM tenant_private.{table} WHERE tenant_id = %s",
                (TENANT_A,),
            )
        conn.commit()


class TestCrossLibraryPersistent:
    def test_full_graph_journey(self) -> None:
        _reset_graph()
        client = _client(TENANT_A)

        # 1. Nodes across libraries.
        nodes = [
            ("ent_es_transport_agency", "O01", "PUBLIC_ENTITY", "ES Transport Agency"),
            ("ent_renfe", "O05", "COMPANY", "Renfe"),
            ("proj_renfe_hsr", "O04", "PROJECT", "HSR corridor electrification"),
            ("reg_es_rail_2026", "O03", "REGULATION", "Rail sector reform 2026"),
            ("mac_es_gdp", "O06", "INDICATOR", "GDP growth ES"),
        ]
        for node_ref, library_id, entity_type, label in nodes:
            response = client.post(
                "/v1/cross-library/nodes",
                json={"node_ref": node_ref, "library_id": library_id,
                      "entity_type": entity_type, "label": label},
            )
            assert response.status_code == 201, response.text

        listed = client.get("/v1/cross-library/nodes").json()
        assert len(listed) == 5

        # 2. Edges with evidence.
        edges = [
            ("ent_renfe", "proj_renfe_hsr", "OPERATES", ["ev-1"],
             "src_o04_o09_fixture_v1"),
            ("proj_renfe_hsr", "reg_es_rail_2026", "SUBJECT_TO", ["ev-2"],
             "src_o04_o09_fixture_v1"),
            ("proj_renfe_hsr", "mac_es_gdp", "AFFECTED_BY", ["ev-3"],
             "src_o04_o09_fixture_v1"),
            ("ent_es_transport_agency", "proj_renfe_hsr", "REGULATES", ["ev-4"],
             "src_o04_o09_fixture_v1"),
        ]
        for from_ref, to_ref, relation, evidence_refs, source_id in edges:
            response = client.post(
                "/v1/cross-library/edges",
                json={"from_ref": from_ref, "to_ref": to_ref, "relation": relation,
                      "evidence_refs": evidence_refs, "source_id": source_id},
            )
            assert response.status_code == 201, response.text

        # 3. Timeline.
        for node_ref, event_type, _days_ago in [
            ("proj_renfe_hsr", "PROCUREMENT_LAUNCHED", 30),
            ("proj_renfe_hsr", "PERMIT_GRANTED", 10),
            ("reg_es_rail_2026", "PUBLISHED", 60),
        ]:
            response = client.post(
                "/v1/cross-library/timeline",
                json={"node_ref": node_ref,
                      "occurred_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
                      "event_type": event_type},
            )
            assert response.status_code == 201, response.text

        timeline = client.get("/v1/cross-library/timeline").json()
        assert len(timeline) == 3

        # 4. Contradiction: explicit, never silently resolved.
        contradiction = client.post(
            "/v1/cross-library/contradictions",
            json={"claim_a_ref": "canonical:proj_renfe_hsr.budget.2026",
                  "claim_b_ref": "canonical:mac_es_gdp.investment.2026",
                  "description": "Reported project budget exceeds public investment envelope."},
        )
        assert contradiction.status_code == 201
        contradictions = client.get("/v1/cross-library/contradictions").json()
        assert len(contradictions) == 1
        assert contradictions[0]["status"] == "OPEN"

        # 5. Causal hypothesis: NON-canonical, refuses admission.
        hypothesis = client.post(
            "/v1/cross-library/hypotheses",
            json={"hypothesis_ref": "hyp_001", "cause_ref": "reg_es_rail_2026",
                  "effect_ref": "proj_renfe_hsr",
                  "description": "Rail reform may accelerate HSR procurement.",
                  "confidence": "MEDIUM"},
        )
        assert hypothesis.status_code == 201
        assert hypothesis.json()["canonical"] is False
        hypotheses = client.get("/v1/cross-library/hypotheses").json()
        assert len(hypotheses) == 1
        # Hypothesis table is separate from canonical_claims: never admitted.
        import psycopg
        from psycopg.rows import dict_row

        with psycopg.connect(DSN, row_factory=dict_row) as conn, conn.cursor() as cursor:
            cursor.execute(
                "SELECT count(*) AS n FROM axignal_global.canonical_claims "
                "WHERE subject_id = 'hyp_001'"
            )
            assert cursor.fetchone()["n"] == 0

        # 6. Neighbors query.
        neighbors = client.get(
            "/v1/cross-library/nodes/proj_renfe_hsr/neighbors"
        ).json()
        assert len(neighbors["neighbors"]) == 4
        relations = {n["relation"] for n in neighbors["neighbors"]}
        assert relations == {"OPERATES", "SUBJECT_TO", "AFFECTED_BY", "REGULATES"}

        # 7. Source quarantine: edges flagged, kept.
        quarantined = client.post(
            "/v1/cross-library/sources/src_o04_o09_fixture_v1/quarantine"
        )
        assert quarantined.status_code == 200
        assert quarantined.json()["quarantined_edges"] >= 3
        edges_after = client.get("/v1/cross-library/edges").json()
        quarantined_edges = [
            edge for edge in edges_after if edge["status"] == "QUARANTINED"
        ]
        assert len(quarantined_edges) >= 3

        # 8. Restart-equivalence: new session reads the same graph.
        fresh = _client(TENANT_A, subject="usr_xlib_2")
        assert len(fresh.get("/v1/cross-library/nodes").json()) == 5
        assert len(fresh.get("/v1/cross-library/timeline").json()) == 3
        assert len(fresh.get("/v1/cross-library/hypotheses").json()) == 1

        # 9. Tenant isolation.
        other = _client(TENANT_B, subject="usr_xlib_b")
        assert other.get("/v1/cross-library/nodes").json() == []
        assert other.get("/v1/cross-library/edges").json() == []
        assert other.get("/v1/cross-library/contradictions").json() == []
