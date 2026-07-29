from __future__ import annotations

from dataclasses import dataclass
from os import environ


def _bool_env(name: str, default: bool = False) -> bool:
    value = environ.get(name)
    if value is None:
        return default
    return value.strip().casefold() in {"1", "true", "yes", "on"}


def _int_env(name: str, default: int) -> int:
    value = environ.get(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer") from exc


@dataclass(frozen=True)
class EntitlementSettings:
    database_url: str | None
    trial_runtime_enabled: bool
    end_user_ai_enabled: bool
    capability_token_secret: str | None
    capability_token_ttl_seconds: int

    @classmethod
    def from_env(cls) -> EntitlementSettings:
        return cls(
            database_url=(
                environ.get("AXIGNAL_ENTITLEMENT_DATABASE_URL")
                or environ.get("AXIGNAL_DATABASE_URL")
            ),
            trial_runtime_enabled=_bool_env("AXIGNAL_TRIAL_RUNTIME_ENABLED"),
            end_user_ai_enabled=_bool_env("AXIGNAL_END_USER_AI_ENABLED"),
            capability_token_secret=environ.get("AXIGNAL_CAPABILITY_TOKEN_SECRET"),
            capability_token_ttl_seconds=_int_env(
                "AXIGNAL_CAPABILITY_TOKEN_TTL_SECONDS",
                120,
            ),
        )

    def require_store(self) -> None:
        if not self.database_url:
            raise RuntimeError("AXIGNAL_ENTITLEMENT_DATABASE_URL is required")

    def require_trial_activation(self) -> None:
        self.require_store()
        if not self.trial_runtime_enabled:
            raise RuntimeError("Controlled trial runtime is disabled")

    def require_ai_authorization(self) -> None:
        self.require_store()
        if not self.end_user_ai_enabled:
            raise RuntimeError("End-user AXIGNAL AI is disabled")
        if not self.capability_token_secret:
            raise RuntimeError("AXIGNAL_CAPABILITY_TOKEN_SECRET is required")
        if len(self.capability_token_secret.encode("utf-8")) < 32:
            raise RuntimeError(
                "AXIGNAL_CAPABILITY_TOKEN_SECRET must be at least 32 bytes"
            )
        if not 1 <= self.capability_token_ttl_seconds <= 300:
            raise RuntimeError(
                "AXIGNAL_CAPABILITY_TOKEN_TTL_SECONDS must be between 1 and 300"
            )
