from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from fastapi import Response

from axignal_api import axent_routes
from axignal_api.axent_routes import (
    AxentConversationCreate,
    AxentDeletionRequest,
    AxentMessageCreate,
)
from axignal_api.identity import AuthenticatedIdentity


class FakeAxentRepository:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, object]]] = []
        self.conversation_id = uuid4()
        self.message_id = uuid4()
        self.now = datetime.now(UTC)

    def list_conversations(self, **kwargs: object) -> list[dict[str, object]]:
        self.calls.append(("list", kwargs))
        return [
            {
                "conversation_id": self.conversation_id,
                "title": "Persistent AXENT",
                "retention_class": "STANDARD_90D",
                "retention_until": self.now + timedelta(days=90),
                "state": "ACTIVE",
                "message_count": 2,
                "created_at": self.now,
                "updated_at": self.now,
            }
        ]

    def create_conversation(self, **kwargs: object) -> dict[str, object]:
        self.calls.append(("create", kwargs))
        return {
            "conversation_id": self.conversation_id,
            "title": kwargs["title"],
            "retention_class": kwargs["retention_class"],
            "retention_until": self.now + timedelta(days=90),
            "state": "ACTIVE",
            "created_at": self.now,
            "updated_at": self.now,
        }

    def append_message(self, **kwargs: object) -> dict[str, object]:
        self.calls.append(("append", kwargs))
        return {
            "message_id": self.message_id,
            "conversation_id": self.conversation_id,
            "ordinal": 1,
            "message_role": kwargs["message_role"],
            "content_hash": "sha256:" + "a" * 64,
            "created_at": self.now,
        }

    def export_conversation(self, **kwargs: object) -> dict[str, object]:
        self.calls.append(("export", kwargs))
        return {
            "schema": "axignal.axent-conversation-export.v1",
            "conversation_id": self.conversation_id,
            "messages": [],
        }

    def request_deletion(self, **kwargs: object) -> dict[str, object]:
        self.calls.append(("delete", kwargs))
        return {
            "conversation_id": self.conversation_id,
            "state": "DELETION_REQUESTED",
            "retention_until": kwargs["delete_after"],
            "deletion_requested_at": self.now,
        }


def identity() -> AuthenticatedIdentity:
    now = datetime.now(UTC)
    return AuthenticatedIdentity(
        subject="user:axent-owner",
        email="owner@example.test",
        tenant_id=UUID("00000000-0000-4000-8000-000000000042"),
        issued_at=now,
        expires_at=now + timedelta(minutes=1),
    )


def test_axent_routes_propagate_server_resolved_tenant_and_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = FakeAxentRepository()
    monkeypatch.setattr(axent_routes, "_repository", lambda: repository)
    actor = identity()
    response = Response()

    created = axent_routes.create_axent_conversation(
        AxentConversationCreate(
            request_id="axent_req_conversation_0001",
            title="  Persistent AXENT  ",
            retention_class="STANDARD_90D",
        ),
        actor,
        response,
    )
    assert created["conversation_id"] == repository.conversation_id
    assert response.headers["location"].endswith(str(repository.conversation_id))
    create_call = repository.calls[-1][1]
    assert create_call["tenant_id"] == actor.tenant_id
    assert create_call["identity_subject"] == actor.subject
    assert create_call["actor_subject"] == actor.subject
    assert create_call["title"] == "Persistent AXENT"

    message = axent_routes.append_axent_message(
        repository.conversation_id,
        AxentMessageCreate(
            request_id="axent_req_message_00000001",
            role="USER",
            content="  Explain this evidence.  ",
        ),
        actor,
    )
    assert message["message_id"] == repository.message_id
    append_call = repository.calls[-1][1]
    assert append_call["tenant_id"] == actor.tenant_id
    assert append_call["identity_subject"] == actor.subject
    assert append_call["content"] == "Explain this evidence."


def test_axent_routes_list_export_and_request_governed_deletion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = FakeAxentRepository()
    monkeypatch.setattr(axent_routes, "_repository", lambda: repository)
    actor = identity()

    listing = axent_routes.list_axent_conversations(actor)
    assert listing["schema"] == "axignal.axent-conversation-list.v1"
    assert listing["conversations"][0]["conversation_id"] == repository.conversation_id

    exported = axent_routes.get_axent_conversation(repository.conversation_id, actor)
    assert exported["schema"] == "axignal.axent-conversation-export.v1"
    assert repository.calls[-1][1]["identity_subject"] == actor.subject

    deletion = axent_routes.request_axent_conversation_deletion(
        repository.conversation_id,
        AxentDeletionRequest(delete_after=datetime.now(UTC) - timedelta(days=1)),
        actor,
    )
    assert deletion["state"] == "DELETION_REQUESTED"
    delete_call = repository.calls[-1][1]
    assert delete_call["identity_subject"] == actor.subject
    assert delete_call["delete_after"] >= datetime.now(UTC) - timedelta(seconds=2)


def test_axent_idempotency_conflict_is_fail_closed() -> None:
    error = axent_routes._translate_error(RuntimeError("axent_idempotency_conflict"))
    assert error.status_code == 409
    assert "different content" in str(error.detail)


def test_c4_axent_migration_preserves_single_authority_and_exact_ownership() -> None:
    migration = Path("infra/postgres/141-c4-axent-idempotency.sql").read_text()
    assert "ENABLE ROW LEVEL SECURITY" in migration
    assert "FORCE ROW LEVEL SECURITY" in migration
    assert "pg_advisory_xact_lock" in migration
    assert "create_axent_conversation_idempotent" in migration
    assert "append_axent_message_idempotent" in migration
    assert "export_axent_conversation_for_identity" in migration
    assert "request_axent_conversation_deletion_for_identity" in migration
    assert "identity_subject = p_identity_subject" in migration
    assert "REVOKE EXECUTE ON FUNCTION tenant_private.append_axent_message" in migration
    assert "REVOKE EXECUTE ON FUNCTION tenant_private.export_axent_conversation" in migration
    assert "TO axignal_app" in migration
    assert "GRANT SELECT" not in migration


def test_repository_uses_identity_scoped_database_functions_without_list_authorization() -> None:
    source = Path("apps/api/src/axignal_api/axent_repository.py").read_text()
    assert "append_axent_message_idempotent" in source
    assert "export_axent_conversation_for_identity" in source
    assert "request_axent_conversation_deletion_for_identity" in source
    assert "_require_owned_conversation" not in source
