"""AXENT core persistence repository (Mandato AXENT — sección 6).

Conversations, messages with append-only citations, verified facts,
typed tool invocations, action ledger, confirmations, notifications,
feedback and evaluations. All tenant-scoped via forced RLS; composite
tenant-aware FKs.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from psycopg.types.json import Jsonb

from axignal_api.repository import ResearchRepository


def sha256_ref(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, separators=(",", ":"), sort_keys=True, default=str
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


RISK_CLASSES = (
    "READ",
    "LOW_RISK_REVERSIBLE",
    "EXPLICIT_CONFIRMATION",
    "STEP_UP_REQUIRED",
    "HUMAN_ONLY",
    "DENY",
)


class AxentCoreRepository(ResearchRepository):
    # --- Conversations -------------------------------------------------------

    def create_conversation(
        self,
        *,
        tenant_id: UUID,
        identity_subject: str,
        title: str,
        retention_class: str = "STANDARD_90D",
    ) -> dict[str, Any]:
        retention_days = 30 if retention_class == "EPHEMERAL_30D" else 90
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                INSERT INTO tenant_private.axent_conversations (
                  conversation_id, tenant_id, identity_subject, title,
                  retention_class, retention_until
                ) VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING conversation_id, title, created_at
                """,
                (
                    uuid4(), tenant_id, identity_subject, title,
                    retention_class, datetime.now(UTC) + timedelta(days=retention_days),
                ),
            )
            row = cursor.fetchone()
            return dict(row) if row else {}

    def list_conversations(
        self, *, tenant_id: UUID, subject: str | None = None
    ) -> list[dict[str, Any]]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            if subject:
                cursor.execute(
                    """
                    SELECT conversation_id, title, state, created_at, updated_at
                    FROM tenant_private.axent_conversations
                    WHERE tenant_id = %s AND identity_subject = %s
                    ORDER BY updated_at DESC
                    """,
                    (tenant_id, subject),
                )
            else:
                cursor.execute(
                    """
                    SELECT conversation_id, title, state, created_at, updated_at
                    FROM tenant_private.axent_conversations
                    WHERE tenant_id = %s
                    ORDER BY updated_at DESC
                    """,
                    (tenant_id,),
                )
            return [dict(row) for row in cursor.fetchall()]

    def append_message(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
        message_role: str,
        content: str,
        citations: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        """Append a message + optional citations in one transaction."""
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT COALESCE(MAX(ordinal), 0) + 1 AS next_ordinal
                FROM tenant_private.axent_messages
                WHERE tenant_id = %s AND conversation_id = %s
                """,
                (tenant_id, conversation_id),
            )
            ordinal = int(cursor.fetchone()["next_ordinal"])
            message_id = uuid4()
            cursor.execute(
                """
                INSERT INTO tenant_private.axent_messages (
                  message_id, tenant_id, conversation_id, ordinal,
                  message_role, ciphertext, content_hash
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    message_id, tenant_id, conversation_id, ordinal,
                    message_role, content.encode("utf-8"),
                    sha256_ref({"content": content}),
                ),
            )
            cursor.execute(
                """
                UPDATE tenant_private.axent_conversations
                SET updated_at = now()
                WHERE tenant_id = %s AND conversation_id = %s
                """,
                (tenant_id, conversation_id),
            )
            for citation in citations or []:
                cursor.execute(
                    """
                    INSERT INTO tenant_private.axent_message_citations (
                      citation_id, tenant_id, message_id, authority_type,
                      authority_id, authority_version, excerpt_hash
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        uuid4(), tenant_id, message_id,
                        citation["authority_type"], citation["authority_id"],
                        citation.get("authority_version", "v1"),
                        sha256_ref(citation.get("excerpt", "")),
                    ),
                )
            return {"message_id": message_id, "ordinal": ordinal}

    def get_messages(
        self, *, tenant_id: UUID, conversation_id: UUID
    ) -> list[dict[str, Any]]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT message_id, ordinal, message_role, ciphertext, created_at
                FROM tenant_private.axent_messages
                WHERE tenant_id = %s AND conversation_id = %s
                ORDER BY ordinal
                """,
                (tenant_id, conversation_id),
            )
            messages = []
            for row in cursor.fetchall():
                message = dict(row)
                message["content"] = bytes(message.pop("ciphertext")).decode("utf-8")
                messages.append(message)
            return messages

    def get_citations(
        self, *, tenant_id: UUID, message_id: UUID
    ) -> list[dict[str, Any]]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT citation_id, authority_type, authority_id,
                       authority_version, retrieved_at
                FROM tenant_private.axent_message_citations
                WHERE tenant_id = %s AND message_id = %s
                ORDER BY retrieved_at, citation_id
                """,
                (tenant_id, message_id),
            )
            return [dict(row) for row in cursor.fetchall()]

    # --- Verified facts ------------------------------------------------------

    def record_verified_fact(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
        fact_type: str,
        subject_type: str,
        subject_id: str,
        value: dict[str, Any],
        citation_ids: list[UUID] | None = None,
    ) -> None:
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                INSERT INTO tenant_private.axent_verified_facts (
                  fact_id, tenant_id, conversation_id, fact_type,
                  subject_type, subject_id, value_json, citation_ids
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (tenant_id, conversation_id, subject_type,
                             subject_id, fact_type) DO UPDATE SET
                  value_json = EXCLUDED.value_json
                """,
                (
                    uuid4(), tenant_id, conversation_id, fact_type,
                    subject_type, subject_id, Jsonb(value),
                    citation_ids or [],
                ),
            )

    # --- Tool invocations ----------------------------------------------------

    def create_invocation(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
        tool_name: str,
        tool_version: str,
        parameters: dict[str, Any],
        risk_class: str,
    ) -> dict[str, Any]:
        if risk_class not in RISK_CLASSES:
            raise ValueError(f"invalid risk class {risk_class!r}")
        invocation_id = uuid4()
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                INSERT INTO tenant_private.axent_tool_invocations (
                  invocation_id, tenant_id, conversation_id, tool_name,
                  tool_version, parameters_hash, parameters_json, risk_class
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING invocation_id, tool_name, risk_class, state
                """,
                (
                    invocation_id, tenant_id, conversation_id, tool_name,
                    tool_version, sha256_ref(parameters), Jsonb(parameters),
                    risk_class,
                ),
            )
            row = cursor.fetchone()
            return dict(row) if row else {}

    def complete_invocation(
        self,
        *,
        tenant_id: UUID,
        invocation_id: UUID,
        state: str,
        before_state_hash: str | None = None,
        after_state_hash: str | None = None,
        error_code: str | None = None,
    ) -> None:
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                UPDATE tenant_private.axent_tool_invocations
                SET state = %s, before_state_hash = COALESCE(%s, before_state_hash),
                    after_state_hash = COALESCE(%s, after_state_hash),
                    error_code = %s, executed_at = now()
                WHERE tenant_id = %s AND invocation_id = %s
                """,
                (
                    state, before_state_hash, after_state_hash, error_code,
                    tenant_id, invocation_id,
                ),
            )

    # --- Actions ledger ------------------------------------------------------

    def record_action(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
        invocation_id: UUID,
        action_type: str,
        object_type: str,
        object_ref: str,
        parameters: dict[str, Any],
        receipt: dict[str, Any],
        outcome: str,
        actor_subject: str,
    ) -> None:
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                INSERT INTO tenant_private.axent_actions (
                  action_id, tenant_id, conversation_id, invocation_id,
                  action_type, object_type, object_ref, parameters_hash,
                  receipt_json, outcome, actor_subject
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    uuid4(), tenant_id, conversation_id, invocation_id,
                    action_type, object_type, object_ref,
                    sha256_ref(parameters), Jsonb(receipt), outcome, actor_subject,
                ),
            )

    def list_actions(
        self, *, tenant_id: UUID, conversation_id: UUID | None = None
    ) -> list[dict[str, Any]]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            if conversation_id:
                cursor.execute(
                    """
                    SELECT action_id, action_type, object_type, object_ref,
                           outcome, receipt_json, created_at
                    FROM tenant_private.axent_actions
                    WHERE tenant_id = %s AND conversation_id = %s
                    ORDER BY created_at
                    """,
                    (tenant_id, conversation_id),
                )
            else:
                cursor.execute(
                    """
                    SELECT action_id, action_type, object_type, object_ref,
                           outcome, receipt_json, created_at
                    FROM tenant_private.axent_actions
                    WHERE tenant_id = %s
                    ORDER BY created_at
                    """,
                    (tenant_id,),
                )
            return [dict(row) for row in cursor.fetchall()]

    # --- Confirmations -------------------------------------------------------

    def create_confirmation(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
        invocation_id: UUID,
        action_type: str,
        parameters: dict[str, Any],
        before_state_hash: str,
        ttl_seconds: int = 300,
    ) -> dict[str, Any]:
        confirmation_id = uuid4()
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                INSERT INTO tenant_private.axent_confirmations (
                  confirmation_id, tenant_id, conversation_id, invocation_id,
                  action_type, parameters_hash, before_state_hash,
                  expires_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING confirmation_id, expires_at
                """,
                (
                    confirmation_id, tenant_id, conversation_id, invocation_id,
                    action_type, sha256_ref(parameters), before_state_hash,
                    datetime.now(UTC) + timedelta(seconds=ttl_seconds),
                ),
            )
            row = cursor.fetchone()
            return dict(row) if row else {}

    def resolve_confirmation(
        self,
        *,
        tenant_id: UUID,
        confirmation_id: UUID,
        decision: str,
        confirmed_by: str,
    ) -> dict[str, Any]:
        """CONFIRMED / REJECTED; rejects expired confirmations."""
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                UPDATE tenant_private.axent_confirmations
                SET state = CASE
                      WHEN expires_at < now() THEN 'EXPIRED'
                      ELSE %s::text
                    END,
                    confirmed_at = now(), confirmed_by = %s
                WHERE tenant_id = %s AND confirmation_id = %s
                  AND state = 'PENDING'
                RETURNING confirmation_id, state
                """,
                (decision, confirmed_by, tenant_id, confirmation_id),
            )
            row = cursor.fetchone()
            if row is None:
                raise LookupError("confirmation not found or already resolved")
            return dict(row)

    def list_pending_confirmations(
        self, *, tenant_id: UUID, conversation_id: UUID
    ) -> list[dict[str, Any]]:
        """Pending confirmations for a conversation (newest first)."""
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT c.confirmation_id, c.invocation_id, c.action_type,
                       c.parameters_hash, c.before_state_hash, c.expires_at,
                       i.parameters_json, i.tool_name, i.risk_class
                FROM tenant_private.axent_confirmations c
                JOIN tenant_private.axent_tool_invocations i
                  ON i.invocation_id = c.invocation_id
                WHERE c.tenant_id = %s AND c.conversation_id = %s
                  AND c.state = 'PENDING'
                ORDER BY c.issued_at DESC
                """,
                (tenant_id, conversation_id),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_confirmation(
        self, *, tenant_id: UUID, confirmation_id: UUID
    ) -> dict[str, Any] | None:
        """Fetch a confirmation with its conversation + invocation context."""
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT c.confirmation_id, c.conversation_id, c.invocation_id,
                       c.action_type, c.parameters_hash, c.before_state_hash,
                       c.state, c.expires_at,
                       i.parameters_json, i.tool_name, i.risk_class
                FROM tenant_private.axent_confirmations c
                JOIN tenant_private.axent_tool_invocations i
                  ON i.invocation_id = c.invocation_id
                WHERE c.tenant_id = %s AND c.confirmation_id = %s
                """,
                (tenant_id, confirmation_id),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    # --- Notifications -------------------------------------------------------

    def create_notification(
        self,
        *,
        tenant_id: UUID,
        recipient_subject: str,
        notification_type: str,
        title: str,
        body: str,
        route_path: str | None = None,
        severity: str = "INFO",
    ) -> None:
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                INSERT INTO tenant_private.axent_notifications (
                  notification_id, tenant_id, recipient_subject,
                  notification_type, title, body, route_path, severity
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    uuid4(), tenant_id, recipient_subject, notification_type,
                    title, body, route_path, severity,
                ),
            )

    def list_notifications(
        self, *, tenant_id: UUID, recipient_subject: str
    ) -> list[dict[str, Any]]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT notification_id, notification_type, title, body,
                       route_path, severity, read_at, acknowledged_at, created_at
                FROM tenant_private.axent_notifications
                WHERE tenant_id = %s AND recipient_subject = %s
                ORDER BY created_at DESC
                """,
                (tenant_id, recipient_subject),
            )
            return [dict(row) for row in cursor.fetchall()]

    def acknowledge_notification(
        self, *, tenant_id: UUID, notification_id: UUID
    ) -> None:
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                UPDATE tenant_private.axent_notifications
                SET acknowledged_at = now()
                WHERE tenant_id = %s AND notification_id = %s
                """,
                (tenant_id, notification_id),
            )

    # --- Feedback ------------------------------------------------------------

    def record_feedback(
        self,
        *,
        tenant_id: UUID,
        message_id: UUID,
        rating: int,
        comment: str | None = None,
        category: str | None = None,
    ) -> None:
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                INSERT INTO tenant_private.axent_feedback (
                  feedback_id, tenant_id, message_id, rating, comment, category
                ) VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (uuid4(), tenant_id, message_id, rating, comment, category),
            )

    # --- Evaluations ---------------------------------------------------------

    def record_evaluation(
        self,
        *,
        tenant_id: UUID,
        message_id: UUID,
        grounded: bool,
        grounded_with_uncertainty: bool,
        cross_tenant_ok: bool,
        policy_violation: str | None = None,
        notes: str | None = None,
    ) -> None:
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                INSERT INTO tenant_private.axent_evaluations (
                  evaluation_id, tenant_id, message_id, grounded,
                  grounded_with_uncertainty, cross_tenant_ok,
                  policy_violation, notes
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    uuid4(), tenant_id, message_id, grounded,
                    grounded_with_uncertainty, cross_tenant_ok,
                    policy_violation, notes,
                ),
            )
