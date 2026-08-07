"""Bid Workspace O01 HTTP API (Prioridad 3)."""

from __future__ import annotations

import os
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from axignal_api.bid_workspace_repository import BidWorkspaceRepository
from axignal_api.identity import AuthenticatedIdentity, require_identity

router = APIRouter(prefix="/v1/bid-workspaces", tags=["bid-workspace"])
Authenticated = Annotated[AuthenticatedIdentity, Depends(require_identity)]


def _repository() -> BidWorkspaceRepository:
    dsn = os.environ.get("AXIGNAL_DATABASE_URL")
    if not dsn:
        raise HTTPException(
            status_code=503, detail="AXIGNAL_DATABASE_URL is required"
        )
    return BidWorkspaceRepository(dsn)


class RequirementCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirement_ref: str = Field(pattern=r"^req_[A-Za-z0-9_-]{3,}$", max_length=200)
    kind: str = Field(pattern=r"^(OFFICIAL|INFERENCE|RECOMMENDATION)$")
    title: str = Field(min_length=3, max_length=500)
    description: str = Field(default="", max_length=4000)
    source_notice_version: int | None = None


class RequirementUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=3, max_length=500)
    description: str = Field(default="", max_length=4000)


class AmendmentInvalidateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    amendment_ref: str = Field(min_length=3, max_length=200)


class QuestionCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_ref: str = Field(pattern=r"^q_[A-Za-z0-9_-]{3,}$", max_length=200)
    question: str = Field(min_length=3, max_length=2000)


class QuestionAnswerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer: str = Field(min_length=1, max_length=4000)


class RiskCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    risk_ref: str = Field(pattern=r"^risk_[A-Za-z0-9_-]{3,}$", max_length=200)
    description: str = Field(min_length=3, max_length=2000)
    likelihood: str = Field(pattern=r"^(LOW|MEDIUM|HIGH)$")
    impact: str = Field(pattern=r"^(LOW|MEDIUM|HIGH)$")
    mitigation: str = Field(default="", max_length=2000)


class TaskCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_ref: str = Field(pattern=r"^t_[A-Za-z0-9_-]{3,}$", max_length=200)
    title: str = Field(min_length=3, max_length=500)
    owner: str = Field(min_length=3, max_length=200)
    requirement_ref: str | None = None


class TaskTransitionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    new_status: str = Field(pattern=r"^(OPEN|IN_PROGRESS|DONE|BLOCKED|CANCELLED)$")


class ReadinessRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirement_ref: str
    satisfied: bool
    evidence_refs: list[str] = Field(default_factory=list)
    notes: str = Field(default="", max_length=2000)


class ApprovalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    approval_ref: str = Field(pattern=r"^appr_[A-Za-z0-9_-]{3,}$", max_length=200)
    decision: str = Field(pattern=r"^(APPROVED|REJECTED)$")
    notes: str = Field(default="", max_length=2000)


class HandoffRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    handoff_ref: str = Field(pattern=r"^ho_[A-Za-z0-9_-]{3,}$", max_length=200)
    target: str = Field(min_length=3, max_length=200)
    payload: dict = Field(default_factory=dict)


def _workspace_exists(
    repository: BidWorkspaceRepository, tenant_id: UUID, workspace_id: UUID
) -> None:
    row = repository.get_workspace(tenant_id=tenant_id, workspace_id=workspace_id)
    if row is None:
        raise HTTPException(status_code=404, detail="workspace not found")


# --- Requirements ------------------------------------------------------------


@router.post("/{workspace_id}/requirements", status_code=status.HTTP_201_CREATED)
def add_requirement(
    workspace_id: UUID,
    request: RequirementCreateRequest,
    identity: Authenticated,
) -> dict[str, object]:
    repository = _repository()
    _workspace_exists(repository, identity.tenant_id, workspace_id)
    requirement_id = repository.add_requirement(
        tenant_id=identity.tenant_id,
        workspace_id=workspace_id,
        requirement_ref=request.requirement_ref,
        kind=request.kind,
        title=request.title,
        description=request.description,
        source_notice_version=request.source_notice_version,
        created_by=identity.subject,
    )
    return {"requirement_id": str(requirement_id), "requirement_ref": request.requirement_ref}


@router.get("/{workspace_id}/requirements")
def list_requirements(
    workspace_id: UUID, identity: Authenticated
) -> list[dict[str, object]]:
    repository = _repository()
    _workspace_exists(repository, identity.tenant_id, workspace_id)
    return repository.list_requirements(
        tenant_id=identity.tenant_id, workspace_id=workspace_id
    )


