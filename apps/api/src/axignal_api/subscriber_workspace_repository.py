from __future__ import annotations

from hashlib import sha256
from typing import Any
from uuid import UUID, uuid4

from psycopg.types.json import Jsonb

from axignal_api.repository import ResearchRepository


class SubscriberWorkspaceRepository(ResearchRepository):
    """Tenant-scoped persistence for the visible no-fixture subscriber path."""

    def list_run_views(self, *, tenant_id: UUID, limit: int = 20) -> list[dict[str, Any]]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT research_run_id
                FROM tenant_private.research_runs
                WHERE tenant_id = %s
                ORDER BY created_at DESC, research_run_id DESC
                LIMIT %s
                """,
                (tenant_id, limit),
            )
            run_ids = [row["research_run_id"] for row in cursor.fetchall()]
        return [
            view
            for run_id in run_ids
            if (view := self.get_run_view(tenant_id=tenant_id, run_id=run_id)) is not None
        ]

    def bootstrap(self, *, tenant_id: UUID) -> dict[str, Any]:
        runs = self.list_run_views(tenant_id=tenant_id)
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT *
                FROM tenant_private.subscriber_workspaces
                WHERE tenant_id = %s
                ORDER BY updated_at DESC, workspace_id DESC
                """,
                (tenant_id,),
            )
            workspaces = list(cursor.fetchall())
            cursor.execute(
                """
                SELECT *
                FROM tenant_private.subscriber_workspace_documents
                WHERE tenant_id = %s
                ORDER BY updated_at DESC, document_id DESC
                """,
                (tenant_id,),
            )
            documents = list(cursor.fetchall())
            cursor.execute(
                """
                SELECT export_id, tenant_id, workspace_id, document_id, format,
                       filename, content_hash, created_by, created_at
                FROM tenant_private.subscriber_workspace_exports
                WHERE tenant_id = %s
                ORDER BY created_at DESC, export_id DESC
                """,
                (tenant_id,),
            )
            exports = list(cursor.fetchall())
            cursor.execute(
                """
                SELECT *
                FROM tenant_private.subscriber_workspace_audit_events
                WHERE tenant_id = %s
                ORDER BY occurred_at DESC, audit_event_id DESC
                LIMIT 100
                """,
                (tenant_id,),
            )
            audit = list(cursor.fetchall())
        return {
            "research_runs": runs,
            "workspaces": workspaces,
            "documents": documents,
            "exports": exports,
            "audit": audit,
        }

    def ensure_workspace(
        self,
        *,
        tenant_id: UUID,
        research_run_id: UUID,
        actor_subject: str,
    ) -> dict[str, Any]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT research_run_id, opportunity_id, question, state, dossier_id
                FROM tenant_private.research_runs
                WHERE tenant_id = %s AND research_run_id = %s
                FOR SHARE
                """,
                (tenant_id, research_run_id),
            )
            run = cursor.fetchone()
            if run is None:
                raise LookupError("research_run_not_found")
            if run["state"] not in ("COMPLETED", "COMPLETED_PROVISIONAL"):
                raise ValueError("research_run_not_completed")
            if run["dossier_id"] is None:
                raise ValueError("persistent_dossier_required")

            cursor.execute(
                """
                INSERT INTO tenant_private.subscriber_workspaces (
                  tenant_id, research_run_id, opportunity_id, title, owner_subject
                ) VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (tenant_id, research_run_id) DO UPDATE
                SET updated_at = now(), revision = tenant_private.subscriber_workspaces.revision + 1
                RETURNING *
                """,
                (
                    tenant_id,
                    research_run_id,
                    run["opportunity_id"],
                    str(run["question"])[:300],
                    actor_subject,
                ),
            )
            workspace = cursor.fetchone()
            assert workspace is not None
            self._append_audit(
                cursor=cursor,
                tenant_id=tenant_id,
                workspace_id=workspace["workspace_id"],
                actor_subject=actor_subject,
                event_type="WORKSPACE_CREATED",
                object_type="workspace",
                object_id=workspace["workspace_id"],
                details={"research_run_id": str(research_run_id)},
            )
            return workspace

    def create_document(
        self,
        *,
        tenant_id: UUID,
        workspace_id: UUID,
        title: str,
        body: str,
        actor_subject: str,
    ) -> dict[str, Any]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            workspace = self._workspace_for_update(
                cursor=cursor,
                tenant_id=tenant_id,
                workspace_id=workspace_id,
            )
            cursor.execute(
                """
                INSERT INTO tenant_private.subscriber_workspace_documents (
                  tenant_id, workspace_id, title, body, created_by, updated_by
                ) VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (tenant_id, workspace_id, title, body, actor_subject, actor_subject),
            )
            document = cursor.fetchone()
            assert document is not None
            cursor.execute(
                """
                UPDATE tenant_private.subscriber_workspaces
                SET revision = revision + 1, updated_at = now()
                WHERE tenant_id = %s AND workspace_id = %s
                """,
                (tenant_id, workspace_id),
            )
            self._append_audit(
                cursor=cursor,
                tenant_id=tenant_id,
                workspace_id=workspace_id,
                actor_subject=actor_subject,
                event_type="DOCUMENT_CREATED",
                object_type="document",
                object_id=document["document_id"],
                details={"workspace_revision": int(workspace["revision"]) + 1},
            )
            return document

    def create_markdown_export(
        self,
        *,
        tenant_id: UUID,
        workspace_id: UUID,
        document_id: UUID | None,
        actor_subject: str,
    ) -> dict[str, Any]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            workspace = self._workspace_for_update(
                cursor=cursor,
                tenant_id=tenant_id,
                workspace_id=workspace_id,
            )
            cursor.execute(
                """
                SELECT r.*, d.title AS dossier_title, d.summary AS dossier_summary,
                       d.sections AS dossier_sections, d.attribution AS dossier_attribution
                FROM tenant_private.research_runs r
                JOIN tenant_private.dossiers d ON d.dossier_id = r.dossier_id
                WHERE r.tenant_id = %s AND r.research_run_id = %s
                """,
                (tenant_id, workspace["research_run_id"]),
            )
            run = cursor.fetchone()
            if run is None:
                raise LookupError("persistent_dossier_not_found")

            document = None
            if document_id is not None:
                cursor.execute(
                    """
                    SELECT *
                    FROM tenant_private.subscriber_workspace_documents
                    WHERE tenant_id = %s AND workspace_id = %s AND document_id = %s
                    """,
                    (tenant_id, workspace_id, document_id),
                )
                document = cursor.fetchone()
                if document is None:
                    raise LookupError("document_not_found")

            content = self._render_markdown(workspace=workspace, run=run, document=document)
            digest = f"sha256:{sha256(content.encode('utf-8')).hexdigest()}"
            export_id = uuid4()
            filename = f"axignal-{workspace_id}-{export_id}.md"
            cursor.execute(
                """
                INSERT INTO tenant_private.subscriber_workspace_exports (
                  export_id, tenant_id, workspace_id, document_id, format,
                  filename, content, content_hash, created_by
                ) VALUES (%s, %s, %s, %s, 'MARKDOWN', %s, %s, %s, %s)
                RETURNING export_id, tenant_id, workspace_id, document_id, format,
                          filename, content_hash, created_by, created_at
                """,
                (
                    export_id,
                    tenant_id,
                    workspace_id,
                    document_id,
                    filename,
                    content,
                    digest,
                    actor_subject,
                ),
            )
            export = cursor.fetchone()
            assert export is not None
            self._append_audit(
                cursor=cursor,
                tenant_id=tenant_id,
                workspace_id=workspace_id,
                actor_subject=actor_subject,
                event_type="EXPORT_CREATED",
                object_type="export",
                object_id=export_id,
                details={"content_hash": digest, "format": "MARKDOWN"},
            )
            return export

    def export_content(
        self,
        *,
        tenant_id: UUID,
        export_id: UUID,
    ) -> dict[str, Any] | None:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT export_id, filename, content, content_hash, created_at
                FROM tenant_private.subscriber_workspace_exports
                WHERE tenant_id = %s AND export_id = %s
                """,
                (tenant_id, export_id),
            )
            return cursor.fetchone()

    @staticmethod
    def _workspace_for_update(
        *, cursor: Any, tenant_id: UUID, workspace_id: UUID
    ) -> dict[str, Any]:
        cursor.execute(
            """
            SELECT *
            FROM tenant_private.subscriber_workspaces
            WHERE tenant_id = %s AND workspace_id = %s
            FOR UPDATE
            """,
            (tenant_id, workspace_id),
        )
        workspace = cursor.fetchone()
        if workspace is None:
            raise LookupError("workspace_not_found")
        return workspace

    @staticmethod
    def _append_audit(
        *,
        cursor: Any,
        tenant_id: UUID,
        workspace_id: UUID,
        actor_subject: str,
        event_type: str,
        object_type: str,
        object_id: UUID,
        details: dict[str, Any],
    ) -> None:
        cursor.execute(
            """
            INSERT INTO tenant_private.subscriber_workspace_audit_events (
              tenant_id, workspace_id, actor_subject, event_type,
              object_type, object_id, details
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                tenant_id,
                workspace_id,
                actor_subject,
                event_type,
                object_type,
                object_id,
                Jsonb(details),
            ),
        )

    @staticmethod
    def _render_markdown(
        *,
        workspace: dict[str, Any],
        run: dict[str, Any],
        document: dict[str, Any] | None,
    ) -> str:
        sections = run.get("dossier_sections") or []
        lines = [
            f"# {run['dossier_title']}",
            "",
            str(run["dossier_summary"]),
            "",
            f"- ResearchRun: `{run['research_run_id']}`",
            f"- Workspace: `{workspace['workspace_id']}`",
            f"- State: `{run['state']}`",
            f"- Opportunity: `{run['opportunity_id']}`",
            "",
        ]
        for index, section in enumerate(sections, start=1):
            title = section.get("title") if isinstance(section, dict) else None
            text = section.get("text") if isinstance(section, dict) else None
            lines.extend([f"## {title or f'Section {index}'}", "", str(text or section), ""])
        if document is not None:
            lines.extend([f"## {document['title']}", "", str(document["body"]), ""])
        attribution = run.get("dossier_attribution") or {}
        lines.extend(["## Attribution", "", f"```json\n{attribution}\n```", ""])
        return "\n".join(lines)
