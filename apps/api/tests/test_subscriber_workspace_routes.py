from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi.testclient import TestClient

from axignal_api import subscriber_workspace_routes as routes
from axignal_api.application import app
from axignal_api.identity import AuthenticatedIdentity, require_identity

TENANT_ID = UUID("55555555-5555-4555-8555-555555555555")
USER_ID = UUID("55555555-5555-4555-8555-555555555556")
SESSION_ID = UUID("55555555-5555-4555-8555-555555555557")


class _Settings:
    database_url = "postgresql://unused"
    valkey_url = "redis://unused"
    queue_key = "unused"
    ted_procurement_enabled = True

    def require_persistent_research(self) -> None:
        return None

    def require_ted_procurement(self) -> None:
        return None


class _Repository:
    def __init__(self, _database_url: str) -> None:
        pass

    def bootstrap(self, *, tenant_id: UUID):
        assert tenant_id == TENANT_ID
        return {
            "research_runs": [],
            "workspaces": [],
            "documents": [],
            "exports": [],
            "audit": [],
        }


def _identity(
    *, roles: tuple[str, ...], seat_state: str = "ACTIVE"
) -> AuthenticatedIdentity:
    now = datetime.now(UTC)
    return AuthenticatedIdentity(
        subject="usr_workspace_test",
        email="workspace@example.test",
        tenant_id=TENANT_ID,
        issued_at=now,
        expires_at=now + timedelta(minutes=5),
        user_id=USER_ID,
        session_id=SESSION_ID,
        assurance_level="AAL2",
        role_ids=roles,
        seat_state=seat_state,
        seat_plan_code="PROFESSIONAL_MONTHLY",
    )


def test_capabilities_require_active_entitlement_and_write_role() -> None:
    active = {"state": "ACTIVE"}
    read_only = {"state": "READ_ONLY"}
    assert "research:create" in routes._capabilities(
        _identity(roles=("ORG_OWNER",)), active
    )
    assert "research:create" in routes._capabilities(
        _identity(roles=("RESEARCH_OPERATOR",)), active
    )
    assert routes._capabilities(_identity(roles=("VIEWER",)), active) == [
        "workspace:view",
        "audit:view",
    ]
    assert routes._capabilities(
        _identity(roles=("ORG_OWNER",), seat_state="READ_ONLY"), read_only
    ) == ["workspace:view", "audit:view"]


def test_bootstrap_is_persistent_and_has_no_fixture_fallback(monkeypatch) -> None:
    monkeypatch.setattr(routes, "_settings", lambda: _Settings())
    monkeypatch.setattr(routes, "SubscriberWorkspaceRepository", _Repository)
    monkeypatch.setattr(
        routes,
        "_entitlement",
        lambda _identity_value, _database_url: {
            "state": "ACTIVE",
            "plan_code": "PROFESSIONAL_MONTHLY",
        },
    )
    monkeypatch.setattr(routes, "_seat_summary", lambda *_args: {"active_seats": 1})
    app.dependency_overrides[require_identity] = lambda: _identity(
        roles=("ORG_OWNER",)
    )
    try:
        response = TestClient(app).get("/v1/subscriber-workspace/bootstrap")
    finally:
        app.dependency_overrides.pop(require_identity, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["identity"]["tenant_id"] == str(TENANT_ID)
    assert payload["fixture_boundary"] == {
        "active": False,
        "mode": "PERSISTENT_REAL_ADAPTER",
        "fallback_allowed": False,
    }
    assert "research:create" in payload["capabilities"]
    assert payload["research_runs"] == []


def test_write_capability_is_denied_to_viewer(monkeypatch) -> None:
    monkeypatch.setattr(routes, "_settings", lambda: _Settings())
    monkeypatch.setattr(
        routes,
        "_entitlement",
        lambda _identity_value, _database_url: {"state": "ACTIVE"},
    )
    app.dependency_overrides[require_identity] = lambda: _identity(roles=("VIEWER",))
    try:
        response = TestClient(app).post(
            "/v1/subscriber-workspace/documents",
            json={
                "workspace_id": "55555555-5555-4555-8555-555555555558",
                "title": "Denied",
                "body": "A viewer cannot create this document.",
            },
        )
    finally:
        app.dependency_overrides.pop(require_identity, None)

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "subscriber_capability_required:document:create"
    )
