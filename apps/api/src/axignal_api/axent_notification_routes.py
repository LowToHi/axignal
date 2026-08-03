from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from axignal_api.axent_notification_repository import AxentNotificationRepository
from axignal_api.identity import AuthenticatedIdentity, require_identity
from axignal_api.settings import Settings

router = APIRouter(prefix="/v1/axent", tags=["axent-notifications"])
Authenticated = Annotated[AuthenticatedIdentity, Depends(require_identity)]


def _repository() -> AxentNotificationRepository:
    settings = Settings.from_env()
    if not settings.database_url:
        raise HTTPException(status_code=503, detail="axent_persistence_unavailable")
    return AxentNotificationRepository(settings.database_url)


@router.get("/notifications")
def list_notifications(identity: Authenticated) -> dict[str, Any]:
    return {
        "schema_version": "axignal.axent-notifications/v1",
        "notifications": _repository().list_notifications(
            tenant_id=identity.tenant_id,
            recipient_subject=identity.subject,
        ),
    }


@router.post("/notifications/{notification_id}/acknowledge")
def acknowledge_notification(
    notification_id: UUID,
    identity: Authenticated,
) -> dict[str, Any]:
    try:
        notification = _repository().acknowledge_notification(
            tenant_id=identity.tenant_id,
            recipient_subject=identity.subject,
            notification_id=notification_id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        "schema_version": "axignal.axent-notification-delivery/v1",
        "notification": notification,
    }
