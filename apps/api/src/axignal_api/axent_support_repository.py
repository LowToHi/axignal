"""AXENT customer support repository (Mandato AXENT — secciones 12-13).

Cases, case events, incident deduplication (fingerprint), case-to-
incident linkage, notifications, feedback, and governed knowledge
(candidates -> approval -> versioned revisions). Tenant-scoped via
forced RLS.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any
from uuid import UUID, uuid4

from psycopg.types.json import Jsonb

from axignal_api.repository import ResearchRepository


def sha256_ref(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, separators=(",", ":"), sort_keys=True, default=str
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


SEVERITIES = ("S0", "S1", "S2", "S3", "S4")
CASE_STATUSES = (
    "OPEN", "INVESTIGATING", "AWAITING_CUSTOMER", "AWAITING_SYSTEM",
    "ESCALATED", "RESOLVED", "CLOSED", "REOPENED",
)


class AxentSupportRepository(ResearchRepository):
    # --- Cases ---------------------------------------------------------------

    def create_case(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
        subject: str,
        description: str,
        severity: str = "S3",
        opened_by: str,
    ) -> dict[str, Any]:
        if severity not in SEVERITIES:
            raise ValueError(f"invalid severity {severity!r}")
        case_id = uuid4()
        case_ref = "case_" + uuid4().hex[:10]
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                INSERT INTO tenant_private.support_cases (
                  case_id, tenant_id, conversation_id, case_ref, subject,
                  description, severity, assigned_to
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (case_id, tenant_id, conversation_id, case_ref, subject,
                 description, severity, opened_by),
            )
            cursor.execute(
                """
                INSERT INTO tenant_private.support_case_events (
                  event_id, tenant_id, case_id, event_type, actor_subject
                ) VALUES (%s, %s, %s, 'OPENED', %s)
                """,
                (uuid4(), tenant_id, case_id, opened_by),
            )
        return {"case_id": case_id, "case_ref": case_ref, "severity": severity}

    def transition_case(
        self,
        *,
        tenant_id: UUID,
        case_ref: str,
        new_status: str,
        actor_subject: str,
        resolution_code: str | None = None,
    ) -> dict[str, Any]:
        if new_status not in CASE_STATUSES:
            raise ValueError(f"invalid case status {new_status!r}")
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                UPDATE tenant_private.support_cases
                SET status = %s, updated_at = now(),
                    resolution_code = COALESCE(%s, resolution_code),
                    resolved_at = CASE WHEN %s IN ('RESOLVED', 'CLOSED')
                                 THEN now() ELSE resolved_at END
                WHERE tenant_id = %s AND case_ref = %s
                RETURNING case_id, case_ref, status
                """,
                (new_status, resolution_code, new_status, tenant_id, case_ref),
            )
            row = cursor.fetchone()
            if row is None:
                raise LookupError(f"case {case_ref!r} not found")
            cursor.execute(
                """
                INSERT INTO tenant_private.support_case_events (
                  event_id, tenant_id, case_id, event_type, actor_subject,
                  payload
                ) VALUES (%s, %s, %s, 'STATUS_CHANGED', %s, %s)
                """,
                (uuid4(), tenant_id, row["case_id"], actor_subject,
                 Jsonb({"new_status": new_status})),
            )
            return dict(row)

    def list_cases(
        self, *, tenant_id: UUID, status: str | None = None
    ) -> list[dict[str, Any]]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            if status:
                cursor.execute(
                    """
                    SELECT case_id, case_ref, subject, description, status,
                           severity, priority, assigned_to, created_at, updated_at
                    FROM tenant_private.support_cases
                    WHERE tenant_id = %s AND status = %s
                    ORDER BY created_at DESC
                    """,
                    (tenant_id, status),
                )
            else:
                cursor.execute(
                    """
                    SELECT case_id, case_ref, subject, description, status,
                           severity, priority, assigned_to, created_at, updated_at
                    FROM tenant_private.support_cases
                    WHERE tenant_id = %s
                    ORDER BY created_at DESC
                    """,
                    (tenant_id,),
                )
            return [dict(row) for row in cursor.fetchall()]

    def case_events(
        self, *, tenant_id: UUID, case_ref: str
    ) -> list[dict[str, Any]]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT e.event_id, e.event_type, e.actor_subject, e.payload,
                       e.created_at
                FROM tenant_private.support_case_events e
                JOIN tenant_private.support_cases c
                  ON c.tenant_id = e.tenant_id AND c.case_id = e.case_id
                WHERE e.tenant_id = %s AND c.case_ref = %s
                ORDER BY e.created_at
                """,
                (tenant_id, case_ref),
            )
            return [dict(row) for row in cursor.fetchall()]

    # --- Incidents + deduplication -------------------------------------------

    def upsert_incident(
        self,
        *,
        tenant_id: UUID,
        fingerprint: str,
        severity: str = "S3",
        summary: str = "",
    ) -> dict[str, Any]:
        """Deduplicate: same fingerprint -> same incident, returns it."""
        incident_ref = "inc_" + uuid4().hex[:8]
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                INSERT INTO tenant_private.support_incidents (
                  incident_id, tenant_id, incident_ref, fingerprint,
                  severity, summary
                ) VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (tenant_id, fingerprint) DO UPDATE SET
                  updated_at = now()
                RETURNING incident_id, incident_ref, fingerprint, severity,
                          status
                """,
                (uuid4(), tenant_id, incident_ref, fingerprint, severity, summary),
            )
            row = cursor.fetchone()
            return dict(row) if row else {}

    def link_case_to_incident(
        self, *, tenant_id: UUID, case_ref: str, incident_id: UUID
    ) -> None:
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                INSERT INTO tenant_private.support_incident_links (
                  link_id, tenant_id, case_id, incident_id
                )
                SELECT %s, c.tenant_id, c.case_id, %s
                FROM tenant_private.support_cases c
                WHERE c.tenant_id = %s AND c.case_ref = %s
                ON CONFLICT (tenant_id, case_id, incident_id) DO NOTHING
                """,
                (uuid4(), incident_id, tenant_id, case_ref),
            )

    def list_incidents(
        self, *, tenant_id: UUID
    ) -> list[dict[str, Any]]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT incident_id, incident_ref, fingerprint, severity,
                       status, summary, created_at, updated_at
                FROM tenant_private.support_incidents
                WHERE tenant_id = %s
                ORDER BY created_at DESC
                """,
                (tenant_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    # --- Notifications -------------------------------------------------------

    def notify_case_update(
        self,
        *,
        tenant_id: UUID,
        case_ref: str,
        recipient_subject: str,
        notification_type: str,
        body: str,
    ) -> None:
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                INSERT INTO tenant_private.support_notifications (
                  notification_id, tenant_id, case_id, recipient_subject,
                  notification_type, body
                )
                SELECT %s, c.tenant_id, c.case_id, %s, %s, %s
                FROM tenant_private.support_cases c
                WHERE c.tenant_id = %s AND c.case_ref = %s
                """,
                (uuid4(), recipient_subject, notification_type, body,
                 tenant_id, case_ref),
            )

    # --- Feedback ------------------------------------------------------------

    def record_case_feedback(
        self,
        *,
        tenant_id: UUID,
        case_ref: str,
        rating: int,
        comment: str | None = None,
    ) -> None:
        if not 1 <= rating <= 5:
            raise ValueError("rating must be 1..5")
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                INSERT INTO tenant_private.support_feedback (
                  feedback_id, tenant_id, case_id, rating, comment
                )
                SELECT %s, c.tenant_id, c.case_id, %s, %s
                FROM tenant_private.support_cases c
                WHERE c.tenant_id = %s AND c.case_ref = %s
                """,
                (uuid4(), rating, comment, tenant_id, case_ref),
            )

    # --- Governed knowledge --------------------------------------------------

    def create_knowledge_candidate(
        self,
        *,
        title: str,
        content: str,
        source_authority: str,
        owner_subject: str,
        language: str = "es",
    ) -> dict[str, Any]:
        """A resolution can create a candidate; NEVER active automatically."""
        document_id = uuid4()
        revision_id = uuid4()
        with self._cursor(role="axignal_worker") as cursor:
            cursor.execute(
                """
                INSERT INTO axignal_global.knowledge_documents (
                  knowledge_document_id, title, source_authority, language
                ) VALUES (%s, %s, %s, %s)
                """,
                (document_id, title, source_authority, language),
            )
            cursor.execute(
                """
                INSERT INTO axignal_global.knowledge_revisions (
                  revision_id, document_id, version, content, content_hash,
                  status, owner_subject
                ) VALUES (%s, %s, 1, %s, %s, 'CANDIDATE', %s)
                """,
                (
                    revision_id, document_id, content,
                    sha256_ref({"content": content}), owner_subject,
                ),
            )
            cursor.execute(
                """
                INSERT INTO axignal_global.knowledge_chunks (
                  chunk_id, revision_id, section_path, content, search_vector
                ) VALUES (%s, %s, 'root', %s,
                          to_tsvector('simple', %s))
                """,
                (uuid4(), revision_id, content, content),
            )
        return {"document_id": document_id, "revision_id": revision_id,
                "status": "CANDIDATE"}

    def approve_knowledge_revision(
        self, *, revision_id: UUID, reviewed_by: str
    ) -> dict[str, Any]:
        """Human approval activates a revision (effective immediately)."""
        with self._cursor(role="axignal_worker") as cursor:
            cursor.execute(
                """
                UPDATE axignal_global.knowledge_revisions
                SET status = 'APPROVED', reviewed_by = %s,
                    effective_at = now()
                WHERE revision_id = %s AND status = 'CANDIDATE'
                RETURNING revision_id, version, status, effective_at
                """,
                (reviewed_by, revision_id),
            )
            row = cursor.fetchone()
            if row is None:
                raise LookupError("revision not found or not a candidate")
            return dict(row)

    def search_knowledge(
        self, *, query: str, limit: int = 5
    ) -> list[dict[str, Any]]:
        """Retrieval eligibility: APPROVED revisions only."""
        with self._cursor(role="axignal_app") as cursor:
            cursor.execute(
                """
                SELECT kc.chunk_id, kc.section_path, kc.content,
                       kr.revision_id, kr.version, kd.title,
                       kd.source_authority, kd.language
                FROM axignal_global.knowledge_chunks kc
                JOIN axignal_global.knowledge_revisions kr
                  ON kr.revision_id = kc.revision_id AND kr.status = 'APPROVED'
                JOIN axignal_global.knowledge_documents kd
                  ON kd.knowledge_document_id = kr.document_id
                WHERE kc.search_vector @@ plainto_tsquery('simple', %s)
                ORDER BY kc.created_at DESC
                LIMIT %s
                """,
                (query, limit),
            )
            return [dict(row) for row in cursor.fetchall()]
