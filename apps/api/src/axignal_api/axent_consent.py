from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID


class ConsentError(ValueError):
    """Raised when an Axent confirmation token is invalid or stale."""


@dataclass(frozen=True)
class ConsentClaims:
    confirmation_id: UUID
    tenant_id: UUID
    conversation_id: UUID
    subject: str
    action_type: str
    parameters_hash: str
    before_state_hash: str
    assurance_level: str
    issued_at: datetime
    expires_at: datetime
    nonce: str


def canonical_hash(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        default=str,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def token_hash(token: str) -> str:
    return f"sha256:{hashlib.sha256(token.encode('utf-8')).hexdigest()}"


def _b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    try:
        return base64.urlsafe_b64decode(value + padding)
    except Exception as exc:  # pragma: no cover - library-specific failures
        raise ConsentError("confirmation_token_malformed") from exc


def _sign(payload: str, secret: str) -> str:
    signature = hmac.new(
        secret.encode("utf-8"),
        f"axignal.axent-consent/v1.{payload}".encode("ascii"),
        hashlib.sha256,
    ).digest()
    return _b64url_encode(signature)


def issue_confirmation_token(
    *,
    confirmation_id: UUID,
    tenant_id: UUID,
    conversation_id: UUID,
    subject: str,
    action_type: str,
    parameters_hash: str,
    before_state_hash: str,
    assurance_level: str,
    secret: str,
    now: datetime | None = None,
    lifetime: timedelta = timedelta(minutes=5),
) -> tuple[str, ConsentClaims]:
    if len(secret) < 32:
        raise ConsentError("confirmation_secret_too_short")
    issued_at = (now or datetime.now(UTC)).astimezone(UTC)
    expires_at = issued_at + lifetime
    claims = ConsentClaims(
        confirmation_id=confirmation_id,
        tenant_id=tenant_id,
        conversation_id=conversation_id,
        subject=subject,
        action_type=action_type,
        parameters_hash=parameters_hash,
        before_state_hash=before_state_hash,
        assurance_level=assurance_level,
        issued_at=issued_at,
        expires_at=expires_at,
        nonce=secrets.token_urlsafe(18),
    )
    body = {
        "cid": str(claims.confirmation_id),
        "tid": str(claims.tenant_id),
        "coid": str(claims.conversation_id),
        "sub": claims.subject,
        "act": claims.action_type,
        "ph": claims.parameters_hash,
        "sh": claims.before_state_hash,
        "aal": claims.assurance_level,
        "iat": int(claims.issued_at.timestamp()),
        "exp": int(claims.expires_at.timestamp()),
        "nonce": claims.nonce,
    }
    payload = _b64url_encode(
        json.dumps(body, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    return f"axc1.{payload}.{_sign(payload, secret)}", claims


def verify_confirmation_token(
    token: str,
    *,
    secret: str,
    expected_tenant_id: UUID,
    expected_conversation_id: UUID,
    expected_subject: str,
    expected_action_type: str,
    expected_parameters_hash: str,
    expected_before_state_hash: str,
    minimum_assurance: frozenset[str] = frozenset({"AAL2", "PHISHING_RESISTANT"}),
    now: datetime | None = None,
) -> ConsentClaims:
    try:
        prefix, payload, supplied_signature = token.split(".", 2)
    except ValueError as exc:
        raise ConsentError("confirmation_token_malformed") from exc
    if prefix != "axc1":
        raise ConsentError("confirmation_token_version_unsupported")
    if not hmac.compare_digest(_sign(payload, secret), supplied_signature):
        raise ConsentError("confirmation_token_signature_invalid")
    try:
        body = json.loads(_b64url_decode(payload))
        claims = ConsentClaims(
            confirmation_id=UUID(body["cid"]),
            tenant_id=UUID(body["tid"]),
            conversation_id=UUID(body["coid"]),
            subject=str(body["sub"]),
            action_type=str(body["act"]),
            parameters_hash=str(body["ph"]),
            before_state_hash=str(body["sh"]),
            assurance_level=str(body["aal"]),
            issued_at=datetime.fromtimestamp(int(body["iat"]), UTC),
            expires_at=datetime.fromtimestamp(int(body["exp"]), UTC),
            nonce=str(body["nonce"]),
        )
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ConsentError("confirmation_token_claims_invalid") from exc

    current = (now or datetime.now(UTC)).astimezone(UTC)
    if claims.expires_at <= current:
        raise ConsentError("confirmation_token_expired")
    if claims.issued_at > current + timedelta(seconds=30):
        raise ConsentError("confirmation_token_issued_in_future")
    expected = (
        (claims.tenant_id, expected_tenant_id, "tenant"),
        (claims.conversation_id, expected_conversation_id, "conversation"),
        (claims.subject, expected_subject, "subject"),
        (claims.action_type, expected_action_type, "action"),
        (claims.parameters_hash, expected_parameters_hash, "parameters"),
        (claims.before_state_hash, expected_before_state_hash, "state"),
    )
    for actual, required, name in expected:
        if not hmac.compare_digest(str(actual), str(required)):
            raise ConsentError(f"confirmation_token_{name}_mismatch")
    if claims.assurance_level not in minimum_assurance:
        raise ConsentError("confirmation_token_assurance_insufficient")
    return claims
