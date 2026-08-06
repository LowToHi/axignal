from __future__ import annotations

from fastapi import HTTPException, status

from axignal_api.identity import (
    AuthenticatedIdentity,
    IdentityAssertionHeader,
    verify_identity_assertion,
)
from axignal_api.settings import Settings


def require_founder_identity(
    assertion: IdentityAssertionHeader = None,
) -> AuthenticatedIdentity:
    """Resolve founder identity without treating a tenant seat as global authority."""
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
            detail="Authenticated founder identity is required",
        )
    assert settings.identity_assertion_secret is not None
    try:
        return verify_identity_assertion(
            assertion,
            secret=settings.identity_assertion_secret,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired founder identity assertion",
        ) from exc
