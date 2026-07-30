from __future__ import annotations

from dataclasses import dataclass
from os import environ
from urllib.parse import urlparse

EXPECTED_AXIGNAL_STRIPE_ACCOUNT_ID = "acct_1TybkH8feyjV8Pem"
SUPPORTED_BILLING_PROVIDERS = {"stripe", "test"}


def _bool_env(name: str, default: bool = False) -> bool:
    value = environ.get(name)
    if value is None:
        return default
    return value.strip().casefold() in {"1", "true", "yes", "on"}


def _required_url(name: str, value: str | None) -> str:
    if not value:
        raise RuntimeError(f"{name} is required")
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise RuntimeError(f"{name} must be an absolute HTTP(S) URL")
    return value


@dataclass(frozen=True)
class BillingSettings:
    database_url: str | None
    billing_provider: str
    environment: str
    test_runtime_enabled: bool
    test_checkout_base_url: str | None
    billing_runtime_enabled: bool
    stripe_checkout_enabled: bool
    stripe_webhooks_enabled: bool
    stripe_lifecycle_enabled: bool
    stripe_sandbox_only: bool
    stripe_secret_key: str | None
    stripe_webhook_secret: str | None
    stripe_account_id: str | None
    stripe_api_base: str
    stripe_api_version: str | None
    professional_price_id: str | None
    team_price_id: str | None
    checkout_success_url: str | None
    checkout_cancel_url: str | None
    webhook_tolerance_seconds: int

    @classmethod
    def from_env(cls) -> BillingSettings:
        tolerance_raw = environ.get("AXIGNAL_STRIPE_WEBHOOK_TOLERANCE_SECONDS", "300")
        try:
            tolerance = int(tolerance_raw)
        except ValueError as exc:
            raise RuntimeError(
                "AXIGNAL_STRIPE_WEBHOOK_TOLERANCE_SECONDS must be an integer"
            ) from exc
        provider = environ.get("AXIGNAL_BILLING_PROVIDER", "stripe").strip().casefold()
        return cls(
            database_url=(
                environ.get("AXIGNAL_BILLING_DATABASE_URL")
                or environ.get("AXIGNAL_DATABASE_URL")
            ),
            billing_provider=provider,
            environment=environ.get("AXIGNAL_ENVIRONMENT", "production")
            .strip()
            .casefold(),
            test_runtime_enabled=_bool_env("AXIGNAL_TEST_RUNTIME_ENABLED"),
            test_checkout_base_url=environ.get("AXIGNAL_TEST_CHECKOUT_BASE_URL"),
            billing_runtime_enabled=_bool_env("AXIGNAL_BILLING_RUNTIME_ENABLED"),
            stripe_checkout_enabled=_bool_env("AXIGNAL_STRIPE_CHECKOUT_ENABLED"),
            stripe_webhooks_enabled=_bool_env("AXIGNAL_STRIPE_WEBHOOKS_ENABLED"),
            stripe_lifecycle_enabled=_bool_env("AXIGNAL_STRIPE_LIFECYCLE_ENABLED"),
            stripe_sandbox_only=_bool_env("AXIGNAL_STRIPE_SANDBOX_ONLY", True),
            stripe_secret_key=environ.get("AXIGNAL_STRIPE_SECRET_KEY"),
            stripe_webhook_secret=environ.get("AXIGNAL_STRIPE_WEBHOOK_SECRET"),
            stripe_account_id=environ.get("AXIGNAL_STRIPE_ACCOUNT_ID"),
            stripe_api_base=environ.get(
                "AXIGNAL_STRIPE_API_BASE", "https://api.stripe.com"
            ).rstrip("/"),
            stripe_api_version=environ.get("AXIGNAL_STRIPE_API_VERSION"),
            professional_price_id=environ.get(
                "AXIGNAL_STRIPE_PRICE_PROFESSIONAL_MONTHLY"
            ),
            team_price_id=environ.get("AXIGNAL_STRIPE_PRICE_TEAM_MONTHLY"),
            checkout_success_url=environ.get("AXIGNAL_STRIPE_CHECKOUT_SUCCESS_URL"),
            checkout_cancel_url=environ.get("AXIGNAL_STRIPE_CHECKOUT_CANCEL_URL"),
            webhook_tolerance_seconds=tolerance,
        )

    def require_store(self) -> None:
        if not self.database_url:
            raise RuntimeError("AXIGNAL_BILLING_DATABASE_URL is required")

    def require_runtime(self) -> None:
        self.require_store()
        if not self.billing_runtime_enabled:
            raise RuntimeError("AXIGNAL billing runtime is disabled")
        if self.billing_provider not in SUPPORTED_BILLING_PROVIDERS:
            raise RuntimeError("Unsupported AXIGNAL billing provider")

    def _require_expected_account(self) -> None:
        if self.stripe_account_id != EXPECTED_AXIGNAL_STRIPE_ACCOUNT_ID:
            raise RuntimeError(
                "Stripe account mismatch: AXIGNAL requires "
                f"{EXPECTED_AXIGNAL_STRIPE_ACCOUNT_ID}"
            )

    def _require_sandbox_secret(self) -> None:
        if not self.stripe_secret_key:
            raise RuntimeError("AXIGNAL_STRIPE_SECRET_KEY is required")
        if self.stripe_sandbox_only and self.stripe_secret_key.startswith("sk_live_"):
            raise RuntimeError("A live Stripe secret is forbidden in sandbox-only mode")
        if self.stripe_sandbox_only and not self.stripe_secret_key.startswith(
            ("sk_test_", "rk_test_")
        ):
            raise RuntimeError("A Stripe test or sandbox secret is required")

    def require_test_provider(self) -> None:
        self.require_runtime()
        if self.billing_provider != "test":
            raise RuntimeError("Deterministic billing provider is not selected")
        if not self.test_runtime_enabled or self.environment != "test":
            raise RuntimeError(
                "Deterministic billing provider requires the isolated test runtime"
            )
        self._require_expected_account()
        _required_url("AXIGNAL_TEST_CHECKOUT_BASE_URL", self.test_checkout_base_url)

    def _require_price_mappings(self) -> None:
        for name, price in (
            ("AXIGNAL_STRIPE_PRICE_PROFESSIONAL_MONTHLY", self.professional_price_id),
            ("AXIGNAL_STRIPE_PRICE_TEAM_MONTHLY", self.team_price_id),
        ):
            if not price or not price.startswith("price_"):
                raise RuntimeError(f"{name} must be a Stripe Price id")

    def require_checkout(self) -> None:
        self.require_runtime()
        if not self.stripe_checkout_enabled:
            raise RuntimeError("Stripe Checkout is disabled")
        self._require_expected_account()
        if self.billing_provider == "test":
            self.require_test_provider()
            self._require_price_mappings()
            return
        self._require_sandbox_secret()
        if not self.stripe_api_version:
            raise RuntimeError("AXIGNAL_STRIPE_API_VERSION is required")
        self._require_price_mappings()
        _required_url(
            "AXIGNAL_STRIPE_CHECKOUT_SUCCESS_URL", self.checkout_success_url
        )
        _required_url("AXIGNAL_STRIPE_CHECKOUT_CANCEL_URL", self.checkout_cancel_url)

    def require_webhooks(self) -> None:
        self.require_runtime()
        if not self.stripe_webhooks_enabled:
            raise RuntimeError("Stripe webhooks are disabled")
        self._require_expected_account()
        if self.billing_provider == "test":
            self.require_test_provider()
        if not self.stripe_webhook_secret or not self.stripe_webhook_secret.startswith(
            "whsec_"
        ):
            raise RuntimeError("AXIGNAL_STRIPE_WEBHOOK_SECRET is required")
        if not 30 <= self.webhook_tolerance_seconds <= 900:
            raise RuntimeError(
                "AXIGNAL_STRIPE_WEBHOOK_TOLERANCE_SECONDS must be between 30 and 900"
            )

    def require_lifecycle(self) -> None:
        self.require_checkout()
        if not self.stripe_lifecycle_enabled:
            raise RuntimeError("Stripe paid lifecycle changes are disabled")

    def price_for_plan(self, plan_code: str) -> str:
        mapping = {
            "PROFESSIONAL_MONTHLY": self.professional_price_id,
            "TEAM_MONTHLY": self.team_price_id,
        }
        price = mapping.get(plan_code)
        if not price:
            raise RuntimeError("Stripe price mapping is unavailable")
        return price

    def plan_for_price(self, price_id: str | None) -> str | None:
        if price_id == self.professional_price_id:
            return "PROFESSIONAL_MONTHLY"
        if price_id == self.team_price_id:
            return "TEAM_MONTHLY"
        return None
