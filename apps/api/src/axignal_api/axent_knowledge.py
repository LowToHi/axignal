from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from axignal_api.repository import ResearchRepository


@dataclass(frozen=True)
class KnowledgeHit:
    revision_id: UUID
    document_id: UUID
    title: str
    section_path: str
    content: str
    content_hash: str
    source_authority: str
    version: int
    language: str
    rank: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "revision_id": self.revision_id,
            "document_id": self.document_id,
            "title": self.title,
            "section_path": self.section_path,
            "content": self.content,
            "content_hash": self.content_hash,
            "source_authority": self.source_authority,
            "version": self.version,
            "language": self.language,
            "rank": self.rank,
        }


class AxentKnowledgeRepository(ResearchRepository):
    """Read-only governed retrieval over approved, effective knowledge revisions."""

    def search(
        self,
        *,
        tenant_id: UUID,
        query: str,
        language: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        normalized = " ".join(query.split()).strip()
        if len(normalized) < 2:
            return []
        bounded_limit = max(1, min(limit, 10))
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                WITH requested AS (
                  SELECT plainto_tsquery('simple', %s) AS query
                )
                SELECT
                  revision.revision_id,
                  document.knowledge_document_id AS document_id,
                  document.title,
                  chunk.section_path,
                  chunk.content,
                  chunk.content_hash,
                  revision.source_authority,
                  revision.version,
                  chunk.language,
                  ts_rank_cd(chunk.search_vector, requested.query) AS rank
                FROM axignal_global.knowledge_chunks AS chunk
                JOIN axignal_global.knowledge_revisions AS revision
                  ON revision.revision_id = chunk.revision_id
                JOIN axignal_global.knowledge_documents AS document
                  ON document.knowledge_document_id = revision.document_id
                CROSS JOIN requested
                WHERE document.status = 'ACTIVE'
                  AND revision.review_status = 'APPROVED'
                  AND document.current_revision_id = revision.revision_id
                  AND revision.effective_from <= now()
                  AND (
                    revision.effective_until IS NULL
                    OR revision.effective_until > now()
                  )
                  AND (
                    document.scope = 'GLOBAL'
                    OR (
                      document.scope = 'TENANT'
                      AND document.tenant_id = %s
                    )
                  )
                  AND chunk.language IN (%s, 'und')
                  AND chunk.search_vector @@ requested.query
                ORDER BY rank DESC, document.title, chunk.section_path
                LIMIT %s
                """,
                (normalized, tenant_id, language, bounded_limit),
            )
            return [
                KnowledgeHit(
                    revision_id=row["revision_id"],
                    document_id=row["document_id"],
                    title=row["title"],
                    section_path=row["section_path"],
                    content=row["content"],
                    content_hash=row["content_hash"],
                    source_authority=row["source_authority"],
                    version=int(row["version"]),
                    language=row["language"],
                    rank=float(row["rank"]),
                ).as_dict()
                for row in cursor.fetchall()
            ]


def knowledge_coverage(hits: list[dict[str, Any]]) -> str:
    if not hits:
        return "NONE"
    if len(hits) == 1 or max(float(hit["rank"]) for hit in hits) < 0.05:
        return "PARTIAL"
    return "SUFFICIENT"
