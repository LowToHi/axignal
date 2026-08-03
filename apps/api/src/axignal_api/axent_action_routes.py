from __future__ import annotations

from typing import Annotated, Any, Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from axignal_api.axent_context import AxentContextBuilder
from axignal_api.axent_policy import AxentDecision, decide_tool
from axignal_api.axent_repository import AxentRepository
from axignal_api.identity import AuthenticatedIdentity, require_identity
from axignal_api.settings import Settings

router = APIRouter(prefix="/v1/axent", tags=["axent-actions"])
Authenticated = Annotated[AuthenticatedIdentity, Depends(require_identity)]


class LowRiskAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action_type: Literal["rename_support_conversation", "reopen_support_case"]
    parameters: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str = Field(min_length=16, max_length=200)


@router.post("/conversations/{conversation_id}/actions/low-risk")
def execute_low_risk_action(
    conversation_id: UUID,
    command: LowRiskAction,
    identity: Authenticated,
) -> dict[str, Any]:
    settings = Settings.from_env()
    if not settings.database_url:
        raise HTTPException(status_code=503, detail="axent_persistence_unavailable")
    repository = AxentRepository(settings.database_url)
    conversation = repository.get_conversation(
        tenant_id=identity.tenant_id,
        conversation_id=conversation_id,
    )
    if conversation is None:
        raise HTTPException(status_code=404, detail="support_conversation_not_found")

    context = AxentContextBuilder(settings.database_url).build(identity=identity)
    entitlement = context["commercial"]["entitlement"] or {}
    policy = decide_tool(
        tool_name=command.action_type,
        role_ids=identity.role_ids,
        entitlement_state=entitlement.get("state") or identity.seat_state,
        assurance_level=identity.assurance_level,
    )
    if policy.decision != AxentDecision.ALLOW:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "axent_low_risk_action_denied",
                "decision": policy.decision.value,
                "reasons": policy.reasons,
            },
        )

    try:
        if command.action_type == "rename_support_conversation":
            intent = str(command.parameters.get("intent") or "").strip()
            if not intent or len(intent) > 200:
                raise ValueError("support_conversation_intent_invalid")
            result = repository.rename_conversation(
                tenant_id=identity.tenant_id,
                conversation_id=conversation_id,
                intent=intent,
            )
        else:
            case_id = UUID(str(command.parameters.get("case_id") or ""))
            result = repository.transition_case(
                tenant_id=identity.tenant_id,
                case_id=case_id,
                actor_subject=identity.subject,
                transition="REOPEN",
            )
    except (LookupError, ValueError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    invocation = repository.record_tool_invocation(
        tenant_id=identity.tenant_id,
        conversation_id=conversation_id,
        tool_name=command.action_type,
        requested_by_subject=identity.subject,
        input_payload=command.parameters,
        decision=policy.decision.value,
        reasons=policy.reasons,
        result_status="SUCCEEDED",
        result={"reconciled": result},
        idempotency_key=command.idempotency_key,
        correlation_id=f"axent_{uuid4().hex}",
    )
    return {
        "schema_version": "axignal.axent-low-risk-action/v1",
        "decision": policy.decision.value,
        "result": result,
        "invocation": invocation,
        "reconciled": True,
    }
