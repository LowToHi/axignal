from __future__ import annotations

from typing import Any
from uuid import UUID

from redis.exceptions import RedisError

from axignal_api.queue import ResearchJob
from axignal_api.repository import OutboxEvent
from axignal_api.ted_repository import TEDResearchRepository


class ConcurrentTEDResearchRepository(TEDResearchRepository):
    """Repository operations that must remain atomic across concurrent workers."""

    def claim_run_for_worker(
        self,
        *,
        tenant_id: UUID,
        run_id: UUID,
    ) -> dict[str, Any] | None:
        """Atomically acquire a queued run for exactly one worker."""
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                UPDATE tenant_private.research_runs
                SET state = 'RETRIEVING', updated_at = now()
                WHERE research_run_id = %s AND state = 'QUEUED'
                RETURNING *
                """,
                (run_id,),
            )
            return cursor.fetchone()

    def publish_pending_to_queue(self, *, queue: Any, limit: int) -> int:
        """Publish an outbox batch while holding row locks until commit.

        Redis plus PostgreSQL still provides at-least-once delivery if the process
        dies after enqueue and before commit. Consumer-side run claiming therefore
        remains mandatory. The row locks prevent the normal multi-worker duplicate
        publication storm observed by G7.
        """
        published = 0
        with self._cursor(role="axignal_worker") as cursor:
            cursor.execute(
                """
                SELECT outbox_event_id, aggregate_id, event_type, payload, attempts
                FROM axignal_global.outbox_events
                WHERE status = 'PENDING' AND available_at <= now()
                ORDER BY created_at
                FOR UPDATE SKIP LOCKED
                LIMIT %s
                """,
                (limit,),
            )
            rows = cursor.fetchall()
            for row in rows:
                event = OutboxEvent(
                    outbox_event_id=row["outbox_event_id"],
                    aggregate_id=row["aggregate_id"],
                    event_type=row["event_type"],
                    payload=row["payload"],
                    attempts=row["attempts"],
                )
                try:
                    if event.event_type == "research.run.requested":
                        queue.enqueue(ResearchJob.from_payload(event.payload))
                    else:
                        queue.publish_event(event)
                except (RedisError, ValueError, KeyError, TypeError) as exc:
                    cursor.execute(
                        """
                        UPDATE axignal_global.outbox_events
                        SET attempts = attempts + 1,
                            last_error = %s,
                            status = CASE
                              WHEN attempts >= 4 THEN 'FAILED'
                              ELSE 'PENDING'
                            END,
                            available_at = now() + interval '30 seconds'
                        WHERE outbox_event_id = %s AND status = 'PENDING'
                        """,
                        (
                            f"{exc.__class__.__name__}: {exc}"[:500],
                            event.outbox_event_id,
                        ),
                    )
                    continue

                cursor.execute(
                    """
                    UPDATE axignal_global.outbox_events
                    SET status = 'PUBLISHED',
                        published_at = now(),
                        attempts = attempts + 1,
                        last_error = NULL
                    WHERE outbox_event_id = %s AND status = 'PENDING'
                    """,
                    (event.outbox_event_id,),
                )
                if cursor.rowcount != 1:
                    raise RuntimeError("Locked outbox event lost its PENDING state")
                published += 1
        return published
