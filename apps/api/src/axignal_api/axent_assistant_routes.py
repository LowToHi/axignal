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
    context_opportunity_ref: str | None = Field(default=None, max_length=200)
    context_pursuit_ref: str | None = Field(default=None, max_length=200)


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
    """Deterministic grounded pipeline with operational intents.

    1. The user message is persisted first.
    2. If a confirmation is pending and the user confirms/rejects, the
       pending operation is executed (or cancelled) and the result is
       answered with the created/updated object.
    3. If the message is an operational order (add to workspace, create
       pursuit, create task, priority, dismiss, compare), the references
       are resolved against the conversation results and a preview is
       issued (invocation PENDING + confirmation token).
    4. Otherwise the standard grounded RAG pipeline answers.
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

    from axignal_api.axent_operations import (
        AxentOperationPipeline,
        detect_intent,
        is_confirmation,
        is_rejection,
        resolve_ordinal_refs,
    )
    from axignal_api.axent_tool_registry import AxentToolExecutor
    from axignal_api.bid_workspace_repository import BidWorkspaceRepository
    from axignal_api.opportunity_repository import OpportunityOperationsRepository

    class _Domain:
        def __init__(self) -> None:
            self.opportunities = OpportunityOperationsRepository(dsn)
            self.bid_workspace = BidWorkspaceRepository(dsn)
            self.retrieval = retrieval

        def plan_for(self, params: dict) -> object:
            return planner.plan(params)

    executor = AxentToolExecutor(domain=_Domain())
    pipeline = AxentOperationPipeline(core=core, executor=executor, dsn=dsn)

    def _assistant_reply(
        text: str, *, operation: dict[str, object] | None = None
    ) -> dict[str, object]:
        assistant = core.append_message(
            tenant_id=identity.tenant_id,
            conversation_id=conversation_id,
            message_role="ASSISTANT",
            content=text,
        )
        response: dict[str, object] = {
            "message": assistant,
            "segments": [{"text": text, "epistemic_class": "RECOMMENDATION",
                          "citations": []}],
            "bundle": {"query_plan": {}, "operation": operation or {}},
        }
        return response

    # 1. Pending confirmation resolution.
    pending = pipeline.pending_confirmation(
        tenant_id=identity.tenant_id, conversation_id=conversation_id
    )
    if pending is not None:
        if is_confirmation(request.content):
            resolved = core.resolve_confirmation(
                tenant_id=identity.tenant_id,
                confirmation_id=pending["confirmation_id"],
                decision="CONFIRMED",
                confirmed_by=identity.subject,
            )
            if resolved.get("state") == "CONFIRMED":
                result = pipeline.execute_tool(
                    tenant_id=identity.tenant_id,
                    actor_subject=identity.subject,
                    conversation_id=conversation_id,
                    tool_name=pending["tool_name"],
                    parameters=dict(pending["parameters_json"]),
                    risk_class=pending["risk_class"],
                )
                receipt = result.get("receipt", result)
                text = (
                    f"Operación confirmada y persistida: "
                    f"{pending['tool_name']} → {receipt}."
                )
                return _assistant_reply(
                    text, operation={"tool_name": pending["tool_name"],
                                     "status": "EXECUTED", "receipt": receipt}
                )
            # Expired: fall through to intent handling.
        elif is_rejection(request.content):
            core.resolve_confirmation(
                tenant_id=identity.tenant_id,
                confirmation_id=pending["confirmation_id"],
                decision="REJECTED",
                confirmed_by=identity.subject,
            )
            return _assistant_reply(
                "Operación cancelada. No se ha modificado nada.",
                operation={"tool_name": pending["tool_name"],
                           "status": "REJECTED"},
            )

    # 2. Operational intent detection.
    intent = detect_intent(request.content)
    if intent is not None:
        tool_name, raw_params = intent
        ordered_refs = pipeline.last_ordered_opportunity_refs(
            tenant_id=identity.tenant_id, conversation_id=conversation_id
        )

        if tool_name in ("add_to_workspace", "create_pursuit",
                         "create_task", "update_internal_priority",
                         "dismiss_opportunity"):
            if tool_name in ("add_to_workspace", "create_pursuit",
                             "dismiss_opportunity"):
                refs = resolve_ordinal_refs(request.content, ordered_refs)
                if not refs:
                    return _assistant_reply(
                        "No encuentro a qué oportunidad te refieres. "
                        "Puedes citar su referencia (ej. opp_ted_123456_2026) "
                        "o pedir una búsqueda antes."
                    )
            else:
                refs = []

            preview_params: dict[str, object] = dict(raw_params)
            if tool_name == "add_to_workspace":
                preview_params["opportunity_refs"] = refs
            elif tool_name == "create_pursuit" or tool_name == "dismiss_opportunity":
                preview_params["opportunity_ref"] = refs[0]

            if tool_name == "update_internal_priority":
                pursuit_refs = [p["pursuit_ref"] for p in
                                executor.domain.opportunities.list_pursuits(
                                    tenant_id=identity.tenant_id)]
                if not pursuit_refs:
                    return _assistant_reply(
                        "No hay pursuits activos para cambiar la prioridad. "
                        "Crea un pursuit primero."
                    )
                preview_params["pursuit_ref"] = pursuit_refs[0]

            if tool_name == "create_task":
                workspaces = executor.domain.opportunities.list_workspaces(
                    tenant_id=identity.tenant_id)
                if not workspaces:
                    return _assistant_reply(
                        "No hay workspaces. Añade primero una oportunidad "
                        "a un workspace."
                    )
                preview_params["workspace_id"] = str(workspaces[0]["workspace_id"])

            # Create the invocation (PENDING) + confirmation preview.
            policy_result = executor.policy_for(tool_name)
            invocation = core.create_invocation(
                tenant_id=identity.tenant_id,
                conversation_id=conversation_id,
                tool_name=tool_name, tool_version="v1",
                parameters=preview_params, risk_class=policy_result.risk_class,
            )
            confirmation = core.create_confirmation(
                tenant_id=identity.tenant_id,
                conversation_id=conversation_id,
                invocation_id=invocation["invocation_id"],
                action_type=tool_name,
                parameters=preview_params,
                before_state_hash="sha256:" + "0" * 64,
            )
            preview = {
                "tool_name": tool_name,
                "parameters": preview_params,
                "confirmation_id": str(confirmation["confirmation_id"]),
                "policy": policy_result.risk_class,
                "requires_confirmation": (
                    policy_result.decision.value == "ALLOW_WITH_CONFIRMATION"
                ),
            }
            text = (
                f"Previsualización de la operación **{tool_name}**: "
                f"{preview_params}. "
                + ("Confirma con «sí» para ejecutarla."
                   if preview["requires_confirmation"]
                   else "Ejecutando ahora (bajo riesgo).")
            )
            if not preview["requires_confirmation"]:
                result = pipeline.execute_tool(
                    tenant_id=identity.tenant_id,
                    actor_subject=identity.subject,
                    conversation_id=conversation_id,
                    tool_name=tool_name,
                    parameters=preview_params,
                    risk_class=policy_result.risk_class,
                )
                receipt = result.get("receipt", result)
                text = (
                    f"Operación ejecutada y persistida: "
                    f"{tool_name} → {receipt}."
                )
                preview["status"] = "EXECUTED"
                preview["receipt"] = receipt
            return _assistant_reply(
                text, operation=preview
            )

        if tool_name == "compare_opportunities":
            refs = resolve_ordinal_refs(request.content, ordered_refs)
            if len(refs) < 2:
                return _assistant_reply(
                    "Necesito al menos dos oportunidades para comparar. "
                    "Haz una búsqueda y dime cuáles (ej. «compara la primera "
                    "y la tercera»)."
                )
            result = pipeline.execute_tool(
                tenant_id=identity.tenant_id,
                actor_subject=identity.subject,
                conversation_id=conversation_id,
                tool_name="compare_opportunities",
                parameters={"opportunity_refs": refs},
                risk_class="READ",
            )
            rows = result.get("rows", [])
            lines = [f"Comparación de {len(rows)} oportunidades:"]
            for row in rows:
                payload = row.get("payload") or {}
                lines.append(
                    f"- {row['opportunity_ref']}: {payload.get('title')} "
                    f"[{row.get('state')}]"
                )
            return _assistant_reply(
                "\n".join(lines),
                operation={"tool_name": "compare_opportunities",
                           "status": "EXECUTED", "rows": rows},
            )

    # 2b. Contextual explanation (requirement 4): when the panel is opened
    # from an Opportunity / Pursuit / Workspace, the user can ask about the
    # object in context without naming it.
    contextual_ref = request.context_opportunity_ref or request.context_pursuit_ref
    if contextual_ref and any(
        word in request.content.casefold()
        for word in ("explícame", "explicame", "explica", "qué es", "que es",
                     "resume", "qué requisitos", "que requisitos",
                     "qué falta", "que falta", "estado", "bloquea")
    ):
        opportunity = executor.domain.opportunities.get_opportunity(
            tenant_id=identity.tenant_id,
            opportunity_ref=request.context_opportunity_ref or contextual_ref,
        )
        pursuit = None
        if request.context_pursuit_ref:
            pursuit = executor.domain.opportunities.get_pursuit(
                tenant_id=identity.tenant_id,
                pursuit_ref=request.context_pursuit_ref,
            )
        lines: list[str] = []
        if opportunity:
            payload = opportunity.get("payload") or {}
            lines.append(
                f"**{payload.get('title') or opportunity['opportunity_ref']}** "
                f"({opportunity['opportunity_ref']}, {opportunity.get('state')})."
            )
            if payload.get("buyer"):
                lines.append(f"Comprador: {payload['buyer']}.")
            if payload.get("description"):
                lines.append(
                    f"Descripción: {str(payload['description'])[:220]}..."
                )
            claims = retrieval.claims_for(
                tenant_id=identity.tenant_id,
                subject_id=opportunity["opportunity_ref"],
            )
            if claims:
                lines.append(
                    f"Reclamaciones admitidas: {len(claims)} "
                    f"(fuente {claims[0].get('source_id', 'verificada')})."
                )
        else:
            lines.append(
                f"No encuentro la oportunidad {contextual_ref} en tu tenant."
            )
        if pursuit:
            lines.append(
                f"Pursuit {pursuit['pursuit_ref']}: estado "
                f"{pursuit.get('state')}, prioridad "
                f"{pursuit.get('priority', 'MEDIUM')}."
            )
        return _assistant_reply(
            "\n".join(lines),
            operation={"tool_name": "explain_context",
                       "status": "EXECUTED",
                       "context": {"opportunity_ref": request.context_opportunity_ref,
                                   "pursuit_ref": request.context_pursuit_ref}},
        )

    # 3. Standard grounded RAG pipeline.
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


class ResolveConfirmationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: str = Field(pattern=r"^(CONFIRMED|REJECTED)$")


@router.post("/confirmations/{confirmation_id}/resolve")
def resolve_confirmation_endpoint(
    confirmation_id: UUID,
    request: ResolveConfirmationRequest,
    identity: Authenticated,
) -> dict[str, object]:
    """Explicit confirmation endpoint (UI buttons).

    Resolves the confirmation and, when CONFIRMED, executes the pending
    invocation through the domain and returns the persisted receipt.
    """
    dsn = _database_url()
    core = AxentCoreRepository(dsn)
    from axignal_api.axent_operations import AxentOperationPipeline
    from axignal_api.axent_tool_registry import AxentToolExecutor
    from axignal_api.bid_workspace_repository import BidWorkspaceRepository
    from axignal_api.opportunity_repository import OpportunityOperationsRepository

    row = core.get_confirmation(
        tenant_id=identity.tenant_id, confirmation_id=confirmation_id
    )
    if row is None:
        raise HTTPException(
            status_code=404,
            detail="confirmation not found or not pending for this tenant",
        )

    class _Domain:
        def __init__(self) -> None:
            self.opportunities = OpportunityOperationsRepository(dsn)
            self.bid_workspace = BidWorkspaceRepository(dsn)

        def plan_for(self, params: dict) -> object:
            return {}

    executor = AxentToolExecutor(domain=_Domain())
    pipeline = AxentOperationPipeline(core=core, executor=executor, dsn=dsn)

    resolved = core.resolve_confirmation(
        tenant_id=identity.tenant_id,
        confirmation_id=confirmation_id,
        decision=request.decision,
        confirmed_by=identity.subject,
    )
    if request.decision == "REJECTED":
        return {
            "confirmation_id": str(confirmation_id),
            "state": "REJECTED",
            "executed": False,
        }
    if resolved.get("state") != "CONFIRMED":
        return {
            "confirmation_id": str(confirmation_id),
            "state": resolved.get("state", "UNKNOWN"),
            "executed": False,
        }
    result = pipeline.execute_tool(
        tenant_id=identity.tenant_id,
        actor_subject=identity.subject,
        conversation_id=row["conversation_id"],
        tool_name=row["tool_name"],
        parameters=dict(row["parameters_json"]),
        risk_class=row["risk_class"],
    )
    return {
        "confirmation_id": str(confirmation_id),
        "state": "CONFIRMED",
        "executed": True,
        "receipt": result.get("receipt", result),
    }


class OnboardingPreferenceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    preference_key: str = Field(min_length=2, max_length=100)
    value: dict = Field(default_factory=dict)


class FirstValueRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: str = Field(min_length=2, max_length=100)


@router.get("/onboarding")
def get_onboarding(identity: Authenticated) -> dict[str, object]:
    """Current onboarding journey state + preferences (persisted)."""
    from axignal_api.axent_onboarding_repository import AxentOnboardingRepository

    repository = AxentOnboardingRepository(_database_url())
    journey = repository.get_or_create_journey(tenant_id=identity.tenant_id)
    return {
        "journey": journey,
        "preferences": repository.preferences(tenant_id=identity.tenant_id),
    }


@router.post("/onboarding/preferences")
def set_onboarding_preference(
    request: OnboardingPreferenceRequest, identity: Authenticated
) -> dict[str, object]:
    """Persist an explicitly confirmed onboarding preference."""
    from axignal_api.axent_onboarding_repository import AxentOnboardingRepository

    repository = AxentOnboardingRepository(_database_url())
    repository.set_preference(
        tenant_id=identity.tenant_id,
        preference_key=request.preference_key,
        value=request.value,
        confirmed_by_subject=identity.subject,
    )
    return {"preference_key": request.preference_key, "persisted": True}


@router.post("/onboarding/first-value")
def record_first_value(
    request: FirstValueRequest, identity: Authenticated
) -> dict[str, object]:
    """Record the first-value milestone (relevant opportunity + action)."""
    from axignal_api.axent_onboarding_repository import AxentOnboardingRepository

    repository = AxentOnboardingRepository(_database_url())
    journey = repository.record_first_value(
        tenant_id=identity.tenant_id, action=request.action
    )
    return {"journey_state": journey.get("state"), "action": request.action}


@router.post("/onboarding/advance")
def advance_onboarding(identity: Authenticated) -> dict[str, object]:
    """Advance the journey to the next canonical state (idempotent)."""
    from axignal_api.axent_onboarding_repository import (
        JOURNEY_STATES,
        AxentOnboardingRepository,
    )

    repository = AxentOnboardingRepository(_database_url())
    current = repository.get_or_create_journey(tenant_id=identity.tenant_id)
    current_state = current.get("state", "CREATED")
    try:
        next_state = JOURNEY_STATES[JOURNEY_STATES.index(current_state) + 1]
    except IndexError:
        next_state = current_state
    advanced = repository.advance_state(
        tenant_id=identity.tenant_id, journey_type="COMPANY", new_state=next_state
    )
    return {"previous_state": current_state, "state": advanced.get("state")}


class CreateSupportCaseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    conversation_id: UUID
    subject: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=5, max_length=2000)
    severity: str = Field(default="S3", pattern=r"^S[1-4]$")


class ResolveSupportCaseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_ref: str = Field(min_length=3, max_length=100)
    action: str = Field(pattern=r"^(OPENED|IN_PROGRESS|RESOLVED|CLOSED)$")
    note: str | None = Field(default=None, max_length=2000)


@router.post("/support/cases")
def create_support_case(
    request: CreateSupportCaseRequest, identity: Authenticated
) -> dict[str, object]:
    """Escalate a conversation to a human support case (round-trip)."""
    from axignal_api.axent_support_repository import AxentSupportRepository

    repository = AxentSupportRepository(_database_url())
    case = repository.create_case(
        tenant_id=identity.tenant_id,
        conversation_id=request.conversation_id,
        subject=request.subject,
        description=request.description,
        severity=request.severity,
        opened_by=identity.subject,
    )
    repository.notify_case_update(
        tenant_id=identity.tenant_id,
        case_ref=case["case_ref"],
        recipient_subject=identity.subject,
        notification_type="CASE_OPENED",
        body=f"Caso {case['case_ref']} abierto (severidad {request.severity}).",
    )
    return {
        "case_ref": case["case_ref"],
        "case_id": str(case["case_id"]),
        "severity": case["severity"],
        "status": "OPENED",
    }


@router.get("/support/cases")
def list_support_cases(
    identity: Authenticated, status: str | None = None
) -> dict[str, object]:
    """List support cases (optionally filtered by status)."""
    from axignal_api.axent_support_repository import AxentSupportRepository

    repository = AxentSupportRepository(_database_url())
    cases = repository.list_cases(tenant_id=identity.tenant_id, status=status)
    return {"cases": cases}


@router.post("/support/cases/resolve")
def resolve_support_case(
    request: ResolveSupportCaseRequest, identity: Authenticated
) -> dict[str, object]:
    """Advance a case (human response) and notify the user."""
    from axignal_api.axent_support_repository import AxentSupportRepository

    repository = AxentSupportRepository(_database_url())
    updated = repository.transition_case(
        tenant_id=identity.tenant_id,
        case_ref=request.case_ref,
        new_status=request.action,
        actor_subject=identity.subject,
        resolution_code=request.note,
    )
    repository.notify_case_update(
        tenant_id=identity.tenant_id,
        case_ref=request.case_ref,
        recipient_subject=identity.subject,
        notification_type="CASE_UPDATE",
        body=request.note or f"Caso {request.case_ref} → {request.action}.",
    )
    return {"case_ref": request.case_ref, "status": updated.get("status", request.action)}
