from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi.testclient import TestClient

from axignal_api import axent_routes as routes
from axignal_api.application import app
from axignal_api.identity import AuthenticatedIdentity, require_identity

TENANT_ID = UUID("77777777-7777-4777-8777-777777777777")
USER_ID = UUID("77777777-7777-4777-8777-777777777778")
SESSION_ID = UUID("77777777-7777-4777-8777-777777777779")
CONVERSATION_ID = UUID("77777777-7777-4777-8777-777777777780")
USER_MESSAGE_ID = UUID("77777777-7777-4777-8777-777777777781")
AXENT_MESSAGE_ID = UUID("77777777-7777-4777-8777-777777777782")
REVISION_ID = UUID("77777777-7777-4777-8777-777777777783")


class _Settings:
    database_url = "postgresql://unused"


class _Repository:
    citations: list[dict[str, object]] = []

    def __init__(self, _database_url: str) -> None:
        pass

    def create_conversation(self, **kwargs):
        assert kwargs["tenant_id"] == TENANT_ID
        return {
            "conversation_id": CONVERSATION_ID,
            "tenant_id": TENANT_ID,
            "language": kwargs["language"],
        }

    def get_conversation(self, *, tenant_id: UUID, conversation_id: UUID):
        assert tenant_id == TENANT_ID
        if conversation_id != CONVERSATION_ID:
            return None
        return {
            "conversation_id": conversation_id,
            "tenant_id": tenant_id,
            "language": "es",
            "workspace_id": None,
            "research_run_id": None,
            "messages": [],
        }

    def append_message(self, **kwargs):
        message_id = (
            USER_MESSAGE_ID if kwargs["author_type"] == "USER" else AXENT_MESSAGE_ID
        )
        return {"message_id": message_id, **kwargs}

    def add_citation(self, **kwargs):
        citation = {"citation_id": REVISION_ID, **kwargs}
        self.citations.append(citation)
        return citation


class _ContextBuilder:
    def __init__(self, _database_url: str) -> None:
        pass

    def build(self, **_kwargs):
        return {
            "identity": {"tenant_id": str(TENANT_ID)},
            "commercial": {"entitlement": None, "seats": None},
            "research_run": None,
            "workspace": None,
        }


class _Knowledge:
    def __init__(self, _database_url: str) -> None:
        pass

    def search(self, **kwargs):
        assert kwargs["tenant_id"] == TENANT_ID
        assert kwargs["language"] == "es"
        return [
            {
                "revision_id": REVISION_ID,
                "document_id": REVISION_ID,
                "title": "Límites de Axent",
                "section_path": "authority/boundaries",
                "content": "Axent no puede modificar entitlements.",
                "content_hash": "sha256:" + "a" * 64,
                "source_authority": "AX-CONTRACT-AXENT-SUPPORT-E2E-v1.0",
                "version": 1,
                "language": "es",
                "rank": 0.8,
            }
        ]


def _identity() -> AuthenticatedIdentity:
    now = datetime.now(UTC)
    return AuthenticatedIdentity(
        subject="usr_axent_test",
        email="axent@example.test",
        tenant_id=TENANT_ID,
        issued_at=now,
        expires_at=now + timedelta(minutes=5),
        user_id=USER_ID,
        session_id=SESSION_ID,
        assurance_level="AAL2",
        role_ids=("ORG_OWNER",),
        seat_state="ACTIVE",
        seat_plan_code="PROFESSIONAL_MONTHLY",
    )


def _install(monkeypatch) -> None:
    _Repository.citations = []
    monkeypatch.setattr(routes, "_settings", lambda: _Settings())
    monkeypatch.setattr(routes, "AxentRepository", _Repository)
    monkeypatch.setattr(routes, "AxentContextBuilder", _ContextBuilder)
    monkeypatch.setattr(routes, "AxentKnowledgeRepository", _Knowledge)
    app.dependency_overrides[require_identity] = _identity


def _uninstall() -> None:
    app.dependency_overrides.pop(require_identity, None)


def test_create_conversation_uses_authenticated_tenant(monkeypatch) -> None:
    _install(monkeypatch)
    try:
        response = TestClient(app).post(
            "/v1/axent/conversations",
            json={"language": "es"},
        )
    finally:
        _uninstall()
    assert response.status_code == 201
    assert response.json()["conversation"]["tenant_id"] == str(TENANT_ID)


def test_message_falls_back_to_approved_knowledge_with_citation(monkeypatch) -> None:
    _install(monkeypatch)
    try:
        response = TestClient(app).post(
            f"/v1/axent/conversations/{CONVERSATION_ID}/messages",
            json={"content": "¿Qué puede hacer Axent?"},
        )
    finally:
        _uninstall()
    assert response.status_code == 201
    payload = response.json()
    assert payload["message"]["content"] == "Axent no puede modificar entitlements."
    assert payload["citations"][0]["authority_type"] == "KNOWLEDGE_REVISION"
    assert payload["uncertainty"] == "PARTIAL_KNOWLEDGE"
    assert _Repository.citations


def test_unknown_conversation_is_not_disclosed(monkeypatch) -> None:
    _install(monkeypatch)
    try:
        response = TestClient(app).get(
            "/v1/axent/conversations/77777777-7777-4777-8777-777777777799"
        )
    finally:
        _uninstall()
    assert response.status_code == 404
    assert response.json()["detail"] == "support_conversation_not_found"
