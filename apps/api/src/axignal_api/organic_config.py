from __future__ import annotations

import os
from dataclasses import dataclass


def _bool_env(name: str) -> bool:
    return os.getenv(name, "").strip().casefold() in {"1", "true", "yes", "on"}


def _subjects(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(sorted({item.strip() for item in value.split(",") if item.strip()}))


@dataclass(frozen=True)
class OrganicDiscoverySettings:
    enabled: bool
    public_indexing_enabled: bool
    public_alerts_enabled: bool
    database_url: str | None
    founder_subjects: tuple[str, ...]
    hmac_pepper: str | None
    public_site_url: str
    environment: str
    test_runtime_enabled: bool

    @classmethod
    def from_env(cls) -> OrganicDiscoverySettings:
        return cls(
            enabled=_bool_env("AXIGNAL_ORGANIC_DISCOVERY_ENABLED"),
            public_indexing_enabled=_bool_env(
                "AXIGNAL_ORGANIC_PUBLIC_INDEXING_ENABLED"
            ),
            public_alerts_enabled=_bool_env("AXIGNAL_TENDER_ALERTS_ENABLED"),
            database_url=(
                os.getenv("AXIGNAL_ORGANIC_DATABASE_URL")
                or os.getenv("AXIGNAL_DATABASE_URL")
            ),
            founder_subjects=_subjects(os.getenv("AXIGNAL_FOUNDER_SUBJECTS")),
            hmac_pepper=os.getenv("AXIGNAL_ORGANIC_HMAC_PEPPER"),
            public_site_url=os.getenv(
                "AXIGNAL_PUBLIC_SITE_URL", "https://axignal.com"
            ).rstrip("/"),
            environment=os.getenv("AXIGNAL_ENVIRONMENT", "development"),
            test_runtime_enabled=_bool_env("AXIGNAL_TEST_RUNTIME_ENABLED"),
        )

    def require_runtime(self) -> None:
        if not self.enabled:
            raise RuntimeError("Organic discovery runtime is disabled")
        if not self.database_url:
            raise RuntimeError("AXIGNAL_ORGANIC_DATABASE_URL is required")
        if not self.hmac_pepper or len(self.hmac_pepper) < 32:
            raise RuntimeError(
                "AXIGNAL_ORGANIC_HMAC_PEPPER must contain at least 32 characters"
            )

    def require_public_indexing(self) -> None:
        self.require_runtime()
        if not self.public_indexing_enabled:
            raise RuntimeError("Public organic indexing is not authorised")

    def require_public_alerts(self) -> None:
        self.require_runtime()
        if not self.public_alerts_enabled:
            raise RuntimeError("Public tender alerts are not authorised")

    def require_founder_subject(self, subject: str) -> None:
        self.require_runtime()
        if subject not in self.founder_subjects:
            raise RuntimeError("Founder admin subject is not allowlisted")

    def require_test_runtime(self) -> None:
        if self.environment != "test" or not self.test_runtime_enabled:
            raise RuntimeError("Founder test bootstrap is unavailable")
