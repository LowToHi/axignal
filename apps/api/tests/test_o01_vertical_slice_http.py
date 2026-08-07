"""Vertical Slice O01 — HTTP E2E over the real stack (Prioridad 3).

Journey: frozen official TED fixture -> TEDSearchConnector ->
evidence/candidate artifacts -> opportunity -> pursuit -> workspace ->
outcome, all through the real FastAPI application (TestClient) with
PostgreSQL persistence. Ends with a recovery from a NEW session and
tenant isolation verification.

This is a LOCAL_PRODUCT vertical slice: the Legal/Privacy signature is
absent, so commercial admission/launch stay blocked, but the technical
private journey is fully exercised.
"""

from __future__ import annotations

import os
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from axignal_api.application import app
from axignal_api.connectors.ted import TEDSearchConnector
from axignal_api.identity import build_identity_assertion
from axignal_api.ted_runtime import build_ted_search_artifacts

DSN = os.environ.get(
    "AXIGNAL_DATABASE_URL",
    "postgresql://axignal:axignal-local@localhost:5432/axignal",
)
FIXTURE = Path(__file__).parent / "fixtures" / "ted_search_probe.json"

TENANT_A = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
TENANT_B = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
IDENTITY_SECRET = "vertical-slice-identity-secret-with-at-least-32-bytes"

pytestmark = pytest.mark.skipif(
    not os.environ.get("AXIGNAL_INTEGRATION_TESTS"),
    reason="vertical slice needs a live PostgreSQL; set AXIGNAL_INTEGRATION_TESTS=1",
)


def _client(tenant_id: UUID, subject: str = "usr_o01_slice") -> TestClient:
    headers = {
        "X-AXIGNAL-Identity-Assertion": build_identity_assertion(
            secret=IDENTITY_SECRET,
            subject=subject,
            email=f"{subject}@example.test",
            tenant_id=tenant_id,
        )
    }
    return TestClient(app, headers=headers)


