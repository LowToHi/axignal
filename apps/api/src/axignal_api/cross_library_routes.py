"""Persistent cross-library graph HTTP API (Prioridad 5)."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from axignal_api.cross_library_repository import CrossLibraryRepository
from axignal_api.identity import AuthenticatedIdentity, require_identity

router = APIRouter(prefix="/v1/cross-library", tags=["cross-library"])
Authenticated = Annotated[AuthenticatedIdentity, Depends(require_identity)]


def _repository() -> CrossLibraryRepository:
    dsn = os.environ.get("AXIGNAL_DATABASE_URL")
    if not dsn:
        raise HTTPException(status_code=503, detail="AXIGNAL_DATABASE_URL is required")
    return CrossLibraryRepository(dsn)


class NodeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node_ref: str = Field(min_length=3, max_length=200)
    library_id: str = Field(pattern=r"^O0[1-9]$")
    entity_type: str = Field(min_length=3, max_length=100)
    label: str = Field(min_length=3, max_length=300)
    payload: dict = Field(default_factory=dict)


class EdgeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    from_ref: str = Field(min_length=3, max_length=200)
    to_ref: str = Field(min_length=3, max_length=200)
    relation: str = Field(min_length=3, max_length=100)
    evidence_refs: list[str] = Field(default_factory=list)
    source_id: str | None = None


class TimelineRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node_ref: str = Field(min_length=3, max_length=200)
    occurred_at: datetime
    event_type: str = Field(min_length=3, max_length=100)
    payload: dict = Field(default_factory=dict)


class ContradictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim_a_ref: str = Field(min_length=3, max_length=200)
    claim_b_ref: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10, max_length=2000)


class HypothesisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hypothesis_ref: str = Field(min_length=3, max_length=200)
    cause_ref: str = Field(min_length=3, max_length=200)
    effect_ref: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10, max_length=2000)
    confidence: str = Field(default="LOW", pattern=r"^(LOW|MEDIUM|HIGH)$")


@router.post("/nodes", status_code=status.HTTP_201_CREATED)
def upsert_node(request: NodeRequest, identity: Authenticated) -> dict[str, object]:
    _repository().upsert_node(
        tenant_id=identity.tenant_id,
        node_ref=request.node_ref,
        library_id=request.library_id,
        entity_type=request.entity_type,
        label=request.label,
        payload=request.payload,
    )
    return {"node_ref": request.node_ref, "created": True}


@router.get("/nodes")
def list_nodes(
    identity: Authenticated, library_id: str | None = None
) -> list[dict[str, object]]:
    return _repository().list_nodes(
        tenant_id=identity.tenant_id, library_id=library_id
    )


@router.post("/edges", status_code=status.HTTP_201_CREATED)
def upsert_edge(request: EdgeRequest, identity: Authenticated) -> dict[str, object]:
    _repository().upsert_edge(
        tenant_id=identity.tenant_id,
        from_ref=request.from_ref,
        to_ref=request.to_ref,
        relation=request.relation,
        evidence_refs=request.evidence_refs,
        source_id=request.source_id,
    )
    return {"edge": f"{request.from_ref} -[{request.relation}]-> {request.to_ref}"}


@router.get("/edges")
def list_edges(
    identity: Authenticated, node_ref: str | None = None
) -> list[dict[str, object]]:
    return _repository().list_edges(
        tenant_id=identity.tenant_id, node_ref=node_ref
    )


@router.post("/sources/{source_id}/quarantine")
def quarantine_source(
    source_id: str, identity: Authenticated
) -> dict[str, object]:
    count = _repository().quarantine_source_edges(
        tenant_id=identity.tenant_id, source_id=source_id
    )
    return {"source_id": source_id, "quarantined_edges": count}


@router.post("/timeline", status_code=status.HTTP_201_CREATED)
def add_timeline_event(
    request: TimelineRequest, identity: Authenticated
) -> dict[str, object]:
    _repository().add_timeline_event(
        tenant_id=identity.tenant_id,
        node_ref=request.node_ref,
        occurred_at=request.occurred_at,
        event_type=request.event_type,
        payload=request.payload,
    )
    return {"node_ref": request.node_ref, "event_type": request.event_type}


@router.get("/timeline")
def timeline(
    identity: Authenticated, node_ref: str | None = None
) -> list[dict[str, object]]:
    return _repository().timeline(
        tenant_id=identity.tenant_id, node_ref=node_ref
    )


@router.post("/contradictions", status_code=status.HTTP_201_CREATED)
def record_contradiction(
    request: ContradictionRequest, identity: Authenticated
) -> dict[str, object]:
    _repository().record_contradiction(
        tenant_id=identity.tenant_id,
        claim_a_ref=request.claim_a_ref,
        claim_b_ref=request.claim_b_ref,
        description=request.description,
    )
    return {"contradiction": f"{request.claim_a_ref} <> {request.claim_b_ref}"}


@router.get("/contradictions")
def list_contradictions(
    identity: Authenticated,
) -> list[dict[str, object]]:
    return _repository().list_contradictions(tenant_id=identity.tenant_id)


@router.post("/hypotheses", status_code=status.HTTP_201_CREATED)
def record_hypothesis(
    request: HypothesisRequest, identity: Authenticated
) -> dict[str, object]:
    _repository().record_hypothesis(
        tenant_id=identity.tenant_id,
        hypothesis_ref=request.hypothesis_ref,
        cause_ref=request.cause_ref,
        effect_ref=request.effect_ref,
        description=request.description,
        confidence=request.confidence,
    )
    return {
        "hypothesis_ref": request.hypothesis_ref,
        "canonical": False,
        "note": "Hypotheses are NEVER canonical; they do not enter the claim ledger.",
    }


@router.get("/hypotheses")
def list_hypotheses(identity: Authenticated) -> list[dict[str, object]]:
    return _repository().list_hypotheses(tenant_id=identity.tenant_id)


@router.get("/nodes/{node_ref}/neighbors")
def neighbors(node_ref: str, identity: Authenticated) -> dict[str, object]:
    return _repository().neighbors(
        tenant_id=identity.tenant_id, node_ref=node_ref
    )


@router.post("/portfolio", status_code=status.HTTP_201_CREATED)
def add_portfolio(
    identity: Authenticated,
) -> dict[str, object]:
    """Placeholder kept for route parity; use /v1/opportunities/portfolio."""
    raise HTTPException(status_code=501, detail="use /v1/opportunities/portfolio")
