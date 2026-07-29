from __future__ import annotations

import hashlib
import hmac
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class VerifiedStripeSignature:
    timestamp: int
    signature: str


def verify_stripe_signature(
    *,
    payload: bytes,
    header: str,
    secret: str,
    tolerance_seconds: int = 300,
    now: int | None = None,
) -> VerifiedStripeSignature:
    if not payload:
        raise ValueError("stripe_payload_empty")
    if not header:
        raise ValueError("stripe_signature_missing")
    if not secret.startswith("whsec_"):
        raise ValueError("stripe_webhook_secret_invalid")

    timestamp: int | None = None
    signatures: list[str] = []
    for item in header.split(","):
        key, separator, value = item.strip().partition("=")
        if not separator:
            continue
        if key == "t":
            try:
                timestamp = int(value)
            except ValueError as exc:
                raise ValueError("stripe_signature_timestamp_invalid") from exc
        elif key == "v1" and value:
            signatures.append(value)

    if timestamp is None or not signatures:
        raise ValueError("stripe_signature_malformed")

    current = int(time.time()) if now is None else now
    if abs(current - timestamp) > tolerance_seconds:
        raise ValueError("stripe_signature_tolerance_exceeded")

    signed_payload = str(timestamp).encode("ascii") + b"." + payload
    expected = hmac.new(
        secret.encode("utf-8"), signed_payload, hashlib.sha256
    ).hexdigest()
    for candidate in signatures:
        if hmac.compare_digest(expected, candidate):
            return VerifiedStripeSignature(timestamp=timestamp, signature=candidate)
    raise ValueError("stripe_signature_mismatch")


def build_test_stripe_signature(*, payload: bytes, secret: str, timestamp: int) -> str:
    signed_payload = str(timestamp).encode("ascii") + b"." + payload
    signature = hmac.new(
        secret.encode("utf-8"), signed_payload, hashlib.sha256
    ).hexdigest()
    return f"t={timestamp},v1={signature}"