class TestVerticalSliceO01:
    def test_full_private_journey(self, monkeypatch) -> None:
        monkeypatch.setenv("AXIGNAL_IDENTITY_ASSERTION_SECRET", IDENTITY_SECRET)
        monkeypatch.setenv("AXIGNAL_DATABASE_URL", DSN)

        client = _client(TENANT_A)

        # 1. Libraries and sources over HTTP.
        libraries = client.get("/v1/opportunities/libraries")
        assert libraries.status_code == 200
        library_ids = {item["library_id"] for item in libraries.json()}
        assert "O01" in library_ids

        sources = client.get("/v1/opportunities/sources")
        assert sources.status_code == 200
        assert sources.json()[0]["source_id"] == "src_ted_search_api_v3"

        coverage = client.get("/v1/opportunities/coverage/src_ted_search_api_v3")
        assert coverage.status_code == 200
        assert coverage.json()["scope_id"] == "src_ted_search_api_v3"

        # 2. Ingest the frozen official fixture (reproducible source).
        connector = TEDSearchConnector(live_enabled=False, fixture_path=FIXTURE)
        page = connector.fetch_probe_page()
        assert page.retrieval_mode == "FROZEN_FIXTURE"
        assert len(page.notices) == 2

        opportunity_id = f"opp_slice_{uuid4().hex[:8]}"
        evidence, candidates = build_ted_search_artifacts(
            page=page, opportunity_id=opportunity_id
        )
        assert len(evidence) >= 1
        assert len(candidates) >= 1
        first_notice = page.notices[0]

        # 3. Pursuit over HTTP (persisted to PostgreSQL).
        pursuit_ref = f"prs_slice_{uuid4().hex[:10]}"
        created = client.post(
            "/v1/opportunities/pursuits",
            json={
                "pursuit_ref": pursuit_ref,
                "opportunity_ref": opportunity_id,
                "state": "QUALIFIED",
            },
        )
        assert created.status_code == 201, created.text

        transition = client.post(
            f"/v1/opportunities/pursuits/{pursuit_ref}/transition",
            json={"new_state": "DECISION_REVIEW"},
        )
        assert transition.status_code == 200, transition.text
        assert transition.json()["state"] == "DECISION_REVIEW"

        # 4. Workspace over HTTP.
        workspace_id = uuid4()
        workspace = client.post(
            "/v1/opportunities/workspaces",
            json={
                "workspace_id": str(workspace_id),
                "pursuit_ref": pursuit_ref,
                "opportunity_ref": opportunity_id,
                "opportunity_version_digest": page.content_hash,
                "subscriber_profile_version": "v1",
                "assessment_version": "v1",
            },
        )
        assert workspace.status_code == 201, workspace.text

        ws_state = client.post(
            f"/v1/opportunities/workspaces/{workspace_id}/state",
            json={"state": "PREPARING"},
        )
        assert ws_state.status_code == 200
        assert ws_state.json()["state"] == "PREPARING"

        # 5. Outcome + learning over HTTP.
        outcome_ref = f"out_slice_{uuid4().hex[:10]}"
        outcome = client.post(
            "/v1/opportunities/outcomes",
            json={
                "outcome_ref": outcome_ref,
                "pursuit_ref": pursuit_ref,
                "result": "WON",
                "evidence_refs": [evidence[0].evidence_key],
            },
        )
        assert outcome.status_code == 201, outcome.text

        transition_terminal = client.post(
            f"/v1/opportunities/pursuits/{pursuit_ref}/transition",
            json={
                "new_state": "WON",
                "decided_by": "usr_o01_slice",
                "outcome_ref": outcome_ref,
            },
        )
        assert transition_terminal.status_code == 200

        learning_ref = f"lrn_slice_{uuid4().hex[:10]}"
        learning = client.post(
            "/v1/opportunities/learnings",
            json={
                "learning_ref": learning_ref,
                "outcome_ref": outcome_ref,
                "insight": "Frozen TED fixtures enable reproducible ingestion.",
                "evidence_refs": [evidence[0].evidence_key],
            },
        )
        assert learning.status_code == 201, learning.text

        # 6. Portfolio.
        item_ref = f"pf_slice_{uuid4().hex[:10]}"
        portfolio = client.post(
            "/v1/opportunities/portfolio",
            json={
                "item_ref": item_ref,
                "opportunity_ref": opportunity_id,
                "library_id": "O01",
            },
        )
        assert portfolio.status_code == 201

        # 7. Recovery from a NEW session (restart equivalence).
        fresh_client = _client(TENANT_A)
        pursuits = fresh_client.get("/v1/opportunities/pursuits")
        assert pursuits.status_code == 200
        assert any(p["pursuit_ref"] == pursuit_ref for p in pursuits.json())

        ws = fresh_client.get(f"/v1/opportunities/workspaces/{workspace_id}")
        assert ws.status_code == 200
        assert ws.json()["state"] == "PREPARING"

        outcomes = fresh_client.get("/v1/opportunities/outcomes")
        assert any(o["outcome_ref"] == outcome_ref for o in outcomes.json())

        learnings = fresh_client.get("/v1/opportunities/learnings")
        assert any(item["learning_ref"] == learning_ref for item in learnings.json())

        portfolio_list = fresh_client.get("/v1/opportunities/portfolio")
        assert any(i["item_ref"] == item_ref for i in portfolio_list.json())

        # 8. Tenant isolation: TENANT_B sees nothing.
        other_client = _client(TENANT_B, subject="usr_o01_other")
        other_pursuits = other_client.get("/v1/opportunities/pursuits")
        assert all(p["pursuit_ref"] != pursuit_ref for p in other_pursuits.json())
        assert other_client.get(f"/v1/opportunities/workspaces/{workspace_id}").status_code == 404
        other_outcomes = other_client.get("/v1/opportunities/outcomes").json()
        assert all(o["outcome_ref"] != outcome_ref for o in other_outcomes)

        # 9. Notice data is present in the source surface.
        assert first_notice.publication_number.startswith("123456")
