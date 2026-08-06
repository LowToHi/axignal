from __future__ import annotations

from dataclasses import dataclass
from os import environ


def _bool_env(name: str, default: bool = False) -> bool:
    value = environ.get(name)
    if value is None:
        return default
    return value.strip().casefold() in {"1", "true", "yes", "on"}


def _csv_env(name: str) -> tuple[str, ...]:
    return tuple(
        item.strip()
        for item in environ.get(name, "").split(",")
        if item.strip()
    )


def _int_env(name: str, default: int) -> int:
    raw = environ.get(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer") from exc


@dataclass(frozen=True)
class SeatSettings:
    enabled: bool
    database_url: str | None
    owner_subjects: tuple[str, ...]
    invitation_provider: str
    invitation_ttl_hours: int
    public_base_url: str | None
    environment: str
    test_runtime_enabled: bool
    smtp_host: str | None
    smtp_port: int
    smtp_username: str | None
    smtp_password: str | None
    smtp_from: str | None
    smtp_starttls: bool

    @classmethod
    def from_env(cls) -> SeatSettings:
        return cls(
            enabled=_bool_env("AXIGNAL_SEAT_GOVERNANCE_ENABLED"),
            database_url=(
                environ.get("AXIGNAL_SEAT_DATABASE_URL")
                or environ.get("AXIGNAL_DATABASE_URL")
            ),
            owner_subjects=_csv_env("AXIGNAL_ORGANISATION_OWNER_SUBJECTS"),
            invitation_provider=environ.get(
                "AXIGNAL_SEAT_INVITATION_PROVIDER", "disabled"
            ).strip().casefold(),
            invitation_ttl_hours=_int_env(
                "AXIGNAL_SEAT_INVITATION_TTL_HOURS", 72
            ),
            public_base_url=environ.get("AXIGNAL_PUBLIC_APP_URL"),
            environment=environ.get("AXIGNAL_ENVIRONMENT", "").strip().casefold(),
            test_runtime_enabled=_bool_env("AXIGNAL_TEST_RUNTIME_ENABLED"),
            smtp_host=environ.get("AXIGNAL_SMTP_HOST"),
            smtp_port=_int_env("AXIGNAL_SMTP_PORT", 587),
            smtp_username=environ.get("AXIGNAL_SMTP_USERNAME"),
            smtp_password=environ.get("AXIGNAL_SMTP_PASSWORD"),
            smtp_from=environ.get("AXIGNAL_SMTP_FROM"),
            smtp_starttls=_bool_env("AXIGNAL_SMTP_STARTTLS", True),
        )

    def require_runtime(self) -> None:
        if not self.enabled:
            raise RuntimeError("Seat governance is disabled")
        if not self.database_url:
            raise RuntimeError("AXIGNAL_SEAT_DATABASE_URL or AXIGNAL_DATABASE_URL is required")

    def require_owner_bootstrap(self, subject: str) -> None:
        self.require_runtime()
        if subject not in self.owner_subjects:
            raise RuntimeError("Authenticated subject is not an approved organisation owner")

    def require_invitation_delivery(self) -> None:
        self.require_runtime()
        if not 1 <= self.invitation_ttl_hours <= 24 * 14:
            raise RuntimeError("AXIGNAL_SEAT_INVITATION_TTL_HOURS must be between 1 and 336")
        if self.invitation_provider == "test":
            if not self.test_runtime_enabled or self.environment != "test":
                raise RuntimeError("Test invitation provider is restricted to the test runtime")
            return
        if self.invitation_provider != "smtp":
            raise RuntimeError("A seat invitation delivery provider is required")
        if not self.public_base_url or not self.public_base_url.startswith(("https://", "http://")):
            raise RuntimeError("AXIGNAL_PUBLIC_APP_URL is required for invitation delivery")
        if not self.smtp_host or not self.smtp_from:
            raise RuntimeError("SMTP host and sender are required for invitation delivery")
        if bool(self.smtp_username) != bool(self.smtp_password):
            raise RuntimeError("SMTP username and password must be configured together")
