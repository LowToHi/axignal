from __future__ import annotations

import hashlib
import hmac
from typing import Annotated, Any, Literal
from uuid import UUID

import psycopg
from fastapi import APIRouter, Depends, HTTPException, status
from psycopg.rows import dict_row
from pydantic import BaseModel, Field

from axignal_api.identity import AuthenticatedIdentity, require_identity
from axignal_api.settings import Settings

ParticipantProfile = Literal[
    "DOMAIN_EXPERT",
    "ANALYST",
    "DECISION_MAKER",
    "OTHER_QUALIFIED",
]
ValidationEventType = Literal[
    "TASK_OPENED",
    "SOURCE_OPENED",
    "EVIDENCE_INSPECTED",
    "CLAIM_INSPECTED",
    "TIMELINE_USED",
    "HUMAN_REVIEW_OPENED",
]


class StartValidationSessionRequest(BaseModel):
    task_id: str = Field(min_length=3, max_length=120, pattern=r"^[A-Z0-9-]+$")
    participant_profile: ParticipantProfile


class ValidationEventRequest(BaseModel):
    event_type: ValidationEventType
    idempotency_key: str = Field(min_length=3, max_length=160)
    payload: dict[str, Any] = Field(default_factory=dict)


class CompleteValidationSessionRequest(BaseModel):
    authority_layer: str = Field(min_length=3, max_length=120)
    evidence_ids: list[str] = Field(default_factory=list, max_length=20)
    unknown_ids: list[str] = Field(default_factory=list, max_length=20)
    confidence: int = Field(ge=0, le=100)
    answer: str = Field(default="", max_length=4_000)


router = APIRouter(prefix="/v1/validation", tags=["qualified-user-validation"])
Authenticated = Annotated[AuthenticatedIdentity, Depends(require_identity)]


def participant_hash(identity: AuthenticatedIdentity, salt: str) -> str:
    message = f"{identity.tenant_id}|{identity.subject}".encode()
    digest = hmac.new(salt.encode(), message, hashlib.sha256).hexdigest()
    return f"sha256:{digest}"


def _settings() -> Settings:
    settings = Settings.from_env()
    try:
        settings.require_validation()
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    return settings


def _connect(settings: Settings) -> psycopg.Connection[dict[str, Any]]:
    assert settings.validation_database_url is not None
    return psycopg.connect(settings.validation_database_url, row_factory=dict_row)


def _translate_database_error(exc: psycopg.Error) -> HTTPException:
    detail = str(exc)
    not_found = (
        "AXIGNAL_VALIDATION_TASK_NOT_FOUND",
        "AXIGNAL_VALIDATION_SESSION_NOT_FOUND",
    )
    if any(marker in detail for marker in not_found):
        return HTTPException(status_code=404, detail="Validation resource not found")
    conflicts = (
        "AXIGNAL_VALIDATION_SESSION_NOT_OPEN",
        "AXIGNAL_VALIDATION_RESPONSE_IMMUTABLE",
        "AXIGNAL_VALIDATION_HISTORY_APPEND_ONLY",
    )
    if any(marker in detail for marker in conflicts):
        return HTTPException(status_code=409, detail="Immutable validation state conflict")
    invalid = (
        "AXIGNAL_VALIDATION_PROFILE_INVALID",
        "AXIGNAL_VALIDATION_EVENT_NOT_ALLOWED",
        "AXIGNAL_VALIDATION_CONFIDENCE_INVALID",
        "AXIGNAL_VALIDATION_PARTICIPANT_HASH_INVALID",
    )
    if any(marker in detail for marker in invalid):
        return HTTPException(status_code=422, detail="Invalid validation command")
    return HTTPException(
        status_code=503,
        detail=f"Validation boundary unavailable: {exc.__class__.__name__}",
    )


def _set_tenant(cursor: psycopg.Cursor[dict[str, Any]], tenant_id: UUID) -> None:
    cursor.execute("SELECT set_config('app.tenant_id', %s, false)", (str(tenant_id),))


