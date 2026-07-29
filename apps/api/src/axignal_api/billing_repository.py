from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from axignal_api.repository import ResearchRepository


class BillingRepository(ResearchRepository):
    def request_selection(
        self,
        *,
        tenant_id: UUID,
        operation_id: str,
        plan_code: str,
        provider_account_id: str,
        actor_subject: str,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        current = now or datetime.now(UTC)
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT * FROM tenant_private.request_paid_plan_selection(
                  %s, %s, %s, %s, %s
                )
                """,
                (operation_id, plan_code, provider_account_id, actor_subject, current),
            )
            row = cursor.fetchone()
            if row is None:
                raise RuntimeError("Paid selection returned no row")
            return row

    def mark_checkout_created(
        self,
        *,
        tenant_id: UUID,
        selection_id: UUID,
        checkout_session_id: str,
        price_id: str,
        actor_subject: str,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        current = now or datetime.now(UTC)
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT * FROM tenant_private.mark_checkout_session_created(
                  %s, %s, %s, %s, %s
                )
                """,
                (
                    selection_id,
                    checkout_session_id,
                    price_id,
                    actor_subject,
                    current,
                ),
            )
            row = cursor.fetchone()
            if row is None:
                raise RuntimeError("Checkout creation returned no selection")
            return row

    def current_selection(self, *, tenant_id: UUID) -> dict[str, Any] | None:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT *
                FROM tenant_private.billing_plan_selections
                WHERE tenant_id = %s
                ORDER BY (state NOT IN ('CANCELLED', 'FAILED', 'ROLLED_BACK')) DESC,
                         updated_at DESC
                LIMIT 1
                """,
                (tenant_id,),
            )
            return cursor.fetchone()

    def request_upgrade(
        self,
        *,
        tenant_id: UUID,
        target_plan_code: str,
        target_price_id: str,
        actor_subject: str,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        current = now or datetime.now(UTC)
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT * FROM tenant_private.request_paid_plan_upgrade(
                  %s, %s, %s, %s
                )
                """,
                (target_plan_code, target_price_id, actor_subject, current),
            )
            row = cursor.fetchone()
            if row is None:
                raise RuntimeError("Paid upgrade returned no selection")
            return row

    def request_cancellation(
        self,
        *,
        tenant_id: UUID,
        cancel_at_period_end: bool,
        actor_subject: str,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        current = now or datetime.now(UTC)
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT * FROM tenant_private.request_paid_cancellation(%s, %s, %s)
                """,
                (cancel_at_period_end, actor_subject, current),
            )
            row = cursor.fetchone()
            if row is None:
                raise RuntimeError("Paid cancellation returned no selection")
            return row

    def apply_stripe_event(
        self,
        *,
        event_id: str,
        event_type: str,
        event_created_at: datetime,
        livemode: bool,
        payload_digest: str,
        provider_account_id: str,
        selection_id: UUID | None,
        checkout_session_id: str | None,
        customer_id: str | None,
        subscription_id: str | None,
        subscription_item_id: str | None,
        price_id: str | None,
        plan_code: str | None,
        subscription_status: str | None,
        current_period_end: datetime | None,
        cancel_at_period_end: bool,
        amount_minor: int | None,
        currency: str | None,
        actor_subject: str,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        current = now or datetime.now(UTC)
        with self._cursor(role="axignal_billing_worker") as cursor:
            cursor.execute(
                """
                SELECT tenant_private.apply_stripe_billing_event(
                  %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                  %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) AS result
                """,
                (
                    event_id,
                    event_type,
                    event_created_at,
                    livemode,
                    payload_digest,
                    provider_account_id,
                    selection_id,
                    checkout_session_id,
                    customer_id,
                    subscription_id,
                    subscription_item_id,
                    price_id,
                    plan_code,
                    subscription_status,
                    current_period_end,
                    cancel_at_period_end,
                    amount_minor,
                    currency,
                    actor_subject,
                    current,
                ),
            )
            row = cursor.fetchone()
            if row is None or not isinstance(row.get("result"), dict):
                raise RuntimeError("Stripe event returned no result")
            return row["result"]

    def rollback(
        self,
        *,
        selection_id: UUID,
        actor_subject: str,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        current = now or datetime.now(UTC)
        with self._cursor(role="axignal_billing_worker") as cursor:
            cursor.execute(
                "SELECT * FROM tenant_private.rollback_paid_lifecycle(%s, %s, %s)",
                (selection_id, actor_subject, current),
            )
            row = cursor.fetchone()
            if row is None:
                raise RuntimeError("Paid rollback returned no selection")
            return row

    def ledger(self, *, tenant_id: UUID) -> list[dict[str, Any]]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT *
                FROM tenant_private.payment_ledger_entries
                WHERE tenant_id = %s
                ORDER BY occurred_at, created_at, ledger_entry_id
                """,
                (tenant_id,),
            )
            return list(cursor.fetchall())
