from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict

from axignal_api.identity import AuthenticatedIdentity, require_identity
from axignal_api.retention_config import RetentionSettings
from axignal_api.retention_repository import RetentionRepository

router = APIRouter(prefix="/v1/workspace", tags=["retention"])
Authenticated = Annotated[AuthenticatedIdentity, Depends(require_identity)]


class DeletionRequestCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    confirm_permanent_deletion: Literal[True]


class WorkspaceLifecycleView(BaseModel):
    model_config = ConfigDict(extra="ignore")

    tenant_id: UUID
    deletion_id: UUID | None
    state: Literal[
        "ACTIVE",
        "READ_ONLY",
        "SUSPENDED",
        "DELETION_REQUESTED",
        "RETENTION_HOLD",
        "PURGE_QUEUED",
        "PURGING",
        "PURGE_FAILED",
    ]
    policy_version: str
    reason_code: str | None
    deletion_requested_at: datetime | None
    retention_until: datetime | None
    updated_at: datetime


def _settings_and_repository() -> tuple[RetentionSettings, RetentionRepository]:
    settings = RetentionSettings.from_env()
    try:
        settings.require_store()
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    assert settings.database_url is not None
    return settings, RetentionRepository(settings.database_url)


def _raise_store_error(exc: Exception) -> None:
    message = str(exc)
    known = {
        "workspace_lifecycle_not_found": (
            status.HTTP_404_NOT_FOUND,
            "Workspace lifecycle not found",
        ),
        "retention_deadline_invalid": (
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Retention deadline is invalid",
        ),
        "workspace_purge_requires_operator_review": (
            status.HTTP_409_CONFLICT,
            "Workspace purge requires operator review",
        ),
        "workspace_terminally_deleted": (
            status.HTTP_410_GONE,
            "Workspace has been permanently deleted",
        ),
    }
    for marker, (code, detail) in known.items():
        if marker in message:
            raise HTTPException(status_code=code, detail=detail) from exc
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=f"Retention runtime unavailable: {exc.__class__.__name__}",
    ) from exc


@router.get("/lifecycle", response_model=WorkspaceLifecycleView)
def workspace_lifecycle(identity: Authenticated) -> WorkspaceLifecycleView:
    _, repository = _settings_and_repository()
    row = repository.lifecycle(tenant_id=identity.tenant_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace lifecycle not found",
        )
    return WorkspaceLifecycleView.model_validate(row)


@router.post(
    "/deletion-requests",
    response_model=WorkspaceLifecycleView,
    status_code=status.HTTP_202_ACCEPTED,
)
def request_workspace_deletion(
    command: DeletionRequestCommand,
    identity: Authenticated,
) -> WorkspaceLifecycleView:
    del command
    settings, repository = _settings_and_repository()
    try:
        settings.require_deletion_requests()
        row = repository.request_deletion(
            tenant_id=identity.tenant_id,
            actor_subject=identity.subject,
            retention_seconds=settings.retention_seconds,
        )
    except RuntimeError as exc:
        if "disabled" in str(exc) or "must be configured" in str(exc):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc
        _raise_store_error(exc)
    except Exception as exc:
        _raise_store_error(exc)
    return WorkspaceLifecycleView.model_validate(row)
