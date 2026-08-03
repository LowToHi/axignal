from __future__ import annotations

from typing import Annotated, Any, Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from axignal_api.axent_context import AxentContextBuilder
from axignal_api.axent_policy import AxentDecision, decide_tool
from axignal_api.axent_repository import AxentRepository
from axignal_api.identity import AuthenticatedIdentity, require_identity
from axignal_api.settings import Settings

router = APIRouter(prefix="/v1/axent", tags=["axent"])
Authenticated = Annotated[AuthenticatedIdentity, Depends(require_identity)]


class ConversationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    language: str = Field(default="es", min_length=2, max_length=12)
    workspace_id: UUID | None = None
    research_run_id: UUID | None = None


class MessageCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    content: str = Field(min_length=1, max_length=20_000)


class ToolInvoke(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tool_name: str = Field(min_length=1, max_length=120)
    input: dict[str, Any] = Field(default_factory=dict)
    confirmed: bool = False
    idempotency_key: str | None = Field(default=None, max_length=200)


class CaseCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    case_type: Literal[
        "HOW_TO",
        "ACCOUNT_ACCESS",
        "BILLING",
        "SUBSCRIPTION",
        "SEAT_MANAGEMENT",
        "RESEARCH_RUN",
        "SOURCE_DATA",
        "ALERT",
        "EXPORT",
        "DOCUMENT",
        "INTEGRATION",
        "SECURITY",
        "PRIVACY",
        "LEGAL",
        "BUG",
        "SERVICE_INCIDENT",
        "FEATURE_REQUEST",
    ]
    severity: Literal["S0", "S1", "S2", "S3", "S4"] = "S3"
    service_area: str = Field(min_length=1, max_length=120)
    customer_impact: str | None = Field(default=None, max_length=4000)


def _settings() -> Settings:
    settings = Settings.from_env()
    if not settings.database_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="axent_persistence_unavailable",
        )
    return settings


def _repository() -> AxentRepository:
    settings = _settings()
    assert settings.database_url is not None
    return AxentRepository(settings.database_url)


def _citation(
    *,
    authority_type: str,
    authority_id: object,
    authority_version: object,
) -> dict[str, str]:
    return {
        "authority_type": authority_type,
        "authority_id": str(authority_id),
        "authority_version": str(authority_version),
    }


def _answer_from_context(
    question: str,
    context: dict[str, Any],
) -> tuple[str, list[dict[str, str]]]:
    q = question.casefold()
    commercial = context["commercial"]
    entitlement = commercial.get("entitlement") or {}
    seats = commercial.get("seats") or {}

    if any(
        token in q
        for token in ("plan", "suscripción", "suscripcion", "pago", "factura")
    ):
        state = entitlement.get("state") or "UNKNOWN"
        plan = (
            entitlement.get("plan_code")
            or entitlement.get("product_code")
            or "UNKNOWN"
        )
        citations = [
            _citation(
                authority_type="ENTITLEMENT",
                authority_id=context["identity"]["tenant_id"],
                authority_version=entitlement.get("provider_event_id") or "current",
            )
        ]
        answer = (
            f"Tu autoridad comercial actual indica plan {plan} y estado {state}. "
            "Axent no modifica esta autoridad; solo los eventos firmados del "
            "proveedor y la reconciliación controlada pueden hacerlo."
        )
        return answer, citations

    if any(token in q for token in ("asiento", "seat", "usuario", "equipo")):
        citations = [
            _citation(
                authority_type="ENTITLEMENT",
                authority_id=context["identity"]["tenant_id"],
                authority_version="seat-summary/current",
            )
        ]
        answer = (
            f"El resumen de asientos registrado es: {seats}. La disponibilidad "
            "efectiva depende de la autoridad de seats y del entitlement actual."
        )
        return answer, citations

    research_tokens = (
        "investigación",
        "investigacion",
        "research",
        "ejecución",
        "ejecucion",
    )
    if any(token in q for token in research_tokens):
        run = context.get("research_run")
        if run is None:
            return (
                "No encuentro una investigación autorizada vinculada a esta "
                "conversación. Abre Axent desde el ResearchRun concreto.",
                [],
            )
        citations = [
            _citation(
                authority_type="RESEARCH_RUN",
                authority_id=run["research_run_id"],
                authority_version=(
                    run.get("updated_at") or run.get("state") or "current"
                ),
            )
        ]
        answer = (
            f"La investigación está en estado {run.get('state', 'UNKNOWN')}. "
            "El estado procede del runtime persistente de AXIGNAL."
        )
        return answer, citations

    if any(
        token in q
        for token in ("workspace", "documento", "exportación", "exportacion")
    ):
        workspace = context.get("workspace")
        if workspace is None:
            return (
                "No encuentro un workspace autorizado vinculado a esta "
                "conversación. Su creación requiere un ResearchRun completado "
                "y un dossier persistente.",
                [],
            )
        citations = [
            _citation(
                authority_type="WORKSPACE",
                authority_id=workspace["workspace_id"],
                authority_version=workspace.get("revision") or "current",
            )
        ]
        answer = (
            f"El workspace está en estado {workspace.get('state', 'UNKNOWN')} "
            f"y revisión {workspace.get('revision', 'UNKNOWN')}."
        )
        return answer, citations

    return (
        "Puedo ayudarte con cuenta, plan, seats, facturación, ResearchRuns, "
        "workspaces, documentos, exportaciones e incidencias. Para una "
        "respuesta material consultaré autoridades del servidor y citaré su origen.",
        [],
    )


