from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from psycopg.types.json import Jsonb

from axignal_api.axent_repository import AxentRepository


class AxentTelemetryRepository(AxentRepository):
    def create_feedback(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
        submitted_by_subject: str,
        rating: int,
        resolution_helpful: bool | None,
        comment_redacted: str | None,
        message_id: UUID | None,
    ) -> dict[str, Any]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT 1
                FROM tenant_private.support_conversations
                WHERE tenant_id = %s AND conversation_id = %s
                """,
                (tenant_id, conversation_id),
            )
            if cursor.fetchone() is None:
                raise LookupError("support_conversation_not_found")
            cursor.execute(
                """
                INSERT INTO tenant_private.support_feedback (
                  tenant_id, conversation_id, message_id,
                  submitted_by_subject, rating, resolution_helpful,
                  comment_redacted
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    tenant_id,
                    conversation_id,
                    message_id,
                    submitted_by_subject,
                    rating,
                    resolution_helpful,
                    comment_redacted,
                ),
            )
            row = cursor.fetchone()
            assert row is not None
            return row

    def create_evaluation(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
        evaluator_type: str,
        evaluator_subject: str | None,
        policy_version: str,
        grounded: bool,
        citation_valid: bool,
        correct_resolution: bool | None,
        escalation_correct: bool | None,
        security_violation: bool,
        score: Decimal | None,
        evidence_redacted: dict[str, Any],
    ) -> dict[str, Any]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                INSERT INTO tenant_private.support_evaluations (
                  tenant_id, conversation_id, evaluator_type,
                  evaluator_subject, policy_version, grounded,
                  citation_valid, correct_resolution, escalation_correct,
                  security_violation, score, evidence_redacted
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    tenant_id,
                    conversation_id,
                    evaluator_type,
                    evaluator_subject,
                    policy_version,
                    grounded,
                    citation_valid,
                    correct_resolution,
                    escalation_correct,
                    security_violation,
                    score,
                    Jsonb(evidence_redacted),
                ),
            )
            row = cursor.fetchone()
            assert row is not None
            return row

    def metrics(self, *, tenant_id: UUID) -> dict[str, Any]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT *
                FROM tenant_private.axent_support_metrics
                WHERE tenant_id = %s
                """,
                (tenant_id,),
            )
            summary = cursor.fetchone() or {
                "tenant_id": tenant_id,
                "conversations_total": 0,
                "conversations_resolved": 0,
                "conversations_escalated": 0,
                "median_resolution_seconds": None,
            }
            cursor.execute(
                """
                SELECT
                  count(*) AS feedback_total,
                  avg(rating)::numeric(5,2) AS average_rating,
                  count(*) FILTER (WHERE resolution_helpful IS TRUE)
                    AS helpful_total
                FROM tenant_private.support_feedback
                WHERE tenant_id = %s
                """,
                (tenant_id,),
            )
            feedback = cursor.fetchone()
            assert feedback is not None
            cursor.execute(
                """
                SELECT
                  count(*) AS evaluations_total,
                  count(*) FILTER (WHERE grounded) AS grounded_total,
                  count(*) FILTER (WHERE citation_valid) AS citation_valid_total,
                  count(*) FILTER (WHERE security_violation)
                    AS security_violation_total,
                  avg(score)::numeric(5,4) AS average_score
                FROM tenant_private.support_evaluations
                WHERE tenant_id = %s
                """,
                (tenant_id,),
            )
            evaluations = cursor.fetchone()
            assert evaluations is not None
            return {
                "summary": summary,
                "feedback": feedback,
                "evaluations": evaluations,
            }
