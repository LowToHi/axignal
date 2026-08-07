"""Opportunity Operations HTTP API (Prioridad 1).

Routers over the durable OpportunityOperationsRepository:

- GET    /v1/opportunities/libraries        canonical libraries
- GET    /v1/opportunities/sources          source manifests
- POST   /v1/opportunities/pursuits         create pursuit
- GET    /v1/opportunities/pursuits         list pursuits (tenant)
- POST   /v1/opportunities/pursuits/{ref}/transition
- POST   /v1/opportunities/workspaces       create workspace
- GET    /v1/opportunities/workspaces       list workspaces (tenant)
- GET    /v1/opportunities/workspaces/{id}
- POST   /v1/opportunities/outcomes         create outcome
- GET    /v1/opportunities/outcomes
- POST   /v1/opportunities/learnings        create learning
- GET    /v1/opportunities/learnings
- POST   /v1/opportunities/portfolio        add portfolio item
- GET    /v1/opportunities/portfolio
- GET    /v1/opportunities/manifests/{kind}/{id}
- GET    /v1/opportunities/coverage/{scope_id}
"""

from __future__ import annotations

import os
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from axignal_api.coverage_disclosure import CoverageDisclosure
from axignal_api.identity import AuthenticatedIdentity, require_identity
from axignal_api.library_manifest import (
    LibraryManifest,
    canonical_library_manifests,
)
from axignal_api.o01_procurement import (
    ted_coverage_disclosure,
    ted_profiles,
    ted_source_manifest,
)
from axignal_api.opportunity_repository import OpportunityOperationsRepository
from axignal_api.source_manifest import SourceManifest

router = APIRouter(prefix="/v1/opportunities", tags=["opportunity-operations"])
Authenticated = Annotated[AuthenticatedIdentity, Depends(require_identity)]


def _repository() -> OpportunityOperationsRepository:
    dsn = os.environ.get(
        "AXIGNAL_DATABASE_URL",
        "postgresql://axignal:axignal-local@localhost:5432/axignal",
    )
    return OpportunityOperationsRepository(dsn)


class PursuitCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pursuit_ref: str = Field(pattern=r"^prs_[A-Za-z0-9_-]{8,}$", max_length=200)
    opportunity_ref: str = Field(min_length=3, max_length=200)
    state: str = "QUALIFIED"
    workspace_ref: UUID | None = None


class PursuitTransitionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    new_state: str
    decided_by: str | None = None
    outcome_ref: str | None = None


class WorkspaceCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workspace_id: UUID
    pursuit_ref: str
    opportunity_ref: str
    opportunity_version_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    subscriber_profile_version: str = "v1"
    assessment_version: str = "v1"


class WorkspaceStateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    state: str


class OutcomeCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    outcome_ref: str = Field(pattern=r"^out_[A-Za-z0-9_-]{8,}$", max_length=200)
    pursuit_ref: str
    result: str = Field(pattern=r"^(WON|LOST|WITHDRAWN)$")
    evidence_refs: list[str] = Field(default_factory=list, min_length=1)
    notes: str | None = None


class LearningCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    learning_ref: str = Field(pattern=r"^lrn_[A-Za-z0-9_-]{8,}$", max_length=200)
    outcome_ref: str
    insight: str = Field(min_length=10, max_length=2000)
    evidence_refs: list[str] = Field(default_factory=list, min_length=1)


class PortfolioAddRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item_ref: str = Field(pattern=r"^pf_[A-Za-z0-9_-]{8,}$", max_length=200)
    opportunity_ref: str
    library_id: str = Field(pattern=r"^O0[1-9]$")


# --- Libraries and sources ---------------------------------------------------


@router.get("/libraries", response_model=list[LibraryManifest])
def list_libraries() -> list[LibraryManifest]:
    return canonical_library_manifests()


@router.get("/sources", response_model=list[SourceManifest])
def list_sources() -> list[SourceManifest]:
    return [ted_source_manifest()]


@router.get("/sources/{source_id}", response_model=SourceManifest)
def get_source(source_id: str) -> SourceManifest:
    if source_id != "src_ted_search_api_v3":
        raise HTTPException(status_code=404, detail="unknown source")
    return ted_source_manifest()


@router.get("/sources/{source_id}/profiles")
def get_source_profiles(source_id: str) -> dict[str, object]:
    if source_id != "src_ted_search_api_v3":
        raise HTTPException(status_code=404, detail="unknown source")
    return ted_profiles()


@router.get("/coverage/{scope_id}", response_model=CoverageDisclosure)
def get_coverage(scope_id: str) -> CoverageDisclosure:
    if scope_id == "src_ted_search_api_v3":
        return ted_coverage_disclosure()
    raise HTTPException(status_code=404, detail="unknown coverage scope")


# --- Pursuits ----------------------------------------------------------------


@router.post("/pursuits", status_code=status.HTTP_201_CREATED)
def create_pursuit(
    request: PursuitCreateRequest,
    identity: Authenticated,
) -> dict[str, object]:
    repository = _repository()
    pursuit_id = repository.create_pursuit(
        tenant_id=identity.tenant_id,
        pursuit_ref=request.pursuit_ref,
        opportunity_ref=request.opportunity_ref,
        state=request.state,
        created_by=identity.subject,
        workspace_ref=request.workspace_ref,
    )
    return {"pursuit_id": str(pursuit_id), "pursuit_ref": request.pursuit_ref}


