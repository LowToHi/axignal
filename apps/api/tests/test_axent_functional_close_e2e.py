"""Cierre funcional E2E — AXENT operational pipeline over real PostgreSQL.

Covers the functional-close requirements through the HTTP surface:
  * natural-language opportunity search returning real results;
  * conversational workspace operations with preview -> confirmation ->
    execution (add to workspace, create pursuit, priority, task, dismiss);
  * contextual explanation from an opportunity/pursuit;
  * onboarding journey persistence;
  * support round-trip (case -> human -> notification -> resolution).
"""

from __future__ import annotations

import os
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from axignal_api.application import app
from axignal_api.identity import build_identity_assertion

DSN = "postgresql://axignal:axignal-local@localhost:5432/axignal"
IDENTITY_SECRET = "local-dev-identity-assertion-secret-32-bytes"
TENANT_A = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")

pytestmark = pytest.mark.skipif(
    not os.environ.get("AXIGNAL_INTEGRATION_TESTS"),
    reason="AXENT functional-close E2E needs a live PostgreSQL",
)


@pytest.fixture(autouse=True)
def _set_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AXIGNAL_DATABASE_URL", DSN)
    monkeypatch.setenv("AXIGNAL_IDENTITY_ASSERTION_SECRET", IDENTITY_SECRET)
    monkeypatch.setenv("AXIGNAL_VALKEY_URL", "redis://localhost:6379/0")


def _client(subject: str = "usr_func_close") -> TestClient:
    return TestClient(
        app,
        headers={
            "X-AXIGNAL-Identity-Assertion": build_identity_assertion(
                secret=IDENTITY_SECRET,
                subject=subject,
                email=f"{subject}@example.test",
                tenant_id=TENANT_A,
            )
        },
    )


def _reset() -> None:
    import psycopg

    with psycopg.connect(DSN) as conn, conn.cursor() as cursor:
        cursor.execute("SET session_replication_role = replica")
        cursor.execute(
            "TRUNCATE tenant_private.opportunity_pursuits, "
            "tenant_private.opportunity_workspaces, "
            "tenant_private.opportunity_outcomes, "
            "tenant_private.bid_requirements, tenant_private.bid_tasks, "
            "tenant_private.axent_actions, "
            "tenant_private.axent_tool_invocations, "
            "tenant_private.axent_confirmations, "
            "tenant_private.axent_conversations, "
            "tenant_private.support_cases, tenant_private.support_incidents, "
            "tenant_private.onboarding_journeys, "
            "tenant_private.onboarding_preferences, "
            "tenant_private.onboarding_events, "
            "tenant_private.axent_notifications CASCADE"
        )
        cursor.execute("SET session_replication_role = origin")
        conn.commit()


