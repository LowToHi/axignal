from __future__ import annotations

from dataclasses import dataclass
from os import environ


def _bool_env(name: str, default: bool = False) -> bool:
    raw = environ.get(name)
    if raw is None:
        return default
    return raw.strip().casefold() in {"1", "true", "yes", "on"}


def _int_env(name: str, default: int) -> int:
    raw = environ.get(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer") from exc


@dataclass(frozen=True)
class IdentityRuntimeSettings:
    enabled: bool
    database_url: str | None
    environment: str
    test_runtime_enabled: bool
    public_app_url: str | None
    rp_id: str | None
    rp_name: str
    expected_origin: str | None
    identity_pepper: str | None
    session_idle_seconds: int
    session_absolute_seconds: int
    session_touch_interval_seconds: int
    challenge_ttl_seconds: int
    email_provider: str
    bot_provider: str
    turnstile_secret: str | None
    smtp_host: str | None
    smtp_port: int
    smtp_username: str | None
    smtp_password: str | None
    smtp_from: str | None
    smtp_starttls: bool
    trusted_proxy_headers: bool
    trial_full_token_budget: int
    trial_restricted_token_budget: int
    trial_full_cost_budget_microunits: int
    trial_restricted_cost_budget_microunits: int

    @classmethod
    def from_env(cls) -> IdentityRuntimeSettings:
        return cls(
            enabled=_bool_env("AXIGNAL_IDENTITY_RUNTIME_ENABLED"),
            database_url=(
                environ.get("AXIGNAL_IDENTITY_DATABASE_URL")
                or environ.get("AXIGNAL_DATABASE_URL")
            ),
            environment=environ.get("AXIGNAL_ENVIRONMENT", "").strip().casefold(),
            test_runtime_enabled=_bool_env("AXIGNAL_TEST_RUNTIME_ENABLED"),
            public_app_url=environ.get("AXIGNAL_PUBLIC_APP_URL"),
            rp_id=environ.get("AXIGNAL_WEBAUTHN_RP_ID"),
            rp_name=environ.get("AXIGNAL_WEBAUTHN_RP_NAME", "AXIGNAL").strip(),
            expected_origin=environ.get("AXIGNAL_WEBAUTHN_ORIGIN"),
            identity_pepper=environ.get("AXIGNAL_IDENTITY_HMAC_PEPPER"),
            session_idle_seconds=_int_env(
                "AXIGNAL_IDENTITY_SESSION_IDLE_SECONDS", 60 * 60
            ),
            session_absolute_seconds=_int_env(
                "AXIGNAL_IDENTITY_SESSION_ABSOLUTE_SECONDS", 24 * 60 * 60
            ),
            session_touch_interval_seconds=_int_env(
                "AXIGNAL_IDENTITY_SESSION_TOUCH_SECONDS", 5 * 60
            ),
            challenge_ttl_seconds=_int_env(
                "AXIGNAL_IDENTITY_CHALLENGE_TTL_SECONDS", 10 * 60
            ),
            email_provider=environ.get(
                "AXIGNAL_IDENTITY_EMAIL_PROVIDER", "disabled"
            ).strip().casefold(),
            bot_provider=environ.get(
                "AXIGNAL_IDENTITY_BOT_PROVIDER", "disabled"
            ).strip().casefold(),
            turnstile_secret=environ.get("AXIGNAL_TURNSTILE_SECRET"),
            smtp_host=environ.get("AXIGNAL_SMTP_HOST"),
            smtp_port=_int_env("AXIGNAL_SMTP_PORT", 587),
            smtp_username=environ.get("AXIGNAL_SMTP_USERNAME"),
            smtp_password=environ.get("AXIGNAL_SMTP_PASSWORD"),
            smtp_from=environ.get("AXIGNAL_SMTP_FROM"),
            smtp_starttls=_bool_env("AXIGNAL_SMTP_STARTTLS", True),
            trusted_proxy_headers=_bool_env("AXIGNAL_TRUST_PROXY_HEADERS"),
            trial_full_token_budget=_int_env(
                "AXIGNAL_TRIAL_FULL_TOKEN_BUDGET", 1_000_000
            ),
            trial_restricted_token_budget=_int_env(
                "AXIGNAL_TRIAL_RESTRICTED_TOKEN_BUDGET", 250_000
            ),
            trial_full_cost_budget_microunits=_int_env(
                "AXIGNAL_TRIAL_FULL_COST_BUDGET_MICROUNITS", 5_000_000
            ),
            trial_restricted_cost_budget_microunits=_int_env(
                "AXIGNAL_TRIAL_RESTRICTED_COST_BUDGET_MICROUNITS", 1_000_000
            ),
        )

    def require_runtime(self) -> None:
        if not self.enabled:
            raise RuntimeError("Passwordless identity runtime is disabled")
        if not self.database_url:
            raise RuntimeError(
                "AXIGNAL_IDENTITY_DATABASE_URL or AXIGNAL_DATABASE_URL is required"
            )
        if not self.rp_id:
            raise RuntimeError("AXIGNAL_WEBAUTHN_RP_ID is required")
        if not self.expected_origin:
            raise RuntimeError("AXIGNAL_WEBAUTHN_ORIGIN is required")
        allowed_origins = ("https://", "http://localhost", "http://127.0.0.1")
        if not self.expected_origin.startswith(allowed_origins):
            raise RuntimeError("AXIGNAL_WEBAUTHN_ORIGIN must be HTTPS outside localhost")
        if not self.identity_pepper or len(self.identity_pepper.encode("utf-8")) < 32:
            raise RuntimeError("AXIGNAL_IDENTITY_HMAC_PEPPER must be at least 32 bytes")
        if not 300 <= self.session_idle_seconds <= 24 * 60 * 60:
            raise RuntimeError(
                "AXIGNAL_IDENTITY_SESSION_IDLE_SECONDS must be between 300 and 86400"
            )
        if not (
            self.session_idle_seconds
            <= self.session_absolute_seconds
            <= 7 * 24 * 60 * 60
        ):
            raise RuntimeError(
                "AXIGNAL_IDENTITY_SESSION_ABSOLUTE_SECONDS is outside policy"
            )
        if not 60 <= self.challenge_ttl_seconds <= 30 * 60:
            raise RuntimeError(
                "AXIGNAL_IDENTITY_CHALLENGE_TTL_SECONDS must be between 60 and 1800"
            )
        if self.trial_full_token_budget != 1_000_000:
            raise RuntimeError("The controlled trial token budget must remain 1,000,000")
        if not 1 <= self.trial_restricted_token_budget < self.trial_full_token_budget:
            raise RuntimeError("Restricted trial budget is outside policy")
        if self.trial_full_cost_budget_microunits <= 0:
            raise RuntimeError("Trial cost budget must be positive")
        if not (
            0
            < self.trial_restricted_cost_budget_microunits
            < self.trial_full_cost_budget_microunits
        ):
            raise RuntimeError("Restricted trial cost budget is outside policy")

    def require_email_delivery(self) -> None:
        self.require_runtime()
        if self.email_provider == "test":
            if self.environment != "test" or not self.test_runtime_enabled:
                raise RuntimeError("Test email delivery is restricted to the test runtime")
            return
        if self.email_provider != "smtp":
            raise RuntimeError("A verified identity email provider is required")
        if not self.public_app_url or not self.public_app_url.startswith("https://"):
            raise RuntimeError("AXIGNAL_PUBLIC_APP_URL must be HTTPS")
        if not self.smtp_host or not self.smtp_from:
            raise RuntimeError("SMTP host and sender are required")
        if bool(self.smtp_username) != bool(self.smtp_password):
            raise RuntimeError("SMTP username and password must be configured together")

    def require_bot_verification(self) -> None:
        self.require_runtime()
        if self.bot_provider == "test":
            if self.environment != "test" or not self.test_runtime_enabled:
                raise RuntimeError("Test bot provider is restricted to the test runtime")
            return
        if self.bot_provider != "turnstile":
            raise RuntimeError("A bot-verification provider is required")
        if not self.turnstile_secret:
            raise RuntimeError("AXIGNAL_TURNSTILE_SECRET is required")
