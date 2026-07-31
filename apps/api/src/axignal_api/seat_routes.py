from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from axignal_api.identity import AuthenticatedIdentity, require_identity
from axignal_api.seat_config import SeatSettings
from axignal_api.seat_delivery import (
    SeatInvitationDelivery,
    create_invitation_secret,
    digest_invitation_token,
)
from axignal_api.seat_repository import SeatRepository

router = APIRouter(prefix="/v1/organisation/seats", tags=["organisation-seats"])
Authenticated = Annotated[AuthenticatedIdentity, Depends(require_identity)]
RoleId = Literal[
    "ORG_OWNER",
    "ORG_ADMIN",
    "B2G_MANAGER",
    "RESEARCH_OPERATOR",
    "BID_REVIEWER",
    "VIEWER",
    "BILLING_ADMIN",
    "AUDITOR",
]
InvitableRoleId = Literal[
    "ORG_ADMIN",
    "B2G_MANAGER",
    "RESEARCH_OPERATOR",
    "BID_REVIEWER",
    "VIEWER",
    "BILLING_ADMIN",
    "AUDITOR",
]


class BootstrapOwnerCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    confirm_owner_bootstrap: Literal[True]


class InviteMemberCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operation_id: str = Field(pattern=r"^op_[A-Za-z0-9_-]{8,}$", max_length=200)
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=320)
    role_id: InvitableRoleId


class AcceptInvitationCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token: str = Field(min_length=20, max_length=512)
    confirm_acceptance: Literal[True]


class ChangeRoleCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role_id: RoleId
    confirm_role_change: Literal[True]


class ConfirmCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    confirm: Literal[True]


class SeatEntitlementView(BaseModel):
    model_config = ConfigDict(extra="ignore")

    seat_entitlement_id: UUID
    plan_code: str
    billing_model: Literal["FLAT_TIER"]
    seat_capacity: int
    state: Literal["ACTIVE", "READ_ONLY", "SUSPENDED", "CANCELLED"]
    policy_version: str
    valid_from: datetime
    valid_until: datetime | None


class MemberView(BaseModel):
    model_config = ConfigDict(extra="ignore")

    membership_id: UUID
    principal_id: str
    email_normalized: str
    status: Literal["ACTIVE", "SUSPENDED", "REVOKED", "EXPIRED"]
    roles: list[RoleId]
    joined_at: datetime
    revoked_at: datetime | None


class InvitationView(BaseModel):
    model_config = ConfigDict(extra="ignore")

    invitation_id: UUID
    operation_id: str
    email_normalized: str
    requested_role_id: InvitableRoleId
    status: Literal[
        "PENDING",
        "ACCEPTED",
        "EXPIRED",
        "REVOKED",
        "DELIVERY_FAILED",
    ]
    delivery_provider: Literal["TEST", "SMTP"]
    invited_at: datetime
    expires_at: datetime
    accepted_at: datetime | None
    revoked_at: datetime | None


class AuditView(BaseModel):
    model_config = ConfigDict(extra="ignore")

    audit_event_id: UUID
    event_type: str
    actor_subject: str
    membership_id: UUID | None
    invitation_id: UUID | None
    seat_allocation_id: UUID | None
    payload: dict
    occurred_at: datetime


class SeatSummaryView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    seat_entitlement: SeatEntitlementView
    active_seats: int
    reserved_seats: int
    occupied_seats: int
    available_seats: int
    members: list[MemberView]
    invitations: list[InvitationView]
    audit: list[AuditView]


class InvitationCreatedView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    invitation: InvitationView
    delivery_provider: Literal["TEST", "SMTP"]
    delivery_status: Literal["DELIVERED", "ALREADY_DELIVERED"]
    test_acceptance_token: str | None = None


def _settings_repository() -> tuple[SeatSettings, SeatRepository]:
    settings = SeatSettings.from_env()
    try:
        settings.require_runtime()
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    assert settings.database_url is not None
    return settings, SeatRepository(settings.database_url)


