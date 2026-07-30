from __future__ import annotations

from axignal_api.billing_config import BillingSettings
from axignal_api.billing_provider import (
    BillingProvider,
    CheckoutSessionResult,
    SubscriptionCommandResult,
    billing_provider,
)


class StripeGateway:
    """Backward-compatible billing-provider facade.

    Production defaults to the real Stripe implementation. The deterministic
    provider can be selected only by the fail-closed test-runtime gates in
    ``BillingSettings``.
    """

    def __new__(cls, settings: BillingSettings) -> BillingProvider:
        return billing_provider(settings)


__all__ = [
    "CheckoutSessionResult",
    "StripeGateway",
    "SubscriptionCommandResult",
]
