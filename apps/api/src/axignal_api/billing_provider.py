from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol
from urllib.parse import urlencode
from uuid import UUID

import httpx

from axignal_api.billing_config import BillingSettings


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
        self.settings = settings

    def _headers(self, *, idempotency_key: str | None = None) -> dict[str, str]:
        assert self.settings.stripe_secret_key is not None
        assert self.settings.stripe_api_version is not None
        headers = {
            "Authorization": f"Bearer {self.settings.stripe_secret_key}",
            "Stripe-Version": self.settings.stripe_api_version,
            "User-Agent": "AXIGNAL-Billing/0.1",
        }
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        return headers

    def _client(self) -> httpx.Client:
        return httpx.Client(
            base_url=self.settings.stripe_api_base,
            timeout=httpx.Timeout(15.0, connect=5.0),
            follow_redirects=False,
        )

    @staticmethod
    def _json(response: httpx.Response) -> dict[str, Any]:
        try:
            payload = response.json()
        except ValueError as exc:
            raise RuntimeError("Stripe returned a non-JSON response") from exc
        if not isinstance(payload, dict):
            raise RuntimeError("Stripe returned an invalid object")
        return payload

    def verify_account(self, client: httpx.Client) -> None:
        response = client.get("/v1/account", headers=self._headers())
        response.raise_for_status()
        payload = self._json(response)
        if payload.get("id") != self.settings.stripe_account_id:
            raise RuntimeError("Stripe API key is bound to the wrong account")

    def create_checkout_session(
        self,
        *,
        selection_id: UUID,
        plan_code: str,
        customer_email: str,
        operation_id: str,
    ) -> CheckoutSessionResult:
        self.settings.require_checkout()
        price_id = self.settings.price_for_plan(plan_code)
        assert self.settings.checkout_success_url is not None
        assert self.settings.checkout_cancel_url is not None
        form = {
            "mode": "subscription",
            "success_url": self.settings.checkout_success_url,
            "cancel_url": self.settings.checkout_cancel_url,
            "client_reference_id": str(selection_id),
            "customer_email": customer_email,
            "line_items[0][price]": price_id,
            "line_items[0][quantity]": "1",
            "allow_promotion_codes": "false",
            "metadata[axignal_selection_id]": str(selection_id),
            "metadata[axignal_plan_code]": plan_code,
            "subscription_data[metadata][axignal_selection_id]": str(selection_id),
            "subscription_data[metadata][axignal_plan_code]": plan_code,
        }
        idempotency_key = f"axignal:checkout:{selection_id}:{operation_id}:v1"
        with self._client() as client:
            self.verify_account(client)
            response = client.post(
                "/v1/checkout/sessions",
                headers=self._headers(idempotency_key=idempotency_key),
                data=form,
            )
            response.raise_for_status()
            payload = self._json(response)
        session_id = payload.get("id")
        url = payload.get("url")
        if not isinstance(session_id, str) or not session_id.startswith("cs_"):
            raise RuntimeError("Stripe Checkout Session id is missing")
        if not isinstance(url, str) or not url.startswith("https://"):
            raise RuntimeError("Stripe Checkout URL is missing")
        return CheckoutSessionResult(session_id=session_id, url=url, price_id=price_id)

    def upgrade_subscription(
        self,
        *,
        subscription_id: str,
        subscription_item_id: str,
        target_plan_code: str,
        operation_id: str,
    ) -> SubscriptionCommandResult:
        self.settings.require_lifecycle()
        price_id = self.settings.price_for_plan(target_plan_code)
        form = {
            "items[0][id]": subscription_item_id,
            "items[0][price]": price_id,
            "proration_behavior": "none",
            "metadata[axignal_pending_plan_code]": target_plan_code,
        }
        with self._client() as client:
            self.verify_account(client)
            response = client.post(
                f"/v1/subscriptions/{subscription_id}",
                headers=self._headers(
                    idempotency_key=(
                        f"axignal:upgrade:{subscription_id}:{operation_id}:v1"
                    )
                ),
                data=form,
            )
            response.raise_for_status()
            payload = self._json(response)
        return SubscriptionCommandResult(
            subscription_id=str(payload.get("id") or subscription_id),
            status=str(payload.get("status") or "unknown"),
            cancel_at_period_end=bool(payload.get("cancel_at_period_end", False)),
        )

    def cancel_subscription(
        self,
        *,
        subscription_id: str,
        cancel_at_period_end: bool,
        operation_id: str,
    ) -> SubscriptionCommandResult:
        self.settings.require_lifecycle()
        with self._client() as client:
            self.verify_account(client)
            if cancel_at_period_end:
                response = client.post(
                    f"/v1/subscriptions/{subscription_id}",
                    headers=self._headers(
                        idempotency_key=(
                            f"axignal:cancel-period-end:{subscription_id}:{operation_id}:v1"
                        )
                    ),
                    data={"cancel_at_period_end": "true"},
                )
            else:
                response = client.delete(
                    f"/v1/subscriptions/{subscription_id}",
                    headers=self._headers(
                        idempotency_key=(
                            f"axignal:cancel-now:{subscription_id}:{operation_id}:v1"
                        )
                    ),
                )
            response.raise_for_status()
            payload = self._json(response)
        return SubscriptionCommandResult(
            subscription_id=str(payload.get("id") or subscription_id),
            status=str(payload.get("status") or "unknown"),
            cancel_at_period_end=bool(
                payload.get("cancel_at_period_end", cancel_at_period_end)
            ),
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