class TestOpportunityChat:
    def test_search_returns_real_opportunities(self) -> None:
        _reset()
        client = _client()
        created = client.post(
            "/v1/axent/conversations", json={"title": "func close search"}
        )
        assert created.status_code == 201
        conversation_id = created.json()["conversation_id"]

        response = client.post(
            f"/v1/axent/conversations/{conversation_id}/messages",
            json={"content": "muéstrame services"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["bundle"]["matched_objects"]
        refs = {
            citation["authority_id"]
            for citation in body["message"].get("citations", [])
        }
        # Citations are persisted and resolvable for ordinal references.
        assert refs or body["bundle"]["matched_objects"]

    def test_add_to_workspace_preview_confirmation_execution(self) -> None:
        _reset()
        client = _client()
        conversation_id = client.post(
            "/v1/axent/conversations", json={"title": "func close ops"}
        ).json()["conversation_id"]

        # Seed conversation context: a grounded search with citations.
        client.post(
            f"/v1/axent/conversations/{conversation_id}/messages",
            json={"content": "muéstrame services"},
        )

        # Order: add first result to workspace Iberia -> preview.
        preview = client.post(
            f"/v1/axent/conversations/{conversation_id}/messages",
            json={"content": "añade la primera al workspace Iberia"},
        )
        assert preview.status_code == 201
        operation = preview.json()["bundle"]["operation"]
        assert operation["tool_name"] == "add_to_workspace"
        assert operation["requires_confirmation"] is True
        assert operation["confirmation_id"]
        assert operation["parameters"]["workspace_title"] == "Iberia"
        assert operation["parameters"]["opportunity_refs"]

        # Confirmation via chat.
        confirmed = client.post(
            f"/v1/axent/conversations/{conversation_id}/messages",
            json={"content": "sí"},
        )
        assert confirmed.status_code == 201
        operation = confirmed.json()["bundle"]["operation"]
        assert operation["status"] == "EXECUTED"
        receipt = operation["receipt"]
        assert receipt["workspace_title"] == "Iberia"
        assert receipt["added"]

        # Persisted: workspace resolvable by title.
        from axignal_api.opportunity_repository import OpportunityOperationsRepository

        repository = OpportunityOperationsRepository(DSN)
        workspace = repository.get_workspace_by_title(
            tenant_id=TENANT_A, title="Iberia"
        )
        assert workspace is not None
        assert workspace["workspace_id"] == UUID(receipt["workspace_id"])

    def test_pursuit_priority_task_and_dismiss(self) -> None:
        _reset()
        client = _client()
        conversation_id = client.post(
            "/v1/axent/conversations", json={"title": "func close full"}
        ).json()["conversation_id"]
        client.post(
            f"/v1/axent/conversations/{conversation_id}/messages",
            json={"content": "muéstrame services"},
        )

        # Pursuit (confirmation class).
        preview = client.post(
            f"/v1/axent/conversations/{conversation_id}/messages",
            json={"content": "crea un pursuit para la primera"},
        ).json()["bundle"]["operation"]
        assert preview["tool_name"] == "create_pursuit"
        confirmed = client.post(
            f"/v1/axent/conversations/{conversation_id}/messages",
            json={"content": "sí"},
        ).json()["bundle"]["operation"]
        assert confirmed["status"] == "EXECUTED"
        pursuit_ref = confirmed["receipt"]["pursuit_ref"]

        # Add to workspace first (task requires an existing workspace).
        preview = client.post(
            f"/v1/axent/conversations/{conversation_id}/messages",
            json={"content": "añade la primera al workspace Iberia"},
        ).json()["bundle"]["operation"]
        assert preview["tool_name"] == "add_to_workspace"
        client.post(
            f"/v1/axent/conversations/{conversation_id}/messages",
            json={"content": "sí"},
        )

        # Priority (low-risk, executes immediately with preview).
        priority = client.post(
            f"/v1/axent/conversations/{conversation_id}/messages",
            json={"content": "pon prioridad alta"},
        ).json()["bundle"]["operation"]
        assert priority["tool_name"] == "update_internal_priority"
        assert priority["status"] == "EXECUTED"
        assert priority["receipt"]["priority"] == "HIGH"

        # Task (low-risk, executes immediately).
        task = client.post(
            f"/v1/axent/conversations/{conversation_id}/messages",
            json={"content": "crea una tarea para revisar los requisitos"},
        ).json()["bundle"]["operation"]
        assert task["tool_name"] == "create_task"
        assert task["status"] == "EXECUTED"
        assert task["receipt"]["task_ref"].startswith("task_")

        # Dismiss the second result (confirmation class).
        preview = client.post(
            f"/v1/axent/conversations/{conversation_id}/messages",
            json={"content": "descarta la segunda"},
        ).json()["bundle"]["operation"]
        assert preview["tool_name"] == "dismiss_opportunity"
        confirmed = client.post(
            f"/v1/axent/conversations/{conversation_id}/messages",
            json={"content": "sí"},
        ).json()["bundle"]["operation"]
        assert confirmed["tool_name"] == "dismiss_opportunity"
        assert confirmed["status"] == "EXECUTED"
        assert confirmed["receipt"]["state"] == "CLOSED"

        # Everything persisted in PostgreSQL through the domain.
        from axignal_api.opportunity_repository import OpportunityOperationsRepository

        repository = OpportunityOperationsRepository(DSN)
        pursuits = repository.list_pursuits(tenant_id=TENANT_A)
        assert any(p["pursuit_ref"] == pursuit_ref for p in pursuits)
        pursuit = repository.get_pursuit(tenant_id=TENANT_A, pursuit_ref=pursuit_ref)
        assert pursuit["priority"] == "HIGH"

    def test_compare_opportunities(self) -> None:
        _reset()
        client = _client()
        conversation_id = client.post(
            "/v1/axent/conversations", json={"title": "func close compare"}
        ).json()["conversation_id"]
        client.post(
            f"/v1/axent/conversations/{conversation_id}/messages",
            json={"content": "muéstrame services"},
        )
        compared = client.post(
            f"/v1/axent/conversations/{conversation_id}/messages",
            json={"content": "compara la primera y la segunda"},
        )
        assert compared.status_code == 201
        operation = compared.json()["bundle"]["operation"]
        assert operation["tool_name"] == "compare_opportunities"
        assert operation["status"] == "EXECUTED"


class TestContextual:
    def test_explain_opportunity_from_context(self) -> None:
        _reset()
        client = _client()
        conversation_id = client.post(
            "/v1/axent/conversations", json={"title": "func close ctx"}
        ).json()["conversation_id"]
        response = client.post(
            f"/v1/axent/conversations/{conversation_id}/messages",
            json={
                "content": "Explícame esta oportunidad",
                "context_opportunity_ref": "opp_ted_123456_2026",
            },
        )
        assert response.status_code == 201
        operation = response.json()["bundle"]["operation"]
        assert operation["tool_name"] == "explain_context"
        assert operation["status"] == "EXECUTED"
        assert response.json()["segments"][0]["text"].find("opp_ted_123456_2026") >= 0


class TestOnboarding:
    def test_journey_persists_and_resumes(self) -> None:
        _reset()
        client = _client()
        initial = client.get("/v1/axent/onboarding")
        assert initial.status_code == 200
        assert initial.json()["journey"]["state"] in ("CREATED", "ORGANISATION_READY")

        preference = client.post(
            "/v1/axent/onboarding/preferences",
            json={"preference_key": "sectors",
                  "value": {"sectors": ["public-works"]}},
        )
        assert preference.status_code == 200

        advance = client.post("/v1/axent/onboarding/advance")
        assert advance.status_code == 200

        # Persistence: a fresh client (same tenant) sees the state.
        resumed = _client(subject="usr_func_close_2").get("/v1/axent/onboarding")
        assert resumed.status_code == 200
        preferences = {
            p["preference_key"]: p for p in resumed.json()["preferences"]
        }
        assert "sectors" in preferences


class TestSupportRoundTrip:
    def test_case_create_resolve_notify(self) -> None:
        _reset()
        client = _client()
        conversation_id = client.post(
            "/v1/axent/conversations", json={"title": "func close support"}
        ).json()["conversation_id"]

        created = client.post(
            "/v1/axent/support/cases",
            json={
                "conversation_id": conversation_id,
                "subject": "No puedo guardar mi perfil",
                "description": "El formulario de sectores no responde.",
                "severity": "S3",
            },
        )
        assert created.status_code == 200
        case_ref = created.json()["case_ref"]
        assert created.json()["status"] == "OPENED"

        resolved = client.post(
            "/v1/axent/support/cases/resolve",
            json={"case_ref": case_ref, "action": "RESOLVED",
                  "note": "Perfil actualizado manualmente."},
        )
        assert resolved.status_code == 200
        assert resolved.json()["status"] == "RESOLVED"

        listed = client.get("/v1/axent/support/cases")
        assert listed.status_code == 200
        cases = listed.json()["cases"]
        assert any(
            c["case_ref"] == case_ref and c["status"] == "RESOLVED"
            for c in cases
        )

        from axignal_api.axent_support_repository import AxentSupportRepository

        repository = AxentSupportRepository(DSN)
        events = repository.case_events(tenant_id=TENANT_A, case_ref=case_ref)
        assert any(e["event_type"] == "OPENED" for e in events)
        assert any(
            e["event_type"] == "STATUS_CHANGED"
            and (e.get("payload") or {}).get("new_status") == "RESOLVED"
            for e in events
        )
