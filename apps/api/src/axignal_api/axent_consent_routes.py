from __future__ import annotations

from datetime import timedelta
from typing import Annotated, Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from axignal_api.axent_consent import (
    canonical_hash,
    issue_confirmation_token,
    token_hash,
)
from axignal_api.axent_context import AxentContextBuilder
from axignal_api.axent_policy import AxentDecision, decide_tool
from axignal_api.axent_repository import AxentRepository
from axignal_api.identity import AuthenticatedIdentity, require_identity
from axignal_api.settings import Settings

router = APIRouter(prefix="/v1/axent", tags=["axent-consent"])
Authenticated = Annotated[AuthenticatedIdentity, Depends(require_identity)]


class ConfirmationPreview(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action_type: str = Field(min_length=1, max_length=120)
    parameters: dict[str, Any] = Field(default_factory=dict)


def _before_state(
    command: ConfirmationPreview,
    context: dict[str, Any],
) -> dict[str, Any]:
    if command.action_type in {"archive_workspace", "restore_workspace"}:
        workspace = context.get("workspace")
        if workspace is None:
            raise HTTPException(status_code=404, detail="workspace_not_found")
        requested_workspace = str(command.parameters.get("workspace_id") or "")
        if requested_workspace != str(workspace["workspace_id"]):
            raise HTTPException(status_code=409, detail="workspace_context_mismatch")
        return {
            "workspace_id": str(workspace["workspace_id"]),
            "state": workspace["state"],
            "revision": workspace["revision"],
            "owner_subject": workspace["owner_subject"],
            "research_run_id": str(workspace["research_run_id"]),
            "updated_at": workspace["updated_at"],
        }
    return {
        "commercial": context["commercial"],
        "workspace": context.get("workspace"),
        "research_run": context.get("research_run"),
    }


@router.post(
    "/conversations/{conversation_id}/confirmations",
    status_code=status.HTTP_201_CREATED,
)
def create_confirmation(
    conversation_id: UUID,
    command: ConfirmationPreview,
    identity: Authenticated,
) -> dict[str, Any]:
    settings = Settings.from_env()
    if not settings.database_url:
        raise HTTPException(status_code=503, detail="axent_persistence_unavailable")
    if not settings.identity_assertion_secret:
        raise HTTPException(status_code=503, detail="axent_consent_secret_unavailable")

    repository = AxentRepository(settings.database_url)
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
    entitlement = context["commercial"]["entitlement"] or {}
    policy = decide_tool(
        tool_name=command.action_type,
        role_ids=identity.role_ids,
        entitlement_state=entitlement.get("state") or identity.seat_state,
        assurance_level=identity.assurance_level,
        confirmed=False,
    )
    if policy.decision == AxentDecision.REQUIRE_STEP_UP_AUTH:
        raise HTTPException(status_code=403, detail="axent_step_up_auth_required")
    if policy.decision != AxentDecision.ALLOW_WITH_CONFIRMATION:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "axent_confirmation_not_permitted",
                "decision": policy.decision.value,
                "reasons": policy.reasons,
            },
        )

    parameters_hash = canonical_hash(command.parameters)
    before_state = _before_state(command, context)
    before_state_hash = canonical_hash(before_state)
    confirmation_id = uuid4()
    token, claims = issue_confirmation_token(
        confirmation_id=confirmation_id,
        tenant_id=identity.tenant_id,
        conversation_id=conversation_id,
        subject=identity.subject,
        action_type=command.action_type,
        parameters_hash=parameters_hash,
        before_state_hash=before_state_hash,
        assurance_level=str(identity.assurance_level),
        secret=settings.identity_assertion_secret,
        lifetime=timedelta(minutes=5),
    )
    repository.create_confirmation(
        confirmation_id=confirmation_id,
        tenant_id=identity.tenant_id,
        conversation_id=conversation_id,
        requested_by_subject=identity.subject,
        action_type=command.action_type,
        parameters_hash=parameters_hash,
        before_state_hash=before_state_hash,
        token_hash=token_hash(token),
        assurance_level=str(identity.assurance_level),
        expires_at=claims.expires_at,
    )
    return {
        "schema_version": "axignal.axent-confirmation/v1",
        "confirmation_token": token,
        "confirmation_id": confirmation_id,
        "action_type": command.action_type,
        "parameters": command.parameters,
        "parameters_hash": parameters_hash,
        "before_state_hash": before_state_hash,
        "expires_at": claims.expires_at,
        "warning": "This token authorizes exactly the previewed action once.",
    }
