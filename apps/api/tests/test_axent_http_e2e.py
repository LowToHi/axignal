"""AXENT conversational HTTP E2E (Mandato AXENT — secciones 6-9).

Real HTTP over FastAPI + PostgreSQL: conversation creation, grounded
message pipeline (plan -> retrieve -> compose -> persist -> citations),
standalone RAG query, tools listing, context bundle, health/degradation,
tenant isolation, restart equivalence.
"""

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
DSN = "postgresql://axignal:axignal-local@localhost:5432/axignal"

pytestmark = pytest.mark.skipif(
    not os.environ.get("AXIGNAL_INTEGRATION_TESTS"),
    reason="AXENT HTTP E2E needs a live PostgreSQL",
)


@pytest.fixture(autouse=True)
def _set_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AXIGNAL_DATABASE_URL", DSN)
    monkeypatch.setenv("AXIGNAL_IDENTITY_ASSERTION_SECRET", IDENTITY_SECRET)


def _client(tenant_id: UUID, subject: str = "usr_axent_http") -> TestClient:
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


def _reset() -> None:
    import psycopg

    with psycopg.connect(DSN) as conn, conn.cursor() as cursor:
        cursor.execute("SET session_replication_role = replica")
        cursor.execute(
            "TRUNCATE tenant_private.axent_evaluations, "
            "tenant_private.axent_feedback, tenant_private.axent_notifications, "
            "tenant_private.axent_confirmations, tenant_private.axent_actions, "
            "tenant_private.axent_tool_invocations, "
            "tenant_private.axent_verified_facts, "
            "tenant_private.axent_message_citations, "
            "tenant_private.axent_messages, "
            "tenant_private.axent_conversations CASCADE"
        )
        cursor.execute("SET session_replication_role = origin")
        conn.commit()


class TestAxentHttp:
    def test_conversation_grounded_pipeline(self) -> None:
        _reset()
        client = _client(TENANT_A)

        # Health: explicit capability status.
        health = client.get("/v1/axent/health")
        assert health.status_code == 200
        assert health.json()["mode"] in ("FULL_AI", "DEGRADED_DETERMINISTIC")

        # Create conversation.
        created = client.post(
            "/v1/axent/conversations",
            json={"title": "Licitaciones ciberseguridad ES/PT"},
        )
        assert created.status_code == 201, created.text
        conversation_id = created.json()["conversation_id"]

        # Natural-language message -> grounded pipeline.
        answer = client.post(
            f"/v1/axent/conversations/{conversation_id}/messages",
            json={"content": "Muéstrame licitaciones de ciberseguridad en España."},
        )
        assert answer.status_code == 201, answer.text
        payload = answer.json()
        assert "segments" in payload
        assert "bundle" in payload
        # Grounded: bundle has a query plan; segments carry epistemic classes.
        assert payload["bundle"]["query_plan"]["intent"] == "SEARCH_OPPORTUNITIES"
        classes = {s["epistemic_class"] for s in payload["segments"]}
        assert classes <= {
            "SOURCE_FACT", "CANONICAL_CLAIM", "INFERENCE",
            "RECOMMENDATION", "UNKNOWN", "CONTRADICTION",
        }

        # Both messages persisted with citations where matched.
        messages = client.get(
            f"/v1/axent/conversations/{conversation_id}/messages"
        ).json()
        assert len(messages["messages"]) == 2
        roles = {m["message_role"] for m in messages["messages"]}
        assert roles == {"USER", "ASSISTANT"}

        # Restart equivalence: a fresh client sees the conversation.
        fresh = _client(TENANT_A, subject="usr_axent_http")
        conversations = fresh.get("/v1/axent/conversations").json()
        assert any(c["conversation_id"] == conversation_id for c in conversations)

        # Tenant isolation: B cannot read the conversation.
        other = _client(TENANT_B, subject="usr_axent_b")
        other_messages = other.get(
            f"/v1/axent/conversations/{conversation_id}/messages"
        )
        assert other_messages.status_code == 200
        assert other_messages.json()["messages"] == []

    def test_standalone_query_and_tools(self) -> None:
        _reset()
        client = _client(TENANT_A)

        query = client.post(
            "/v1/axent/query",
            json={"query": "Busca oportunidades de digitalización superiores a 200000 euros.",
                  "limit": 5},
        )
        assert query.status_code == 200, query.text
        assert query.json()["query_plan"]["value_min"] is not None
        assert isinstance(query.json()["results"], list)

        tools = client.get("/v1/axent/tools")
        assert tools.status_code == 200
        tool_names = {t["name"] for t in tools.json()["tools"]}
        assert "search_opportunities" in tool_names
        assert "create_pursuit" in tool_names
        risk_classes = {t["risk_class"] for t in tools.json()["tools"]}
        assert risk_classes <= {
            "READ", "LOW_RISK_REVERSIBLE", "EXPLICIT_CONFIRMATION",
            "STEP_UP_REQUIRED", "HUMAN_ONLY",
        }

    def test_context_endpoint(self) -> None:
        _reset()
        client = _client(TENANT_A)
        context = client.get(
            "/v1/axent/context",
            params={"route": "/opportunity-intelligence/pursuits"},
        )
        assert context.status_code == 200
        body = context.json()
        assert body["identity"]["subject"] == "usr_axent_http"
        assert body["tenant_scope"] == str(TENANT_A)
        assert body["current_route"] == "/opportunity-intelligence/pursuits"
        assert "workspaces" in body
        assert body["permitted_actions"]["submit_official_bid"] is False

    def test_unknown_fields_rejected(self) -> None:
        _reset()
        client = _client(TENANT_A)
        response = client.post(
            "/v1/axent/conversations",
            json={"title": "Hola", "hacked": True},
        )
        assert response.status_code == 422
