from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from psycopg.types.json import Jsonb

from axignal_api.axent_consent import canonical_hash
from axignal_api.axent_repository import AxentRepository


class AxentActionRepository(AxentRepository):
    def archive_workspace(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
        workspace_id: UUID,
        subject: str,
        confirmation_id: UUID,
        confirmation_token_hash: str,
        expected_before_state_hash: str,
        parameters: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> dict[str, Any]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT *
                FROM tenant_private.support_tool_invocations
                WHERE tenant_id = %s
                  AND tool_name = 'archive_workspace'
                  AND idempotency_key = %s
                """,
                (tenant_id, idempotency_key),
            )
            existing = cursor.fetchone()
            if existing is not None:
                return {"invocation": existing, "replayed": True}

            cursor.execute(
                """
                SELECT workspace_id, tenant_id, state, revision, owner_subject,
                       research_run_id, updated_at
                FROM tenant_private.subscriber_workspaces
                WHERE tenant_id = %s AND workspace_id = %s
                FOR UPDATE
                """,
                (tenant_id, workspace_id),
            )
            workspace = cursor.fetchone()
            if workspace is None:
                raise LookupError("workspace_not_found")
            before_state = {
                "workspace_id": str(workspace["workspace_id"]),
                "state": workspace["state"],
                "revision": workspace["revision"],
                "owner_subject": workspace["owner_subject"],
                "research_run_id": str(workspace["research_run_id"]),
                "updated_at": workspace["updated_at"],
            }
            actual_before_hash = canonical_hash(before_state)
            if actual_before_hash != expected_before_state_hash:
                raise ValueError("confirmation_state_stale")
            if workspace["state"] != "ACTIVE":
                raise ValueError("workspace_not_active")

            invocation_id = uuid4()
            input_hash = canonical_hash(parameters)
            cursor.execute(
                """
                INSERT INTO tenant_private.support_tool_invocations (
                  invocation_id, tenant_id, conversation_id, tool_name,
                  tool_version, requested_by_subject, input_redacted,
                  input_hash, decision, decision_reason, result_status,
                  result_redacted, idempotency_key, correlation_id
                ) VALUES (
                  %s, %s, %s, 'archive_workspace', 'v1', %s, %s, %s,
                  'ALLOW', '["confirmation_and_authority_current"]'::jsonb,
                  'PENDING', '{}'::jsonb, %s, %s
                )
                """,
                (
                    invocation_id,
                    tenant_id,
                    conversation_id,
                    subject,
                    Jsonb(parameters),
                    input_hash,
                    idempotency_key,
                    correlation_id,
                ),
            )
            cursor.execute(
                """
                UPDATE tenant_private.support_confirmations
                SET consumed_at = now(), consumed_by_invocation_id = %s
                WHERE tenant_id = %s
                  AND confirmation_id = %s
                  AND token_hash = %s
                  AND requested_by_subject = %s
                  AND action_type = 'archive_workspace'
                  AND before_state_hash = %s
                  AND consumed_at IS NULL
                  AND expires_at > now()
                RETURNING confirmation_id
                """,
                (
                    invocation_id,
                    tenant_id,
                    confirmation_id,
                    confirmation_token_hash,
                    subject,
                    expected_before_state_hash,
                ),
            )
            if cursor.fetchone() is None:
                raise ValueError("confirmation_missing_expired_or_replayed")

            cursor.execute(
                """
                UPDATE tenant_private.subscriber_workspaces
                SET state = 'CLOSED', revision = revision + 1, updated_at = now()
                WHERE tenant_id = %s AND workspace_id = %s AND state = 'ACTIVE'
                RETURNING workspace_id, state, revision, updated_at
                """,
                (tenant_id, workspace_id),
            )
            after = cursor.fetchone()
            if after is None:
                raise ValueError("workspace_archive_conflict")
            after_state_hash = canonical_hash(after)
            cursor.execute(
                """
                INSERT INTO tenant_private.support_actions (
                  tenant_id, conversation_id, invocation_id, action_type,
                  target_type, target_id, before_state_hash, after_state_hash,
                  approval_mode, approved_by, rollback_status
                ) VALUES (
                  %s, %s, %s, 'archive_workspace', 'WORKSPACE', %s, %s, %s,
                  'STEP_UP_AUTH', %s, 'AVAILABLE'
                )
                RETURNING *
                """,
                (
                    tenant_id,
                    conversation_id,
                    invocation_id,
                    str(workspace_id),
                    actual_before_hash,
                    after_state_hash,
                    subject,
                ),
            )
            action = cursor.fetchone()
            assert action is not None
            result = {
                "workspace_id": str(workspace_id),
                "state": after["state"],
                "revision": after["revision"],
                "after_state_hash": after_state_hash,
            }
            cursor.execute(
                """
                UPDATE tenant_private.support_tool_invocations
                SET result_status = 'SUCCEEDED', result_redacted = %s,
                    finished_at = now()
                WHERE tenant_id = %s AND invocation_id = %s
                RETURNING *
                """,
                (Jsonb(result), tenant_id, invocation_id),
            )
            invocation = cursor.fetchone()
            assert invocation is not None
            return {
                "invocation": invocation,
                "action": action,
                "result": result,
                "replayed": False,
            }
