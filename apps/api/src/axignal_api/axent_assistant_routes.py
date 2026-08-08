"""AXENT assistant HTTP API (Mandato AXENT — secciones 6-9).

Prefix /v1/axent — the conversational assistant surface:

/health: explicit capability status (degradation, never silent)
/conversations: persistent conversations (AxentCoreRepository)
/conversations/{id}/messages: grounded message pipeline
/query: standalone RAG query
/tools: typed tool registry with risk classes
/context: server-authoritative context bundle

The legacy C4 surface (/v1/subscriber-workspace/axent) remains untouched
in axent_routes.py.
"""

from __future__ import annotations

import os
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from axignal_api.axent_context import AxentContextBuilder, AxentDegradation
from axignal_api.axent_core_repository import AxentCoreRepository
from axignal_api.axent_evidence_bundle import (
    AxentRanker,
    EvidenceBundle,
    GroundedResponseComposer,
)
from axignal_api.axent_query_planner import QueryPlanError, QueryPlanner
from axignal_api.axent_retrieval_repository import AxentRetrievalRepository
from axignal_api.identity import AuthenticatedIdentity, require_identity

router = APIRouter(prefix="/v1/axent", tags=["axent"])
Authenticated = Annotated[AuthenticatedIdentity, Depends(require_identity)]


def _database_url() -> str:
    dsn = os.environ.get("AXIGNAL_DATABASE_URL")
    if not dsn:
        raise HTTPException(status_code=503, detail="AXIGNAL_DATABASE_URL is required")
    return dsn


class CreateConversationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=3, max_length=200)
    retention_class: str = Field(
        default="STANDARD_90D", pattern=r"^(EPHEMERAL_30D|STANDARD_90D)$"
    )


class AppendMessageRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str = Field(min_length=1, max_length=2000)


class QueryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1, max_length=2000)
    limit: int = Field(default=10, ge=1, le=50)


@router.get("/health")
def axent_health(identity: Authenticated) -> dict[str, object]:
    model_available = os.environ.get("AXENT_MODEL_PROVIDER_AVAILABLE", "true") == "true"
    return AxentDegradation().status(model_available=model_available)


@router.post("/conversations", status_code=status.HTTP_201_CREATED)
def create_conversation(
    request: CreateConversationRequest, identity: Authenticated
) -> dict[str, object]:
    return AxentCoreRepository(_database_url()).create_conversation(
        tenant_id=identity.tenant_id,
        identity_subject=identity.subject,
        title=request.title,
        retention_class=request.retention_class,
    )


@router.get("/conversations")
def list_conversations(identity: Authenticated) -> list[dict[str, object]]:
    return AxentCoreRepository(_database_url()).list_conversations(
        tenant_id=identity.tenant_id, subject=identity.subject
    )


@router.get("/conversations/{conversation_id}/messages")
def get_messages(
    conversation_id: UUID, identity: Authenticated
) -> dict[str, object]:
    repository = AxentCoreRepository(_database_url())
    messages = repository.get_messages(
        tenant_id=identity.tenant_id, conversation_id=conversation_id
    )
    return {"conversation_id": str(conversation_id), "messages": messages}


