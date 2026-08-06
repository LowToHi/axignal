from __future__ import annotations

import base64
import json
import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any, Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Header, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field
from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    options_to_json,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers.structs import (
    AttestationConveyancePreference,
    AuthenticatorSelectionCriteria,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

from axignal_api.identity_config import IdentityRuntimeSettings
from axignal_api.identity_delivery import IdentityEmailDelivery, verify_bot_token
from axignal_api.identity_repository import IdentityRepository
from axignal_api.identity_risk import (
    digest_random_token,
    email_identity_key,
    keyed_digest,
    risk_subjects,
)

router = APIRouter(prefix="/v1/identity", tags=["identity-passwordless"])

InstallationHeader = Annotated[
    str | None,
    Header(alias="X-AXIGNAL-Installation-ID"),
]
SessionHeader = Annotated[
    str | None,
    Header(alias="X-AXIGNAL-Session-Token"),
]


class SignupStartCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=320)
    bot_token: str = Field(min_length=3, max_length=4_096)


class SignupStartView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    accepted: Literal[True] = True
    test_verification_token: str | None = None


class SignupVerifyCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token: str = Field(min_length=20, max_length=512)


class SignupVerifyView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    registration_ticket: str
    decision: str
    trial_state: str
    reason_codes: list[str]


class RegistrationOptionsCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    registration_ticket: str = Field(min_length=20, max_length=512)


class PasskeyVerifyCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    registration_ticket: str = Field(min_length=20, max_length=512)
    challenge: str = Field(min_length=20, max_length=512)
    credential: dict[str, Any]


class AuthenticationOptionsCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bot_token: str = Field(min_length=3, max_length=4_096)


class AuthenticationVerifyCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    challenge: str = Field(min_length=20, max_length=512)
    credential: dict[str, Any]


class RecoveryStartCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=320)
    recovery_code: str = Field(min_length=8, max_length=100)
    bot_token: str = Field(min_length=3, max_length=4_096)


class RecoveryStartView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recovery_ticket: str


class SessionView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: UUID
    session_id: UUID
    subject: str
    email: str
    tenant_id: UUID
    membership_id: UUID | None = None
    roles: list[str] = Field(default_factory=list)
    auth_method: str
    assurance_level: str
    authenticated_at: datetime
    step_up_valid_until: datetime | None
    absolute_expires_at: datetime


class AuthenticationResultView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_token: str
    identity: SessionView
    recovery_codes: list[str] = Field(default_factory=list)


class LogoutView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    revoked: bool


class TrialStatusView(BaseModel):
    model_config = ConfigDict(extra="allow")

    trial_grant_id: UUID
    tenant_id: UUID
    state: str
    decision: str
    risk_score: int
    reason_codes: list[str]
    token_budget_ceiling: int
    cost_budget_microunits: int
    prepared_at: datetime
    started_at: datetime | None
    expires_at: datetime | None


class TestStepUpCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_type: Literal["VERIFIED_PHONE", "PAYMENT_INSTRUMENT"]
    evidence_value: str = Field(min_length=6, max_length=500)
    confirm_test_step_up: Literal[True]


def _runtime() -> tuple[IdentityRuntimeSettings, IdentityRepository]:
    settings = IdentityRuntimeSettings.from_env()
    try:
        settings.require_runtime()
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    assert settings.database_url is not None
    return settings, IdentityRepository(settings.database_url)


def _b64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    encoded = (value + "=" * (-len(value) % 4)).encode("ascii")
    return base64.urlsafe_b64decode(encoded)


def _request_ip(request: Request, settings: IdentityRuntimeSettings) -> str | None:
    if settings.trusted_proxy_headers:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",", 1)[0].strip()
    return request.client.host if request.client else None


def _context_digests(
    *,
    request: Request,
    settings: IdentityRuntimeSettings,
    installation: str,
) -> tuple[str, str, str]:
    assert settings.identity_pepper is not None
    subjects = risk_subjects(
        email="context-placeholder@axignal.invalid",
        installation_id=installation,
        network=_request_ip(request, settings),
        pepper=settings.identity_pepper,
    )
    user_agent = request.headers.get("user-agent", "unknown")[:500]
    return (
        subjects["installation_hmac"],
        subjects["network_hmac"],
        keyed_digest(
            user_agent,
            pepper=settings.identity_pepper,
            namespace="user-agent",
        ),
    )


