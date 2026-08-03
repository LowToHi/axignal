from __future__ import annotations

from hashlib import sha256
from typing import Any
from uuid import UUID, uuid4

from psycopg.types.json import Jsonb

from axignal_api.repository import ResearchRepository


class AxentRepository(ResearchRepository):
    def create_conversation(
        self,
        *,
        tenant_id: UUID,
        opened_by_subject: str,
        language: str,
        workspace_id: UUID | None = None,
        research_run_id: UUID | None = None,
    ) -> dict[str, Any]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                INSERT INTO tenant_private.support_conversations (
                  tenant_id, workspace_id, research_run_id, opened_by_subject, language
                ) VALUES (%s, %s, %s, %s, %s)
                RETURNING *
                """,
                (tenant_id, workspace_id, research_run_id, opened_by_subject, language),
            )
            row = cursor.fetchone()
            assert row is not None
            return row

    def get_conversation(self, *, tenant_id: UUID, conversation_id: UUID) -> dict[str, Any] | None:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT * FROM tenant_private.support_conversations
                WHERE tenant_id = %s AND conversation_id = %s
                """,
                (tenant_id, conversation_id),
            )
            conversation = cursor.fetchone()
            if conversation is None:
                return None
            cursor.execute(
                """
                SELECT * FROM tenant_private.support_messages
                WHERE tenant_id = %s AND conversation_id = %s
                ORDER BY created_at, message_id
                """,
                (tenant_id, conversation_id),
            )
            return {**conversation, "messages": list(cursor.fetchall())}

    def append_message(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
        author_type: str,
        author_subject: str | None,
        content: str,
        model_id: str | None = None,
        prompt_policy_version: str | None = None,
    ) -> dict[str, Any]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT 1 FROM tenant_private.support_conversations
                WHERE tenant_id = %s AND conversation_id = %s FOR UPDATE
                """,
                (tenant_id, conversation_id),
            )
            if cursor.fetchone() is None:
                raise LookupError("support_conversation_not_found")
            cursor.execute(
                """
                INSERT INTO tenant_private.support_messages (
                  tenant_id, conversation_id, author_type, author_subject, content,
                  model_id, prompt_policy_version
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    tenant_id,
                    conversation_id,
                    author_type,
                    author_subject,
                    content,
                    model_id,
                    prompt_policy_version,
                ),
            )
            message = cursor.fetchone()
            assert message is not None
            cursor.execute(
                """
                UPDATE tenant_private.support_conversations
                SET last_message_at = %s, updated_at = %s
                WHERE tenant_id = %s AND conversation_id = %s
                """,
                (message["created_at"], message["created_at"], tenant_id, conversation_id),
            )
            return message

    def add_citation(
        self,
        *,
        tenant_id: UUID,
        message_id: UUID,
        authority_type: str,
        authority_id: str,
        authority_version: str,
        excerpt: str,
    ) -> dict[str, Any]:
        digest = f"sha256:{sha256(excerpt.encode('utf-8')).hexdigest()}"
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                INSERT INTO tenant_private.support_message_citations (
                  tenant_id, message_id, authority_type, authority_id,
                  authority_version, excerpt_hash
                ) VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (tenant_id, message_id, authority_type, authority_id, authority_version, digest),
            )
            row = cursor.fetchone()
            assert row is not None
            return row

    def create_case(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
        case_type: str,
        severity: str,
        service_area: str,
        customer_impact: str | None,
    ) -> dict[str, Any]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                INSERT INTO tenant_private.support_cases (
                  tenant_id, conversation_id, case_type, severity,
                  service_area, customer_impact
                ) VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (tenant_id, conversation_id, case_type, severity, service_area, customer_impact),
            )
            case = cursor.fetchone()
            assert case is not None
            cursor.execute(
                """
                UPDATE tenant_private.support_conversations
                SET status = 'ESCALATED', updated_at = now()
                WHERE tenant_id = %s AND conversation_id = %s
                """,
                (tenant_id, conversation_id),
            )
            return case

    def record_tool_invocation(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
        tool_name: str,
        requested_by_subject: str,
        input_payload: dict[str, Any],
        decision: str,
        reasons: tuple[str, ...],
        result_status: str,
        result: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> dict[str, Any]:
        input_hash = f"sha256:{sha256(repr(sorted(input_payload.items())).encode('utf-8')).hexdigest()}"
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                INSERT INTO tenant_private.support_tool_invocations (
                  tenant_id, conversation_id, tool_name, tool_version,
                  requested_by_subject, input_redacted, input_hash, decision,
                  decision_reason, result_status, result_redacted,
                  idempotency_key, correlation_id, finished_at
                ) VALUES (%s, %s, %s, 'v1', %s, %s, %s, %s, %s, %s, %s, %s, %s, now())
                ON CONFLICT (tenant_id, tool_name, idempotency_key)
                DO UPDATE SET idempotency_key = EXCLUDED.idempotency_key
                RETURNING *
                """,
                (
                    tenant_id,
                    conversation_id,
                    tool_name,
                    requested_by_subject,
                    Jsonb(input_payload),
                    input_hash,
                    decision,
                    Jsonb(list(reasons)),
                    result_status,
                    Jsonb(result),
                    idempotency_key,
                    correlation_id,
                ),
            )
            row = cursor.fetchone()
            assert row is not None
            return row
