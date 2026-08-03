from __future__ import annotations

from typing import Any
from uuid import UUID

from axignal_api.axent_repository import AxentRepository


class AxentNotificationRepository(AxentRepository):
    def list_notifications(
        self,
        *,
        tenant_id: UUID,
        recipient_subject: str,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT *
                FROM tenant_private.support_notifications
                WHERE tenant_id = %s
                  AND recipient_subject = %s
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (tenant_id, recipient_subject, limit),
            )
            return list(cursor.fetchall())

    def acknowledge_notification(
        self,
        *,
        tenant_id: UUID,
        recipient_subject: str,
        notification_id: UUID,
    ) -> dict[str, Any]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                UPDATE tenant_private.support_notifications
                SET delivery_state = 'DELIVERED', delivered_at = COALESCE(delivered_at, now())
                WHERE tenant_id = %s
                  AND recipient_subject = %s
                  AND notification_id = %s
                  AND delivery_state IN ('PENDING', 'DELIVERED')
                RETURNING *
                """,
                (tenant_id, recipient_subject, notification_id),
            )
            row = cursor.fetchone()
            if row is None:
                raise LookupError("support_notification_not_found")
            return row