def _store_error(exc: Exception, *, generic: bool = False) -> None:
    message = str(exc)
    if generic:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The authentication request could not be completed",
        ) from exc
    conflict = {
        "email_challenge_not_found": "Verification link is invalid",
        "email_challenge_expired": "Verification link has expired",
        "bootstrap_ticket_not_found": "Registration ticket is invalid",
        "bootstrap_ticket_expired": "Registration ticket has expired",
        "webauthn_challenge_not_found": "Passkey challenge is invalid",
        "webauthn_challenge_expired": "Passkey challenge has expired",
        "webauthn_credential_not_found": "Passkey is not recognised",
        "webauthn_sign_count_regression": (
            "Passkey was rejected as potentially cloned"
        ),
        "identity_session_not_found": "Session is invalid",
        "identity_session_expired": "Session has expired",
        "trial_step_up_not_pending": "Trial step-up is not pending",
    }
    for marker, detail in conflict.items():
        if marker in message:
            raise HTTPException(status_code=409, detail=detail) from exc
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=f"Identity runtime unavailable: {exc.__class__.__name__}",
    ) from exc


def _trial_state(decision: str) -> str:
    if decision in {"ALLOW", "ALLOW_RESTRICTED"}:
        return "READY"
    if decision == "REUSE_EXISTING_TRIAL":
        return "REUSED"
    return "ELIGIBILITY_PENDING"


def _recovery_codes() -> list[str]:
    return [
        "-".join(
            [
                "AX",
                secrets.token_hex(2).upper(),
                secrets.token_hex(2).upper(),
                secrets.token_hex(2).upper(),
            ]
        )
        for _ in range(8)
    ]


@router.post("/signup/start", response_model=SignupStartView, status_code=202)
def signup_start(
    command: SignupStartCommand,
    request: Request,
    installation_id: InstallationHeader = None,
) -> SignupStartView:
    settings, repository = _runtime()
    try:
        settings.require_email_delivery()
        verify_bot_token(
            settings=settings,
            token=command.bot_token,
            remote_ip=_request_ip(request, settings),
        )
        if installation_id is None:
            raise ValueError("installation_id_required")
        assert settings.identity_pepper is not None
        subjects = risk_subjects(
            email=command.email,
            installation_id=installation_id,
            network=_request_ip(request, settings),
            pepper=settings.identity_pepper,
        )
        if not repository.consume_rate_limit(
            key_hmac=subjects["email_identity_hmac"],
            route_key="signup-email",
            limit=3,
            window_seconds=60 * 60,
        ):
            raise RuntimeError("signup_rate_limited")
        if not repository.consume_rate_limit(
            key_hmac=subjects["network_hmac"],
            route_key="signup-network",
            limit=20,
            window_seconds=60 * 60,
        ):
            raise RuntimeError("signup_rate_limited")
        token = secrets.token_urlsafe(48)
        repository.begin_email_challenge(
            purpose="SIGNUP",
            token_digest=digest_random_token(token),
            subjects=subjects,
            expires_at=(
                datetime.now(UTC)
                + timedelta(seconds=settings.challenge_ttl_seconds)
            ),
        )
        receipt = IdentityEmailDelivery(settings).deliver_verification(
            recipient=subjects["email_normalized"],
            token=token,
        )
    except ValueError:
        return SignupStartView()
    except RuntimeError as exc:
        if "rate_limited" in str(exc):
            return SignupStartView()
        if "bot_verification" in str(exc):
            raise HTTPException(status_code=403, detail="Bot verification failed") from exc
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return SignupStartView(test_verification_token=receipt.test_token)


@router.post("/signup/verify", response_model=SignupVerifyView)
def signup_verify(command: SignupVerifyCommand) -> SignupVerifyView:
    settings, repository = _runtime()
    registration_ticket = secrets.token_urlsafe(48)
    try:
        result = repository.consume_signup_challenge(
            token_digest=digest_random_token(command.token),
            registration_ticket_digest=digest_random_token(registration_ticket),
            operation_id=f"op_signup_{uuid4().hex}",
            full_token_budget=settings.trial_full_token_budget,
            restricted_token_budget=settings.trial_restricted_token_budget,
            full_cost_budget_microunits=(
                settings.trial_full_cost_budget_microunits
            ),
            restricted_cost_budget_microunits=(
                settings.trial_restricted_cost_budget_microunits
            ),
        )
    except Exception as exc:
        _store_error(exc)
    reasons = result.get("reason_codes")
    return SignupVerifyView(
        registration_ticket=registration_ticket,
        decision=str(result["decision"]),
        trial_state=_trial_state(str(result["decision"])),
        reason_codes=(
            [str(item) for item in reasons]
            if isinstance(reasons, list)
            else []
        ),
    )


