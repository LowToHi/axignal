from __future__ import annotations

from datetime import datetime
from hashlib import sha256
from typing import Any
from uuid import UUID

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
                  tenant_id, workspace_id, research_run_id,
                  opened_by_subject, language
                ) VALUES (%s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    tenant_id,
                    workspace_id,
                    research_run_id,
                    opened_by_subject,
                    language,
                ),
            )
            row = cursor.fetchone()
            assert row is not None
            return row

    def get_conversation(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
    ) -> dict[str, Any] | None:
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

    def rename_conversation(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
        intent: str,
    ) -> dict[str, Any]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                UPDATE tenant_private.support_conversations
                SET intent = %s, updated_at = now()
                WHERE tenant_id = %s AND conversation_id = %s
                RETURNING *
                """,
                (intent, tenant_id, conversation_id),
            )
            row = cursor.fetchone()
            if row is None:
                raise LookupError("support_conversation_not_found")
            return row

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
                  tenant_id, conversation_id, author_type, author_subject,
                  content, model_id, prompt_policy_version
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
                (
                    message["created_at"],
                    message["created_at"],
                    tenant_id,
                    conversation_id,
                ),
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
                (
                    tenant_id,
                    message_id,
                    authority_type,
                    authority_id,
                    authority_version,
                    digest,
                ),
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
                (
                    tenant_id,
                    conversation_id,
                    case_type,
                    severity,
                    service_area,
                    customer_impact,
                ),
            )
            case = cursor.fetchone()
            assert case is not None
            cursor.execute(
                """
                INSERT INTO tenant_private.support_case_events (
                  tenant_id, case_id, event_type, actor_type, payload_redacted
                ) VALUES (%s, %s, 'OPENED', 'AXENT', %s)
                """,
                (
                    tenant_id,
                    case["case_id"],
                    Jsonb({"case_type": case_type, "severity": severity}),
                ),
            )
            cursor.execute(
                """
                UPDATE tenant_private.support_conversations
                SET status = 'ESCALATED', updated_at = now()
                WHERE tenant_id = %s AND conversation_id = %s
                """,
                (tenant_id, conversation_id),
            )
            return case

    def list_open_cases(self, *, tenant_id: UUID) -> list[dict[str, Any]]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT c.*, v.opened_by_subject
                FROM tenant_private.support_cases AS c
                JOIN tenant_private.support_conversations AS v
                  ON v.tenant_id = c.tenant_id
                 AND v.conversation_id = c.conversation_id
                WHERE c.tenant_id = %s
                  AND c.status NOT IN ('RESOLVED', 'CLOSED')
                ORDER BY c.severity, c.opened_at
                """,
                (tenant_id,),
            )
            return list(cursor.fetchall())

    def transition_case(
        self,
        *,
        tenant_id: UUID,
        case_id: UUID,
        actor_subject: str,
        transition: str,
        resolution: str | None = None,
    ) -> dict[str, Any]:
        transitions = {
            "ACKNOWLEDGE": ("ACKNOWLEDGED", "ACKNOWLEDGED"),
            "ASSIGN": ("INVESTIGATING", "ASSIGNED"),
            "RESOLVE": ("RESOLVED", "RESOLVED"),
            "REOPEN": ("OPEN", "REOPENED"),
            "CLOSE": ("CLOSED", "CLOSED"),
        }
        if transition not in transitions:
            raise ValueError("support_case_transition_invalid")
        next_status, event_type = transitions[transition]
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT * FROM tenant_private.support_cases
                WHERE tenant_id = %s AND case_id = %s FOR UPDATE
                """,
                (tenant_id, case_id),
            )
            current = cursor.fetchone()
            if current is None:
                raise LookupError("support_case_not_found")
            if transition == "REOPEN" and current["status"] not in {"RESOLVED", "CLOSED"}:
                raise ValueError("support_case_not_resolved")
            if transition == "RESOLVE" and not resolution:
                raise ValueError("support_case_resolution_required")
            cursor.execute(
                """
                UPDATE tenant_private.support_cases
                SET status = %s,
                    owner_type = CASE WHEN %s = 'ASSIGN' THEN 'HUMAN' ELSE owner_type END,
                    owner_subject = CASE WHEN %s = 'ASSIGN' THEN %s ELSE owner_subject END,
                    acknowledged_at = CASE WHEN %s = 'ACKNOWLEDGE' THEN now() ELSE acknowledged_at END,
                    resolution = CASE WHEN %s = 'RESOLVE' THEN %s ELSE resolution END,
                    resolved_at = CASE WHEN %s = 'RESOLVE' THEN now() WHEN %s = 'REOPEN' THEN NULL ELSE resolved_at END,
                    closed_at = CASE WHEN %s = 'CLOSE' THEN now() WHEN %s = 'REOPEN' THEN NULL ELSE closed_at END
                WHERE tenant_id = %s AND case_id = %s
                RETURNING *
                """,
                (
                    next_status,
                    transition,
                    transition,
                    actor_subject,
                    transition,
                    transition,
                    resolution,
                    transition,
                    transition,
                    transition,
                    transition,
                    tenant_id,
                    case_id,
                ),
            )
            updated = cursor.fetchone()
            assert updated is not None
            cursor.execute(
                """
                INSERT INTO tenant_private.support_case_events (
                  tenant_id, case_id, event_type, actor_type,
                  actor_subject, payload_redacted
                ) VALUES (%s, %s, %s, 'HUMAN_AGENT', %s, %s)
                """,
                (
                    tenant_id,
                    case_id,
                    event_type,
                    actor_subject,
                    Jsonb({"resolution": resolution} if resolution else {}),
                ),
            )
            if transition in {"RESOLVE", "REOPEN"}:
                notification_type = (
                    "CASE_RESOLVED" if transition == "RESOLVE" else "CASE_REOPENED"
                )
                cursor.execute(
                    """
                    INSERT INTO tenant_private.support_notifications (
                      tenant_id, case_id, conversation_id, recipient_subject,
                      notification_type, payload_redacted
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING notification_id
                    """,
                    (
                        tenant_id,
                        case_id,
                        current["conversation_id"],
                        self._conversation_owner(cursor, tenant_id, current["conversation_id"]),
                        notification_type,
                        Jsonb({"resolution": resolution} if resolution else {}),
                    ),
                )
                if transition == "RESOLVE":
                    cursor.execute(
                        """
                        UPDATE tenant_private.support_conversations
                        SET status = 'RESOLVED', resolved_at = now(), updated_at = now(),
                            resolution_code = 'HUMAN_RESOLVED'
                        WHERE tenant_id = %s AND conversation_id = %s
                        """,
                        (tenant_id, current["conversation_id"]),
                    )
                else:
                    cursor.execute(
                        """
                        UPDATE tenant_private.support_conversations
                        SET status = 'ESCALATED', resolved_at = NULL,
                            resolution_code = NULL, updated_at = now()
                        WHERE tenant_id = %s AND conversation_id = %s
                        """,
                        (tenant_id, current["conversation_id"]),
                    )
            return updated

    @staticmethod
    def _conversation_owner(cursor, tenant_id: UUID, conversation_id: UUID) -> str:
        cursor.execute(
            """
            SELECT opened_by_subject
            FROM tenant_private.support_conversations
            WHERE tenant_id = %s AND conversation_id = %s
            """,
            (tenant_id, conversation_id),
        )
        row = cursor.fetchone()
        assert row is not None
        return str(row["opened_by_subject"])

    def create_confirmation(
        self,
        *,
        confirmation_id: UUID,
        tenant_id: UUID,
        conversation_id: UUID,
        requested_by_subject: str,
        action_type: str,
        parameters_hash: str,
        before_state_hash: str,
        token_hash: str,
        assurance_level: str,
        expires_at: datetime,
    ) -> dict[str, Any]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                INSERT INTO tenant_private.support_confirmations (
                  confirmation_id, tenant_id, conversation_id,
                  requested_by_subject, action_type, parameters_hash,
                  before_state_hash, token_hash, assurance_level, expires_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    confirmation_id,
                    tenant_id,
                    conversation_id,
                    requested_by_subject,
                    action_type,
                    parameters_hash,
                    before_state_hash,
                    token_hash,
                    assurance_level,
                    expires_at,
                ),
            )
            row = cursor.fetchone()
            assert row is not None
            return row

    def consume_confirmation(
        self,
        *,
        tenant_id: UUID,
        confirmation_id: UUID,
        token_hash: str,
        invocation_id: UUID,
    ) -> dict[str, Any]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                UPDATE tenant_private.support_confirmations
                SET consumed_at = now(), consumed_by_invocation_id = %s
                WHERE tenant_id = %s
                  AND confirmation_id = %s
                  AND token_hash = %s
                  AND consumed_at IS NULL
                  AND expires_at > now()
                RETURNING *
                """,
                (invocation_id, tenant_id, confirmation_id, token_hash),
            )
            row = cursor.fetchone()
            if row is None:
                raise ValueError("confirmation_missing_expired_or_replayed")
            return row

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
        serialized_input = repr(sorted(input_payload.items())).encode("utf-8")
        input_hash = f"sha256:{sha256(serialized_input).hexdigest()}"
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                INSERT INTO tenant_private.support_tool_invocations (
                  tenant_id, conversation_id, tool_name, tool_version,
                  requested_by_subject, input_redacted, input_hash, decision,
                  decision_reason, result_status, result_redacted,
                  idempotency_key, correlation_id, finished_at
                ) VALUES (
                  %s, %s, %s, 'v1', %s, %s, %s, %s,
                  %s, %s, %s, %s, %s, now()
                )
                ON CONFLICT (tenant_id, tool_name, idempotency_key)
                DO NOTHING
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
            if row is not None:
                return row
            cursor.execute(
                """
                SELECT *
                FROM tenant_private.support_tool_invocations
                WHERE tenant_id = %s
                  AND tool_name = %s
                  AND idempotency_key = %s
                """,
                (tenant_id, tool_name, idempotency_key),
            )
            existing = cursor.fetchone()
            assert existing is not None
            return existing
