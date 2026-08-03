from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from axignal_api.axent_telemetry_repository import AxentTelemetryRepository
from axignal_api.identity import AuthenticatedIdentity, require_identity
from axignal_api.settings import Settings

router = APIRouter(prefix="/v1/axent", tags=["axent-telemetry"])
admin_router = APIRouter(prefix="/v1/axent-admin", tags=["axent-admin-telemetry"])
Authenticated = Annotated[AuthenticatedIdentity, Depends(require_identity)]


class FeedbackCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message_id: UUID | None = None
    rating: int = Field(ge=1, le=5)
    resolution_helpful: bool | None = None
    comment: str | None = Field(default=None, max_length=4000)


class EvaluationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    evaluator_type: Literal["AUTOMATED", "HUMAN"] = "HUMAN"
    policy_version: str = Field(min_length=1, max_length=120)
    grounded: bool
    citation_valid: bool
    correct_resolution: bool | None = None
    escalation_correct: bool | None = None
    security_violation: bool = False
    score: Decimal | None = Field(default=None, ge=0, le=1)
    evidence: dict[str, Any] = Field(default_factory=dict)


def _settings() -> Settings:
    settings = Settings.from_env()
    if not settings.database_url:
        raise HTTPException(status_code=503, detail="axent_persistence_unavailable")
    return settings


def _repository() -> AxentTelemetryRepository:
    settings = _settings()
    assert settings.database_url is not None
    return AxentTelemetryRepository(settings.database_url)


def _require_human_authority(identity: AuthenticatedIdentity) -> None:
    settings = _settings()
    if identity.subject not in settings.human_reviewer_subjects:
        raise HTTPException(status_code=403, detail="axent_human_authority_required")
    if identity.assurance_level not in {"AAL2", "PHISHING_RESISTANT"}:
        raise HTTPException(status_code=403, detail="axent_step_up_auth_required")


@router.post(
    "/conversations/{conversation_id}/feedback",
    status_code=status.HTTP_201_CREATED,
)
def create_feedback(
    conversation_id: UUID,
    command: FeedbackCreate,
    identity: Authenticated,
) -> dict[str, Any]:
    try:
        feedback = _repository().create_feedback(
            tenant_id=identity.tenant_id,
            conversation_id=conversation_id,
            submitted_by_subject=identity.subject,
            rating=command.rating,
            resolution_helpful=command.resolution_helpful,
            comment_redacted=command.comment,
            message_id=command.message_id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        "schema_version": "axignal.axent-feedback/v1",
        "feedback": feedback,
    }


@admin_router.get("/metrics")
def get_metrics(identity: Authenticated) -> dict[str, Any]:
    _require_human_authority(identity)
    return {
        "schema_version": "axignal.axent-support-metrics/v1",
        "metrics": _repository().metrics(tenant_id=identity.tenant_id),
    }


@admin_router.post(
    "/conversations/{conversation_id}/evaluations",
    status_code=status.HTTP_201_CREATED,
)
def create_evaluation(
    conversation_id: UUID,
    command: EvaluationCreate,
    identity: Authenticated,
) -> dict[str, Any]:
    _require_human_authority(identity)
    evaluation = _repository().create_evaluation(
        tenant_id=identity.tenant_id,
        conversation_id=conversation_id,
        evaluator_type=command.evaluator_type,
        evaluator_subject=identity.subject,
        policy_version=command.policy_version,
        grounded=command.grounded,
        citation_valid=command.citation_valid,
        correct_resolution=command.correct_resolution,
        escalation_correct=command.escalation_correct,
        security_violation=command.security_violation,
        score=command.score,
        evidence_redacted=command.evidence,
    )
    return {
        "schema_version": "axignal.axent-evaluation/v1",
        "evaluation": evaluation,
    }
