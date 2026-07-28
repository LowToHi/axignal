from __future__ import annotations

from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field

from axignal_api.identity import AuthenticatedIdentity, require_identity
from axignal_api.proposal_queue import ProposalOutboxPublisher, ValkeyDocumentProposalQueue
from axignal_api.proposal_repository import (
    DOCUMENT_ID,
    SOURCE_ID,
    DocumentProposalRepository,
)
from axignal_api.settings import Settings

router = APIRouter(prefix="/v1", tags=["persistent-document-research"])
Authenticated = Annotated[AuthenticatedIdentity, Depends(require_identity)]


class PersistentDocumentResearchRunCreate(BaseModel):
    context_id: str = Field(pattern=r"^ctx_[A-Za-z0-9_-]{8,}$")
    opportunity_id: str = Field(min_length=3, max_length=200)
    question: str = Field(min_length=3, max_length=8_000)
    include_private_knowledge: Literal[False] = False


class PersistentDocumentResearchRunAccepted(BaseModel):
    research_run_id: UUID
    state: Literal["QUEUED"] = "QUEUED"
    queue_delivery: Literal["PUBLISHED", "OUTBOX_PENDING"]
    source_ids: list[Literal["world-bank-rer41"]] = Field(
        default_factory=lambda: [SOURCE_ID]
    )
    document_id: Literal["doc_world_bank_rer41"] = DOCUMENT_ID
    job_kind: Literal["DOCUMENT_PROPOSAL"] = "DOCUMENT_PROPOSAL"
    synthetic: Literal[False] = False


def _services() -> tuple[DocumentProposalRepository, ProposalOutboxPublisher]:
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
    repository = DocumentProposalRepository(app_dsn=settings.database_url)
    queue = ValkeyDocumentProposalQueue(
        settings.valkey_url,
        queue_key=settings.proposal_queue_key,
    )
    return repository, ProposalOutboxPublisher(repository, queue)


@router.post(
    "/research-runs/document-proposals",
    response_model=PersistentDocumentResearchRunAccepted,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_persistent_document_research_run(
    command: PersistentDocumentResearchRunCreate,
    identity: Authenticated,
    response: Response,
) -> PersistentDocumentResearchRunAccepted:
    """Queue a tenant-scoped document proposal run with no canonical-write path."""
    repository, publisher = _services()
    try:
        run_id = repository.create_run(
            tenant_id=identity.tenant_id,
            context_id=command.context_id,
            opportunity_id=command.opportunity_id,
            question=command.question,
        )
        published = publisher.publish_pending(limit=100)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Persistent document proposal spine unavailable: {exc.__class__.__name__}",
        ) from exc

    response.headers["Location"] = f"/v1/research-runs/{run_id}"
    response.headers["Retry-After"] = "1"
    return PersistentDocumentResearchRunAccepted(
        research_run_id=run_id,
        queue_delivery="PUBLISHED" if published else "OUTBOX_PENDING",
    )