@router.post(
    "/conversations/{conversation_id}/messages",
    status_code=status.HTTP_201_CREATED,
)
def append_message(
    conversation_id: UUID,
    request: AppendMessageRequest,
    identity: Authenticated,
) -> dict[str, object]:
    """Deterministic grounded pipeline: plan -> retrieve -> compose.

    The user message is persisted first; the assistant answer is built
    ONLY from the evidence bundle. When the model provider is
    unavailable the same deterministic path still answers (degraded
    but grounded).
    """
    dsn = _database_url()
    core = AxentCoreRepository(dsn)
    retrieval = AxentRetrievalRepository(dsn)
    planner = QueryPlanner()

    core.append_message(
        tenant_id=identity.tenant_id,
        conversation_id=conversation_id,
        message_role="USER",
        content=request.content,
    )

    try:
        plan = planner.from_natural_language(request.content)
    except QueryPlanError:
        plan = planner.plan(
            {
                "intent": "SEARCH_OPPORTUNITIES",
                "keywords": [request.content[:100]],
                "limit": 5,
            },
            original_query=request.content,
        )

    objects = retrieval.search_opportunities(tenant_id=identity.tenant_id, plan=plan)
    ranked = AxentRanker().rank(objects=objects, plan=plan.as_dict())

    missing = tuple(
        item for result in ranked for item in result.missing_information
    )
    bundle = EvidenceBundle(
        query_plan=plan.as_dict(),
        matched_objects=tuple(objects),
        claims=tuple(
            retrieval.claims_for(
                tenant_id=identity.tenant_id,
                subject_id=objects[0]["opportunity_ref"] if objects else "none",
            )
        ),
        evidence=tuple(
            retrieval.evidence_for(
                tenant_id=identity.tenant_id,
                subject_id=objects[0]["opportunity_ref"] if objects else "none",
            )
        ),
        contradictions=tuple(
            retrieval.contradictions(tenant_id=identity.tenant_id)
        ),
        source_status=tuple(retrieval.source_status(tenant_id=identity.tenant_id)),
        coverage="PARTIAL",
        ranking=tuple(ranked),
        missing_information=missing or ("no matches",),
        tenant_context={"subject": identity.subject},
        permitted_actions=(
            "search_opportunities", "create_pursuit", "create_task",
            "get_opportunity",
        ),
    )

    response = GroundedResponseComposer().compose(
        bundle=bundle, user_query=request.content
    )
    segments_text = " ".join(
        segment["text"] for segment in response["segments"]
    )
    assistant = core.append_message(
        tenant_id=identity.tenant_id,
        conversation_id=conversation_id,
        message_role="ASSISTANT",
        content=segments_text,
        citations=[
            {
                "authority_type": "OPPORTUNITY",
                "authority_id": result.object_ref,
                "authority_version": "v1",
                "excerpt": result.title,
            }
            for result in ranked[:5]
        ],
    )
    return {
        "message": assistant,
        "segments": response["segments"],
        "bundle": response["bundle"],
    }


@router.post("/query")
def natural_language_query(
    request: QueryRequest, identity: Authenticated
) -> dict[str, object]:
    """Standalone RAG query (no conversation persistence)."""
    dsn = _database_url()
    retrieval = AxentRetrievalRepository(dsn)
    planner = QueryPlanner()
    plan = planner.from_natural_language(request.query)
    objects = retrieval.search_opportunities(
        tenant_id=identity.tenant_id, plan=plan
    )
    return {
        "query_plan": plan.as_dict(),
        "results": [
            {
                "opportunity_ref": obj["opportunity_ref"],
                "library_id": obj["library_id"],
                "state": obj["state"],
                "title": (obj.get("payload") or {}).get("title"),
            }
            for obj in objects[: request.limit]
        ],
    }


@router.get("/tools")
def list_tools(identity: Authenticated) -> dict[str, object]:
    from axignal_api import axent_policy as policy_module

    all_tools = (
        policy_module.READ_TOOLS | policy_module.LOW_RISK_TOOLS
        | policy_module.CONFIRMATION_TOOLS | policy_module.STEP_UP_TOOLS
        | policy_module.HUMAN_ONLY_TOOLS
    )
    policy = policy_module.AxentPolicyEngine()
    return {
        "tools": [
            {"name": name, "risk_class": policy.classify(name).risk_class}
            for name in sorted(all_tools)
        ]
    }


@router.get("/context")
def build_context(
    identity: Authenticated,
    route: str | None = None,
    opportunity_ref: str | None = None,
    pursuit_ref: str | None = None,
) -> dict[str, object]:
    return AxentContextBuilder(_database_url()).build(
        identity=identity,
        current_route=route,
        opportunity_ref=opportunity_ref,
        pursuit_ref=pursuit_ref,
    )
