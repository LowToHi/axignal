"""Prioridad 2 — pipeline opportunity operations over HTTP + PostgreSQL."""

from __future__ import annotations

import os
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from axignal_api.application import app
from axignal_api.identity import build_identity_assertion

TENANT_A = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
TENANT_B = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
IDENTITY_SECRET = "local-dev-identity-assertion-secret-32-bytes"

pytestmark = pytest.mark.skipif(
    not os.environ.get("AXIGNAL_INTEGRATION_TESTS"),
    reason="needs live PostgreSQL with the O01 chain materialised",
)


def _client(tenant_id: UUID) -> TestClient:
    return TestClient(
        app,
        headers={
            "X-AXIGNAL-Identity-Assertion": build_identity_assertion(
                secret=IDENTITY_SECRET,
                subject="usr_o01_ops",
                email="usr_o01_ops@example.test",
                tenant_id=tenant_id,
            )
        },
    )


class TestPipelineOpportunityOperations:
    def test_qualify_bid_and_no_bid(self) -> None:
        client = _client(TENANT_A)
        ref = "opp_ted_123456_2026"

        response = client.post(
            f"/v1/opportunities/opportunities/{ref}/qualify",
            json={"decision": "BID", "decided_by": "web-user"},
        )
        assert response.status_code == 200, response.text
        assert response.json()["qualification"] == "BID"

        detail = client.get(f"/v1/opportunities/opportunities/{ref}")
        assert detail.status_code == 200
        assert detail.json()["state"] == "QUALIFIED"

        response = client.post(
            f"/v1/opportunities/opportunities/{ref}/qualify",
            json={"decision": "NO_BID", "decided_by": "web-user"},
        )
        assert response.status_code == 200
        detail = client.get(f"/v1/opportunities/opportunities/{ref}")
        assert detail.json()["state"] == "CLOSED"

    def test_opportunity_claims_bundle(self) -> None:
        client = _client(TENANT_A)
        response = client.get(
            "/v1/opportunities/opportunities/opp_ted_123456_2026/claims"
        )
        assert response.status_code == 200
        bundle = response.json()
        assert bundle["notices"], "no notices bound"
        assert bundle["evidence"], "no evidence"
        assert bundle["canonical_claims"], "no canonical claims"

    def test_tenant_isolation_on_opportunities(self) -> None:
        client_a = _client(TENANT_A)
        client_b = _client(TENANT_B)
        refs_a = {item["opportunity_ref"] for item in client_a.get(
            "/v1/opportunities/opportunities"
        ).json()}
        refs_b = {item["opportunity_ref"] for item in client_b.get(
            "/v1/opportunities/opportunities"
        ).json()}
        assert refs_a
        assert refs_a.isdisjoint(refs_b)
        # Tenant B cannot qualify A's opportunity.
        response = client_b.post(
            "/v1/opportunities/opportunities/opp_ted_123456_2026/qualify",
            json={"decision": "BID", "decided_by": "intruder"},
        )
        assert response.status_code == 404

    def test_notices_versioned_list(self) -> None:
        client = _client(TENANT_A)
        response = client.get("/v1/opportunities/notices")
        assert response.status_code == 200
        notices = response.json()
        assert any(n["publication_number"] == "123456-2026" for n in notices)
        assert any(n["current_version"] >= 2 for n in notices)
