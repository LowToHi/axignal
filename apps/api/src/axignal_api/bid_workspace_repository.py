"""PostgreSQL repository for the O01 Bid Workspace (Prioridad 3).

Implements the full operational journey over durable storage:

notice -> lots -> requirements -> criteria -> documents -> amendments ->
questions -> risks -> corporate evidence -> tasks -> owners -> readiness
-> review -> human approval -> handoff -> outcome

with:
- versioned requirements (bid_requirement_versions, append-only);
- OFFICIAL / INFERENCE / RECOMMENDATION distinction;
- amendment invalidation of affected requirements (status AMENDED +
  invalidated_by, kept in history);
- append-only audit enforced by the database (no UPDATE/DELETE grants);
- tenant isolation (forced RLS);
- every mutation is transactional and audited by triggers.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from psycopg.types.json import Jsonb

from axignal_api.opportunity_repository import OpportunityOperationsRepository

REQUIREMENT_KINDS = ("OFFICIAL", "INFERENCE", "RECOMMENDATION")
REQUIREMENT_STATUSES = ("ACTIVE", "AMENDED", "SUPERSEDED", "REJECTED")
QUESTION_STATUSES = ("OPEN", "ANSWERED", "CLOSED")
RISK_STATUSES = ("OPEN", "MITIGATED", "ACCEPTED", "CLOSED")
TASK_STATUSES = ("OPEN", "IN_PROGRESS", "DONE", "BLOCKED", "CANCELLED")
WORKSPACE_OPERATION_STATES = (
    "CREATED", "QUALIFYING", "GO_REVIEW", "NO_GO_REVIEW", "PREPARING",
    "AWAITING_INFORMATION", "READY_FOR_INTERNAL_REVIEW",
    "READY_FOR_SUBSCRIBER_APPROVAL", "APPROVED", "HANDED_OFF", "CLOSED",
)


class BidWorkspaceRepository(OpportunityOperationsRepository):
    # --- Requirements --------------------------------------------------------

    def add_requirement(
        self,
        *,
        tenant_id: UUID,
        workspace_id: UUID,
        requirement_ref: str,
        kind: str,
        title: str,
        description: str = "",
        source_notice_version: int | None = None,
        created_by: str,
    ) -> UUID:
        if kind not in REQUIREMENT_KINDS:
            raise ValueError(f"invalid requirement kind: {kind}")
        requirement_id = uuid4()
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                INSERT INTO tenant_private.bid_requirements (
                  requirement_id, tenant_id, workspace_id, requirement_ref,
                  kind, title, description, source_notice_version, created_by
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    requirement_id, tenant_id, workspace_id, requirement_ref,
                    kind, title, description, source_notice_version, created_by,
                ),
            )
            cursor.execute(
                """
                INSERT INTO tenant_private.bid_requirement_versions (
                  version_id, requirement_id, tenant_id, version, title,
                  description, kind, changed_by
                ) VALUES (%s, %s, %s, 1, %s, %s, %s, %s)
                """,
                (
                    uuid4(), requirement_id, tenant_id, title, description,
                    kind, created_by,
                ),
            )
        return requirement_id

    def update_requirement(
        self,
        *,
        tenant_id: UUID,
        workspace_id: UUID,
        requirement_ref: str,
        title: str,
        description: str = "",
        changed_by: str,
    ) -> None:
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT requirement_id
                FROM tenant_private.bid_requirements
                WHERE tenant_id = %s AND workspace_id = %s AND requirement_ref = %s
                FOR UPDATE
                """,
                (tenant_id, workspace_id, requirement_ref),
            )
            row = cursor.fetchone()
            if row is None:
                raise LookupError("requirement not found")
            requirement_id = row["requirement_id"]
            cursor.execute(
                """
                SELECT COALESCE(MAX(version), 0) + 1 AS next_version
                FROM tenant_private.bid_requirement_versions
                WHERE requirement_id = %s
                """,
                (requirement_id,),
            )
            version = int(cursor.fetchone()["next_version"])
            cursor.execute(
                """
                INSERT INTO tenant_private.bid_requirement_versions (
                  version_id, requirement_id, tenant_id, version, title,
                  description, kind, changed_by
                ) VALUES (%s, %s, %s, %s, %s, %s,
                  (SELECT kind FROM tenant_private.bid_requirements
                   WHERE requirement_id = %s), %s)
                """,
                (
                    uuid4(), requirement_id, tenant_id, version, title,
                    description, requirement_id, changed_by,
                ),
            )
            cursor.execute(
                """
                UPDATE tenant_private.bid_requirements
                SET title = %s, description = %s, updated_at = now()
                WHERE requirement_id = %s
                """,
                (title, description, requirement_id),
            )

    def invalidate_requirement_by_amendment(
        self,
        *,
        tenant_id: UUID,
        workspace_id: UUID,
        requirement_ref: str,
        amendment_ref: str,
        invalidated_by: str,
    ) -> None:
        """Amendment invalidation: requirement becomes AMENDED, kept in history."""
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                UPDATE tenant_private.bid_requirements
                SET status = 'AMENDED', affected_by_amendment = %s,
                    invalidated_by = %s, updated_at = now()
                WHERE tenant_id = %s AND workspace_id = %s AND requirement_ref = %s
                """,
                (amendment_ref, invalidated_by, tenant_id, workspace_id, requirement_ref),
            )

    def list_requirements(
        self, *, tenant_id: UUID, workspace_id: UUID
    ) -> list[dict[str, Any]]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT requirement_id, requirement_ref, kind, title, description,
                       source_notice_version, affected_by_amendment, status,
                       invalidated_by, created_by, created_at, updated_at
                FROM tenant_private.bid_requirements
                WHERE tenant_id = %s AND workspace_id = %s
                ORDER BY created_at
                """,
                (tenant_id, workspace_id),
            )
            return [dict(row) for row in cursor.fetchall()]

    def list_requirement_versions(
        self, *, tenant_id: UUID, requirement_id: UUID
    ) -> list[dict[str, Any]]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT version_id, requirement_id, version, title, description,
                       kind, changed_by, changed_at
                FROM tenant_private.bid_requirement_versions
                WHERE tenant_id = %s AND requirement_id = %s
                ORDER BY version
                """,
                (tenant_id, requirement_id),
            )
            return [dict(row) for row in cursor.fetchall()]

    # --- Questions -----------------------------------------------------------

    def add_question(
        self,
        *,
        tenant_id: UUID,
        workspace_id: UUID,
        question_ref: str,
        question: str,
        asked_by: str,
    ) -> UUID:
        question_id = uuid4()
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                INSERT INTO tenant_private.bid_questions (
                  question_id, tenant_id, workspace_id, question_ref,
                  question, asked_by
                ) VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (question_id, tenant_id, workspace_id, question_ref, question, asked_by),
            )
        return question_id

    def answer_question(
        self,
        *,
        tenant_id: UUID,
        workspace_id: UUID,
        question_ref: str,
        answer: str,
    ) -> None:
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                UPDATE tenant_private.bid_questions
                SET answer = %s, status = 'ANSWERED'
                WHERE tenant_id = %s AND workspace_id = %s AND question_ref = %s
                """,
                (answer, tenant_id, workspace_id, question_ref),
            )

    def list_questions(
        self, *, tenant_id: UUID, workspace_id: UUID
    ) -> list[dict[str, Any]]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT question_id, question_ref, question, answer, status,
                       asked_by, asked_at
                FROM tenant_private.bid_questions
                WHERE tenant_id = %s AND workspace_id = %s
                ORDER BY asked_at
                """,
                (tenant_id, workspace_id),
            )
            return [dict(row) for row in cursor.fetchall()]

    # --- Risks ---------------------------------------------------------------

    def add_risk(
        self,
        *,
        tenant_id: UUID,
        workspace_id: UUID,
        risk_ref: str,
        description: str,
        likelihood: str,
        impact: str,
        mitigation: str = "",
        registered_by: str,
    ) -> UUID:
        if likelihood not in ("LOW", "MEDIUM", "HIGH") or impact not in (
            "LOW", "MEDIUM", "HIGH"
        ):
            raise ValueError("likelihood/impact must be LOW|MEDIUM|HIGH")
        risk_id = uuid4()
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                INSERT INTO tenant_private.bid_risks (
                  risk_id, tenant_id, workspace_id, risk_ref, description,
                  likelihood, impact, mitigation, registered_by
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    risk_id, tenant_id, workspace_id, risk_ref, description,
                    likelihood, impact, mitigation, registered_by,
                ),
            )
        return risk_id

    def list_risks(
        self, *, tenant_id: UUID, workspace_id: UUID
    ) -> list[dict[str, Any]]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT risk_id, risk_ref, description, likelihood, impact,
                       mitigation, status, registered_by, registered_at
                FROM tenant_private.bid_risks
                WHERE tenant_id = %s AND workspace_id = %s
                ORDER BY registered_at
                """,
                (tenant_id, workspace_id),
            )
            return [dict(row) for row in cursor.fetchall()]

    # --- Tasks ---------------------------------------------------------------

    def add_task(
        self,
        *,
        tenant_id: UUID,
        workspace_id: UUID,
        task_ref: str,
        title: str,
        owner: str,
        requirement_ref: str | None = None,
        due_at: Any = None,
        created_by: str,
    ) -> UUID:
        task_id = uuid4()
        requirement_id: UUID | None = None
        if requirement_ref is not None:
            with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
                cursor.execute(
                    """
                    SELECT requirement_id FROM tenant_private.bid_requirements
                    WHERE tenant_id = %s AND workspace_id = %s AND requirement_ref = %s
                    """,
                    (tenant_id, workspace_id, requirement_ref),
                )
                row = cursor.fetchone()
                if row is None:
                    raise LookupError("requirement not found")
                requirement_id = row["requirement_id"]
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                INSERT INTO tenant_private.bid_tasks (
                  task_id, tenant_id, workspace_id, task_ref, requirement_id,
                  title, owner, due_at, created_by
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    task_id, tenant_id, workspace_id, task_ref, requirement_id,
                    title, owner, due_at, created_by,
                ),
            )
        return task_id

    def transition_task(
        self,
        *,
        tenant_id: UUID,
        workspace_id: UUID,
        task_ref: str,
        new_status: str,
    ) -> None:
        if new_status not in TASK_STATUSES:
            raise ValueError(f"invalid task status: {new_status}")
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                UPDATE tenant_private.bid_tasks
                SET status = %s
                WHERE tenant_id = %s AND workspace_id = %s AND task_ref = %s
                """,
                (new_status, tenant_id, workspace_id, task_ref),
            )

    def list_tasks(
        self, *, tenant_id: UUID, workspace_id: UUID
    ) -> list[dict[str, Any]]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT task_id, task_ref, requirement_id, title, owner, due_at,
                       status, created_by, created_at
                FROM tenant_private.bid_tasks
                WHERE tenant_id = %s AND workspace_id = %s
                ORDER BY created_at
                """,
                (tenant_id, workspace_id),
            )
            return [dict(row) for row in cursor.fetchall()]

    # --- Readiness -----------------------------------------------------------

    def set_readiness(
        self,
        *,
        tenant_id: UUID,
        workspace_id: UUID,
        requirement_ref: str,
        satisfied: bool,
        evidence_refs: list[str],
        notes: str = "",
        updated_by: str,
    ) -> None:
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT requirement_id FROM tenant_private.bid_requirements
                WHERE tenant_id = %s AND workspace_id = %s AND requirement_ref = %s
                """,
                (tenant_id, workspace_id, requirement_ref),
            )
            row = cursor.fetchone()
            if row is None:
                raise LookupError("requirement not found")
            cursor.execute(
                """
                INSERT INTO tenant_private.bid_readiness (
                  readiness_id, tenant_id, workspace_id, requirement_id,
                  satisfied, evidence_refs, notes, updated_by
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (tenant_id, workspace_id, requirement_id) DO UPDATE SET
                  satisfied = EXCLUDED.satisfied,
                  evidence_refs = EXCLUDED.evidence_refs,
                  notes = EXCLUDED.notes,
                  updated_by = EXCLUDED.updated_by,
                  updated_at = now()
                """,
                (
                    uuid4(), tenant_id, workspace_id, row["requirement_id"],
                    satisfied, Jsonb(evidence_refs), notes, updated_by,
                ),
            )

    def readiness_summary(
        self, *, tenant_id: UUID, workspace_id: UUID
    ) -> dict[str, Any]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT r.requirement_ref, r.kind, r.status,
                       rd.satisfied, rd.evidence_refs, rd.notes, rd.updated_by
                FROM tenant_private.bid_requirements r
                LEFT JOIN tenant_private.bid_readiness rd
                  ON rd.requirement_id = r.requirement_id
                WHERE r.tenant_id = %s AND r.workspace_id = %s
                ORDER BY r.created_at
                """,
                (tenant_id, workspace_id),
            )
            rows = [dict(row) for row in cursor.fetchall()]
        satisfied = sum(1 for row in rows if row["satisfied"])
        official = sum(1 for row in rows if row["kind"] == "OFFICIAL")
        return {
            "requirements": len(rows),
            "official": official,
            "satisfied": satisfied,
            "satisfied_ratio": round(satisfied / len(rows), 3) if rows else 0.0,
            "ready": bool(rows) and satisfied == official,
            "detail": rows,
        }

    # --- Approval + handoff --------------------------------------------------

    def record_approval(
        self,
        *,
        tenant_id: UUID,
        workspace_id: UUID,
        approval_ref: str,
        decision: str,
        approved_by: str,
        notes: str = "",
    ) -> None:
        if decision not in ("APPROVED", "REJECTED"):
            raise ValueError("approval decision must be APPROVED|REJECTED")
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                INSERT INTO tenant_private.bid_approvals (
                  approval_id, tenant_id, workspace_id, approval_ref,
                  decision, approved_by, notes
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    uuid4(), tenant_id, workspace_id, approval_ref,
                    decision, approved_by, notes,
                ),
            )
            if decision == "APPROVED":
                cursor.execute(
                    """
                    UPDATE tenant_private.opportunity_workspaces
                    SET state = 'APPROVED'
                    WHERE tenant_id = %s AND workspace_id = %s
                    """,
                    (tenant_id, workspace_id),
                )

    def record_handoff(
        self,
        *,
        tenant_id: UUID,
        workspace_id: UUID,
        handoff_ref: str,
        target: str,
        payload: dict[str, Any],
        handed_off_by: str,
    ) -> None:
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                INSERT INTO tenant_private.bid_handoffs (
                  handoff_id, tenant_id, workspace_id, handoff_ref, target,
                  payload, handed_off_by
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    uuid4(), tenant_id, workspace_id, handoff_ref, target,
                    Jsonb(payload), handed_off_by,
                ),
            )
            cursor.execute(
                """
                UPDATE tenant_private.opportunity_workspaces
                SET state = 'HANDED_OFF'
                WHERE tenant_id = %s AND workspace_id = %s
                """,
                (tenant_id, workspace_id),
            )

    # --- Audit ---------------------------------------------------------------

    def audit_log(
        self, *, tenant_id: UUID, workspace_id: UUID, limit: int = 100
    ) -> list[dict[str, Any]]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT audit_id, action, actor, payload, occurred_at
                FROM tenant_private.bid_workspace_audit
                WHERE tenant_id = %s AND workspace_id = %s
                ORDER BY audit_id DESC
                LIMIT %s
                """,
                (tenant_id, workspace_id, limit),
            )
            return [dict(row) for row in cursor.fetchall()]
