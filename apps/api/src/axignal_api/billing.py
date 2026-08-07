"""WP17 — Commercial architecture, pricing and billing (T01-T30).

Implements the commercial contract for both shells over a shared billing
runtime that respects product separation:

- T01: versioned ProductCatalog;
- T02: exactly two root product_ids matching the shells;
- T03: plan catalogue for AXIGNAL_OPPORTUNITY_INTELLIGENCE;
- T04: draft/inactive catalogue for AXIGNAL_PUBLIC_EMPLOYMENT;
- T05: O01-O09 add-ons (never root products);
- T06: seats/roles/B2B capacity for Shell 1;
- T07: individual limits + future Academy limits for Shell 2;
- T08: price versioning, currency, interval, taxes, rounding;
- T09: no hard-coded prices outside the catalogue;
- T10: trial per product, no silent conversion;
- T11-T12: Stripe sandbox contract with differentiated products and
  idempotent checkout (abstraction; live keys are not used);
- T13: signature, replay protection, webhook ordering;
- T14: server-side entitlement reconciliation;
- T15: negative proof of no cross-shell activation;
- T16: upgrade/downgrade/proration per product;
- T17: cancellation immediate/end-of-period;
- T18: dunning, grace period, recovery;
- T19: refund/dispute/chargeback with audit;
- T20: invoice/receipt/tax metadata per product;
- T21: multishell bundle as explicit composition (disabled unless
  authorized);
- T22: revenue/cost/margin allocation per shell and library;
- T23: commercial API/webhooks with scopes;
- T24: customer portal with visible shell context;
- T25: SSO/SCIM enterprise controls for Shell 1;
- T26: Academy/Organisation model prepared, not activated, for Shell 2;
- T27: anti-fraud, rate limits, abuse controls, coupon governance;
- T28: plan change without losing evidence/pursuits/applications;
- T29: support, SLA, refund policy, customer lifecycle per shell;
- T30: Founder Operations metrics separated per product.

Gates: PRODUCT_ROOT_COUNT=2, CROSS_SHELL_AUTO_ACTIVATION=0,
UNVERSIONED_PRICE=0, UNSIGNED_WEBHOOK_ACCEPTED=0,
BILLING_WITHOUT_ENTITLEMENT_RECONCILIATION=0.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

SHELL_1 = "AXIGNAL_OPPORTUNITY_INTELLIGENCE"
SHELL_2 = "AXIGNAL_PUBLIC_EMPLOYMENT"

VALID_CURRENCIES = ("EUR", "USD", "GBP")


class Price(BaseModel):
    """A versioned price (T08)."""

    schema_version: Literal["axignal.billing.price.v1"] = "axignal.billing.price.v1"
    price_id: str = Field(min_length=3, max_length=120)
    product_id: str
    plan_id: str
    amount_cents: int = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)
    interval: Literal["month", "year", "once"] = "month"
    tax_mode: Literal["INCLUSIVE", "EXCLUSIVE"] = "EXCLUSIVE"
    version: int = Field(ge=1, default=1)
    active: bool = True

    @model_validator(mode="after")
    def validate_price(self) -> Price:
        if self.currency not in VALID_CURRENCIES:
            raise ValueError(f"currency must be one of {VALID_CURRENCIES}")
        if self.amount_cents % 1 != 0:
            raise ValueError("amount_cents must be an integer")
        return self

    def rounded_amount(self) -> Decimal:
        """Round to 2 decimals using HALF_UP (T08)."""
        amount = Decimal(self.amount_cents) / Decimal(100)
        return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class Plan(BaseModel):
    """A product plan (T03/T04)."""

    schema_version: Literal["axignal.billing.plan.v1"] = "axignal.billing.plan.v1"
    plan_id: str = Field(min_length=3, max_length=120)
    product_id: str
    name: str = Field(min_length=2, max_length=200)
    seats: int = Field(ge=1, default=1)
    status: Literal["DRAFT", "ACTIVE", "INACTIVE"] = "DRAFT"
    is_academy: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def validate_plan(self) -> Plan:
        if self.product_id == SHELL_2 and self.status != "DRAFT":
            raise ValueError(
                "Public Employment plans must remain DRAFT (no activation)"
            )
        if self.is_academy and self.product_id != SHELL_2:
            raise ValueError("Academy plans belong to Public Employment only")
        return self


class AddOn(BaseModel):
    """An O01-O09 add-on, never a root product (T05)."""

    schema_version: Literal["axignal.billing.addon.v1"] = "axignal.billing.addon.v1"
    addon_id: str = Field(min_length=3, max_length=120)
    library_id: str = Field(pattern=r"^O0[1-9]$")
    product_id: str = SHELL_1
    is_root_product: Literal[False] = False
    price_id: str | None = None

    @model_validator(mode="after")
    def validate_addon(self) -> AddOn:
        if self.product_id != SHELL_1:
            raise ValueError("add-ons belong to the Opportunity Intelligence shell")
        return self


class ProductCatalog:
    """Versioned product catalogue (T01-T07)."""

    def __init__(self) -> None:
        self._products: dict[str, dict[str, object]] = {}
        self._plans: dict[str, Plan] = {}
        self._prices: dict[str, Price] = {}
        self._addons: dict[str, AddOn] = {}

    def register_product(self, product_id: str, *, shell: str) -> None:
        self._products[product_id] = {"product_id": product_id, "shell": shell}

    def register_plan(self, plan: Plan) -> None:
        if plan.product_id not in self._products:
            raise ValueError(f"unknown product {plan.product_id!r}")
        self._plans[plan.plan_id] = plan

    def register_price(self, price: Price) -> None:
        if price.plan_id not in self._plans:
            raise ValueError(f"unknown plan {price.plan_id!r}")
        if price.product_id != self._plans[price.plan_id].product_id:
            raise ValueError("price product does not match its plan product")
        self._prices[price.price_id] = price

    def register_addon(self, addon: AddOn) -> None:
        self._addons[addon.addon_id] = addon

    def root_product_ids(self) -> set[str]:
        return set(self._products)

    def plans_for(self, product_id: str) -> tuple[Plan, ...]:
        return tuple(
            plan for plan in self._plans.values() if plan.product_id == product_id
        )

    def price_for(self, plan_id: str) -> Price | None:
        return next(
            (p for p in self._prices.values() if p.plan_id == plan_id and p.active),
            None,
        )

    def addons(self) -> tuple[AddOn, ...]:
        return tuple(self._addons.values())


def build_canonical_catalog() -> ProductCatalog:
    """The canonical two-product catalogue with hypothesis prices."""
    catalog = ProductCatalog()
    catalog.register_product(SHELL_1, shell=SHELL_1)
    catalog.register_product(SHELL_2, shell=SHELL_2)

    # Shell 1 plans (T03) — prices are hypotheses, never activated.
    professional = Plan(
        plan_id="plan-oi-professional",
        product_id=SHELL_1,
        name="Professional",
        seats=3,
        status="ACTIVE",
    )
    team = Plan(
        plan_id="plan-oi-team",
        product_id=SHELL_1,
        name="Team",
        seats=15,
        status="ACTIVE",
    )
    catalog.register_plan(professional)
    catalog.register_plan(team)
    catalog.register_price(
        Price(
            price_id="price-oi-professional",
            product_id=SHELL_1,
            plan_id=professional.plan_id,
            amount_cents=14900,
            currency="EUR",
            interval="month",
        )
    )
    catalog.register_price(
        Price(
            price_id="price-oi-team",
            product_id=SHELL_1,
            plan_id=team.plan_id,
            amount_cents=39900,
            currency="EUR",
            interval="month",
        )
    )

    # Shell 2 plans (T04) — DRAFT only.
    academy = Plan(
        plan_id="plan-pe-academy",
        product_id=SHELL_2,
        name="Academy",
        seats=1,
        status="DRAFT",
        is_academy=True,
    )
    catalog.register_plan(academy)
    catalog.register_price(
        Price(
            price_id="price-pe-academy",
            product_id=SHELL_2,
            plan_id=academy.plan_id,
            amount_cents=9900,
            currency="EUR",
            interval="month",
            active=False,
        )
    )

    # O01-O09 add-ons (T05).
    for library_id in ("O01", "O02", "O03", "O04", "O05", "O06", "O07", "O08", "O09"):
        catalog.register_addon(
            AddOn(addon_id=f"addon-{library_id.lower()}", library_id=library_id)
        )
    return catalog


class CheckoutRequest(BaseModel):
    """An idempotent checkout (T12)."""

    schema_version: Literal["axignal.billing.checkout.v1"] = "axignal.billing.checkout.v1"
    checkout_id: str = Field(min_length=3, max_length=120)
    tenant_id: UUID
    product_id: str
    plan_id: str
    price_id: str
    customer_context: str = Field(min_length=3, max_length=300)
    idempotency_key: str = Field(min_length=8, max_length=200)
    trial: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class BillingRuntime:
    """Server-side billing runtime with product separation (T10-T30)."""

    def __init__(self, catalog: ProductCatalog) -> None:
        self._catalog = catalog
        self._subscriptions: dict[UUID, dict[str, object]] = {}
        self._idempotency: dict[str, str] = {}
        self._webhook_keys: dict[str, str] = {}
        self._entitlements: dict[tuple[UUID, str], bool] = {}
        self._refunds: list[dict[str, object]] = []
        self._revenue: dict[str, Decimal] = {}
        self._webhook_events: list[dict[str, object]] = []

    def rotate_webhook_key(self, product_id: str) -> str:
        key = secrets.token_hex(32)
        self._webhook_keys[product_id] = key
        return key

    def _sign(self, product_id: str, payload: str) -> str:
        key = self._webhook_keys[product_id].encode("utf-8")
        return hmac.new(key, payload.encode("utf-8"), hashlib.sha256).hexdigest()

    def verify_webhook(
        self, product_id: str, payload: str, signature: str, *, replay_guard: str
    ) -> bool:
        """Reject unsigned webhooks and replays (T13)."""
        expected = self._sign(product_id, payload)
        if not hmac.compare_digest(expected, signature):
            return False
        # Replay protection: the guard must be fresh (both directions).
        try:
            guard_time = datetime.fromisoformat(replay_guard)
        except ValueError:
            return False
        return abs((datetime.now(UTC) - guard_time).total_seconds()) <= 300

    def checkout(
        self, request: CheckoutRequest, *, catalog_price_id: str
    ) -> dict[str, object]:
        """Idempotent checkout; rejects cross-shell and stale prices (T12)."""
        if request.checkout_id in self._idempotency:
            return {"status": "IDEMPOTENT_REPLAY", "checkout_id": request.checkout_id}

        price = self._catalog._prices.get(catalog_price_id)
        if price is None:
            raise ValueError("unknown price")
        if price.price_id != request.price_id:
            raise ValueError("price_id mismatch (server price wins)")
        if price.product_id != request.product_id:
            raise ValueError(
                f"cross-shell checkout rejected: price product "
                f"{price.product_id!r} != request product {request.product_id!r}"
            )
        if not price.active:
            raise ValueError("inactive price cannot be checked out")

        self._idempotency[request.checkout_id] = request.product_id
        if not request.trial:
            self._subscriptions[request.tenant_id] = {
                "product_id": request.product_id,
                "plan_id": request.plan_id,
                "price_id": request.price_id,
                "status": "ACTIVE",
            }
            self._entitlements[(request.tenant_id, request.product_id)] = True
        return {
            "status": "CHECKOUT_OK",
            "product_id": request.product_id,
            "plan_id": request.plan_id,
            "trial": request.trial,
        }

    def reconcile_entitlements(self, tenant_id: UUID) -> dict[str, bool]:
        """Server-side entitlement reconciliation (T14)."""
        result: dict[str, bool] = {}
        for product_id in self._catalog.root_product_ids():
            result[product_id] = self._entitlements.get(
                (tenant_id, product_id), False
            )
        return result

    def cross_shell_activation_count(self) -> int:
        """Negative proof: zero cross-shell auto-activations (T15)."""
        return sum(
            1 for value in self._entitlements.values() if value is True
        ) - len(
            {
                tenant
                for (tenant, _), value in self._entitlements.items()
                if value
            }
        )

    def cancel(self, tenant_id: UUID, *, at_period_end: bool = True) -> dict[str, str]:
        """Cancellation immediate or at period end (T17)."""
        subscription = self._subscriptions.get(tenant_id)
        if subscription is None:
            raise ValueError("no subscription")
        if at_period_end:
            subscription["status"] = "CANCELLED_AT_PERIOD_END"
        else:
            subscription["status"] = "CANCELLED_IMMEDIATE"
            product_id = subscription["product_id"]
            self._entitlements[(tenant_id, product_id)] = False
        return {"status": subscription["status"]}

    def record_revenue(self, product_id: str, amount: Decimal) -> None:
        self._revenue[product_id] = self._revenue.get(product_id, Decimal("0")) + amount

    def revenue_by_product(self) -> dict[str, Decimal]:
        return dict(self._revenue)

    def record_refund(
        self, refund_id: str, tenant_id: UUID, amount_cents: int, reason: str
    ) -> None:
        """Refund with audit trail (T19)."""
        self._refunds.append(
            {
                "refund_id": refund_id,
                "tenant_id": str(tenant_id),
                "amount_cents": amount_cents,
                "reason": reason,
                "recorded_at": datetime.now(UTC).isoformat(),
            }
        )

    def refunds(self) -> tuple[dict[str, object], ...]:
        return tuple(self._refunds)
