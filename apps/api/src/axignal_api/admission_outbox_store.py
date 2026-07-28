from __future__ import annotations

from uuid import UUID

from axignal_api.admission_queue import AdmissionOutboxEvent


class AdmissionOutboxStoreMixin:
    def pending_admission_outbox(self, limit: int = 10) -> list[AdmissionOutboxEvent]:
        with self._cursor("axignal_app") as cursor:
            cursor.execute(
                """
                SELECT admission_outbox_event_id, aggregate_id, event_type,
                       payload, attempts
                FROM axignal_global.admission_outbox_events
                WHERE status = 'PENDING' AND available_at <= now()
                ORDER BY created_at LIMIT %s
                """,
                (limit,),
            )
            return [
                AdmissionOutboxEvent(
                    event_id=row["admission_outbox_event_id"],
                    aggregate_id=row["aggregate_id"],
                    event_type=row["event_type"],
                    payload=row["payload"],
                    attempts=row["attempts"],
                )
                for row in cursor.fetchall()
            ]

    def mark_admission_outbox_published(self, event_id: UUID) -> None:
        with self._cursor("axignal_app") as cursor:
            cursor.execute(
                """
                UPDATE axignal_global.admission_outbox_events
                SET status = 'PUBLISHED', published_at = now(),
                    attempts = attempts + 1
                WHERE admission_outbox_event_id = %s AND status = 'PENDING'
                """,
                (event_id,),
            )

    def mark_admission_outbox_failed(self, event_id: UUID, error: str) -> None:
        with self._cursor("axignal_app") as cursor:
            cursor.execute(
                """
                UPDATE axignal_global.admission_outbox_events
                SET attempts = attempts + 1, last_error = %s,
                    status = CASE WHEN attempts >= 4 THEN 'FAILED' ELSE 'PENDING' END,
                    available_at = now() + interval '30 seconds'
                WHERE admission_outbox_event_id = %s AND status = 'PENDING'
                """,
                (error[:500], event_id),
            )
