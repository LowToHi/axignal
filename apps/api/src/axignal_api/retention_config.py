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
class RetentionSettings:
    database_url: str | None
    deletion_requests_enabled: bool
    purge_worker_enabled: bool
    operator_suspension_enabled: bool
    retention_seconds: int
    purge_lease_seconds: int

    @classmethod
    def from_env(cls) -> RetentionSettings:
        return cls(
            database_url=(
                environ.get("AXIGNAL_RETENTION_DATABASE_URL")
                or environ.get("AXIGNAL_DATABASE_URL")
            ),
            deletion_requests_enabled=_bool_env("AXIGNAL_DELETION_REQUESTS_ENABLED"),
            purge_worker_enabled=_bool_env("AXIGNAL_PURGE_WORKER_ENABLED"),
            operator_suspension_enabled=_bool_env(
                "AXIGNAL_OPERATOR_SUSPENSION_ENABLED"
            ),
            retention_seconds=_int_env("AXIGNAL_TRIAL_RETENTION_SECONDS", 0),
            purge_lease_seconds=_int_env("AXIGNAL_PURGE_LEASE_SECONDS", 60),
        )

    def require_store(self) -> None:
        if not self.database_url:
            raise RuntimeError("AXIGNAL_RETENTION_DATABASE_URL is required")

    def require_deletion_requests(self) -> None:
        self.require_store()
        if not self.deletion_requests_enabled:
            raise RuntimeError("Workspace deletion requests are disabled")
        if self.retention_seconds < 1:
            raise RuntimeError("AXIGNAL_TRIAL_RETENTION_SECONDS must be configured")

    def require_purge_worker(self) -> None:
        self.require_store()
        if not self.purge_worker_enabled:
            raise RuntimeError("Workspace purge worker is disabled")
        if not 1 <= self.purge_lease_seconds <= 3_600:
            raise RuntimeError("AXIGNAL_PURGE_LEASE_SECONDS must be between 1 and 3600")

    def require_operator_suspension(self) -> None:
        self.require_store()
        if not self.operator_suspension_enabled:
            raise RuntimeError("Operator suspension is disabled")