@router.patch("/{workspace_id}/requirements/{requirement_ref}")
def update_requirement(
    workspace_id: UUID,
    requirement_ref: str,
    request: RequirementUpdateRequest,
    identity: Authenticated,
) -> dict[str, object]:
    repository = _repository()
    _workspace_exists(repository, identity.tenant_id, workspace_id)
    repository.update_requirement(
        tenant_id=identity.tenant_id,
        workspace_id=workspace_id,
        requirement_ref=requirement_ref,
        title=request.title,
        description=request.description,
        changed_by=identity.subject,
    )
    return {"requirement_ref": requirement_ref, "updated": True}


@router.post("/{workspace_id}/requirements/{requirement_ref}/invalidate")
def invalidate_requirement(
    workspace_id: UUID,
    requirement_ref: str,
    request: AmendmentInvalidateRequest,
    identity: Authenticated,
) -> dict[str, object]:
    repository = _repository()
    _workspace_exists(repository, identity.tenant_id, workspace_id)
    repository.invalidate_requirement_by_amendment(
        tenant_id=identity.tenant_id,
        workspace_id=workspace_id,
        requirement_ref=requirement_ref,
        amendment_ref=request.amendment_ref,
        invalidated_by=identity.subject,
    )
    return {"requirement_ref": requirement_ref, "status": "AMENDED"}


@router.get("/{workspace_id}/requirements/{requirement_ref}/versions")
def requirement_versions(
    workspace_id: UUID,
    requirement_ref: str,
    identity: Authenticated,
) -> dict[str, object]:
    repository = _repository()
    _workspace_exists(repository, identity.tenant_id, workspace_id)
    rows = repository.list_requirements(
        tenant_id=identity.tenant_id, workspace_id=workspace_id
    )
    match = next((row for row in rows if row["requirement_ref"] == requirement_ref), None)
    if match is None:
        raise HTTPException(status_code=404, detail="requirement not found")
    versions = repository.list_requirement_versions(
        tenant_id=identity.tenant_id, requirement_id=match["requirement_id"]
    )
    return {"requirement_ref": requirement_ref, "versions": versions}


# --- Questions ---------------------------------------------------------------


@router.post("/{workspace_id}/questions", status_code=status.HTTP_201_CREATED)
def add_question(
    workspace_id: UUID,
    request: QuestionCreateRequest,
    identity: Authenticated,
) -> dict[str, object]:
    repository = _repository()
    _workspace_exists(repository, identity.tenant_id, workspace_id)
    question_id = repository.add_question(
        tenant_id=identity.tenant_id,
        workspace_id=workspace_id,
        question_ref=request.question_ref,
        question=request.question,
        asked_by=identity.subject,
    )
    return {"question_id": str(question_id), "question_ref": request.question_ref}


@router.post("/{workspace_id}/questions/{question_ref}/answer")
def answer_question(
    workspace_id: UUID,
    question_ref: str,
    request: QuestionAnswerRequest,
    identity: Authenticated,
) -> dict[str, object]:
    repository = _repository()
    _workspace_exists(repository, identity.tenant_id, workspace_id)
    repository.answer_question(
        tenant_id=identity.tenant_id,
        workspace_id=workspace_id,
        question_ref=question_ref,
        answer=request.answer,
    )
    return {"question_ref": question_ref, "status": "ANSWERED"}


@router.get("/{workspace_id}/questions")
def list_questions(
    workspace_id: UUID, identity: Authenticated
) -> list[dict[str, object]]:
    repository = _repository()
    _workspace_exists(repository, identity.tenant_id, workspace_id)
    return repository.list_questions(
        tenant_id=identity.tenant_id, workspace_id=workspace_id
    )


# --- Risks -------------------------------------------------------------------


@router.post("/{workspace_id}/risks", status_code=status.HTTP_201_CREATED)
def add_risk(
    workspace_id: UUID,
    request: RiskCreateRequest,
    identity: Authenticated,
) -> dict[str, object]:
    repository = _repository()
    _workspace_exists(repository, identity.tenant_id, workspace_id)
    risk_id = repository.add_risk(
        tenant_id=identity.tenant_id,
        workspace_id=workspace_id,
        risk_ref=request.risk_ref,
        description=request.description,
        likelihood=request.likelihood,
        impact=request.impact,
        mitigation=request.mitigation,
        registered_by=identity.subject,
    )
    return {"risk_id": str(risk_id), "risk_ref": request.risk_ref}


