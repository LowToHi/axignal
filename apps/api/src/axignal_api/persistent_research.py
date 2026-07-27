from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Response, status

from axignal_api.persistent_models import (
    PersistentResearchRunAccepted,
    PersistentResearchRunCreate,
    PersistentResearchRunView,
)
from axignal_api.queue import OutboxPublisher, ValkeyResearchQueue
from axignal_api.repository import ResearchRepository
from axignal_api.settings import Settings

router = APIRouter(prefix="/v1", tags=["persistent-research"])
TenantHeader = Annotated[UUID, Header(alias="X-AXIGNAL-Tenant-ID")]


def _services() -> tuple[ResearchRepository, OutboxPublisher]:
    settings = Settings.from_env()
    try:
        settings.require_persistent_research()
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    assert settings.database_url is not None
    assert settings.valkey_url is not None
    repository = ResearchRepository(settings.database_url)
    queue = ValkeyResearchQueue(settings.valkey_url, queue_key=settings.queue_key)
    return repository, OutboxPublisher(repository, queue)


@router.post(
    "/research-runs",
    response_model=PersistentResearchRunAccepted,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_persistent_research_run(
    command: PersistentResearchRunCreate,
    tenant_id: TenantHeader,
    response: Response,
) -> PersistentResearchRunAccepted:
    """Create a tenant-scoped ResearchRun and publish it through the transactional outbox."""
    repository, publisher = _services()
    try:
        run_id = repository.create_run(
            tenant_id=tenant_id,
            context_id=command.context_id,
            opportunity_id=command.opportunity_id,
            question=command.question,
            include_private_knowledge=command.include_private_knowledge,
        )
        published = publisher.publish_pending(limit=100)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Persistent research spine unavailable: {exc.__class__.__name__}",
        ) from exc

    response.headers["Location"] = f"/v1/research-runs/{run_id}"
    response.headers["Retry-After"] = "1"
    return PersistentResearchRunAccepted(
        research_run_id=run_id,
        state="QUEUED",
        queue_delivery="PUBLISHED" if published else "OUTBOX_PENDING",
        source_ids=["world-bank-wdi"],
    )


@router.get(
    "/research-runs/{research_run_id}",
    response_model=PersistentResearchRunView,
)
def get_persistent_research_run(
    research_run_id: UUID,
    tenant_id: TenantHeader,
) -> PersistentResearchRunView:
    """Read a ResearchRun only inside the caller's tenant RLS context."""
    repository, _ = _services()
    try:
        view = repository.get_run_view(tenant_id=tenant_id, run_id=research_run_id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Persistent research spine unavailable: {exc.__class__.__name__}",
        ) from exc
    if view is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ResearchRun not found")
    return PersistentResearchRunView.model_validate(view)