@router.post("/passkeys/registration/options")
def registration_options(command: RegistrationOptionsCommand) -> dict[str, Any]:
    settings, repository = _runtime()
    ticket_digest = digest_random_token(command.registration_ticket)
    purpose = "PASSKEY_REGISTRATION"
    try:
        ticket = repository.resolve_bootstrap_ticket(
            token_digest=ticket_digest,
            purpose=purpose,
        )
    except Exception:
        try:
            purpose = "RECOVERY"
            ticket = repository.resolve_bootstrap_ticket(
                token_digest=ticket_digest,
                purpose=purpose,
            )
        except Exception as exc:
            _store_error(exc)
    challenge = secrets.token_bytes(32)
    challenge_value = _b64url(challenge)
    options = generate_registration_options(
        rp_id=settings.rp_id,
        rp_name=settings.rp_name,
        user_id=bytes.fromhex(str(ticket["webauthn_user_handle_hex"])),
        user_name=str(ticket["email"]),
        user_display_name=str(ticket["email"]),
        challenge=challenge,
        attestation=AttestationConveyancePreference.NONE,
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.REQUIRED,
            user_verification=UserVerificationRequirement.REQUIRED,
        ),
    )
    purpose_name = (
        "RECOVERY_REGISTRATION" if purpose == "RECOVERY" else "REGISTRATION"
    )
    repository.create_webauthn_challenge(
        challenge_value=challenge_value,
        challenge_digest=digest_random_token(challenge_value),
        purpose=purpose_name,
        user_id=UUID(str(ticket["user_id"])),
        bootstrap_ticket_id=UUID(str(ticket["bootstrap_ticket_id"])),
        rp_id=str(settings.rp_id),
        expected_origin=str(settings.expected_origin),
        expires_at=(
            datetime.now(UTC)
            + timedelta(seconds=settings.challenge_ttl_seconds)
        ),
    )
    return json.loads(options_to_json(options))


@router.post(
    "/passkeys/registration/verify",
    response_model=AuthenticationResultView,
)
def registration_verify(
    command: PasskeyVerifyCommand,
    request: Request,
    installation_id: InstallationHeader = None,
) -> AuthenticationResultView:
    settings, repository = _runtime()
    if installation_id is None:
        raise HTTPException(status_code=400, detail="Installation identifier required")
    challenge_digest = digest_random_token(command.challenge)
    try:
        challenge = repository.pending_webauthn_challenge(
            challenge_digest=challenge_digest,
            purpose="REGISTRATION",
        )
    except Exception:
        try:
            challenge = repository.pending_webauthn_challenge(
                challenge_digest=challenge_digest,
                purpose="RECOVERY_REGISTRATION",
            )
        except Exception as exc:
            _store_error(exc)
    try:
        verification = verify_registration_response(
            credential=command.credential,
            expected_challenge=_b64url_decode(str(challenge["challenge_value"])),
            expected_rp_id=str(settings.rp_id),
            expected_origin=str(settings.expected_origin),
            require_user_verification=True,
        )
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Passkey verification failed") from exc

    session_token = secrets.token_urlsafe(64)
    recovery_codes = _recovery_codes()
    installation_hmac, network_hmac, user_agent_hmac = _context_digests(
        request=request,
        settings=settings,
        installation=installation_id,
    )
    device_type_value = getattr(
        verification.credential_device_type,
        "value",
        str(verification.credential_device_type),
    )
    device_type = str(device_type_value).upper()
    if device_type not in {"SINGLE_DEVICE", "MULTI_DEVICE"}:
        device_type = "UNKNOWN"
    response = command.credential.get("response")
    transports = (
        [str(item) for item in response.get("transports", [])]
        if isinstance(response, dict)
        else []
    )
    try:
        repository.complete_registration(
            challenge_digest=challenge_digest,
            bootstrap_ticket_digest=digest_random_token(
                command.registration_ticket
            ),
            credential_id=_b64url(verification.credential_id),
            credential_public_key=verification.credential_public_key,
            sign_count=verification.sign_count,
            transports=transports,
            device_type=device_type,
            backed_up=bool(verification.credential_backed_up),
            aaguid=str(getattr(verification, "aaguid", "") or "") or None,
            session_token_digest=digest_random_token(session_token),
            installation_hmac=installation_hmac,
            network_hmac=network_hmac,
            user_agent_hmac=user_agent_hmac,
            recovery_code_digests=[
                keyed_digest(
                    code.casefold(),
                    pepper=str(settings.identity_pepper),
                    namespace="recovery-code",
                )
                for code in recovery_codes
            ],
            idle_seconds=settings.session_idle_seconds,
            absolute_seconds=settings.session_absolute_seconds,
        )
        resolved = repository.resolve_session(
            token_digest=digest_random_token(session_token),
            touch_interval_seconds=settings.session_touch_interval_seconds,
        )
    except Exception as exc:
        _store_error(exc)
    return AuthenticationResultView(
        session_token=session_token,
        identity=SessionView.model_validate(resolved),
        recovery_codes=recovery_codes,
    )


