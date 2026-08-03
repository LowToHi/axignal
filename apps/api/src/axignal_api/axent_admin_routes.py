from __future__ import annotations

from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from axignal_api.axent_repository import AxentRepository
from axignal_api.identity import AuthenticatedIdentity, require_identity
from axignal_api.settings import Settings

router = APIRouter(prefix="/v1/axent-admin", tags=["axent-admin"])
Authenticated = Annotated[AuthenticatedIdentity, Depends(require_identity)]


class CaseTransition(BaseModel):
    model_config = ConfigDict(extra="forbid")
    transition: Literal["ACKNOWLEDGE", "ASSIGN", "RESOLVE", "REOPEN", "CLOSE"]
    resolution: str | None = Field(default=None, max_length=20_000)


def _repository_and_authorize(
    identity: AuthenticatedIdentity,
) -> AxentRepository:
    settings = Settings.from_env()
    if not settings.database_url:
        raise HTTPException(status_code=503, detail="axent_persistence_unavailable")
    if identity.subject not in settings.human_reviewer_subjects:
        raise HTTPException(status_code=403, detail="axent_human_authority_required")
    if identity.assurance_level not in {"AAL2", "PHISHING_RESISTANT"}:
        raise HTTPException(status_code=403, detail="axent_step_up_auth_required")
    return AxentRepository(settings.database_url)


@router.get("/cases")
def list_cases(identity: Authenticated) -> dict[str, Any]:
    repository = _repository_and_authorize(identity)
    return {
        "schema_version": "axignal.axent-admin-cases/v1",
        "cases": repository.list_open_cases(tenant_id=identity.tenant_id),
    }


@router.post("/cases/{case_id}/transition")
def transition_case(
    case_id: UUID,
    command: CaseTransition,
    identity: Authenticated,
) -> dict[str, Any]:
    repository = _repository_and_authorize(identity)
    try:
        case = repository.transition_case(
            tenant_id=identity.tenant_id,
            case_id=case_id,
            actor_subject=identity.subject,
            transition=command.transition,
            resolution=command.resolution,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {
        "schema_version": "axignal.axent-case-transition/v1",
        "case": case,
        "notification_queued": command.transition in {"RESOLVE", "REOPEN"},
    }
