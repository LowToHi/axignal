from __future__ import annotations

from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field

from axignal_api.connectors.ted import SOURCE_ID
from axignal_api.identity import AuthenticatedIdentity, require_identity
from axignal_api.queue import OutboxPublisher, ValkeyResearchQueue
from axignal_api.settings import Settings
from axignal_api.ted_repository import TEDResearchRepository

router = APIRouter(prefix="/v1", tags=["persistent-ted-research"])
Authenticated = Annotated[AuthenticatedIdentity, Depends(require_identity)]


class PersistentTEDResearchRunCreate(BaseModel):
    context_id: str = Field(pattern=r"^ctx_[A-Za-z0-9_-]{8,}$")
    opportunity_id: str = Field(min_length=3, max_length=200)
    question: str = Field(min_length=3, max_length=8_000)
    include_private_knowledge: Literal[False] = False


class PersistentTEDResearchRunAccepted(BaseModel):
    research_run_id: UUID
    state: Literal["QUEUED"] = "QUEUED"
    queue_delivery: Literal["PUBLISHED", "OUTBOX_PENDING"]
    source_ids: list[Literal["src_ted_search_api_v3"]] = Field(
        default_factory=lambda: [SOURCE_ID]
    )
    job_kind: Literal["TED_PROCUREMENT"] = "TED_PROCUREMENT"
    synthetic: Literal[False] = False


def _services() -> tuple[TEDResearchRepository, OutboxPublisher]:
    settings = Settings.from_env()
    try:
        settings.require_ted_procurement()
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    assert settings.database_url is not None
    assert settings.valkey_url is not None
    repository = TEDResearchRepository(settings.database_url)
    queue = ValkeyResearchQueue(settings.valkey_url, queue_key=settings.queue_key)
    return repository, OutboxPublisher(repository, queue)


@router.post(
    "/research-runs/ted-procurement",
    response_model=PersistentTEDResearchRunAccepted,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_persistent_ted_research_run(
    command: PersistentTEDResearchRunCreate,
    identity: Authenticated,
    response: Response,
) -> PersistentTEDResearchRunAccepted:
    """Queue the admitted bounded TED profile inside the server-resolved tenant."""
    repository, publisher = _services()
    try:
        run_id = repository.create_ted_run(
            tenant_id=identity.tenant_id,
            context_id=command.context_id,
            opportunity_id=command.opportunity_id,
            question=command.question,
        )
        published = publisher.publish_pending(limit=100)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Persistent TED research spine unavailable: {exc.__class__.__name__}",
        ) from exc

    response.headers["Location"] = f"/v1/research-runs/{run_id}"
    response.headers["Retry-After"] = "1"
    return PersistentTEDResearchRunAccepted(
        research_run_id=run_id,
        queue_delivery="PUBLISHED" if published else "OUTBOX_PENDING",
    )
