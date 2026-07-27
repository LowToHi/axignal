from dataclasses import dataclass
from os import environ
from pathlib import Path


def _bool_env(name: str, default: bool = False) -> bool:
    value = environ.get(name)
    if value is None:
        return default
    return value.strip().casefold() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    database_url: str | None
    valkey_url: str | None
    persistent_research_enabled: bool
    live_sources_enabled: bool
    world_bank_fixture_path: Path | None
    queue_key: str
    identity_assertion_secret: str | None

    @classmethod
    def from_env(cls) -> "Settings":
        fixture = environ.get("AXIGNAL_WORLD_BANK_FIXTURE_PATH")
        return cls(
            database_url=environ.get("AXIGNAL_DATABASE_URL"),
            valkey_url=environ.get("AXIGNAL_VALKEY_URL"),
            persistent_research_enabled=_bool_env("AXIGNAL_PERSISTENT_RESEARCH_ENABLED"),
            live_sources_enabled=_bool_env("AXIGNAL_LIVE_SOURCES_ENABLED"),
            world_bank_fixture_path=Path(fixture).resolve() if fixture else None,
            queue_key=environ.get("AXIGNAL_RESEARCH_QUEUE_KEY", "axignal:research:queue:v1"),
            identity_assertion_secret=environ.get("AXIGNAL_IDENTITY_ASSERTION_SECRET"),
        )

    def require_persistent_research(self) -> None:
        if not self.persistent_research_enabled:
            raise RuntimeError("Persistent research is disabled")
        if not self.database_url:
            raise RuntimeError("AXIGNAL_DATABASE_URL is required")
        if not self.valkey_url:
            raise RuntimeError("AXIGNAL_VALKEY_URL is required")

    def require_identity_assertions(self) -> None:
        if not self.identity_assertion_secret:
            raise RuntimeError("AXIGNAL_IDENTITY_ASSERTION_SECRET is required")
        if len(self.identity_assertion_secret.encode("utf-8")) < 32:
            raise RuntimeError("AXIGNAL_IDENTITY_ASSERTION_SECRET must be at least 32 bytes")
