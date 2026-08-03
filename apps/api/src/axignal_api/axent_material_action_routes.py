from __future__ import annotations

from typing import Annotated, Any, Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from axignal_api.axent_action_repository import AxentActionRepository
from axignal_api.axent_consent import (
    ConsentError,
    canonical_hash,
    token_hash,
    verify_confirmation_token,
)
from axignal_api.axent_context import AxentContextBuilder
from axignal_api.axent_policy import AxentDecision, decide_tool
from axignal_api.identity import AuthenticatedIdentity, require_identity
from axignal_api.settings import Settings

router = APIRouter(prefix="/v1/axent", tags=["axent-material-actions"])
Authenticated = Annotated[AuthenticatedIdentity, Depends(require_identity)]


class MaterialAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action_type: Literal["archive_workspace"]
    parameters: dict[str, Any]
    confirmation_token: str = Field(min_length=80, max_length=4096)
    idempotency_key: str = Field(min_length=16, max_length=200)


def _workspace_before_state(workspace: dict[str, Any]) -> dict[str, Any]:
    return {
        "workspace_id": str(workspace["workspace_id"]),
        "state": workspace["state"],
        "revision": workspace["revision"],
        "owner_subject": workspace["owner_subject"],
        "research_run_id": str(workspace["research_run_id"]),
        "updated_at": workspace["updated_at"],
    }


@router.post("/conversations/{conversation_id}/actions/material")
def execute_material_action(
    conversation_id: UUID,
    command: MaterialAction,
    identity: Authenticated,
) -> dict[str, Any]:
    settings = Settings.from_env()
    if not settings.database_url:
        raise HTTPException(status_code=503, detail="axent_persistence_unavailable")
    if not settings.identity_assertion_secret:
        raise HTTPException(status_code=503, detail="axent_consent_secret_unavailable")

    repository = AxentActionRepository(settings.database_url)
    conversation = repository.get_conversation(
        tenant_id=identity.tenant_id,
        conversation_id=conversation_id,
    )
    if conversation is None:
        raise HTTPException(status_code=404, detail="support_conversation_not_found")
    context = AxentContextBuilder(settings.database_url).build(
        identity=identity,
        workspace_id=conversation.get("workspace_id"),
        research_run_id=conversation.get("research_run_id"),
    )
    workspace = context.get("workspace")
    if workspace is None:
        raise HTTPException(status_code=404, detail="workspace_not_found")

    entitlement = context["commercial"]["entitlement"] or {}
    policy = decide_tool(
        tool_name=command.action_type,
        role_ids=identity.role_ids,
        entitlement_state=entitlement.get("state") or identity.seat_state,
        assurance_level=identity.assurance_level,
        confirmed=True,
    )
    if policy.decision != AxentDecision.ALLOW:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "axent_material_action_denied",
                "decision": policy.decision.value,
                "reasons": policy.reasons,
            },
        )

    parameters_hash = canonical_hash(command.parameters)
    before_state_hash = canonical_hash(_workspace_before_state(workspace))
    try:
        claims = verify_confirmation_token(
            command.confirmation_token,
            secret=settings.identity_assertion_secret,
            expected_tenant_id=identity.tenant_id,
            expected_conversation_id=conversation_id,
            expected_subject=identity.subject,
            expected_action_type=command.action_type,
            expected_parameters_hash=parameters_hash,
            expected_before_state_hash=before_state_hash,
        )
        workspace_id = UUID(str(command.parameters["workspace_id"]))
    except (ConsentError, KeyError, ValueError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if workspace_id != workspace["workspace_id"]:
        raise HTTPException(status_code=409, detail="workspace_context_mismatch")

    try:
        receipt = repository.archive_workspace(
            tenant_id=identity.tenant_id,
            conversation_id=conversation_id,
            workspace_id=workspace_id,
            subject=identity.subject,
            confirmation_id=claims.confirmation_id,
            confirmation_token_hash=token_hash(command.confirmation_token),
            expected_before_state_hash=before_state_hash,
            parameters=command.parameters,
            idempotency_key=command.idempotency_key,
            correlation_id=f"axent_{uuid4().hex}",
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {
        "schema_version": "axignal.axent-material-action-receipt/v1",
        "decision": policy.decision.value,
        "receipt": receipt,
        "reconciled": True,
    }
