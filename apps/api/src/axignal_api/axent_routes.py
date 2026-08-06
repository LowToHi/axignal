from __future__ import annotations

from datetime import UTC, datetime
from os import environ
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field

from axignal_api.axent_repository import AxentRepository
from axignal_api.identity import AuthenticatedIdentity, require_identity

router = APIRouter(prefix="/v1/subscriber-workspace/axent", tags=["axent"])
Authenticated = Annotated[AuthenticatedIdentity, Depends(require_identity)]


class AxentConversationCreate(BaseModel):
    request_id: str = Field(pattern=r"^axent_req_[A-Za-z0-9_-]{8,120}$")
    title: str = Field(min_length=1, max_length=160)
    retention_class: Literal["EPHEMERAL_30D", "STANDARD_90D"] = "STANDARD_90D"


class AxentMessageCreate(BaseModel):
    request_id: str = Field(pattern=r"^axent_req_[A-Za-z0-9_-]{8,120}$")
    role: Literal["USER", "ASSISTANT", "SYSTEM"]
    content: str = Field(min_length=1, max_length=4_000)


class AxentDeletionRequest(BaseModel):
    delete_after: datetime


def _repository() -> AxentRepository:
    database_url = environ.get("AXIGNAL_DATABASE_URL")
    encryption_key = environ.get("AXIGNAL_AXENT_ENCRYPTION_KEY")
    if not database_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AXIGNAL_DATABASE_URL is required",
        )
    if not encryption_key or len(encryption_key.encode("utf-8")) < 32:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AXIGNAL_AXENT_ENCRYPTION_KEY must be at least 32 bytes",
        )
    return AxentRepository(database_url, encryption_key)


def _conversation_view(row: dict[str, object]) -> dict[str, object]:
    return {
        "conversation_id": row["conversation_id"],
        "title": row["title"],
        "retention_class": row["retention_class"],
        "retention_until": row["retention_until"],
        "state": row["state"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _message_view(row: dict[str, object]) -> dict[str, object]:
    return {
        "message_id": row["message_id"],
        "conversation_id": row["conversation_id"],
        "ordinal": row["ordinal"],
        "role": row["message_role"],
        "content_hash": row["content_hash"],
        "created_at": row["created_at"],
    }


def _translate_error(exc: Exception) -> HTTPException:
    text = str(exc)
    if isinstance(exc, LookupError) or "not_found" in text:
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    if "idempotency_conflict" in text:
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Request identifier was already used with different content",
        )
    if "not_active" in text:
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Conversation is not active",
        )
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="AXENT persistence authority is unavailable",
    )


@router.get("/conversations")
def list_axent_conversations(identity: Authenticated) -> dict[str, object]:
    try:
        conversations = _repository().list_conversations(
            tenant_id=identity.tenant_id,
            identity_subject=identity.subject,
        )
    except Exception as exc:
        raise _translate_error(exc) from exc
    return {
        "schema": "axignal.axent-conversation-list.v1",
        "conversations": conversations,
    }


@router.post("/conversations", status_code=status.HTTP_201_CREATED)
def create_axent_conversation(
    command: AxentConversationCreate,
    identity: Authenticated,
    response: Response,
) -> dict[str, object]:
    try:
        conversation = _repository().create_conversation(
            tenant_id=identity.tenant_id,
            identity_subject=identity.subject,
            request_id=command.request_id,
            title=command.title.strip(),
            retention_class=command.retention_class,
            actor_subject=identity.subject,
        )
    except Exception as exc:
        raise _translate_error(exc) from exc
    response.headers["Location"] = (
        f"/v1/subscriber-workspace/axent/conversations/{conversation['conversation_id']}"
    )
    return _conversation_view(conversation)


@router.get("/conversations/{conversation_id}")
def get_axent_conversation(
    conversation_id: UUID,
    identity: Authenticated,
) -> dict[str, object]:
    try:
        return _repository().export_conversation(
            tenant_id=identity.tenant_id,
            identity_subject=identity.subject,
            conversation_id=conversation_id,
            actor_subject=identity.subject,
        )
    except Exception as exc:
        raise _translate_error(exc) from exc


@router.post(
    "/conversations/{conversation_id}/messages",
    status_code=status.HTTP_201_CREATED,
)
def append_axent_message(
    conversation_id: UUID,
    command: AxentMessageCreate,
    identity: Authenticated,
) -> dict[str, object]:
    try:
        message = _repository().append_message(
            tenant_id=identity.tenant_id,
            identity_subject=identity.subject,
            conversation_id=conversation_id,
            request_id=command.request_id,
            message_role=command.role,
            content=command.content.strip(),
            actor_subject=identity.subject,
        )
    except Exception as exc:
        raise _translate_error(exc) from exc
    return _message_view(message)


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_202_ACCEPTED,
)
def request_axent_conversation_deletion(
    conversation_id: UUID,
    command: AxentDeletionRequest,
    identity: Authenticated,
) -> dict[str, object]:
    current = datetime.now(UTC)
    delete_after = command.delete_after
    if delete_after.tzinfo is None:
        delete_after = delete_after.replace(tzinfo=UTC)
    if delete_after < current:
        delete_after = current
    try:
        conversation = _repository().request_deletion(
            tenant_id=identity.tenant_id,
            identity_subject=identity.subject,
            conversation_id=conversation_id,
            delete_after=delete_after,
            actor_subject=identity.subject,
        )
    except Exception as exc:
        raise _translate_error(exc) from exc
    return {
        "conversation_id": conversation["conversation_id"],
        "state": conversation["state"],
        "retention_until": conversation["retention_until"],
        "deletion_requested_at": conversation["deletion_requested_at"],
    }
