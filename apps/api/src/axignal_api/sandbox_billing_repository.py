"""PostgreSQL repository for the sandbox billing runtime (Prioridad 6).

Replaces BillingRuntime in-memory state with durable storage:
catalogue (products/plans/prices), subscriptions, idempotency keys,
entitlements, webhook events. Live Stripe remains disabled; the adapter
contract is served by this repository under sandbox mode.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from psycopg.types.json import Jsonb

from axignal_api.repository import ResearchRepository

SUBSCRIPTION_STATES = (
    "ACTIVE",
    "DUNNING",
    "CANCELLED_AT_PERIOD_END",
    "CANCELLED_IMMEDIATE",
    "TRIAL",
)


class SandboxBillingRepository(ResearchRepository):
    """Durable tenant-scoped sandbox billing store."""

    # --- Catalogue ----------------------------------------------------------

    def seed_catalogue(
        self,
        products: list[dict[str, Any]],
        plans: list[dict[str, Any]],
        prices: list[dict[str, Any]],
    ) -> None:
        with self._cursor(role="axignal_worker") as cursor:
            for product in products:
                cursor.execute(
                    """
                    INSERT INTO tenant_private.sandbox_products
                      (product_id, shell_id, commercial_status)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (product_id) DO UPDATE
                      SET shell_id = EXCLUDED.shell_id
                    """,
                    (product["product_id"], product["shell_id"],
                     product.get("commercial_status", "ACTIVE_CONTRACT_DEFINITION")),
                )
            for plan in plans:
                cursor.execute(
                    """
                    INSERT INTO tenant_private.sandbox_plans
                      (plan_id, product_id, name, seats, status, is_academy)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (plan_id) DO UPDATE
                      SET name = EXCLUDED.name, seats = EXCLUDED.seats,
                          status = EXCLUDED.status, is_academy = EXCLUDED.is_academy
                    """,
                    (plan["plan_id"], plan["product_id"], plan["name"],
                     plan["seats"], plan["status"], plan.get("is_academy", False)),
                )
            for price in prices:
                cursor.execute(
                    """
                    INSERT INTO tenant_private.sandbox_prices
                      (price_id, product_id, plan_id, amount_cents, currency,
                       interval_unit, tax_mode, version, active)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (price_id) DO UPDATE
                      SET amount_cents = EXCLUDED.amount_cents,
                          currency = EXCLUDED.currency,
                          interval_unit = EXCLUDED.interval_unit,
                          tax_mode = EXCLUDED.tax_mode,
                          version = EXCLUDED.version,
                          active = EXCLUDED.active
                    """,
                    (price["price_id"], price["product_id"], price["plan_id"],
                     price["amount_cents"], price["currency"],
                     price["interval_unit"], price["tax_mode"],
                     price.get("version", 1), price.get("active", True)),
                )

    def get_price(self, price_id: str) -> dict[str, Any] | None:
        with self._cursor(role="axignal_app") as cursor:
            cursor.execute(
                """
                SELECT price_id, product_id, plan_id, amount_cents, currency,
                       interval_unit, tax_mode, version, active
                FROM tenant_private.sandbox_prices
                WHERE price_id = %s
                """,
                (price_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def list_plans(self, product_id: str) -> list[dict[str, Any]]:
        with self._cursor(role="axignal_app") as cursor:
            cursor.execute(
                """
                SELECT plan_id, product_id, name, seats, status, is_academy
                FROM tenant_private.sandbox_plans
                WHERE product_id = %s
                ORDER BY name
                """,
                (product_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    # --- Subscriptions ------------------------------------------------------

    def create_subscription(
        self,
        *,
        tenant_id: UUID,
        product_id: str,
        plan_id: str,
        price_id: str,
        trial: bool,
    ) -> dict[str, Any]:
        subscription_id = uuid4()
        status = "TRIAL" if trial else "ACTIVE"
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                INSERT INTO tenant_private.sandbox_subscriptions
                  (subscription_id, tenant_id, product_id, plan_id, price_id,
                   status, trial)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING subscription_id, product_id, plan_id, status
                """,
                (subscription_id, tenant_id, product_id, plan_id, price_id,
                 status, trial),
            )
            row = cursor.fetchone()
            return dict(row) if row else {}

    def get_subscription(self, *, tenant_id: UUID) -> dict[str, Any] | None:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT subscription_id, product_id, plan_id, price_id, status,
                       trial, grace_until, created_at, updated_at
                FROM tenant_private.sandbox_subscriptions
                WHERE tenant_id = %s
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (tenant_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_subscription_status(
        self, *, tenant_id: UUID, status: str, grace_until: datetime | None = None
    ) -> dict[str, Any]:
        if status not in SUBSCRIPTION_STATES:
            raise ValueError(f"invalid subscription status {status!r}")
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                UPDATE tenant_private.sandbox_subscriptions
                SET status = %s, grace_until = COALESCE(%s, grace_until),
                    updated_at = now()
                WHERE tenant_id = %s
                RETURNING subscription_id, product_id, status
                """,
                (status, grace_until, tenant_id),
            )
            row = cursor.fetchone()
            if row is None:
                raise LookupError("no subscription")
            return dict(row)

    def change_plan(
        self, *, tenant_id: UUID, new_plan_id: str, new_price_id: str
    ) -> dict[str, Any]:
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                UPDATE tenant_private.sandbox_subscriptions
                SET plan_id = %s, price_id = %s, updated_at = now()
                WHERE tenant_id = %s
                RETURNING subscription_id, product_id, plan_id, price_id
                """,
                (new_plan_id, new_price_id, tenant_id),
            )
            row = cursor.fetchone()
            if row is None:
                raise LookupError("no subscription")
            return dict(row)

    # --- Idempotency --------------------------------------------------------

    def record_idempotency_key(
        self, *, tenant_id: UUID, idempotency_key: str, checkout_id: str, product_id: str
    ) -> bool:
        """Record a key; returns False if it was already present (replay)."""
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                INSERT INTO tenant_private.billing_idempotency_keys
                  (tenant_id, idempotency_key, checkout_id, product_id)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (tenant_id, idempotency_key) DO NOTHING
                """,
                (tenant_id, idempotency_key, checkout_id, product_id),
            )
            return cursor.rowcount == 1

    def has_idempotency_key(self, *, tenant_id: UUID, idempotency_key: str) -> bool:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT 1 FROM tenant_private.billing_idempotency_keys
                WHERE tenant_id = %s AND idempotency_key = %s
                """,
                (tenant_id, idempotency_key),
            )
            return cursor.fetchone() is not None

    # --- Entitlements -------------------------------------------------------

    def set_entitlement(
        self, *, tenant_id: UUID, product_id: str, allowed: bool
    ) -> None:
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                INSERT INTO tenant_private.billing_entitlements
                  (tenant_id, product_id, allowed, updated_at)
                VALUES (%s, %s, %s, now())
                ON CONFLICT (tenant_id, product_id)
                DO UPDATE SET allowed = EXCLUDED.allowed, updated_at = now()
                """,
                (tenant_id, product_id, allowed),
            )

    def entitlements(self, *, tenant_id: UUID) -> dict[str, bool]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT product_id, allowed
                FROM tenant_private.billing_entitlements
                WHERE tenant_id = %s
                """,
                (tenant_id,),
            )
            return {row["product_id"]: row["allowed"] for row in cursor.fetchall()}

    # --- Webhook events -----------------------------------------------------

    def record_webhook_event(
        self,
        *,
        tenant_id: UUID,
        product_id: str,
        event_type: str,
        payload: dict[str, Any],
        signature: str,
    ) -> UUID:
        event_id = uuid4()
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                INSERT INTO tenant_private.billing_webhook_events
                  (webhook_event_id, tenant_id, product_id, event_type,
                   payload, signature)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (event_id, tenant_id, product_id, event_type, Jsonb(payload), signature),
            )
        return event_id

    def list_webhook_events(self, *, tenant_id: UUID) -> list[dict[str, Any]]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT webhook_event_id, product_id, event_type, received_at,
                       processed
                FROM tenant_private.billing_webhook_events
                WHERE tenant_id = %s
                ORDER BY received_at DESC
                """,
                (tenant_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def renew_subscription(self, *, tenant_id: UUID) -> dict[str, Any]:
        """Period renewal: ACTIVE/DUNNING -> ACTIVE with renewed_at set."""
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                UPDATE tenant_private.sandbox_subscriptions
                SET status = 'ACTIVE', grace_until = NULL,
                    renewed_at = now(), updated_at = now()
                WHERE tenant_id = %s AND status IN ('ACTIVE', 'DUNNING')
                RETURNING subscription_id, product_id, plan_id, status
                """,
                (tenant_id,),
            )
            row = cursor.fetchone()
            if row is None:
                raise LookupError("no renewable subscription")
            return dict(row)

    def change_plan_directional(
        self, *, tenant_id: UUID, new_plan_id: str, new_price_id: str
    ) -> dict[str, Any]:
        """Upgrade/downgrade with direction recorded for audit."""
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT plan_id, price_id
                FROM tenant_private.sandbox_subscriptions
                WHERE tenant_id = %s FOR UPDATE
                """,
                (tenant_id,),
            )
            current = cursor.fetchone()
            if current is None:
                raise LookupError("no subscription")
            cursor.execute(
                """
                SELECT amount_cents FROM tenant_private.sandbox_prices
                WHERE price_id = %s
                """,
                (current["price_id"],),
            )
            current_row = cursor.fetchone()
            current_amount = int(current_row["amount_cents"]) if current_row else 0
            cursor.execute(
                """
                SELECT amount_cents FROM tenant_private.sandbox_prices
                WHERE price_id = %s
                """,
                (new_price_id,),
            )
            new_row = cursor.fetchone()
            new_amount = int(new_row["amount_cents"]) if new_row else 0
            direction = "UPGRADE" if new_amount > current_amount else "DOWNGRADE"
            cursor.execute(
                """
                UPDATE tenant_private.sandbox_subscriptions
                SET plan_id = %s, price_id = %s, updated_at = now(),
                    last_change_direction = %s
                WHERE tenant_id = %s
                RETURNING subscription_id, product_id, plan_id, price_id
                """,
                (new_plan_id, new_price_id, direction, tenant_id),
            )
            row = cursor.fetchone()
            return dict(row) | {"direction": direction}

    def reconcile_entitlements(self, *, tenant_id: UUID) -> dict[str, Any]:
        """Server-side reconciliation: entitlement mirrors subscription state."""
        subscription = self.get_subscription(tenant_id=tenant_id)
        if subscription is None:
            self.set_entitlement(
                tenant_id=tenant_id,
                product_id="AXIGNAL_OPPORTUNITY_INTELLIGENCE",
                allowed=False,
            )
            return {
                "status": "NO_SUBSCRIPTION",
                "entitlements": self.entitlements(tenant_id=tenant_id),
            }
        active = subscription["status"] in ("ACTIVE", "TRIAL")
        self.set_entitlement(
            tenant_id=tenant_id,
            product_id=subscription["product_id"],
            allowed=active,
        )
        return {
            "status": subscription["status"],
            "entitlement_expected": active,
            "entitlements": self.entitlements(tenant_id=tenant_id),
        }

    def event_sequence(self, *, tenant_id: UUID) -> list[dict[str, Any]]:
        """Ordered billing event history (webhooks + lifecycle)."""
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT webhook_event_id AS event_id, event_type, received_at
                FROM tenant_private.billing_webhook_events
                WHERE tenant_id = %s
                ORDER BY received_at, webhook_event_id
                """,
                (tenant_id,),
            )
            return [dict(row) for row in cursor.fetchall()]