def _store_error(exc: Exception) -> None:
    message = str(exc)
    conflicts = {
        "seat_capacity_exhausted": "Seat capacity is exhausted",
        "seat_downgrade_capacity_conflict": (
            "The target plan cannot contain the currently allocated seats"
        ),
        "seat_operation_id_conflict": "Seat operation id conflict",
        "membership_email_already_exists": "A membership already uses this email",
        "pending_invitation_already_exists": "A pending invitation already exists",
        "membership_already_exists": "Membership already exists",
        "last_owner_revocation_forbidden": "The last organisation owner cannot be revoked",
        "last_owner_role_change_forbidden": "The last organisation owner cannot change role",
        "owner_bootstrap_closed": "Organisation owner bootstrap is already closed",
        "seat_operation_not_retryable": "The previous seat operation is terminal",
    }
    forbidden = {
        "membership_admin_required": "Organisation owner or admin authority is required",
        "active_seat_entitlement_required": "An active seat entitlement is required",
        "active_membership_required": "An active membership is required",
        "seat_invitation_email_mismatch": (
            "Invitation email does not match the authenticated identity"
        ),
    }
    not_found = {
        "seat_invitation_not_found": "Seat invitation not found",
        "membership_not_found": "Membership not found",
        "reserved_seat_allocation_not_found": "Reserved seat allocation not found",
    }
    unprocessable = {
        "email_invalid": "Email is invalid",
        "seat_role_invalid": "Seat role is invalid",
        "invitation_expiry_invalid": "Invitation expiry is invalid",
        "invitation_token_digest_invalid": "Invitation token is invalid",
        "seat_invitation_expired": "Seat invitation has expired",
        "Invitation token is invalid": "Invitation token is invalid",
    }
    for marker, detail in conflicts.items():
        if marker in message:
            raise HTTPException(status_code=409, detail=detail) from exc
    for marker, detail in forbidden.items():
        if marker in message:
            raise HTTPException(status_code=403, detail=detail) from exc
    for marker, detail in not_found.items():
        if marker in message:
            raise HTTPException(status_code=404, detail=detail) from exc
    for marker, detail in unprocessable.items():
        if marker in message:
            raise HTTPException(status_code=422, detail=detail) from exc
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=f"Seat governance unavailable: {exc.__class__.__name__}",
    ) from exc


def _summary(repository: SeatRepository, tenant_id: UUID) -> SeatSummaryView:
    try:
        return SeatSummaryView.model_validate(repository.summary(tenant_id=tenant_id))
    except RuntimeError as exc:
        if "seat_entitlement_required" in str(exc):
            raise HTTPException(
                status_code=403,
                detail="An active trial or paid package is required",
            ) from exc
        _store_error(exc)
    raise AssertionError("Unreachable")


@router.get("", response_model=SeatSummaryView)
def seat_summary(identity: Authenticated) -> SeatSummaryView:
    _, repository = _settings_repository()
    return _summary(repository, identity.tenant_id)


@router.post("/bootstrap-owner", response_model=SeatSummaryView)
def bootstrap_owner(
    command: BootstrapOwnerCommand,
    identity: Authenticated,
) -> SeatSummaryView:
    del command
    settings, repository = _settings_repository()
    try:
        settings.require_owner_bootstrap(identity.subject)
        repository.bootstrap_owner(
            tenant_id=identity.tenant_id,
            principal_id=identity.subject,
            email=identity.email,
            actor_subject=identity.subject,
        )
    except RuntimeError as exc:
        if "approved organisation owner" in str(exc):
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        _store_error(exc)
    return _summary(repository, identity.tenant_id)


