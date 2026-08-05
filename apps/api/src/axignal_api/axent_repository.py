from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from typing import Any
from uuid import UUID

import psycopg
from psycopg import sql
from psycopg.rows import dict_row


class AxentRepository:
    """Tenant-scoped adapter over the C3 AXENT persistence authority."""

    def __init__(self, dsn: str, encryption_key: str) -> None:
        self.dsn = dsn
        self.encryption_key = encryption_key

    @contextmanager
    def _cursor(self, *, tenant_id: UUID) -> Iterator[psycopg.Cursor[dict[str, Any]]]:
        with (
            psycopg.connect(self.dsn, row_factory=dict_row) as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier("axignal_app")))
            cursor.execute(
                "SELECT set_config('app.tenant_id', %s, true)",
                (str(tenant_id),),
            )
            yield cursor

    def list_conversations(
        self,
        *,
        tenant_id: UUID,
        identity_subject: str,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        with self._cursor(tenant_id=tenant_id) as cursor:
            cursor.execute(
                "SELECT tenant_private.list_axent_conversations(%s, %s) AS value",
                (identity_subject, limit),
            )
            row = cursor.fetchone()
        value = row["value"] if row else []
        return list(value) if isinstance(value, list) else []

    def create_conversation(
        self,
        *,
        tenant_id: UUID,
        identity_subject: str,
        request_id: str,
        title: str,
        retention_class: str,
        actor_subject: str,
    ) -> dict[str, Any]:
        with self._cursor(tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT *
                FROM tenant_private.create_axent_conversation_idempotent(
                  %s, %s, %s, %s, %s
                )
                """,
                (request_id, identity_subject, title, retention_class, actor_subject),
            )
            row = cursor.fetchone()
        if row is None:
            raise RuntimeError("AXENT conversation was not persisted")
        return row

    def append_message(
        self,
        *,
        tenant_id: UUID,
        identity_subject: str,
        conversation_id: UUID,
        request_id: str,
        message_role: str,
        content: str,
        actor_subject: str,
    ) -> dict[str, Any]:
        self._require_owned_conversation(
            tenant_id=tenant_id,
            identity_subject=identity_subject,
            conversation_id=conversation_id,
        )
        with self._cursor(tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT *
                FROM tenant_private.append_axent_message_idempotent(
                  %s, %s, %s, %s, %s, %s
                )
                """,
                (
                    conversation_id,
                    request_id,
                    message_role,
                    content,
                    self.encryption_key,
                    actor_subject,
                ),
            )
            row = cursor.fetchone()
        if row is None:
            raise RuntimeError("AXENT message was not persisted")
        return row

    def export_conversation(
        self,
        *,
        tenant_id: UUID,
        identity_subject: str,
        conversation_id: UUID,
        actor_subject: str,
    ) -> dict[str, Any]:
        self._require_owned_conversation(
            tenant_id=tenant_id,
            identity_subject=identity_subject,
            conversation_id=conversation_id,
        )
        with self._cursor(tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT tenant_private.export_axent_conversation(%s, %s, %s) AS value
                """,
                (conversation_id, self.encryption_key, actor_subject),
            )
            row = cursor.fetchone()
        value = row["value"] if row else None
        if not isinstance(value, dict):
            raise LookupError("AXENT conversation not found")
        return value

    def request_deletion(
        self,
        *,
        tenant_id: UUID,
        identity_subject: str,
        conversation_id: UUID,
        delete_after: datetime,
        actor_subject: str,
    ) -> dict[str, Any]:
        self._require_owned_conversation(
            tenant_id=tenant_id,
            identity_subject=identity_subject,
            conversation_id=conversation_id,
        )
        with self._cursor(tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT *
                FROM tenant_private.request_axent_conversation_deletion(%s, %s, %s)
                """,
                (conversation_id, delete_after, actor_subject),
            )
            row = cursor.fetchone()
        if row is None:
            raise LookupError("AXENT conversation not found")
        return row

    def _require_owned_conversation(
        self,
        *,
        tenant_id: UUID,
        identity_subject: str,
        conversation_id: UUID,
    ) -> None:
        conversations = self.list_conversations(
            tenant_id=tenant_id,
            identity_subject=identity_subject,
            limit=50,
        )
        if not any(
            str(item.get("conversation_id")) == str(conversation_id)
            for item in conversations
        ):
            raise LookupError("AXENT conversation not found")
