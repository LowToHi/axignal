"""WP17 — Pricing and billing tests (T01-T30 core)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

import pytest

from axignal_api.billing import (
    SHELL_1,
    SHELL_2,
    AddOn,
    BillingRuntime,
    CheckoutRequest,
    Plan,
    Price,
    ProductCatalog,
    build_canonical_catalog,
)

TENANT = UUID("11111111-1111-4111-8111-111111111111")
OTHER_TENANT = UUID("22222222-2222-4222-8222-222222222222")


class TestProductCatalog:
    def test_exactly_two_root_products(self) -> None:
        catalog = build_canonical_catalog()
        assert catalog.root_product_ids() == {SHELL_1, SHELL_2}

    def test_shell1_plans(self) -> None:
        catalog = build_canonical_catalog()
        plans = catalog.plans_for(SHELL_1)
        assert {p.plan_id for p in plans} == {"plan-oi-professional", "plan-oi-team"}
        assert all(p.status == "ACTIVE" for p in plans)

    def test_shell2_plans_draft_only(self) -> None:
        catalog = build_canonical_catalog()
        plans = catalog.plans_for(SHELL_2)
        assert all(p.status == "DRAFT" for p in plans)

    def test_addons_never_root(self) -> None:
        catalog = build_canonical_catalog()
        assert len(catalog.addons()) == 9
        for addon in catalog.addons():
            assert addon.is_root_product is False
            assert addon.product_id == SHELL_1

    def test_pe_plan_cannot_be_active(self) -> None:
        with pytest.raises(ValueError, match="DRAFT"):
            Plan(
                plan_id="plan-pe-x",
                product_id=SHELL_2,
                name="Plan X",
                status="ACTIVE",
            )

    def test_academy_only_for_shell2(self) -> None:
        with pytest.raises(ValueError, match="Academy"):
            Plan(
                plan_id="plan-x",
                product_id=SHELL_1,
                name="Plan X",
                is_academy=True,
            )

    def test_addon_requires_shell1(self) -> None:
        with pytest.raises(ValueError, match="Opportunity Intelligence"):
            AddOn(addon_id="addon-x", library_id="O01", product_id=SHELL_2)

    def test_price_requires_matching_product(self) -> None:
        catalog = ProductCatalog()
        catalog.register_product(SHELL_1, shell=SHELL_1)
        plan = Plan(plan_id="plan-1", product_id=SHELL_1, name="Plan P", status="ACTIVE")
        catalog.register_plan(plan)
        with pytest.raises(ValueError, match="does not match"):
            catalog.register_price(
                Price(
                    price_id="price-1",
                    product_id=SHELL_2,
                    plan_id="plan-1",
                    amount_cents=100,
                    currency="EUR",
                )
            )

    def test_unknown_currency_rejected(self) -> None:
        with pytest.raises(ValueError, match="currency"):
            Price(
                price_id="price-1",
                product_id=SHELL_1,
                plan_id="plan-1",
                amount_cents=100,
                currency="XXX",
            )

    def test_price_rounding(self) -> None:
        price = Price(
            price_id="price-1",
            product_id=SHELL_1,
            plan_id="plan-1",
            amount_cents=14999,
            currency="EUR",
        )
        assert price.rounded_amount() == Decimal("149.99")


class TestBillingRuntime:
    def test_checkout_ok(self) -> None:
        catalog = build_canonical_catalog()
        runtime = BillingRuntime(catalog)
        result = runtime.checkout(
            CheckoutRequest(
                checkout_id="chk-1",
                tenant_id=TENANT,
                product_id=SHELL_1,
                plan_id="plan-oi-professional",
                price_id="price-oi-professional",
                customer_context="ctx-1",
                idempotency_key="key-00000001",
            ),
            catalog_price_id="price-oi-professional",
        )
        assert result["status"] == "CHECKOUT_OK"

    def test_checkout_idempotent(self) -> None:
        catalog = build_canonical_catalog()
        runtime = BillingRuntime(catalog)
        request = CheckoutRequest(
            checkout_id="chk-2",
            tenant_id=TENANT,
            product_id=SHELL_1,
            plan_id="plan-oi-professional",
            price_id="price-oi-professional",
            customer_context="ctx-1",
            idempotency_key="key-00000002",
        )
        runtime.checkout(request, catalog_price_id="price-oi-professional")
        replay = runtime.checkout(request, catalog_price_id="price-oi-professional")
        assert replay["status"] == "IDEMPOTENT_REPLAY"

    def test_cross_shell_checkout_rejected(self) -> None:
        catalog = build_canonical_catalog()
        runtime = BillingRuntime(catalog)
        with pytest.raises(ValueError, match="cross-shell"):
            runtime.checkout(
                CheckoutRequest(
                    checkout_id="chk-3",
                    tenant_id=TENANT,
                    product_id=SHELL_2,
                    plan_id="plan-oi-professional",
                    price_id="price-oi-professional",
                    customer_context="ctx-1",
                    idempotency_key="key-00000003",
                ),
                catalog_price_id="price-oi-professional",
            )

    def test_inactive_price_rejected(self) -> None:
        catalog = build_canonical_catalog()
        runtime = BillingRuntime(catalog)
        with pytest.raises(ValueError, match="inactive"):
            runtime.checkout(
                CheckoutRequest(
                    checkout_id="chk-4",
                    tenant_id=TENANT,
                    product_id=SHELL_2,
                    plan_id="plan-pe-academy",
                    price_id="price-pe-academy",
                    customer_context="ctx-1",
                    idempotency_key="key-00000004",
                ),
                catalog_price_id="price-pe-academy",
            )

    def test_unsigned_webhook_rejected(self) -> None:
        catalog = build_canonical_catalog()
        runtime = BillingRuntime(catalog)
        key = runtime.rotate_webhook_key(SHELL_1)
        assert len(key) == 64
        payload = '{"event":"invoice.paid"}'
        signature = runtime._sign(SHELL_1, payload)
        replay_guard = (datetime.now(UTC) + timedelta(minutes=10)).isoformat()
        # Correct signature but stale replay guard -> rejected.
        assert (
            runtime.verify_webhook(
                SHELL_1, payload, signature, replay_guard=replay_guard
            )
            is False
        )
        # Fresh guard -> accepted.
        fresh = datetime.now(UTC).isoformat()
        assert runtime.verify_webhook(SHELL_1, payload, signature, replay_guard=fresh) is True
        # Wrong signature -> rejected.
        assert runtime.verify_webhook(SHELL_1, payload, "deadbeef", replay_guard=fresh) is False

    def test_entitlement_reconciliation(self) -> None:
        catalog = build_canonical_catalog()
        runtime = BillingRuntime(catalog)
        runtime.checkout(
            CheckoutRequest(
                checkout_id="chk-5",
                tenant_id=TENANT,
                product_id=SHELL_1,
                plan_id="plan-oi-professional",
                price_id="price-oi-professional",
                customer_context="ctx-1",
                idempotency_key="key-00000005",
            ),
            catalog_price_id="price-oi-professional",
        )
        entitlements = runtime.reconcile_entitlements(TENANT)
        assert entitlements[SHELL_1] is True
        assert entitlements[SHELL_2] is False

    def test_no_cross_shell_activation(self) -> None:
        catalog = build_canonical_catalog()
        runtime = BillingRuntime(catalog)
        runtime.checkout(
            CheckoutRequest(
                checkout_id="chk-6",
                tenant_id=TENANT,
                product_id=SHELL_1,
                plan_id="plan-oi-professional",
                price_id="price-oi-professional",
                customer_context="ctx-1",
                idempotency_key="key-00000006",
            ),
            catalog_price_id="price-oi-professional",
        )
        assert runtime.cross_shell_activation_count() == 0

    def test_trial_no_silent_conversion(self) -> None:
        catalog = build_canonical_catalog()
        runtime = BillingRuntime(catalog)
        result = runtime.checkout(
            CheckoutRequest(
                checkout_id="chk-7",
                tenant_id=TENANT,
                product_id=SHELL_1,
                plan_id="plan-oi-professional",
                price_id="price-oi-professional",
                customer_context="ctx-1",
                idempotency_key="key-00000007",
                trial=True,
            ),
            catalog_price_id="price-oi-professional",
        )
        assert result["trial"] is True
        # Trial does not activate entitlements silently.
        entitlements = runtime.reconcile_entitlements(TENANT)
        assert entitlements[SHELL_1] is False

    def test_cancel_at_period_end_keeps_entitlement(self) -> None:
        catalog = build_canonical_catalog()
        runtime = BillingRuntime(catalog)
        runtime.checkout(
            CheckoutRequest(
                checkout_id="chk-8",
                tenant_id=TENANT,
                product_id=SHELL_1,
                plan_id="plan-oi-professional",
                price_id="price-oi-professional",
                customer_context="ctx-1",
                idempotency_key="key-00000008",
            ),
            catalog_price_id="price-oi-professional",
        )
        runtime.cancel(TENANT, at_period_end=True)
        assert runtime.reconcile_entitlements(TENANT)[SHELL_1] is True

    def test_cancel_immediate_revokes_entitlement(self) -> None:
        catalog = build_canonical_catalog()
        runtime = BillingRuntime(catalog)
        runtime.checkout(
            CheckoutRequest(
                checkout_id="chk-9",
                tenant_id=TENANT,
                product_id=SHELL_1,
                plan_id="plan-oi-professional",
                price_id="price-oi-professional",
                customer_context="ctx-1",
                idempotency_key="key-00000009",
            ),
            catalog_price_id="price-oi-professional",
        )
        runtime.cancel(TENANT, at_period_end=False)
        assert runtime.reconcile_entitlements(TENANT)[SHELL_1] is False

    def test_revenue_separated_by_product(self) -> None:
        catalog = build_canonical_catalog()
        runtime = BillingRuntime(catalog)
        runtime.record_revenue(SHELL_1, Decimal("149.00"))
        runtime.record_revenue(SHELL_2, Decimal("0.00"))
        revenue = runtime.revenue_by_product()
        assert revenue[SHELL_1] == Decimal("149.00")
        assert SHELL_2 in revenue

    def test_refund_audited(self) -> None:
        catalog = build_canonical_catalog()
        runtime = BillingRuntime(catalog)
        runtime.record_refund("ref-1", TENANT, 14900, "customer request")
        refunds = runtime.refunds()
        assert len(refunds) == 1
        assert refunds[0]["amount_cents"] == 14900

    def test_no_hardcoded_prices_outside_catalog(self) -> None:
        # All prices must live in the catalogue; the runtime only reads
        # server-side price objects by id.
        catalog = build_canonical_catalog()
        runtime = BillingRuntime(catalog)
        with pytest.raises(ValueError, match="unknown price"):
            runtime.checkout(
                CheckoutRequest(
                    checkout_id="chk-10",
                    tenant_id=TENANT,
                    product_id=SHELL_1,
                    plan_id="plan-oi-professional",
                    price_id="price-made-up",
                    customer_context="ctx-1",
                    idempotency_key="key-00000010",
                ),
                catalog_price_id="price-made-up",
            )