@router.post("/conversations", status_code=status.HTTP_201_CREATED)
def create_conversation(
    command: ConversationCreate,
    identity: Authenticated,
) -> dict[str, Any]:
    conversation = _repository().create_conversation(
        tenant_id=identity.tenant_id,
        opened_by_subject=identity.subject,
        language=command.language,
        workspace_id=command.workspace_id,
        research_run_id=command.research_run_id,
    )
    return {
        "schema_version": "axignal.axent-conversation/v1",
        "conversation": conversation,
    }


@router.get("/conversations/{conversation_id}")
def get_conversation(
    conversation_id: UUID,
    identity: Authenticated,
) -> dict[str, Any]:
    conversation = _repository().get_conversation(
        tenant_id=identity.tenant_id,
        conversation_id=conversation_id,
    )
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="support_conversation_not_found",
        )
    return {
        "schema_version": "axignal.axent-conversation/v1",
        "conversation": conversation,
    }


@router.post(
    "/conversations/{conversation_id}/messages",
    status_code=status.HTTP_201_CREATED,
)
def create_message(
    conversation_id: UUID,
    command: MessageCreate,
    identity: Authenticated,
) -> dict[str, Any]:
    settings = _settings()
    assert settings.database_url is not None
    repository = AxentRepository(settings.database_url)
    conversation = repository.get_conversation(
        tenant_id=identity.tenant_id,
        conversation_id=conversation_id,
    )
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="support_conversation_not_found",
        )
    user_message = repository.append_message(
        tenant_id=identity.tenant_id,
        conversation_id=conversation_id,
        author_type="USER",
        author_subject=identity.subject,
        content=command.content.strip(),
    )
    context = AxentContextBuilder(settings.database_url).build(
        identity=identity,
        workspace_id=conversation.get("workspace_id"),
        research_run_id=conversation.get("research_run_id"),
    )
    answer, citations = _answer_from_context(command.content, context)
    axent_message = repository.append_message(
        tenant_id=identity.tenant_id,
        conversation_id=conversation_id,
        author_type="AXENT",
        author_subject=None,
        content=answer,
        model_id="deterministic-support-router/v1",
        prompt_policy_version="axent-read-only/v1",
    )
    stored_citations = [
        repository.add_citation(
            tenant_id=identity.tenant_id,
            message_id=axent_message["message_id"],
            authority_type=citation["authority_type"],
            authority_id=citation["authority_id"],
            authority_version=citation["authority_version"],
            excerpt=answer,
        )
        for citation in citations
    ]
    return {
        "schema_version": "axignal.axent-response/v1",
        "response_type": "ANSWER",
        "user_message": user_message,
        "message": axent_message,
        "citations": stored_citations,
        "uncertainty": None if citations else "GENERAL_GUIDANCE_ONLY",
        "needs_human": False,
    }


@router.post("/conversations/{conversation_id}/tools")
def invoke_tool(
    conversation_id: UUID,
    command: ToolInvoke,
    identity: Authenticated,
) -> dict[str, Any]:
    settings = _settings()
    assert settings.database_url is not None
    repository = AxentRepository(settings.database_url)
    conversation = repository.get_conversation(
        tenant_id=identity.tenant_id,
        conversation_id=conversation_id,
    )
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="support_conversation_not_found",
        )
    context_builder = AxentContextBuilder(settings.database_url)
    commercial = context_builder.build(identity=identity)["commercial"]
    entitlement = commercial["entitlement"] or {}
    policy = decide_tool(
        tool_name=command.tool_name,
        role_ids=identity.role_ids,
        entitlement_state=entitlement.get("state") or identity.seat_state,
        assurance_level=identity.assurance_level,
        confirmed=command.confirmed,
    )
    result: dict[str, Any] = {}
    result_status = "DENIED"
    if policy.decision == AxentDecision.ALLOW_READ:
        context = context_builder.build(
            identity=identity,
            workspace_id=conversation.get("workspace_id"),
            research_run_id=conversation.get("research_run_id"),
        )
        allowlisted = {
            "get_my_identity": context["identity"],
            "get_my_plan": context["commercial"]["entitlement"],
            "get_my_entitlements": context["commercial"]["entitlement"],
            "get_seat_summary": context["commercial"]["seats"],
            "get_subscription_status": context["commercial"]["entitlement"],
            "get_research_run_status": context["research_run"],
            "get_workspace_status": context["workspace"],
        }
        result = {
            "value": allowlisted.get(command.tool_name),
            "authority": "server",
        }
        result_status = "SUCCEEDED"
    invocation = repository.record_tool_invocation(
        tenant_id=identity.tenant_id,
        conversation_id=conversation_id,
        tool_name=command.tool_name,
        requested_by_subject=identity.subject,
        input_payload=command.input,
        decision=policy.decision.value,
        reasons=policy.reasons,
        result_status=result_status,
        result=result,
        idempotency_key=command.idempotency_key,
        correlation_id=f"axent_{uuid4().hex}",
    )
    return {
        "decision": policy.decision,
        "policy": policy.policy,
        "reasons": policy.reasons,
        "result": result,
        "invocation": invocation,
    }


@router.post(
    "/conversations/{conversation_id}/cases",
    status_code=status.HTTP_201_CREATED,
)
def create_case(
    conversation_id: UUID,
    command: CaseCreate,
    identity: Authenticated,
) -> dict[str, Any]:
    repository = _repository()
    conversation = repository.get_conversation(
        tenant_id=identity.tenant_id,
        conversation_id=conversation_id,
    )
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="support_conversation_not_found",
        )
    case = repository.create_case(
        tenant_id=identity.tenant_id,
        conversation_id=conversation_id,
        case_type=command.case_type,
        severity=command.severity,
        service_area=command.service_area,
        customer_impact=command.customer_impact,
    )
    return {
        "schema_version": "axignal.axent-case/v1",
        "case": case,
        "needs_human": True,
    }
