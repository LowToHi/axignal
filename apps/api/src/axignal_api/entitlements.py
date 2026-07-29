from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from axignal_api.ai_scope import classify_axignal_request
from axignal_api.capability_tokens import (
    build_capability_token,
    verify_capability_token,
)
from axignal_api.entitlement_config import EntitlementSettings
from axignal_api.entitlement_repository import EntitlementRepository
from axignal_api.identity import AuthenticatedIdentity, require_identity

router = APIRouter(prefix="/v1", tags=["entitlements"])
Authenticated = Annotated[AuthenticatedIdentity, Depends(require_identity)]

Capability = Literal[
    "NAVIGATE_AXIGNAL",
    "READ_INVESTIGATION_CONTEXT",
    "UPDATE_INVESTIGATION_CONTEXT",
    "SEARCH_ADMITTED_AXIGNAL_DATA",
    "COMPARE_ADMITTED_AXIGNAL_DATA",
    "EXPLAIN_CLAIMS_AND_EVIDENCE",
    "SHOW_CONTRADICTIONS_AND_UNKNOWNS",
    "REQUEST_BOUNDED_RESEARCH_RUN",
    "READ_RESEARCH_RUN_PROGRESS",
    "ASSEMBLE_EVIDENCE_LINKED_DOSSIER",
    "GENERATE_GROUNDED_PDF_REPORT",
    "EXPLAIN_AXIGNAL_PRODUCT_AND_METHOD",
]


class TrialActivationCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    confirm_controlled_trial: Literal[True]


class AIRequestAuthorizationCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operation_id: str = Field(pattern=r"^op_[A-Za-z0-9_-]{8,}$", max_length=200)
    capability: Capability
    intent: str = Field(min_length=3, max_length=4_000)
    max_tokens: int = Field(ge=1, le=100_000)


class TokenReconciliationCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reservation_id: UUID
    capability_token: str = Field(min_length=32, max_length=4_096)
    actual_tokens: int = Field(ge=0)


class TokenReleaseCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reservation_id: UUID
    capability_token: str = Field(min_length=32, max_length=4_096)


class EntitlementView(BaseModel):
    model_config = ConfigDict(extra="ignore")

    entitlement_id: UUID
    entitlement_kind: Literal["TRIAL", "PAID_MONTHLY"]
    plan_code: str
    state: Literal["ACTIVE", "READ_ONLY", "SUSPENDED", "CANCELLED"]
    starts_at: datetime
    expires_at: datetime | None
    unlimited_ai_tokens: bool
    token_budget_total: int | None
    token_budget_reserved: int
    token_budget_consumed: int
    token_budget_available: int | None = None


class AIRequestAuthorization(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: Literal["IN_SCOPE_AXIGNAL"] = "IN_SCOPE_AXIGNAL"
    reason: str
    reservation_id: UUID
    capability: Capability
    capability_token: str
    capability_expires_at: datetime
    entitlement_kind: Literal["TRIAL", "PAID_MONTHLY"]
    token_budget_available: int | None


class TokenUsageResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reservation_id: UUID
    state: Literal["RECONCILED", "RELEASED"]
    requested_tokens: int
    actual_tokens: int


def _settings_and_repository() -> tuple[EntitlementSettings, EntitlementRepository]:
    settings = EntitlementSettings.from_env()
    try:
        settings.require_store()
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    assert settings.database_url is not None
    return settings, EntitlementRepository(settings.database_url)


def _raise_store_error(exc: Exception) -> None:
    message = str(exc)
    known = {
        "trial_already_activated": (status.HTTP_409_CONFLICT, "Trial already activated"),
        "trial_token_budget_exhausted": (
            status.HTTP_409_CONFLICT,
            "Trial token budget exhausted",
        ),
        "trial_expired": (status.HTTP_403_FORBIDDEN, "Trial has expired"),
        "active_entitlement_required": (
            status.HTTP_403_FORBIDDEN,
            "Active entitlement required",
        ),
        "operation_id_conflict": (
            status.HTTP_409_CONFLICT,
            "Operation id conflicts with an existing reservation",
        ),
        "reconciliation_conflict": (
            status.HTTP_409_CONFLICT,
            "Reservation was already reconciled with different usage",
        ),
        "reservation_not_found": (status.HTTP_404_NOT_FOUND, "Reservation not found"),
        "reservation_not_active": (
            status.HTTP_409_CONFLICT,
            "Reservation is not active",
        ),
        "actual_tokens_outside_reservation": (
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Actual usage exceeds the authorised reservation",
        ),
        "trial_not_found": (status.HTTP_404_NOT_FOUND, "Trial not found"),
    }
    for marker, (code, detail) in known.items():
        if marker in message:
            raise HTTPException(status_code=code, detail=detail) from exc
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=f"Entitlement runtime unavailable: {exc.__class__.__name__}",
    ) from exc


def _view(row: dict[str, object]) -> EntitlementView:
    total = row.get("token_budget_total")
    reserved = int(row.get("token_budget_reserved") or 0)
    consumed = int(row.get("token_budget_consumed") or 0)
    available = row.get("token_budget_available")
    if available is None and total is not None:
        available = int(total) - reserved - consumed
    return EntitlementView(
        entitlement_id=row["entitlement_id"],  # type: ignore[arg-type]
        entitlement_kind=row["entitlement_kind"],  # type: ignore[arg-type]
        plan_code=str(row["plan_code"]),
        state=row["state"],  # type: ignore[arg-type]
        starts_at=row["starts_at"],  # type: ignore[arg-type]
        expires_at=row.get("expires_at"),  # type: ignore[arg-type]
        unlimited_ai_tokens=bool(row["unlimited_ai_tokens"]),
        token_budget_total=int(total) if total is not None else None,
        token_budget_reserved=reserved,
        token_budget_consumed=consumed,
        token_budget_available=int(available) if available is not None else None,
    )


