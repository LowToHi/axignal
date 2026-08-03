from __future__ import annotations

from hashlib import sha256
from typing import Annotated, Any, Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, ConfigDict, Field

from axignal_api.concurrent_repository import (
    ConcurrentTEDResearchRepository as TEDResearchRepository,
)
from axignal_api.connectors.ted import SOURCE_ID as TED_SOURCE_ID
from axignal_api.entitlement_repository import EntitlementRepository
from axignal_api.identity import AuthenticatedIdentity, require_identity
from axignal_api.queue import OutboxPublisher, ValkeyResearchQueue
from axignal_api.seat_repository import SeatRepository
from axignal_api.settings import Settings
from axignal_api.subscriber_workspace_repository import SubscriberWorkspaceRepository

router = APIRouter(prefix="/v1/subscriber-workspace", tags=["subscriber-workspace"])
Authenticated = Annotated[AuthenticatedIdentity, Depends(require_identity)]


class ResearchCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=3, max_length=8_000)


class WorkspaceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    research_run_id: UUID


class DocumentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workspace_id: UUID
    title: str = Field(min_length=1, max_length=300)
    body: str = Field(min_length=1, max_length=200_000)


class ExportCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workspace_id: UUID
    document_id: UUID | None = None
    format: Literal["MARKDOWN"] = "MARKDOWN"


def _settings() -> Settings:
    settings = Settings.from_env()
    try:
        settings.require_persistent_research()
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    assert settings.database_url is not None
    return settings


def _repository() -> SubscriberWorkspaceRepository:
    settings = _settings()
    assert settings.database_url is not None
    return SubscriberWorkspaceRepository(settings.database_url)


def _entitlement(identity: AuthenticatedIdentity, database_url: str) -> dict[str, Any] | None:
    try:
        return EntitlementRepository(database_url).current_entitlement(
            tenant_id=identity.tenant_id
        )
    except RuntimeError:
        return None


def _seat_summary(identity: AuthenticatedIdentity, database_url: str) -> dict[str, Any] | None:
    try:
        return SeatRepository(database_url).summary(tenant_id=identity.tenant_id)
    except RuntimeError:
        return None


def _capabilities(identity: AuthenticatedIdentity, entitlement: dict[str, Any] | None) -> list[str]:
    roles = set(identity.role_ids)
    state = str((entitlement or {}).get("state") or identity.seat_state or "READ_ONLY")
    capabilities = ["workspace:view", "audit:view"]
    if state in {"ACTIVE", "TRIAL"}:
        capabilities.extend(["research:create", "workspace:create", "document:create", "export:create"])
    if roles.intersection({"ORGANISATION_OWNER", "ORGANISATION_ADMIN", "B2G_MANAGER", "RESEARCH_OPERATOR"}):
        return capabilities
    return [capability for capability in capabilities if capability in {"workspace:view", "audit:view"}]


@router.get("/bootstrap")
def bootstrap(identity: Authenticated) -> dict[str, Any]:
    settings = _settings()
    assert settings.database_url is not None
    repository = SubscriberWorkspaceRepository(settings.database_url)
    projection = repository.bootstrap(tenant_id=identity.tenant_id)
    entitlement = _entitlement(identity, settings.database_url)
    seats = _seat_summary(identity, settings.database_url)
    return {
        "schema_version": "axignal.subscriber-live-workspace/v1",
        "state": "READY",
        "generated_at": __import__("datetime").datetime.now(
            __import__("datetime").UTC
        ).isoformat(),
        "identity": {
            "subject": identity.subject,
            "email": identity.email,
            "tenant_id": identity.tenant_id,
            "session_id": identity.session_id,
            "assurance_level": identity.assurance_level,
            "roles": list(identity.role_ids),
            "seat_state": identity.seat_state,
            "seat_plan_code": identity.seat_plan_code,
        },
        "organisation": {
            "tenant_id": identity.tenant_id,
            "display_name": f"Organisation {str(identity.tenant_id)[:8]}",
        },
        "entitlement": entitlement,
        "seats": seats,
        "capabilities": _capabilities(identity, entitlement),
        "fixture_boundary": {
            "active": False,
            "mode": "PERSISTENT_REAL_ADAPTER",
            "fallback_allowed": False,
        },
        **projection,
    }


@router.post("/research-runs", status_code=status.HTTP_202_ACCEPTED)
def create_research_run(
    command: ResearchCreate,
    identity: Authenticated,
    response: Response,
) -> dict[str, Any]:
    settings = _settings()
    if not settings.ted_procurement_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="TED procurement runtime is disabled",
        )
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
    publisher = OutboxPublisher(repository, queue)
    context_id = f"ctx_subscriber_{uuid4().hex}"
    opportunity_key = sha256(command.question.strip().encode("utf-8")).hexdigest()[:24]
    opportunity_id = f"opp_ted_query_{opportunity_key}"
    try:
        run_id = repository.create_ted_run(
            tenant_id=identity.tenant_id,
            context_id=context_id,
            opportunity_id=opportunity_id,
            question=command.question.strip(),
        )
        published = publisher.publish_pending(limit=100)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Persistent TED research unavailable: {exc.__class__.__name__}",
        ) from exc
    response.headers["Location"] = f"/v1/research-runs/{run_id}"
    response.headers["Retry-After"] = "1"
    return {
        "research_run_id": run_id,
        "context_id": context_id,
        "opportunity_id": opportunity_id,
        "state": "QUEUED",
        "queue_delivery": "PUBLISHED" if published else "OUTBOX_PENDING",
        "source_ids": [TED_SOURCE_ID],
        "synthetic": False,
    }


@router.post("/workspaces", status_code=status.HTTP_201_CREATED)
def create_workspace(command: WorkspaceCreate, identity: Authenticated) -> dict[str, Any]:
    try:
        workspace = _repository().ensure_workspace(
            tenant_id=identity.tenant_id,
            research_run_id=command.research_run_id,
            actor_subject=identity.subject,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"workspace": workspace}


@router.post("/documents", status_code=status.HTTP_201_CREATED)
def create_document(command: DocumentCreate, identity: Authenticated) -> dict[str, Any]:
    try:
        document = _repository().create_document(
            tenant_id=identity.tenant_id,
            workspace_id=command.workspace_id,
            title=command.title.strip(),
            body=command.body.strip(),
            actor_subject=identity.subject,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"document": document}


@router.post("/exports", status_code=status.HTTP_201_CREATED)
def create_export(command: ExportCreate, identity: Authenticated) -> dict[str, Any]:
    try:
        export = _repository().create_markdown_export(
            tenant_id=identity.tenant_id,
            workspace_id=command.workspace_id,
            document_id=command.document_id,
            actor_subject=identity.subject,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"export": export}


@router.get("/exports/{export_id}/download", response_class=PlainTextResponse)
def download_export(export_id: UUID, identity: Authenticated) -> PlainTextResponse:
    export = _repository().export_content(
        tenant_id=identity.tenant_id,
        export_id=export_id,
    )
    if export is None:
        raise HTTPException(status_code=404, detail="export_not_found")
    return PlainTextResponse(
        str(export["content"]),
        media_type="text/markdown; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename=\"{export['filename']}\"",
            "ETag": f"\"{export['content_hash']}\"",
            "Cache-Control": "private, no-store",
        },
    )