@router.get("/tasks")
def list_validation_tasks(
    identity: Authenticated,
    language: Literal["en", "es"] | None = None,
) -> dict[str, Any]:
    settings = _settings()
    try:
        with _connect(settings) as connection, connection.cursor() as cursor:
            _set_tenant(cursor, identity.tenant_id)
            cursor.execute(
                "SELECT item FROM evaluation.list_validation_tasks(%s) AS item",
                (language,),
            )
            tasks = [row["item"] for row in cursor.fetchall()]
    except psycopg.Error as exc:
        raise _translate_database_error(exc) from exc
    return {"tasks": tasks}


@router.post("/sessions", status_code=status.HTTP_201_CREATED)
def start_validation_session(
    command: StartValidationSessionRequest,
    identity: Authenticated,
) -> dict[str, Any]:
    settings = _settings()
    assert settings.validation_participant_salt is not None
    pseudonym = participant_hash(identity, settings.validation_participant_salt)
    try:
        with _connect(settings) as connection, connection.cursor() as cursor:
            _set_tenant(cursor, identity.tenant_id)
            cursor.execute(
                """
                SELECT evaluation.start_validation_session(%s, %s, %s, %s) AS item
                """,
                (
                    identity.tenant_id,
                    pseudonym,
                    command.participant_profile,
                    command.task_id,
                ),
            )
            row = cursor.fetchone()
    except psycopg.Error as exc:
        raise _translate_database_error(exc) from exc
    assert row is not None
    return row["item"]


@router.get("/sessions/{validation_session_id}")
def get_validation_session(
    validation_session_id: UUID,
    identity: Authenticated,
) -> dict[str, Any]:
    settings = _settings()
    try:
        with _connect(settings) as connection, connection.cursor() as cursor:
            _set_tenant(cursor, identity.tenant_id)
            cursor.execute(
                "SELECT evaluation.validation_session_bundle(%s) AS item",
                (validation_session_id,),
            )
            row = cursor.fetchone()
    except psycopg.Error as exc:
        raise _translate_database_error(exc) from exc
    if row is None or row["item"] is None:
        raise HTTPException(status_code=404, detail="Validation session not found")
    return row["item"]


@router.post("/sessions/{validation_session_id}/events")
def append_validation_event(
    validation_session_id: UUID,
    command: ValidationEventRequest,
    identity: Authenticated,
) -> dict[str, Any]:
    settings = _settings()
    try:
        with _connect(settings) as connection, connection.cursor() as cursor:
            _set_tenant(cursor, identity.tenant_id)
            cursor.execute(
                """
                SELECT evaluation.append_validation_event(
                  %s, %s, %s, %s, %s::jsonb
                ) AS item
                """,
                (
                    identity.tenant_id,
                    validation_session_id,
                    command.event_type,
                    command.idempotency_key,
                    psycopg.types.json.Jsonb(command.payload),
                ),
            )
            row = cursor.fetchone()
    except psycopg.Error as exc:
        raise _translate_database_error(exc) from exc
    assert row is not None
    return row["item"]


@router.post("/sessions/{validation_session_id}/complete")
def complete_validation_session(
    validation_session_id: UUID,
    command: CompleteValidationSessionRequest,
    identity: Authenticated,
) -> dict[str, Any]:
    settings = _settings()
    try:
        with _connect(settings) as connection, connection.cursor() as cursor:
            _set_tenant(cursor, identity.tenant_id)
            cursor.execute(
                """
                SELECT evaluation.complete_validation_session(
                  %s, %s, %s, %s, %s, %s, %s
                ) AS item
                """,
                (
                    identity.tenant_id,
                    validation_session_id,
                    command.authority_layer,
                    command.evidence_ids,
                    command.unknown_ids,
                    command.confidence,
                    command.answer,
                ),
            )
            row = cursor.fetchone()
    except psycopg.Error as exc:
        raise _translate_database_error(exc) from exc
    assert row is not None
    return row["item"]


@router.get("/metrics")
def validation_metrics(identity: Authenticated) -> dict[str, Any]:
    settings = _settings()
    try:
        with _connect(settings) as connection, connection.cursor() as cursor:
            _set_tenant(cursor, identity.tenant_id)
            cursor.execute(
                "SELECT item FROM evaluation.validation_metrics(%s) AS item",
                (identity.tenant_id,),
            )
            metrics = [row["item"] for row in cursor.fetchall()]
    except psycopg.Error as exc:
        raise _translate_database_error(exc) from exc
    return {"metrics": metrics}