def _verify_grant(
    *,
    token: str,
    reservation_id: UUID,
    identity: AuthenticatedIdentity,
    settings: EntitlementSettings,
) -> None:
    secret = settings.capability_token_secret
    if not secret or len(secret.encode("utf-8")) < 32:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AXIGNAL_CAPABILITY_TOKEN_SECRET is required",
        )
    try:
        grant = verify_capability_token(token, secret=secret)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired capability token",
        ) from exc
    if grant.tenant_id != identity.tenant_id or grant.reservation_id != reservation_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Capability token does not authorise this reservation",
        )


@router.post(
    "/trials/activate",
    response_model=EntitlementView,
    status_code=status.HTTP_201_CREATED,
)
def activate_trial(
    command: TrialActivationCommand,
    identity: Authenticated,
) -> EntitlementView:
    del command
    settings, repository = _settings_and_repository()
    try:
        settings.require_trial_activation()
        row = repository.activate_trial(
            tenant_id=identity.tenant_id,
            actor_subject=identity.subject,
        )
    except RuntimeError as exc:
        if "disabled" in str(exc):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc
        _raise_store_error(exc)
    except Exception as exc:
        _raise_store_error(exc)
    return _view(row)


@router.get("/entitlements/current", response_model=EntitlementView)
def current_entitlement(identity: Authenticated) -> EntitlementView:
    _, repository = _settings_and_repository()
    row = repository.current_entitlement(tenant_id=identity.tenant_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No entitlement found",
        )
    return _view(row)


@router.get("/trials/usage", response_model=EntitlementView)
def trial_usage(identity: Authenticated) -> EntitlementView:
    _, repository = _settings_and_repository()
    row = repository.usage(tenant_id=identity.tenant_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No entitlement found",
        )
    return _view(row)


@router.post("/trials/expire", response_model=EntitlementView)
def expire_trial(identity: Authenticated) -> EntitlementView:
    _, repository = _settings_and_repository()
    try:
        row = repository.expire_trial(
            tenant_id=identity.tenant_id,
            actor_subject=identity.subject,
        )
    except Exception as exc:
        _raise_store_error(exc)
    return _view(row)


@router.post("/ai/authorize", response_model=AIRequestAuthorization)
def authorize_ai_request(
    command: AIRequestAuthorizationCommand,
    identity: Authenticated,
) -> AIRequestAuthorization:
    settings, repository = _settings_and_repository()
    try:
        settings.require_ai_authorization()
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    scope = classify_axignal_request(
        capability=command.capability,
        user_intent=command.intent,
    )
    if scope.decision != "IN_SCOPE_AXIGNAL":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"decision": scope.decision, "reason": scope.reason},
        )

    try:
        reservation = repository.reserve(
            tenant_id=identity.tenant_id,
            operation_id=command.operation_id,
            capability=command.capability,
            requested_tokens=command.max_tokens,
            actor_subject=identity.subject,
        )
        entitlement = repository.usage(tenant_id=identity.tenant_id)
    except Exception as exc:
        _raise_store_error(exc)
    if entitlement is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Entitlement disappeared after reservation",
        )

    assert settings.capability_token_secret is not None
    token = build_capability_token(
        secret=settings.capability_token_secret,
        tenant_id=identity.tenant_id,
        reservation_id=reservation["reservation_id"],
        operation_id=command.operation_id,
        capability=command.capability,
        ttl_seconds=settings.capability_token_ttl_seconds,
    )
    grant = verify_capability_token(token, secret=settings.capability_token_secret)
    view = _view(entitlement)
    return AIRequestAuthorization(
        reason=scope.reason,
        reservation_id=reservation["reservation_id"],
        capability=command.capability,
        capability_token=token,
        capability_expires_at=grant.expires_at,
        entitlement_kind=view.entitlement_kind,
        token_budget_available=view.token_budget_available,
    )


@router.post("/ai/usage/reconcile", response_model=TokenUsageResult)
def reconcile_ai_usage(
    command: TokenReconciliationCommand,
    identity: Authenticated,
) -> TokenUsageResult:
    settings, repository = _settings_and_repository()
    _verify_grant(
        token=command.capability_token,
        reservation_id=command.reservation_id,
        identity=identity,
        settings=settings,
    )
    try:
        row = repository.reconcile(
            tenant_id=identity.tenant_id,
            reservation_id=command.reservation_id,
            actual_tokens=command.actual_tokens,
            actor_subject=identity.subject,
        )
    except Exception as exc:
        _raise_store_error(exc)
    return TokenUsageResult(
        reservation_id=row["reservation_id"],
        state="RECONCILED",
        requested_tokens=int(row["requested_tokens"]),
        actual_tokens=int(row["actual_tokens"]),
    )


@router.post("/ai/usage/release", response_model=TokenUsageResult)
def release_ai_reservation(
    command: TokenReleaseCommand,
    identity: Authenticated,
) -> TokenUsageResult:
    settings, repository = _settings_and_repository()
    _verify_grant(
        token=command.capability_token,
        reservation_id=command.reservation_id,
        identity=identity,
        settings=settings,
    )
    try:
        row = repository.release(
            tenant_id=identity.tenant_id,
            reservation_id=command.reservation_id,
            actor_subject=identity.subject,
        )
    except Exception as exc:
        _raise_store_error(exc)
    return TokenUsageResult(
        reservation_id=row["reservation_id"],
        state="RELEASED",
        requested_tokens=int(row["requested_tokens"]),
        actual_tokens=0,
    )
