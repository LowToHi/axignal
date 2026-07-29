from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from typing import Any, Literal
from uuid import UUID

import psycopg
from psycopg import sql
from psycopg.rows import dict_row

RetentionRole = Literal["axignal_app", "axignal_retention_worker", "axignal_operator"]


class RetentionRepository:
    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    @contextmanager
    def _cursor(
        self,
        *,
        role: RetentionRole,
        tenant_id: UUID | None = None,
    ) -> Iterator[psycopg.Cursor[dict[str, Any]]]:
        with (
            psycopg.connect(self.dsn, row_factory=dict_row) as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(role)))
            if tenant_id is not None:
                cursor.execute(
                    "SELECT set_config('app.tenant_id', %s, true)",
                    (str(tenant_id),),
                )
            yield cursor

    def lifecycle(self, *, tenant_id: UUID) -> dict[str, Any] | None:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT * FROM tenant_private.workspace_lifecycle
                WHERE tenant_id = %s
                """,
                (tenant_id,),
            )
            return cursor.fetchone()

    def request_deletion(
        self,
        *,
        tenant_id: UUID,
        actor_subject: str,
        retention_seconds: int,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        current = now or datetime.now(UTC)
        retention_until = current + timedelta(seconds=retention_seconds)
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT * FROM tenant_private.request_workspace_deletion(%s, %s, %s)
                """,
                (actor_subject, retention_until, current),
            )
            row = cursor.fetchone()
            if row is None:
                raise RuntimeError("Deletion request returned no lifecycle row")
            return row

    def suspend(
        self,
        *,
        tenant_id: UUID,
        reason_code: str,
        actor_subject: str,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        current = now or datetime.now(UTC)
        with self._cursor(role="axignal_operator") as cursor:
            cursor.execute(
                """
                SELECT * FROM tenant_private.operator_suspend_workspace(%s, %s, %s, %s)
                """,
                (tenant_id, reason_code, actor_subject, current),
            )
            row = cursor.fetchone()
            if row is None:
                raise RuntimeError("Suspension returned no lifecycle row")
            return row

    def queue_due(self, *, now: datetime | None = None) -> int:
        current = now or datetime.now(UTC)
        with self._cursor(role="axignal_retention_worker") as cursor:
            cursor.execute(
                "SELECT tenant_private.queue_due_workspace_purges(%s) AS queued",
                (current,),
            )
            row = cursor.fetchone()
            return int(row["queued"] if row is not None else 0)

    def claim(
        self,
        *,
        worker_id: str,
        lease_seconds: int,
        now: datetime | None = None,
    ) -> dict[str, Any] | None:
        current = now or datetime.now(UTC)
        with self._cursor(role="axignal_retention_worker") as cursor:
            cursor.execute(
                """
                SELECT * FROM tenant_private.claim_workspace_purge(%s, %s, %s)
                """,
                (worker_id, current, lease_seconds),
            )
            return cursor.fetchone()

    def purge(
        self,
        *,
        deletion_id: UUID,
        worker_id: str,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        current = now or datetime.now(UTC)
        with self._cursor(role="axignal_retention_worker") as cursor:
            cursor.execute(
                """
                SELECT * FROM tenant_private.purge_claimed_workspace(%s, %s, %s)
                """,
                (deletion_id, worker_id, current),
            )
            row = cursor.fetchone()
            if row is None:
                raise RuntimeError("Purge returned no tombstone")
            return row

    def reapply_tombstone(
        self,
        *,
        tenant_id: UUID,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        current = now or datetime.now(UTC)
        with self._cursor(role="axignal_retention_worker") as cursor:
            cursor.execute(
                """
                SELECT tenant_private.reapply_deletion_tombstone(%s, %s) AS result
                """,
                (tenant_id, current),
            )
            row = cursor.fetchone()
            if row is None:
                raise RuntimeError("Tombstone reapplication returned no result")
            return dict(row["result"])
