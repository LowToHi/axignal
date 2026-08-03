from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends

from axignal_api.identity import AuthenticatedIdentity, require_identity

router = APIRouter(prefix="/v1/axent", tags=["axent-step-up"])
Authenticated = Annotated[AuthenticatedIdentity, Depends(require_identity)]


@router.get("/step-up")
def step_up_status(identity: Authenticated) -> dict[str, Any]:
    satisfied = identity.assurance_level in {"AAL2", "PHISHING_RESISTANT"}
    return {
        "schema_version": "axignal.axent-step-up/v1",
        "satisfied": satisfied,
        "current_assurance_level": identity.assurance_level,
        "required_assurance_levels": ["AAL2", "PHISHING_RESISTANT"],
        "method": "PASSKEY_USER_VERIFICATION",
        "round_trip": {
            "options_endpoint": "/v1/identity/passkeys/authentication/options",
            "verify_endpoint": "/v1/identity/passkeys/authentication/verify",
            "session_behavior": (
                "Replace the current session with the newly verified passkey session, "
                "then request a fresh Axent confirmation preview."
            ),
        },
        "material_actions_available": satisfied,
    }