@router.post("/passkeys/authentication/options")
def authentication_options(
    command: AuthenticationOptionsCommand,
    request: Request,
    installation_id: InstallationHeader = None,
) -> dict[str, Any]:
    settings, repository = _runtime()
    verify_bot_token(
        settings=settings,
        token=command.bot_token,
        remote_ip=_request_ip(request, settings),
    )
    if installation_id is None:
        raise HTTPException(status_code=400, detail="Installation identifier required")
    installation_hmac, network_hmac, _ = _context_digests(
        request=request,
        settings=settings,
        installation=installation_id,
    )
    if not repository.consume_rate_limit(
        key_hmac=installation_hmac,
        route_key="passkey-auth-installation",
        limit=20,
        window_seconds=15 * 60,
    ):
        raise HTTPException(status_code=429, detail="Too many authentication attempts")
    if not repository.consume_rate_limit(
        key_hmac=network_hmac,
        route_key="passkey-auth-network",
        limit=100,
        window_seconds=15 * 60,
    ):
        raise HTTPException(status_code=429, detail="Too many authentication attempts")

    challenge = secrets.token_bytes(32)
    challenge_value = _b64url(challenge)
    options = generate_authentication_options(
        rp_id=settings.rp_id,
        challenge=challenge,
        user_verification=UserVerificationRequirement.REQUIRED,
    )
    repository.create_webauthn_challenge(
        challenge_value=challenge_value,
        challenge_digest=digest_random_token(challenge_value),
        purpose="AUTHENTICATION",
        user_id=None,
        bootstrap_ticket_id=None,
        rp_id=str(settings.rp_id),
        expected_origin=str(settings.expected_origin),
        expires_at=(
            datetime.now(UTC)
            + timedelta(seconds=settings.challenge_ttl_seconds)
        ),
    )
    return json.loads(options_to_json(options))


@router.post(
    "/passkeys/authentication/verify",
    response_model=AuthenticationResultView,
)
def authentication_verify(
    command: AuthenticationVerifyCommand,
    request: Request,
    installation_id: InstallationHeader = None,
) -> AuthenticationResultView:
    settings, repository = _runtime()
    if installation_id is None:
        raise HTTPException(status_code=400, detail="Installation identifier required")
    credential_id = command.credential.get("id")
    if not isinstance(credential_id, str):
        raise HTTPException(status_code=401, detail="Passkey verification failed")
    challenge_digest = digest_random_token(command.challenge)
    try:
        challenge = repository.pending_webauthn_challenge(
            challenge_digest=challenge_digest,
            purpose="AUTHENTICATION",
        )
        authenticator = repository.credential_for_authentication(
            credential_id=credential_id,
        )
        verification = verify_authentication_response(
            credential=command.credential,
            expected_challenge=_b64url_decode(str(challenge["challenge_value"])),
            expected_rp_id=str(settings.rp_id),
            expected_origin=str(settings.expected_origin),
            credential_public_key=bytes.fromhex(
                str(authenticator["credential_public_key_hex"])
            ),
            credential_current_sign_count=int(authenticator["sign_count"]),
            require_user_verification=True,
        )
    except Exception as exc:
        _store_error(exc, generic=True)

    session_token = secrets.token_urlsafe(64)
    installation_hmac, network_hmac, user_agent_hmac = _context_digests(
        request=request,
        settings=settings,
        installation=installation_id,
    )
    try:
        repository.complete_authentication(
            challenge_digest=challenge_digest,
            credential_id=credential_id,
            new_sign_count=verification.new_sign_count,
            session_token_digest=digest_random_token(session_token),
            installation_hmac=installation_hmac,
            network_hmac=network_hmac,
            user_agent_hmac=user_agent_hmac,
            idle_seconds=settings.session_idle_seconds,
            absolute_seconds=settings.session_absolute_seconds,
        )
        resolved = repository.resolve_session(
            token_digest=digest_random_token(session_token),
            touch_interval_seconds=settings.session_touch_interval_seconds,
        )
    except Exception as exc:
        _store_error(exc, generic=True)
    return AuthenticationResultView(
        session_token=session_token,
        identity=SessionView.model_validate(resolved),
    )


