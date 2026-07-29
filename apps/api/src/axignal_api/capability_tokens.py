from __future__ import annotations

import base64
import hmac
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from uuid import UUID

TOKEN_VERSION = "v1"
MAX_TTL_SECONDS = 300
CLOCK_SKEW_SECONDS = 15


@dataclass(frozen=True)
class CapabilityGrant:
    tenant_id: UUID
    reservation_id: UUID
    operation_id: str
    capability: str
    issued_at: datetime
    expires_at: datetime


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}".encode("ascii"))


def build_capability_token(
    *,
    secret: str,
    tenant_id: UUID,
    reservation_id: UUID,
    operation_id: str,
    capability: str,
    ttl_seconds: int = 120,
    now: datetime | None = None,
) -> str:
    if len(secret.encode("utf-8")) < 32:
        raise ValueError("Capability token secret must be at least 32 bytes")
    if not 1 <= ttl_seconds <= MAX_TTL_SECONDS:
        raise ValueError("Capability token TTL is outside the allowed range")
    issued_at = (now or datetime.now(UTC)).replace(microsecond=0)
    payload = {
        "aud": "axignal-capability",
        "tenant_id": str(tenant_id),
        "reservation_id": str(reservation_id),
        "operation_id": operation_id,
        "capability": capability,
        "iat": int(issued_at.timestamp()),
        "exp": int((issued_at + timedelta(seconds=ttl_seconds)).timestamp()),
    }
    encoded = _encode(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )
    signing_input = f"{TOKEN_VERSION}.{encoded}".encode("ascii")
    signature = hmac.new(secret.encode("utf-8"), signing_input, sha256).digest()
    return f"{TOKEN_VERSION}.{encoded}.{_encode(signature)}"


def verify_capability_token(
    token: str,
    *,
    secret: str,
    now: datetime | None = None,
) -> CapabilityGrant:
    try:
        version, encoded, supplied_signature = token.split(".", 2)
    except ValueError as exc:
        raise ValueError("Malformed capability token") from exc
    if version != TOKEN_VERSION:
        raise ValueError("Unsupported capability token version")
    expected = hmac.new(
        secret.encode("utf-8"),
        f"{version}.{encoded}".encode("ascii"),
        sha256,
    ).digest()
    try:
        supplied = _decode(supplied_signature)
    except (ValueError, UnicodeError) as exc:
        raise ValueError("Malformed capability token signature") from exc
    if not hmac.compare_digest(expected, supplied):
        raise ValueError("Invalid capability token signature")
    try:
        payload = json.loads(_decode(encoded))
        tenant_id = UUID(payload["tenant_id"])
        reservation_id = UUID(payload["reservation_id"])
        operation_id = str(payload["operation_id"])
        capability = str(payload["capability"])
        issued_at = datetime.fromtimestamp(int(payload["iat"]), tz=UTC)
        expires_at = datetime.fromtimestamp(int(payload["exp"]), tz=UTC)
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError("Malformed capability token payload") from exc
    if payload.get("aud") != "axignal-capability":
        raise ValueError("Invalid capability token audience")
    current = now or datetime.now(UTC)
    if issued_at > current + timedelta(seconds=CLOCK_SKEW_SECONDS):
        raise ValueError("Capability token is not yet valid")
    if expires_at <= current - timedelta(seconds=CLOCK_SKEW_SECONDS):
        raise ValueError("Capability token has expired")
    if expires_at - issued_at > timedelta(seconds=MAX_TTL_SECONDS):
        raise ValueError("Capability token lifetime exceeds policy")
    return CapabilityGrant(
        tenant_id=tenant_id,
        reservation_id=reservation_id,
        operation_id=operation_id,
        capability=capability,
        issued_at=issued_at,
        expires_at=expires_at,
    )
