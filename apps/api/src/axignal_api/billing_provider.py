from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlencode
from uuid import UUID

from axignal_api.billing_config import BillingSettings
from axignal_api.stripe_gateway import StripeGateway


@dataclass(frozen=True)
class CheckoutSessionResult:
    session_id: str
    url: str
    price_id: str


@dataclass(frozen=True)
class SubscriptionCommandResult:
    subscription_id: str
    status: str
    cancel_at_period_end: bool


class BillingProvider(Protocol):
    def create_checkout_session(
        self,
        *,
        selection_id: UUID,
        plan_code: str,
        customer_email: str,
        operation_id: str,
    ) -> CheckoutSessionResult: ...

    def upgrade_subscription(
        self,
        *,
        subscription_id: str,
        subscription_item_id: str,
        target_plan_code: str,
        operation_id: str,
    ) -> SubscriptionCommandResult: ...

    def cancel_subscription(
        self,
        *,
        subscription_id: str,
        cancel_at_period_end: bool,
        operation_id: str,
    ) -> SubscriptionCommandResult: ...


class StripeBillingProvider:
    def __init__(self, settings: BillingSettings) -> None:
        self.gateway = StripeGateway(settings)

    def create_checkout_session(
        self,
        *,
        selection_id: UUID,
        plan_code: str,
        customer_email: str,
        operation_id: str,
    ) -> CheckoutSessionResult:
        result = self.gateway.create_checkout_session(
            selection_id=selection_id,
            plan_code=plan_code,
            customer_email=customer_email,
            operation_id=operation_id,
        )
        return CheckoutSessionResult(
            session_id=result.session_id,
            url=result.url,
            price_id=result.price_id,
        )

    def upgrade_subscription(
        self,
        *,
        subscription_id: str,
        subscription_item_id: str,
        target_plan_code: str,
        operation_id: str,
    ) -> SubscriptionCommandResult:
        result = self.gateway.upgrade_subscription(
            subscription_id=subscription_id,
            subscription_item_id=subscription_item_id,
            target_plan_code=target_plan_code,
            operation_id=operation_id,
        )
        return SubscriptionCommandResult(
            subscription_id=result.subscription_id,
            status=result.status,
            cancel_at_period_end=result.cancel_at_period_end,
        )

    def cancel_subscription(
        self,
        *,
        subscription_id: str,
        cancel_at_period_end: bool,
        operation_id: str,
    ) -> SubscriptionCommandResult:
        result = self.gateway.cancel_subscription(
            subscription_id=subscription_id,
            cancel_at_period_end=cancel_at_period_end,
            operation_id=operation_id,
        )
        return SubscriptionCommandResult(
            subscription_id=result.subscription_id,
            status=result.status,
            cancel_at_period_end=result.cancel_at_period_end,
        )


class DeterministicTestBillingProvider:
    """Provider contract for browser E2E only.

    It never grants an entitlement. Test lifecycle transitions still have to be
    produced as signed provider events and applied by the billing worker path.
    """

    def __init__(self, settings: BillingSettings) -> None:
        settings.require_test_provider()
        self.settings = settings

    def create_checkout_session(
        self,
        *,
        selection_id: UUID,
        plan_code: str,
        customer_email: str,
        operation_id: str,
    ) -> CheckoutSessionResult:
        del customer_email, operation_id
        price_id = self.settings.price_for_plan(plan_code)
        assert self.settings.test_checkout_base_url is not None
        query = urlencode(
            {"selection_id": str(selection_id), "plan_code": plan_code}
        )
        return CheckoutSessionResult(
            session_id=f"cs_test_axignal_{selection_id.hex}",
            url=f"{self.settings.test_checkout_base_url}?{query}",
            price_id=price_id,
        )

    def upgrade_subscription(
        self,
        *,
        subscription_id: str,
        subscription_item_id: str,
        target_plan_code: str,
        operation_id: str,
    ) -> SubscriptionCommandResult:
        del subscription_item_id, target_plan_code, operation_id
        return SubscriptionCommandResult(
            subscription_id=subscription_id,
            status="pending_signed_event",
            cancel_at_period_end=False,
        )

    def cancel_subscription(
        self,
        *,
        subscription_id: str,
        cancel_at_period_end: bool,
        operation_id: str,
    ) -> SubscriptionCommandResult:
        del operation_id
        return SubscriptionCommandResult(
            subscription_id=subscription_id,
            status="pending_signed_event",
            cancel_at_period_end=cancel_at_period_end,
        )


def billing_provider(settings: BillingSettings) -> BillingProvider:
    settings.require_checkout()
    if settings.billing_provider == "stripe":
        return StripeBillingProvider(settings)
    if settings.billing_provider == "test":
        return DeterministicTestBillingProvider(settings)
    raise RuntimeError("Unsupported AXIGNAL billing provider")
