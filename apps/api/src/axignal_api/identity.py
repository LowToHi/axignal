from __future__ import annotations

import base64
import hmac
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import Annotated, Any
from uuid import UUID

from fastapi import Header, HTTPException, Request, status

from axignal_api.seat_config import SeatSettings
from axignal_api.seat_repository import SeatRepository
from axignal_api.settings import Settings

ASSERTION_AUDIENCE = "axignal-api"
ASSERTION_VERSION = "v1"
MAX_ASSERTION_TTL_SECONDS = 300
CLOCK_SKEW_SECONDS = 30
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
SEAT_GOVERNANCE_EXEMPT_PREFIXES = (
    "/v1/billing",
    "/v1/entitlements",
)
SEAT_GOVERNANCE_BOOTSTRAP_PATHS = {
    "/v1/organisation/seats/bootstrap-owner",
    "/v1/organisation/seats/invitations/accept",
}

IdentityAssertionHeader = Annotated[
    str | None,
    Header(alias="X-AXIGNAL-Identity-Assertion"),
]


@dataclass(frozen=True)
class AuthenticatedIdentity:
    subject: str
    email: str
    tenant_id: UUID
    issued_at: datetime
    expires_at: datetime
    membership_id: UUID | None = None
    role_ids: tuple[str, ...] = ()
    seat_state: str | None = None
    seat_plan_code: str | None = None


def _b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}".encode("ascii"))


def build_identity_assertion(
    *,
    secret: str,
    subject: str,
    email: str,
    tenant_id: UUID,
    now: datetime | None = None,
    ttl_seconds: int = 60,
) -> str:
    """Build the short-lived server-to-server assertion used by tests and trusted gateways."""
    if not secret:
        raise ValueError("Identity assertion secret is required")
    if not 1 <= ttl_seconds <= MAX_ASSERTION_TTL_SECONDS:
        raise ValueError("Identity assertion TTL is outside the allowed range")
    issued_at = (now or datetime.now(UTC)).replace(microsecond=0)
    payload = {
        "aud": ASSERTION_AUDIENCE,
        "sub": subject,
        "email": email,
        "tenant_id": str(tenant_id),
        "iat": int(issued_at.timestamp()),
        "exp": int((issued_at + timedelta(seconds=ttl_seconds)).timestamp()),
    }
    encoded_payload = _b64url_encode(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )
    signing_input = f"{ASSERTION_VERSION}.{encoded_payload}".encode("ascii")
    signature = hmac.new(secret.encode("utf-8"), signing_input, sha256).digest()
    return f"{ASSERTION_VERSION}.{encoded_payload}.{_b64url_encode(signature)}"


def verify_identity_assertion(
    assertion: str,
    *,
    secret: str,
    now: datetime | None = None,
) -> AuthenticatedIdentity:
    """Verify a signed identity assertion without accepting client-controlled tenant headers."""
    try:
        version, encoded_payload, encoded_signature = assertion.split(".", 2)
    except ValueError as exc:
        raise ValueError("Malformed identity assertion") from exc
    if version != ASSERTION_VERSION:
        raise ValueError("Unsupported identity assertion version")

    signing_input = f"{version}.{encoded_payload}".encode("ascii")
    expected = hmac.new(secret.encode("utf-8"), signing_input, sha256).digest()
    try:
        supplied = _b64url_decode(encoded_signature)
    except (ValueError, UnicodeError) as exc:
        raise ValueError("Malformed identity assertion signature") from exc
    if not hmac.compare_digest(expected, supplied):
        raise ValueError("Invalid identity assertion signature")

    try:
        payload = json.loads(_b64url_decode(encoded_payload))
    except (ValueError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("Malformed identity assertion payload") from exc
    if not isinstance(payload, dict):
        raise ValueError("Malformed identity assertion payload")

    identity = _identity_from_payload(payload)
    current = now or datetime.now(UTC)
    if identity.issued_at > current + timedelta(seconds=CLOCK_SKEW_SECONDS):
        raise ValueError("Identity assertion is not yet valid")
    if identity.expires_at <= current - timedelta(seconds=CLOCK_SKEW_SECONDS):
        raise ValueError("Identity assertion has expired")
    if identity.expires_at - identity.issued_at > timedelta(
        seconds=MAX_ASSERTION_TTL_SECONDS
    ):
        raise ValueError("Identity assertion lifetime exceeds policy")
    return identity


def _identity_from_payload(payload: dict[str, Any]) -> AuthenticatedIdentity:
    if payload.get("aud") != ASSERTION_AUDIENCE:
        raise ValueError("Invalid identity assertion audience")
    subject = payload.get("sub")
    email = payload.get("email")
    tenant_id = payload.get("tenant_id")
    issued_at = payload.get("iat")
    expires_at = payload.get("exp")
    if not isinstance(subject, str) or not subject.strip():
        raise ValueError("Identity assertion subject is required")
    if not isinstance(email, str) or "@" not in email:
        raise ValueError("Identity assertion email is invalid")
    if not isinstance(issued_at, int) or not isinstance(expires_at, int):
        raise ValueError("Identity assertion timestamps are invalid")
    try:
        parsed_tenant_id = UUID(str(tenant_id))
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError("Identity assertion tenant is invalid") from exc
    return AuthenticatedIdentity(
        subject=subject,
        email=email,
        tenant_id=parsed_tenant_id,
        issued_at=datetime.fromtimestamp(issued_at, tz=UTC),
        expires_at=datetime.fromtimestamp(expires_at, tz=UTC),
    )


def _seat_governance_is_exempt(request: Request | None) -> bool:
    if request is None:
        return False
    path = request.url.path
    if path in SEAT_GOVERNANCE_BOOTSTRAP_PATHS:
        return True
    return any(path.startswith(prefix) for prefix in SEAT_GOVERNANCE_EXEMPT_PREFIXES)


def _enforce_seat_governance(
    identity: AuthenticatedIdentity,
    request: Request | None,
) -> AuthenticatedIdentity:
    seat_settings = SeatSettings.from_env()
    if not seat_settings.enabled or _seat_governance_is_exempt(request):
        return identity
    try:
        seat_settings.require_runtime()
        assert seat_settings.database_url is not None
        decision = SeatRepository(seat_settings.database_url).access_decision(
            tenant_id=identity.tenant_id,
            principal_id=identity.subject,
            write=(request is not None and request.method not in SAFE_METHODS),
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Seat-governance authorization is unavailable",
        ) from exc

    if decision.get("decision") != "ALLOW":
        reason = str(decision.get("reason") or "seat_access_denied")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=reason,
        )

    membership_id = decision.get("membership_id")
    roles = decision.get("roles")
    return AuthenticatedIdentity(
        subject=identity.subject,
        email=identity.email,
        tenant_id=identity.tenant_id,
        issued_at=identity.issued_at,
        expires_at=identity.expires_at,
        membership_id=UUID(str(membership_id)) if membership_id else None,
        role_ids=tuple(str(role) for role in roles) if isinstance(roles, list) else (),
        seat_state=str(decision.get("seat_state") or ""),
        seat_plan_code=str(decision.get("plan_code") or ""),
    )


def require_identity(
    request: Request,
    assertion: IdentityAssertionHeader = None,
) -> AuthenticatedIdentity:
    settings = Settings.from_env()
    try:
        settings.require_identity_assertions()
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    if assertion is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated identity is required",
        )
    assert settings.identity_assertion_secret is not None
    try:
        identity = verify_identity_assertion(
            assertion,
            secret=settings.identity_assertion_secret,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired identity assertion",
        ) from exc
    return _enforce_seat_governance(identity, request)
