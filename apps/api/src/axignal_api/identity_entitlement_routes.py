from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from axignal_api.entitlements import (
    AIRequestAuthorization,
    AIRequestAuthorizationCommand,
    EntitlementView,
    TrialActivationCommand,
    activate_trial as legacy_activate_trial,
    authorize_ai_request as legacy_authorize_ai_request,
)
from axignal_api.identity import AuthenticatedIdentity, require_identity
from axignal_api.identity_config import IdentityRuntimeSettings
from axignal_api.identity_repository import IdentityRepository

router = APIRouter(prefix="/v1", tags=["identity-entitlement-governance"])
Authenticated = Annotated[AuthenticatedIdentity, Depends(require_identity)]


def _identity_repository() -> tuple[IdentityRuntimeSettings, IdentityRepository]:
    settings = IdentityRuntimeSettings.from_env()
    settings.require_runtime()
    assert settings.database_url is not None
    return settings, IdentityRepository(settings.database_url)


@router.post("/trials/activate", response_model=EntitlementView)
def governed_trial_activation(
    command: TrialActivationCommand,
    identity: Authenticated,
) -> EntitlementView:
    settings = IdentityRuntimeSettings.from_env()
    if not settings.enabled:
        return legacy_activate_trial(command, identity)
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=(
            "The controlled trial starts on the first admitted AI request; "
            "direct activation is disabled"
        ),
    )


@router.post("/ai/authorize", response_model=AIRequestAuthorization)
def governed_ai_authorization(
    command: AIRequestAuthorizationCommand,
    identity: Authenticated,
) -> AIRequestAuthorization:
    settings = IdentityRuntimeSettings.from_env()
    if not settings.enabled:
        return legacy_authorize_ai_request(command, identity)
    if identity.user_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="A persistent passwordless identity is required",
        )
    try:
        _, repository = _identity_repository()
        repository.start_prepared_trial(
            tenant_id=identity.tenant_id,
            user_id=identity.user_id,
            subject=identity.subject,
            email=identity.email,
        )
    except Exception as exc:
        message = str(exc)
        if "trial_not_ready" in message:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Trial eligibility requires verification or review",
            ) from exc
        if "trial_grant_not_found" in message:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="A governed trial grant is required",
            ) from exc
        if "trial_already_activated" not in message:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Trial-governance activation is unavailable",
            ) from exc
    return legacy_authorize_ai_request(command, identity)