@router.get("/{workspace_id}/risks")
def list_risks(
    workspace_id: UUID, identity: Authenticated
) -> list[dict[str, object]]:
    repository = _repository()
    _workspace_exists(repository, identity.tenant_id, workspace_id)
    return repository.list_risks(tenant_id=identity.tenant_id, workspace_id=workspace_id)


# --- Tasks -------------------------------------------------------------------


@router.post("/{workspace_id}/tasks", status_code=status.HTTP_201_CREATED)
def add_task(
    workspace_id: UUID,
    request: TaskCreateRequest,
    identity: Authenticated,
) -> dict[str, object]:
    repository = _repository()
    _workspace_exists(repository, identity.tenant_id, workspace_id)
    task_id = repository.add_task(
        tenant_id=identity.tenant_id,
        workspace_id=workspace_id,
        task_ref=request.task_ref,
        title=request.title,
        owner=request.owner,
        requirement_ref=request.requirement_ref,
        created_by=identity.subject,
    )
    return {"task_id": str(task_id), "task_ref": request.task_ref}


@router.post("/{workspace_id}/tasks/{task_ref}/transition")
def transition_task(
    workspace_id: UUID,
    task_ref: str,
    request: TaskTransitionRequest,
    identity: Authenticated,
) -> dict[str, object]:
    repository = _repository()
    _workspace_exists(repository, identity.tenant_id, workspace_id)
    repository.transition_task(
        tenant_id=identity.tenant_id,
        workspace_id=workspace_id,
        task_ref=task_ref,
        new_status=request.new_status,
    )
    return {"task_ref": task_ref, "status": request.new_status}


@router.get("/{workspace_id}/tasks")
def list_tasks(
    workspace_id: UUID, identity: Authenticated
) -> list[dict[str, object]]:
    repository = _repository()
    _workspace_exists(repository, identity.tenant_id, workspace_id)
    return repository.list_tasks(tenant_id=identity.tenant_id, workspace_id=workspace_id)


# --- Readiness ---------------------------------------------------------------


@router.post("/{workspace_id}/readiness")
def set_readiness(
    workspace_id: UUID,
    request: ReadinessRequest,
    identity: Authenticated,
) -> dict[str, object]:
    repository = _repository()
    _workspace_exists(repository, identity.tenant_id, workspace_id)
    repository.set_readiness(
        tenant_id=identity.tenant_id,
        workspace_id=workspace_id,
        requirement_ref=request.requirement_ref,
        satisfied=request.satisfied,
        evidence_refs=request.evidence_refs,
        notes=request.notes,
        updated_by=identity.subject,
    )
    return {"requirement_ref": request.requirement_ref, "satisfied": request.satisfied}


@router.get("/{workspace_id}/readiness")
def readiness_summary(
    workspace_id: UUID, identity: Authenticated
) -> dict[str, object]:
    repository = _repository()
    _workspace_exists(repository, identity.tenant_id, workspace_id)
    return repository.readiness_summary(
        tenant_id=identity.tenant_id, workspace_id=workspace_id
    )


# --- Approval + handoff ------------------------------------------------------


@router.post("/{workspace_id}/approvals", status_code=status.HTTP_201_CREATED)
def record_approval(
    workspace_id: UUID,
    request: ApprovalRequest,
    identity: Authenticated,
) -> dict[str, object]:
    repository = _repository()
    _workspace_exists(repository, identity.tenant_id, workspace_id)
    repository.record_approval(
        tenant_id=identity.tenant_id,
        workspace_id=workspace_id,
        approval_ref=request.approval_ref,
        decision=request.decision,
        approved_by=identity.subject,
        notes=request.notes,
    )
    return {"approval_ref": request.approval_ref, "decision": request.decision}


@router.post("/{workspace_id}/handoffs", status_code=status.HTTP_201_CREATED)
def record_handoff(
    workspace_id: UUID,
    request: HandoffRequest,
    identity: Authenticated,
) -> dict[str, object]:
    repository = _repository()
    _workspace_exists(repository, identity.tenant_id, workspace_id)
    repository.record_handoff(
        tenant_id=identity.tenant_id,
        workspace_id=workspace_id,
        handoff_ref=request.handoff_ref,
        target=request.target,
        payload=request.payload,
        handed_off_by=identity.subject,
    )
    return {"handoff_ref": request.handoff_ref, "target": request.target}


# --- Audit -------------------------------------------------------------------


@router.get("/{workspace_id}/audit")
def audit_log(
    workspace_id: UUID, identity: Authenticated
) -> list[dict[str, object]]:
    repository = _repository()
    _workspace_exists(repository, identity.tenant_id, workspace_id)
    return repository.audit_log(tenant_id=identity.tenant_id, workspace_id=workspace_id)