@router.post("/recovery/start", response_model=RecoveryStartView)
def recovery_start(
    command: RecoveryStartCommand,
    request: Request,
) -> RecoveryStartView:
    settings, repository = _runtime()
    verify_bot_token(
        settings=settings,
        token=command.bot_token,
        remote_ip=_request_ip(request, settings),
    )
    assert settings.identity_pepper is not None
    try:
        email_key = email_identity_key(command.email)
        email_identity_hmac = keyed_digest(
            email_key,
            pepper=settings.identity_pepper,
            namespace="email-identity",
        )
        code_digest = keyed_digest(
            command.recovery_code.strip().casefold(),
            pepper=settings.identity_pepper,
            namespace="recovery-code",
        )
        ticket = secrets.token_urlsafe(48)
        repository.begin_recovery(
            email_identity_hmac=email_identity_hmac,
            code_digest=code_digest,
            recovery_ticket_digest=digest_random_token(ticket),
        )
    except Exception as exc:
        _store_error(exc, generic=True)
    return RecoveryStartView(recovery_ticket=ticket)


@router.get("/sessions/resolve", response_model=SessionView)
def resolve_session(session_token: SessionHeader = None) -> SessionView:
    settings, repository = _runtime()
    if not session_token:
        raise HTTPException(status_code=401, detail="Session required")
    try:
        result = repository.resolve_session(
            token_digest=digest_random_token(session_token),
            touch_interval_seconds=settings.session_touch_interval_seconds,
        )
    except Exception as exc:
        _store_error(exc, generic=True)
    return SessionView.model_validate(result)


@router.post("/sessions/logout", response_model=LogoutView)
def logout(session_token: SessionHeader = None) -> LogoutView:
    _, repository = _runtime()
    if not session_token:
        return LogoutView(revoked=False)
    return LogoutView(
        revoked=repository.revoke_session(
            token_digest=digest_random_token(session_token),
            reason="USER_LOGOUT",
        )
    )


@router.get("/trials/current", response_model=TrialStatusView)
def trial_status(session_token: SessionHeader = None) -> TrialStatusView:
    settings, repository = _runtime()
    if not session_token:
        raise HTTPException(status_code=401, detail="Session required")
    try:
        identity = repository.resolve_session(
            token_digest=digest_random_token(session_token),
            touch_interval_seconds=settings.session_touch_interval_seconds,
        )
        trial = repository.trial_status(tenant_id=UUID(str(identity["tenant_id"])))
    except Exception as exc:
        _store_error(exc)
    if trial is None:
        raise HTTPException(status_code=404, detail="Trial grant not found")
    return TrialStatusView.model_validate(trial)


@router.post("/trials/step-up/test", response_model=TrialStatusView)
def trial_test_step_up(
    command: TestStepUpCommand,
    session_token: SessionHeader = None,
) -> TrialStatusView:
    settings, repository = _runtime()
    if settings.environment != "test" or not settings.test_runtime_enabled:
        raise HTTPException(status_code=404, detail="Not found")
    if not session_token:
        raise HTTPException(status_code=401, detail="Session required")
    identity = repository.resolve_session(
        token_digest=digest_random_token(session_token),
        touch_interval_seconds=settings.session_touch_interval_seconds,
    )
    assert settings.identity_pepper is not None
    claim_hmac = keyed_digest(
        command.evidence_value.strip().casefold(),
        pepper=settings.identity_pepper,
        namespace=f"step-up:{command.evidence_type}",
    )
    try:
        trial = repository.approve_test_step_up(
            tenant_id=UUID(str(identity["tenant_id"])),
            user_id=UUID(str(identity["user_id"])),
            claim_type=command.evidence_type,
            claim_hmac=claim_hmac,
            actor_subject=str(identity["subject"]),
            full_token_budget=settings.trial_full_token_budget,
            full_cost_budget_microunits=(
                settings.trial_full_cost_budget_microunits
            ),
        )
    except Exception as exc:
        _store_error(exc)
    return TrialStatusView.model_validate(trial)
