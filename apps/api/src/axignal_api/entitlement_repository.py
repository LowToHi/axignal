from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from axignal_api.repository import ResearchRepository


class EntitlementRepository(ResearchRepository):
    def activate_trial(
        self,
        *,
        tenant_id: UUID,
        actor_subject: str,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        current = now or datetime.now(UTC)
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                "SELECT * FROM tenant_private.activate_controlled_trial(%s, %s)",
                (actor_subject, current),
            )
            row = cursor.fetchone()
            if row is None:
                raise RuntimeError("Trial activation returned no entitlement")
            return row

    def current_entitlement(
        self,
        *,
        tenant_id: UUID,
    ) -> dict[str, Any] | None:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT *
                FROM tenant_private.organisation_entitlements
                WHERE tenant_id = %s
                ORDER BY (state = 'ACTIVE') DESC, created_at DESC
                LIMIT 1
                """,
                (tenant_id,),
            )
            return cursor.fetchone()

    def reserve(
        self,
        *,
        tenant_id: UUID,
        operation_id: str,
        capability: str,
        requested_tokens: int,
        actor_subject: str,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        current = now or datetime.now(UTC)
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT *
                FROM tenant_private.reserve_ai_tokens(%s, %s, %s, %s, %s)
                """,
                (
                    operation_id,
                    capability,
                    requested_tokens,
                    actor_subject,
                    current,
                ),
            )
            row = cursor.fetchone()
            if row is None:
                raise RuntimeError("Token reservation returned no row")
            return row

    def reconcile(
        self,
        *,
        tenant_id: UUID,
        reservation_id: UUID,
        actual_tokens: int,
        actor_subject: str,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        current = now or datetime.now(UTC)
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT *
                FROM tenant_private.reconcile_ai_tokens(%s, %s, %s, %s)
                """,
                (reservation_id, actual_tokens, actor_subject, current),
            )
            row = cursor.fetchone()
            if row is None:
                raise RuntimeError("Token reconciliation returned no row")
            return row

    def release(
        self,
        *,
        tenant_id: UUID,
        reservation_id: UUID,
        actor_subject: str,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        current = now or datetime.now(UTC)
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT *
                FROM tenant_private.release_ai_token_reservation(%s, %s, %s)
                """,
                (reservation_id, actor_subject, current),
            )
            row = cursor.fetchone()
            if row is None:
                raise RuntimeError("Token release returned no row")
            return row

    def expire_trial(
        self,
        *,
        tenant_id: UUID,
        actor_subject: str,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        current = now or datetime.now(UTC)
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                "SELECT * FROM tenant_private.expire_current_trial(%s, %s)",
                (actor_subject, current),
            )
            row = cursor.fetchone()
            if row is None:
                raise RuntimeError("Trial expiry returned no entitlement")
            return row

    def usage(self, *, tenant_id: UUID) -> dict[str, Any] | None:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT
                  entitlement_id,
                  entitlement_kind,
                  plan_code,
                  state,
                  starts_at,
                  expires_at,
                  unlimited_ai_tokens,
                  token_budget_total,
                  token_budget_reserved,
                  token_budget_consumed,
                  CASE
                    WHEN token_budget_total IS NULL THEN NULL
                    ELSE token_budget_total - token_budget_reserved - token_budget_consumed
                  END AS token_budget_available
                FROM tenant_private.organisation_entitlements
                WHERE tenant_id = %s
                ORDER BY (state = 'ACTIVE') DESC, created_at DESC
                LIMIT 1
                """,
                (tenant_id,),
            )
            return cursor.fetchone()
