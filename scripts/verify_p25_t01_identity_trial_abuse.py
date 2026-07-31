#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "data/security/identity-passwordless-trial-abuse-runtime.v0.1.json"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require(text: str, markers: tuple[str, ...], *, source: str) -> None:
    missing = [marker for marker in markers if marker not in text]
    if missing:
        raise SystemExit(f"{source} is missing required markers: {missing}")


def prohibit(text: str, markers: tuple[str, ...], *, source: str) -> None:
    present = [marker for marker in markers if marker in text]
    if present:
        raise SystemExit(f"{source} contains prohibited markers: {present}")


def main() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["task"] == "AX-GE2E-P25-T01"
    assert contract["status"] == "IMPLEMENTED_NOT_PUBLIC"
    assert contract["identity"]["primary_authenticator"] == "WEBAUTHN_PASSKEY"
    assert contract["identity"]["user_verification"] == "REQUIRED"
    assert contract["identity"]["tenant_from_browser"] is False
    assert contract["sessions"]["type"] == "OPAQUE_SERVER_SIDE_REVOCABLE"
    assert contract["sessions"]["local_storage"] is False
    assert contract["trial"]["duration_seconds"] == 604800
    assert contract["trial"]["starts_on"] == "FIRST_ADMITTED_AI_REQUEST"
    assert contract["trial"]["seat_capacity"] == 2
    assert contract["trial"]["token_budget_ceiling"] == 1_000_000
    assert contract["trial"]["direct_activation_allowed"] is False
    assert contract["anti_abuse"]["weak_signal_can_independently_block"] is False
    assert contract["authority"]["public_signup_enabled"] is False
    assert contract["authority"]["commercial_activation_authorised"] is False

    application = read("apps/api/src/axignal_api/application.py")
    require(
        application,
        (
            "identity_entitlement_router",
            "app.include_router(identity_router)",
            "app.include_router(identity_entitlement_router)",
            "app.include_router(entitlement_router)",
        ),
        source="application.py",
    )
    if application.index("app.include_router(identity_entitlement_router)") > application.index(
        "app.include_router(entitlement_router)"
    ):
        raise SystemExit("Governed entitlement routes must precede legacy routes")

    identity_routes = read("apps/api/src/axignal_api/identity_routes.py")
    require(
        identity_routes,
        (
            "ResidentKeyRequirement.REQUIRED",
            "UserVerificationRequirement.REQUIRED",
            "require_user_verification=True",
            "verify_registration_response",
            "verify_authentication_response",
            "recovery_codes = _recovery_codes()",
            '"/sessions/logout"',
            '"/trials/step-up/test"',
        ),
        source="identity_routes.py",
    )

    governed = read("apps/api/src/axignal_api/identity_entitlement_routes.py")
    require(
        governed,
        (
            '"/trials/activate"',
            '"/ai/authorize"',
            "start_prepared_trial",
            "direct activation is disabled",
            "A persistent passwordless identity is required",
        ),
        source="identity_entitlement_routes.py",
    )

    risk = read("apps/api/src/axignal_api/identity_risk.py")
    require(
        risk,
        (
            'local.split("+", 1)[0].replace(".", "")',
            'domain = "gmail.com"',
            'namespace="email-identity"',
            'namespace="installation"',
            'f"{address}/24"',
            'f"{address}/56"',
        ),
        source="identity_risk.py",
    )

    config = read("apps/api/src/axignal_api/identity_config.py")
    require(
        config,
        (
            "AXIGNAL_IDENTITY_HMAC_PEPPER",
            "AXIGNAL_TURNSTILE_SECRET",
            "Test email delivery is restricted to the test runtime",
            "Test bot provider is restricted to the test runtime",
            "trial_full_token_budget != 1_000_000",
        ),
        source="identity_config.py",
    )

    delivery = read("apps/api/src/axignal_api/identity_delivery.py")
    require(
        delivery,
        (
            "https://challenges.cloudflare.com/turnstile/v0/siteverify",
            "response.raise_for_status()",
            "bot_verification_failed",
            "This link expires shortly and can be used only once.",
        ),
        source="identity_delivery.py",
    )

    web_session = read("apps/web/lib/identity-server.ts")
    require(
        web_session,
        (
            '"__Host-axignal_session"',
            "httpOnly: true",
            'sameSite: "lax"',
            "delete payload.session_token",
            'headers.set("X-AXIGNAL-Session-Token", sessionToken)',
        ),
        source="identity-server.ts",
    )
    prohibit(
        web_session,
        ("localStorage", "sessionStorage", "tenant_id="),
        source="identity-server.ts",
    )

    auth_gate = read("apps/web/components/auth-gate.tsx")
    require(
        auth_gate,
        (
            "navigator.credentials.create",
            "navigator.credentials.get",
            "Verificar email de prueba y crear passkey",
            "Crear otra cuenta no concede otro trial",
            "window.history.replaceState",
        ),
        source="auth-gate.tsx",
    )
    prohibit(auth_gate, ("localStorage.setItem", "sessionStorage.setItem"), source="auth-gate.tsx")

    migrations = "\n".join(
        read(path)
        for path in (
            "infra/postgres/120-identity-passwordless-core.sql",
            "infra/postgres/121-identity-signup-webauthn-challenges.sql",
            "infra/postgres/122-identity-passkeys-sessions-recovery.sql",
            "infra/postgres/123-trial-abuse-runtime.sql",
        )
    )
    require(
        migrations,
        (
            "CREATE SCHEMA IF NOT EXISTS identity_private",
            "identity_private.identity_sessions",
            "identity_private.trial_grants",
            "identity_private.trial_subject_claims",
            "trial_strong_claim_once_idx",
            "REUSE_EXISTING_TRIAL",
            "STEP_UP_REQUIRED",
            "started_at = p_now",
            "expires_at = p_now + interval '7 days'",
            "trial_cost_budget_exhausted",
            "trial_concurrency_exhausted",
            "identity_append_only_ledger",
            "REVOKE ALL ON ALL TABLES IN SCHEMA identity_private FROM PUBLIC",
        ),
        source="P25 SQL migrations",
    )
    prohibit(
        migrations,
        (
            "raw_ip",
            "raw_installation",
            "password_hash",
            "browser_tenant_id",
        ),
        source="P25 SQL migrations",
    )

    dockerfile = read("infra/postgres/Dockerfile")
    for number in range(120, 124):
        if f"COPY {number}-" not in dockerfile:
            raise SystemExit(f"PostgreSQL image does not include migration {number}")

    workflow = read(".github/workflows/p25-t01-identity-trial-abuse-e2e.yml")
    require(
        workflow,
        (
            "Verify P25 contract",
            "Execute identity and trial-abuse database E2E",
            "Execute real WebAuthn browser lifecycle",
            "Verify evidence boundary",
        ),
        source="P25 workflow",
    )

    print("P25-T01 identity, passwordless and trial-abuse contract: PASS")


if __name__ == "__main__":
    main()