@router.post(
    "/invitations",
    response_model=InvitationCreatedView,
    status_code=status.HTTP_201_CREATED,
)
def invite_member(
    command: InviteMemberCommand,
    identity: Authenticated,
) -> InvitationCreatedView:
    settings, repository = _settings_repository()
    try:
        settings.require_invitation_delivery()
        existing = repository.invitation_by_operation(
            tenant_id=identity.tenant_id,
            operation_id=command.operation_id,
        )
        if existing is not None:
            if existing["email_normalized"] != str(command.email).lower():
                raise RuntimeError("seat_operation_id_conflict")
            if existing["requested_role_id"] != command.role_id:
                raise RuntimeError("seat_operation_id_conflict")
            if existing["status"] not in {"PENDING", "ACCEPTED"}:
                raise RuntimeError("seat_operation_not_retryable")
            return InvitationCreatedView(
                invitation=InvitationView.model_validate(existing),
                delivery_provider=existing["delivery_provider"],
                delivery_status="ALREADY_DELIVERED",
                test_acceptance_token=None,
            )

        secret = create_invitation_secret()
        expires_at = datetime.now(UTC) + timedelta(
            hours=settings.invitation_ttl_hours
        )
        delivery_provider = (
            "TEST" if settings.invitation_provider == "test" else "SMTP"
        )
        invitation = repository.reserve_invitation(
            tenant_id=identity.tenant_id,
            operation_id=command.operation_id,
            email=str(command.email),
            role_id=command.role_id,
            token_digest=secret.digest,
            delivery_provider=delivery_provider,
            invited_by=identity.subject,
            expires_at=expires_at,
        )
        if invitation.get("token_digest") != secret.digest:
            return InvitationCreatedView(
                invitation=InvitationView.model_validate(invitation),
                delivery_provider=invitation["delivery_provider"],
                delivery_status="ALREADY_DELIVERED",
                test_acceptance_token=None,
            )
        try:
            receipt = SeatInvitationDelivery(settings).deliver(
                recipient_email=str(command.email),
                token=secret.token,
                inviter_email=identity.email,
                expires_at_iso=expires_at.isoformat(),
            )
        except Exception as delivery_exc:
            repository.revoke_invitation(
                tenant_id=identity.tenant_id,
                invitation_id=invitation["invitation_id"],
                actor_subject=identity.subject,
                reason="DELIVERY_FAILED",
            )
            raise RuntimeError("Seat invitation delivery failed") from delivery_exc
    except RuntimeError as exc:
        if "delivery" in str(exc).casefold() or "provider" in str(exc).casefold():
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        _store_error(exc)

    return InvitationCreatedView(
        invitation=InvitationView.model_validate(invitation),
        delivery_provider=receipt.provider,
        delivery_status="DELIVERED",
        test_acceptance_token=receipt.test_acceptance_token,
    )


@router.post("/invitations/accept", response_model=SeatSummaryView)
def accept_invitation(
    command: AcceptInvitationCommand,
    identity: Authenticated,
) -> SeatSummaryView:
    _, repository = _settings_repository()
    try:
        repository.accept_invitation(
            tenant_id=identity.tenant_id,
            token_digest=digest_invitation_token(command.token),
            principal_id=identity.subject,
            email=identity.email,
            actor_subject=identity.subject,
        )
    except (RuntimeError, ValueError) as exc:
        _store_error(exc)
    return _summary(repository, identity.tenant_id)


@router.post("/invitations/{invitation_id}/revoke", response_model=SeatSummaryView)
def revoke_invitation(
    invitation_id: UUID,
    command: ConfirmCommand,
    identity: Authenticated,
) -> SeatSummaryView:
    del command
    _, repository = _settings_repository()
    try:
        repository.revoke_invitation(
            tenant_id=identity.tenant_id,
            invitation_id=invitation_id,
            actor_subject=identity.subject,
            reason="ADMIN_REVOKED",
        )
    except RuntimeError as exc:
        _store_error(exc)
    return _summary(repository, identity.tenant_id)


@router.post("/members/{membership_id}/revoke", response_model=SeatSummaryView)
def revoke_membership(
    membership_id: UUID,
    command: ConfirmCommand,
    identity: Authenticated,
) -> SeatSummaryView:
    del command
    _, repository = _settings_repository()
    try:
        repository.revoke_membership(
            tenant_id=identity.tenant_id,
            membership_id=membership_id,
            actor_subject=identity.subject,
        )
    except RuntimeError as exc:
        _store_error(exc)
    return _summary(repository, identity.tenant_id)


@router.post("/members/{membership_id}/role", response_model=SeatSummaryView)
def change_membership_role(
    membership_id: UUID,
    command: ChangeRoleCommand,
    identity: Authenticated,
) -> SeatSummaryView:
    _, repository = _settings_repository()
    try:
        repository.change_role(
            tenant_id=identity.tenant_id,
            membership_id=membership_id,
            role_id=command.role_id,
            actor_subject=identity.subject,
        )
    except RuntimeError as exc:
        _store_error(exc)
    return _summary(repository, identity.tenant_id)