@router.get("/pursuits")
def list_pursuits(identity: Authenticated) -> list[dict[str, object]]:
    return _repository().list_pursuits(tenant_id=identity.tenant_id)


@router.get("/pursuits/{pursuit_ref}")
def get_pursuit(pursuit_ref: str, identity: Authenticated) -> dict[str, object]:
    row = _repository().get_pursuit(tenant_id=identity.tenant_id, pursuit_ref=pursuit_ref)
    if row is None:
        raise HTTPException(status_code=404, detail="pursuit not found")
    return row


@router.post("/pursuits/{pursuit_ref}/transition")
def transition_pursuit(
    pursuit_ref: str,
    request: PursuitTransitionRequest,
    identity: Authenticated,
) -> dict[str, object]:
    try:
        return _repository().transition_pursuit(
            tenant_id=identity.tenant_id,
            pursuit_ref=pursuit_ref,
            new_state=request.new_state,
            decided_by=request.decided_by,
            outcome_ref=request.outcome_ref,
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


# --- Workspaces --------------------------------------------------------------


@router.post("/workspaces", status_code=status.HTTP_201_CREATED)
def create_workspace(
    request: WorkspaceCreateRequest,
    identity: Authenticated,
) -> dict[str, object]:
    _repository().create_workspace(
        tenant_id=identity.tenant_id,
        workspace_id=request.workspace_id,
        pursuit_ref=request.pursuit_ref,
        opportunity_ref=request.opportunity_ref,
        opportunity_version_digest=request.opportunity_version_digest,
        subscriber_profile_version=request.subscriber_profile_version,
        assessment_version=request.assessment_version,
        created_by=identity.subject,
    )
    return {"workspace_id": str(request.workspace_id)}


@router.get("/workspaces")
def list_workspaces(identity: Authenticated) -> list[dict[str, object]]:
    return _repository().list_workspaces(tenant_id=identity.tenant_id)


@router.get("/workspaces/{workspace_id}")
def get_workspace(workspace_id: UUID, identity: Authenticated) -> dict[str, object]:
    row = _repository().get_workspace(
        tenant_id=identity.tenant_id, workspace_id=workspace_id
    )
    if row is None:
        raise HTTPException(status_code=404, detail="workspace not found")
    return row


@router.post("/workspaces/{workspace_id}/state")
def update_workspace_state(
    workspace_id: UUID,
    request: WorkspaceStateRequest,
    identity: Authenticated,
) -> dict[str, object]:
    try:
        return _repository().update_workspace_state(
            tenant_id=identity.tenant_id,
            workspace_id=workspace_id,
            state=request.state,
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


# --- Outcomes and learnings --------------------------------------------------


@router.post("/outcomes", status_code=status.HTTP_201_CREATED)
def create_outcome(
    request: OutcomeCreateRequest,
    identity: Authenticated,
) -> dict[str, object]:
    from datetime import UTC, datetime

    outcome_id = _repository().create_outcome(
        tenant_id=identity.tenant_id,
        outcome_ref=request.outcome_ref,
        pursuit_ref=request.pursuit_ref,
        result=request.result,
        decided_at=datetime.now(UTC),
        evidence_refs=request.evidence_refs,
        notes=request.notes,
    )
    return {"outcome_id": str(outcome_id), "outcome_ref": request.outcome_ref}


@router.get("/outcomes")
def list_outcomes(identity: Authenticated) -> list[dict[str, object]]:
    return _repository().list_outcomes(tenant_id=identity.tenant_id)


@router.post("/learnings", status_code=status.HTTP_201_CREATED)
def create_learning(
    request: LearningCreateRequest,
    identity: Authenticated,
) -> dict[str, object]:
    learning_id = _repository().create_learning(
        tenant_id=identity.tenant_id,
        learning_ref=request.learning_ref,
        outcome_ref=request.outcome_ref,
        insight=request.insight,
        evidence_refs=request.evidence_refs,
    )
    return {"learning_id": str(learning_id), "learning_ref": request.learning_ref}


@router.get("/learnings")
def list_learnings(identity: Authenticated) -> list[dict[str, object]]:
    return _repository().list_learnings(tenant_id=identity.tenant_id)


# --- Portfolio ---------------------------------------------------------------


@router.post("/portfolio", status_code=status.HTTP_201_CREATED)
def add_portfolio_item(
    request: PortfolioAddRequest,
    identity: Authenticated,
) -> dict[str, object]:
    item_id = _repository().add_portfolio_item(
        tenant_id=identity.tenant_id,
        item_ref=request.item_ref,
        opportunity_ref=request.opportunity_ref,
        library_id=request.library_id,
    )
    return {"item_id": str(item_id), "item_ref": request.item_ref}


@router.get("/portfolio")
def list_portfolio(identity: Authenticated) -> list[dict[str, object]]:
    return _repository().list_portfolio(tenant_id=identity.tenant_id)


# --- Manifest states ---------------------------------------------------------


@router.get("/manifests/{kind}/{manifest_id}")
def get_manifest_state(kind: str, manifest_id: str) -> dict[str, object]:
    if kind not in ("library", "source"):
        raise HTTPException(status_code=422, detail="kind must be library|source")
    row = _repository().get_manifest_state(manifest_kind=kind, manifest_id=manifest_id)
    if row is None:
        raise HTTPException(status_code=404, detail="manifest state not found")
    return row
