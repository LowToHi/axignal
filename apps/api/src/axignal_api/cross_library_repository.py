"""PostgreSQL repository for the persistent cross-library graph (Prioridad 5).

Nodes, edges, timeline, contradictions and non-canonical hypotheses,
tenant-scoped with forced RLS. Source suspension quarantines its edges;
recomputation updates the graph idempotently.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from psycopg.types.json import Jsonb

from axignal_api.repository import ResearchRepository


class CrossLibraryRepository(ResearchRepository):
    # --- Nodes ---------------------------------------------------------------

    def upsert_node(
        self,
        *,
        tenant_id: UUID,
        node_ref: str,
        library_id: str,
        entity_type: str,
        label: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                INSERT INTO tenant_private.cross_library_nodes (
                  node_id, tenant_id, node_ref, library_id, entity_type,
                  label, payload
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (tenant_id, node_ref) DO UPDATE SET
                  label = EXCLUDED.label, payload = EXCLUDED.payload
                """,
                (
                    uuid4(), tenant_id, node_ref, library_id, entity_type,
                    label, Jsonb(payload or {}),
                ),
            )

    def list_nodes(
        self, *, tenant_id: UUID, library_id: str | None = None
    ) -> list[dict[str, Any]]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            if library_id:
                cursor.execute(
                    """
                    SELECT node_ref, library_id, entity_type, label, payload, created_at
                    FROM tenant_private.cross_library_nodes
                    WHERE tenant_id = %s AND library_id = %s
                    ORDER BY created_at
                    """,
                    (tenant_id, library_id),
                )
            else:
                cursor.execute(
                    """
                    SELECT node_ref, library_id, entity_type, label, payload, created_at
                    FROM tenant_private.cross_library_nodes
                    WHERE tenant_id = %s
                    ORDER BY created_at
                    """,
                    (tenant_id,),
                )
            return [dict(row) for row in cursor.fetchall()]

    # --- Edges ---------------------------------------------------------------

    def upsert_edge(
        self,
        *,
        tenant_id: UUID,
        from_ref: str,
        to_ref: str,
        relation: str,
        evidence_refs: list[str],
        source_id: str | None = None,
    ) -> None:
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                INSERT INTO tenant_private.cross_library_edges (
                  edge_id, tenant_id, from_ref, to_ref, relation,
                  evidence_refs, source_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (tenant_id, from_ref, to_ref, relation) DO UPDATE SET
                  evidence_refs = EXCLUDED.evidence_refs,
                  status = 'ACTIVE'
                """,
                (
                    uuid4(), tenant_id, from_ref, to_ref, relation,
                    Jsonb(evidence_refs), source_id,
                ),
            )

    def quarantine_source_edges(
        self, *, tenant_id: UUID, source_id: str
    ) -> int:
        """Suspend a source: quarantine its edges (kept, flagged)."""
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                UPDATE tenant_private.cross_library_edges
                SET status = 'QUARANTINED'
                WHERE tenant_id = %s AND source_id = %s AND status = 'ACTIVE'
                """,
                (tenant_id, source_id),
            )
            return cursor.rowcount

    def list_edges(
        self, *, tenant_id: UUID, node_ref: str | None = None
    ) -> list[dict[str, Any]]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            if node_ref:
                cursor.execute(
                    """
                    SELECT edge_id, from_ref, to_ref, relation, evidence_refs,
                           status, source_id, created_at
                    FROM tenant_private.cross_library_edges
                    WHERE tenant_id = %s AND (from_ref = %s OR to_ref = %s)
                    ORDER BY created_at
                    """,
                    (tenant_id, node_ref, node_ref),
                )
            else:
                cursor.execute(
                    """
                    SELECT edge_id, from_ref, to_ref, relation, evidence_refs,
                           status, source_id, created_at
                    FROM tenant_private.cross_library_edges
                    WHERE tenant_id = %s
                    ORDER BY created_at
                    """,
                    (tenant_id,),
                )
            return [dict(row) for row in cursor.fetchall()]

    # --- Timeline ------------------------------------------------------------

    def add_timeline_event(
        self,
        *,
        tenant_id: UUID,
        node_ref: str,
        occurred_at: datetime,
        event_type: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                INSERT INTO tenant_private.cross_library_timeline (
                  event_id, tenant_id, node_ref, occurred_at, event_type, payload
                ) VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    uuid4(), tenant_id, node_ref, occurred_at, event_type,
                    Jsonb(payload or {}),
                ),
            )

    def timeline(
        self, *, tenant_id: UUID, node_ref: str | None = None
    ) -> list[dict[str, Any]]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            if node_ref:
                cursor.execute(
                    """
                    SELECT event_id, node_ref, occurred_at, event_type, payload
                    FROM tenant_private.cross_library_timeline
                    WHERE tenant_id = %s AND node_ref = %s
                    ORDER BY occurred_at
                    """,
                    (tenant_id, node_ref),
                )
            else:
                cursor.execute(
                    """
                    SELECT event_id, node_ref, occurred_at, event_type, payload
                    FROM tenant_private.cross_library_timeline
                    WHERE tenant_id = %s
                    ORDER BY occurred_at
                    """,
                    (tenant_id,),
                )
            return [dict(row) for row in cursor.fetchall()]

    # --- Contradictions ------------------------------------------------------

    def record_contradiction(
        self,
        *,
        tenant_id: UUID,
        claim_a_ref: str,
        claim_b_ref: str,
        description: str,
    ) -> None:
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                INSERT INTO tenant_private.cross_library_contradictions (
                  contradiction_id, tenant_id, claim_a_ref, claim_b_ref, description
                ) VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (tenant_id, claim_a_ref, claim_b_ref) DO NOTHING
                """,
                (uuid4(), tenant_id, claim_a_ref, claim_b_ref, description),
            )

    def list_contradictions(
        self, *, tenant_id: UUID
    ) -> list[dict[str, Any]]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT contradiction_id, claim_a_ref, claim_b_ref, description, status
                FROM tenant_private.cross_library_contradictions
                WHERE tenant_id = %s
                ORDER BY created_at
                """,
                (tenant_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    # --- Hypotheses (NON-canonical) ------------------------------------------

    def record_hypothesis(
        self,
        *,
        tenant_id: UUID,
        hypothesis_ref: str,
        cause_ref: str,
        effect_ref: str,
        description: str,
        confidence: str = "LOW",
    ) -> None:
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                INSERT INTO tenant_private.cross_library_hypotheses (
                  hypothesis_id, tenant_id, hypothesis_ref, cause_ref,
                  effect_ref, description, confidence
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (tenant_id, hypothesis_ref) DO NOTHING
                """,
                (
                    uuid4(), tenant_id, hypothesis_ref, cause_ref, effect_ref,
                    description, confidence,
                ),
            )

    def list_hypotheses(
        self, *, tenant_id: UUID
    ) -> list[dict[str, Any]]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT hypothesis_id, hypothesis_ref, cause_ref, effect_ref,
                       description, confidence, status
                FROM tenant_private.cross_library_hypotheses
                WHERE tenant_id = %s
                ORDER BY created_at
                """,
                (tenant_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    # --- Portfolio -----------------------------------------------------------

    def add_portfolio(
        self,
        *,
        tenant_id: UUID,
        item_ref: str,
        opportunity_ref: str,
        library_id: str,
    ) -> None:
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                INSERT INTO tenant_private.opportunity_portfolio (
                  item_id, tenant_id, item_ref, opportunity_ref, library_id
                ) VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (tenant_id, item_ref) DO NOTHING
                """,
                (uuid4(), tenant_id, item_ref, opportunity_ref, library_id),
            )

    def list_portfolio(
        self, *, tenant_id: UUID
    ) -> list[dict[str, Any]]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT item_id, item_ref, opportunity_ref, library_id, added_at
                FROM tenant_private.opportunity_portfolio
                WHERE tenant_id = %s
                ORDER BY added_at DESC
                """,
                (tenant_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    # --- Graph queries -------------------------------------------------------

    def neighbors(
        self, *, tenant_id: UUID, node_ref: str
    ) -> dict[str, Any]:
        edges = self.list_edges(tenant_id=tenant_id, node_ref=node_ref)
        nodes = {row["node_ref"]: row for row in self.list_nodes(tenant_id=tenant_id)}
        neighbors: list[dict[str, Any]] = []
        for edge in edges:
            other = edge["to_ref"] if edge["from_ref"] == node_ref else edge["from_ref"]
            neighbors.append(
                {
                    "node_ref": other,
                    "relation": edge["relation"],
                    "status": edge["status"],
                    "label": nodes.get(other, {}).get("label"),
                    "library_id": nodes.get(other, {}).get("library_id"),
                }
            )
        return {"node_ref": node_ref, "neighbors": neighbors}
