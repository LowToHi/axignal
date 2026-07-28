from __future__ import annotations

from typing import Annotated, Any, Literal
from uuid import UUID

import psycopg
from fastapi import APIRouter, Depends, HTTPException, status
from psycopg.rows import dict_row
from pydantic import BaseModel, Field

from axignal_api.identity import AuthenticatedIdentity, require_identity
from axignal_api.settings import Settings

HumanReviewAction = Literal[
    "ACCEPT_AS_CONTEXT",
    "REJECT_PROPOSAL",
    "CONFIRM_CONTESTED",
    "REQUEST_MORE_EVIDENCE",
    "RETURN_TO_DETERMINISTIC_REVIEW",
    "MARK_OUT_OF_SCOPE",
]


class HumanReviewActionRequest(BaseModel):
    action: HumanReviewAction
    reason_code: str = Field(
        min_length=3,
        max_length=120,
        pattern=r"^[A-Z0-9_]+$",
    )
    note: str | None = Field(default=None, max_length=4_000)


class HumanReviewCaseCollection(BaseModel):
    cases: list[dict[str, Any]]


router = APIRouter(prefix="/v1/human-review-cases", tags=["human-review"])
Authenticated = Annotated[AuthenticatedIdentity, Depends(require_identity)]


def _reviewer_dsn(identity: AuthenticatedIdentity) -> str:
    settings = Settings.from_env()
    try:
        settings.require_human_review()
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    if identity.subject not in settings.human_reviewer_subjects:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Identity is not authorised for human review",
        )
    assert settings.human_review_database_url is not None
    return settings.human_review_database_url


def _translate_database_error(exc: psycopg.Error) -> HTTPException:
    detail = str(exc)
    if "HUMAN_REVIEW_CASE_NOT_FOUND" in detail:
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Human-review case not found",
        )
    conflicts = (
        "HUMAN_REVIEW_NON_BYPASSABLE_GATE_FAILED",
        "HUMAN_REVIEW_CASE_ALREADY_RESOLVED",
        "HUMAN_REVIEW_CASE_CANCELLED",
        "HUMAN_REVIEW_CASE_ASSIGNED_TO_ANOTHER_REVIEWER",
    )
    if any(marker in detail for marker in conflicts):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Human-review action conflicts with immutable case or gate state",
        )
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=f"Human-review boundary unavailable: {exc.__class__.__name__}",
    )


def _connect(identity: AuthenticatedIdentity) -> psycopg.Connection[dict[str, Any]]:
    return psycopg.connect(_reviewer_dsn(identity), row_factory=dict_row)


@router.get("", response_model=HumanReviewCaseCollection)
def list_human_review_cases(
    identity: Authenticated,
    research_run_id: UUID | None = None,
) -> HumanReviewCaseCollection:
    try:
        with _connect(identity) as connection, connection.cursor() as cursor:
            cursor.execute(
                "SELECT set_config('app.tenant_id', %s, false)",
                (str(identity.tenant_id),),
            )
            cursor.execute(
                "SELECT item FROM tenant_private.list_human_review_cases(%s) AS item",
                (research_run_id,),
            )
            cases = [row["item"] for row in cursor.fetchall()]
    except psycopg.Error as exc:
        raise _translate_database_error(exc) from exc
    return HumanReviewCaseCollection(cases=cases)


@router.get("/{human_review_case_id}")
def get_human_review_case(
    human_review_case_id: UUID,
    identity: Authenticated,
) -> dict[str, Any]:
    try:
        with _connect(identity) as connection, connection.cursor() as cursor:
            cursor.execute(
                "SELECT set_config('app.tenant_id', %s, false)",
                (str(identity.tenant_id),),
            )
            cursor.execute(
                "SELECT tenant_private.human_review_case_bundle(%s) AS item",
                (human_review_case_id,),
            )
            row = cursor.fetchone()
    except psycopg.Error as exc:
        raise _translate_database_error(exc) from exc
    if row is None or row["item"] is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Human-review case not found",
        )
    return row["item"]


@router.post("/{human_review_case_id}/actions")
def resolve_human_review_case(
    human_review_case_id: UUID,
    command: HumanReviewActionRequest,
    identity: Authenticated,
) -> dict[str, Any]:
    try:
        with _connect(identity) as connection, connection.cursor() as cursor:
            cursor.execute(
                "SELECT set_config('app.tenant_id', %s, false)",
                (str(identity.tenant_id),),
            )
            cursor.execute(
                """
                SELECT tenant_private.resolve_human_review_case(
                  %s, %s, %s, %s, %s, %s
                ) AS item
                """,
                (
                    human_review_case_id,
                    identity.subject,
                    identity.email,
                    command.action,
                    command.reason_code,
                    command.note,
                ),
            )
            row = cursor.fetchone()
    except psycopg.Error as exc:
        raise _translate_database_error(exc) from exc
    if row is None or row["item"] is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Human-review case not found",
        )
    return row["item"]
