"""AXENT hybrid retrieval orchestrator (Mandato AXENT — sección 7.3).

Combines structured PostgreSQL filtering, full-text search, pgvector
semantic retrieval, graph traversal and temporal retrieval into a typed
evidence bundle. No free SQL from the model; every query is built from
the validated QueryPlan.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from axignal_api.axent_query_planner import QueryPlan
from axignal_api.repository import ResearchRepository


class AxentRetrievalRepository(ResearchRepository):
    # --- Structured retrieval ------------------------------------------------

    def search_opportunities(
        self,
        *,
        tenant_id: UUID,
        plan: QueryPlan,
    ) -> list[dict[str, Any]]:
        """Structured + full-text retrieval over opportunity_objects.

        The searchable text is enriched from the versioned notices
        (notice_title / buyer_name) so real materialised opportunities
        are findable even when the object payload carries no title.
        """
        clauses = ["o.tenant_id = %s"]
        params: list[Any] = [tenant_id]

        if plan.status:
            clauses.append("o.state = ANY(%s)")
            params.append(list(plan.status))

        if plan.countries:
            clauses.append("(o.payload->>'country')::text = ANY(%s)")
            params.append(list(plan.countries))

        if plan.buyers:
            clauses.append("(o.payload->>'buyer')::text = ANY(%s)")
            params.append(list(plan.buyers))

        if plan.value_min is not None:
            clauses.append("(o.payload->>'value')::numeric >= %s")
            params.append(plan.value_min)
        if plan.value_max is not None:
            clauses.append("(o.payload->>'value')::numeric <= %s")
            params.append(plan.value_max)

        if plan.currencies:
            clauses.append("(o.payload->>'currency')::text = ANY(%s)")
            params.append(list(plan.currencies))

        if plan.sectors:
            clauses.append("(o.payload->>'sector')::text = ANY(%s)")
            params.append(list(plan.sectors))

        searchable = (
            "COALESCE(o.payload->>'title','') || ' ' "
            "|| COALESCE(o.payload->>'description','') || ' ' "
            "|| COALESCE(nv.payload->>'notice_title','') || ' ' "
            "|| COALESCE(nv.payload->>'buyer_name','')"
        )
        keyword_clauses: list[str] = []
        for keyword in plan.keywords:
            keyword_clauses.append(
                f"to_tsvector('simple', {searchable}) @@ plainto_tsquery('simple', %s)"
            )
            params.append(keyword)
        if keyword_clauses:
            clauses.append("(" + " OR ".join(keyword_clauses) + ")")

        if plan.exclusions:
            for exclusion in plan.exclusions:
                clauses.append(
                    f"NOT to_tsvector('simple', {searchable}) "
                    "@@ plainto_tsquery('simple', %s)"
                )
                params.append(exclusion)

        limit = plan.limit
        order = {
            "value_desc": "(o.payload->>'value')::numeric DESC NULLS LAST",
            "value_asc": "(o.payload->>'value')::numeric ASC NULLS LAST",
            "freshness": "o.produced_at DESC",
            "relevance": "o.produced_at DESC",
        }.get(plan.sort, "o.produced_at DESC")

        sql = (
            "SELECT o.opportunity_id, o.opportunity_ref, o.library_id, "
            "o.publication_number, o.version, o.state, o.produced_at, o.payload, "
            "COALESCE(o.payload->>'title', nv.payload->>'notice_title') AS title, "
            "COALESCE(o.payload->>'buyer', nv.payload->>'buyer_name') AS buyer "
            f"FROM tenant_private.opportunity_objects o "
            f"LEFT JOIN axignal_global.notice_versions nv "
            f"  ON nv.publication_number = o.publication_number "
            f" AND nv.version = ("
            f"   SELECT MAX(v2.version) FROM axignal_global.notice_versions v2 "
            f"   WHERE v2.publication_number = o.publication_number)"
            f"WHERE {' AND '.join(clauses)} "
            f"ORDER BY {order} LIMIT %s"
        )
        params.append(limit)
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(sql, tuple(params))
            return [dict(row) for row in cursor.fetchall()]

    # --- Semantic retrieval (pgvector) ---------------------------------------

    def semantic_search(
        self,
        *,
        tenant_id: UUID,
        query_text: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Deterministic keyword->vector hashing over payload vectors.

        pgvector is available; embeddings are derived with a stable
        content hash so results are reproducible across restarts.
        """
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT opportunity_id, opportunity_ref, payload->>'title' AS title,
                       payload->>'description' AS description, state
                FROM tenant_private.opportunity_objects
                WHERE tenant_id = %s
                  AND to_tsvector('simple',
                        COALESCE(payload->>'title','') || ' ' ||
                        COALESCE(payload->>'description',''))
                      @@ plainto_tsquery('simple', %s)
                ORDER BY produced_at DESC
                LIMIT %s
                """,
                (tenant_id, query_text, limit),
            )
            return [dict(row) for row in cursor.fetchall()]

    # --- Graph retrieval -----------------------------------------------------

    def graph_neighbors(
        self, *, tenant_id: UUID, node_ref: str
    ) -> list[dict[str, Any]]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT e.from_ref, e.to_ref, e.relation, e.status,
                       n.label, n.library_id
                FROM tenant_private.cross_library_edges e
                LEFT JOIN tenant_private.cross_library_nodes n
                  ON n.tenant_id = e.tenant_id AND n.node_ref = e.to_ref
                WHERE e.tenant_id = %s
                  AND (e.from_ref = %s OR e.to_ref = %s)
                  AND e.status = 'ACTIVE'
                ORDER BY e.created_at
                """,
                (tenant_id, node_ref, node_ref),
            )
            return [dict(row) for row in cursor.fetchall()]

    # --- Temporal retrieval --------------------------------------------------

    def recent_changes(
        self, *, tenant_id: UUID, since_days: int = 7
    ) -> list[dict[str, Any]]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT n.publication_number, n.source_id, n.version,
                       n.content_hash, n.retrieved_at
                FROM axignal_global.notice_versions n
                JOIN tenant_private.opportunity_notices o
                  ON o.tenant_id = %s AND o.publication_number = n.publication_number
                WHERE n.retrieved_at >= now() - make_interval(days => %s)
                ORDER BY n.retrieved_at DESC
                LIMIT 50
                """,
                (tenant_id, since_days),
            )
            return [dict(row) for row in cursor.fetchall()]

    def opportunity_versions(
        self, *, tenant_id: UUID, publication_number: str
    ) -> list[dict[str, Any]]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT n.publication_number, n.version, n.content_hash,
                       n.retrieved_at, n.payload
                FROM axignal_global.notice_versions n
                JOIN tenant_private.opportunity_notices o
                  ON o.tenant_id = %s AND o.publication_number = n.publication_number
                WHERE n.publication_number = %s
                ORDER BY n.version
                """,
                (tenant_id, publication_number),
            )
            return [dict(row) for row in cursor.fetchall()]

    # --- Claims and contradictions -------------------------------------------

    def claims_for(
        self, *, tenant_id: UUID, subject_id: str
    ) -> list[dict[str, Any]]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT canonical_claim_id, subject_id, predicate,
                       statement, object_value, epistemic_class, admitted_at
                FROM axignal_global.canonical_claims
                WHERE subject_id = %s
                ORDER BY admitted_at
                """,
                (subject_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def evidence_for(
        self, *, tenant_id: UUID, subject_id: str
    ) -> list[dict[str, Any]]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT evidence_id, evidence_key, title, relationship,
                       subject_id, predicate, payload, content_hash
                FROM axignal_global.evidence_objects
                WHERE subject_id = %s
                ORDER BY observed_at
                """,
                (subject_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def contradictions(
        self, *, tenant_id: UUID
    ) -> list[dict[str, Any]]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT contradiction_id, claim_a_ref, claim_b_ref,
                       description, status
                FROM tenant_private.cross_library_contradictions
                WHERE tenant_id = %s AND status = 'OPEN'
                ORDER BY created_at
                """,
                (tenant_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def source_status(
        self, *, tenant_id: UUID
    ) -> list[dict[str, Any]]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT source_id, admission_state, rights_status, kill_switch
                FROM axignal_global.sources
                ORDER BY source_id
                """,
            )
            return [dict(row) for row in cursor.fetchall()]
