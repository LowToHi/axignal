from __future__ import annotations

from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field, field_validator

from axignal_api.connectors.ted_xml import SOURCE_ID, TEDXMLConnector
from axignal_api.identity import AuthenticatedIdentity, require_identity
from axignal_api.procurement_queue import (
    ProcurementRetrievalOutboxPublisher,
    ValkeyProcurementRetrievalQueue,
)
from axignal_api.procurement_repository import ProcurementAppRepository
from axignal_api.settings import Settings

router = APIRouter(prefix="/v1/research-runs", tags=["procurement-research"])
Authenticated = Annotated[AuthenticatedIdentity, Depends(require_identity)]


class ProcurementResearchRunCreate(BaseModel):
    context_id: str = Field(pattern=r"^ctx_[A-Za-z0-9_-]{8,}$")
    opportunity_id: str = Field(min_length=3, max_length=200)
    question: str = Field(min_length=3, max_length=8_000)
    publication_numbers: list[str] = Field(min_length=1, max_length=4)

    @field_validator("publication_numbers")
    @classmethod
    def validate_publication_numbers(cls, value: list[str]) -> list[str]:
        if len(set(value)) != len(value):
            raise ValueError("publication_numbers must be unique")
        for item in value:
            TEDXMLConnector.validate_publication_number(item)
        return value


class ProcurementResearchRunAccepted(BaseModel):
    research_run_id: UUID
    state: Literal["QUEUED"]
    queue_delivery: Literal["PUBLISHED", "OUTBOX_PENDING"]
    source_ids: list[Literal["src_ted_search_api_v3"]]
    publication_count: int
    raw_xml_persistence: Literal[False] = False
    personal_values_persistence: Literal[False] = False
    synthetic: Literal[False] = False


def _services() -> tuple[ProcurementAppRepository, ProcurementRetrievalOutboxPublisher]:
    settings = Settings.from_env()
    try:
        settings.require_ted_research_api()
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    assert settings.database_url is not None
    assert settings.valkey_url is not None
    repository = ProcurementAppRepository(settings.database_url)
    queue = ValkeyProcurementRetrievalQueue(
        settings.valkey_url,
        queue_key=settings.ted_retrieval_queue_key,
    )
    return repository, ProcurementRetrievalOutboxPublisher(repository, queue)


@router.post(
    "/procurement",
    response_model=ProcurementResearchRunAccepted,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_procurement_research_run(
    command: ProcurementResearchRunCreate,
    identity: Authenticated,
    response: Response,
) -> ProcurementResearchRunAccepted:
    """Create a bounded TED ResearchRun inside the authenticated tenant."""

    repository, publisher = _services()
    publication_numbers = tuple(command.publication_numbers)
    try:
        run_id = repository.create_run(
            tenant_id=identity.tenant_id,
            context_id=command.context_id,
            opportunity_id=command.opportunity_id,
            question=command.question,
            publication_numbers=publication_numbers,
        )
        published = publisher.publish_pending(limit=100)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Procurement research spine unavailable: {exc.__class__.__name__}",
        ) from exc
    response.headers["Location"] = f"/v1/research-runs/{run_id}"
    response.headers["Retry-After"] = "1"
    return ProcurementResearchRunAccepted(
        research_run_id=run_id,
        state="QUEUED",
        queue_delivery="PUBLISHED" if published else "OUTBOX_PENDING",
        source_ids=[SOURCE_ID],
        publication_count=len(publication_numbers),
    )
