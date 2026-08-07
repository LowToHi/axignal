"""PostgreSQL repository for Opportunity Operations (Prioridad 2).

Replaces the in-memory dictionaries of opportunity_operations/billing/
cross_library with durable tenant-scoped storage backed by the
143-opportunity-operations-spine.sql migration.

Every method is tenant-scoped (RLS + explicit tenant filter), transactional
and idempotent where the contract requires it.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from psycopg.types.json import Jsonb

from axignal_api.repository import ResearchRepository

PURSUIT_STATES = ("QUALIFIED", "DECISION_REVIEW", "ACTIVE", "WON", "LOST", "WITHDRAWN")
WORKSPACE_STATES = (
    "CREATED",
    "QUALIFYING",
    "GO_REVIEW",
    "NO_GO_REVIEW",
    "PREPARING",
    "AWAITING_INFORMATION",
    "READY_FOR_INTERNAL_REVIEW",
    "READY_FOR_SUBSCRIBER_APPROVAL",
    "PRESENTED_EXTERNALLY",
)
OUTCOME_RESULTS = ("WON", "LOST", "WITHDRAWN")
SUBSCRIPTION_STATES = (
    "ACTIVE",
    "DUNNING",
    "CANCELLED_AT_PERIOD_END",
    "CANCELLED_IMMEDIATE",
    "TRIAL",
)


class OpportunityOperationsRepository(ResearchRepository):
    """Durable tenant-scoped store for opportunity operations."""

    # --- Pursuits -----------------------------------------------------------

    def create_pursuit(
        self,
        *,
        tenant_id: UUID,
        pursuit_ref: str,
        opportunity_ref: str,
        state: str,
        created_by: str,
        workspace_ref: UUID | None = None,
    ) -> UUID:
        if state not in PURSUIT_STATES:
            raise ValueError(f"invalid pursuit state {state!r}")
        pursuit_id = uuid4()
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                INSERT INTO tenant_private.opportunity_pursuits
                  (pursuit_id, tenant_id, pursuit_ref, opportunity_ref, state,
                   workspace_ref, created_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (pursuit_id, tenant_id, pursuit_ref, opportunity_ref, state,
                 workspace_ref, created_by),
            )
        return pursuit_id

    def transition_pursuit(
        self,
        *,
        tenant_id: UUID,
        pursuit_ref: str,
        new_state: str,
        decided_by: str | None = None,
        outcome_ref: str | None = None,
    ) -> dict[str, Any]:
        if new_state not in PURSUIT_STATES:
            raise ValueError(f"invalid pursuit state {new_state!r}")
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            if new_state in ("WON", "LOST", "WITHDRAWN"):
                cursor.execute(
                    """
                    UPDATE tenant_private.opportunity_pursuits
                    SET state = %s, decided_by = %s, decided_at = now(),
                        outcome_ref = COALESCE(%s, outcome_ref)
                    WHERE tenant_id = %s AND pursuit_ref = %s
                    RETURNING pursuit_id, state, decided_at
                    """,
                    (new_state, decided_by, outcome_ref, tenant_id, pursuit_ref),
                )
            else:
                cursor.execute(
                    """
                    UPDATE tenant_private.opportunity_pursuits
                    SET state = %s
                    WHERE tenant_id = %s AND pursuit_ref = %s
                    RETURNING pursuit_id, state
                    """,
                    (new_state, tenant_id, pursuit_ref),
                )
            row = cursor.fetchone()
            if row is None:
                raise LookupError(f"pursuit {pursuit_ref!r} not found")
            return dict(row)

    def list_pursuits(self, *, tenant_id: UUID) -> list[dict[str, Any]]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT pursuit_id, pursuit_ref, opportunity_ref, state,
                       workspace_ref, created_by, created_at, decided_by,
                       decided_at, outcome_ref, evidence_refs
                FROM tenant_private.opportunity_pursuits
                WHERE tenant_id = %s
                ORDER BY created_at DESC
                """,
                (tenant_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_pursuit(self, *, tenant_id: UUID, pursuit_ref: str) -> dict[str, Any] | None:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT pursuit_id, pursuit_ref, opportunity_ref, state,
                       workspace_ref, created_by, created_at, decided_by,
                       decided_at, outcome_ref, evidence_refs
                FROM tenant_private.opportunity_pursuits
                WHERE tenant_id = %s AND pursuit_ref = %s
                """,
                (tenant_id, pursuit_ref),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    # --- Workspaces ---------------------------------------------------------

    def create_workspace(
        self,
        *,
        tenant_id: UUID,
        workspace_id: UUID,
        pursuit_ref: str,
        opportunity_ref: str,
        opportunity_version_digest: str,
        subscriber_profile_version: str,
        assessment_version: str,
        created_by: str,
    ) -> None:
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                INSERT INTO tenant_private.opportunity_workspaces
                  (workspace_id, tenant_id, pursuit_ref, opportunity_ref,
                   opportunity_version_digest, subscriber_profile_version,
                   assessment_version, state, created_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'CREATED', %s)
                """,
                (workspace_id, tenant_id, pursuit_ref, opportunity_ref,
                 opportunity_version_digest, subscriber_profile_version,
                 assessment_version, created_by),
            )

    def update_workspace_state(
        self,
        *,
        tenant_id: UUID,
        workspace_id: UUID,
        state: str,
    ) -> dict[str, Any]:
        if state not in WORKSPACE_STATES:
            raise ValueError(f"invalid workspace state {state!r}")
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                UPDATE tenant_private.opportunity_workspaces
                SET state = %s
                WHERE tenant_id = %s AND workspace_id = %s
                RETURNING workspace_id, state
                """,
                (state, tenant_id, workspace_id),
            )
            row = cursor.fetchone()
            if row is None:
                raise LookupError(f"workspace {workspace_id} not found")
            return dict(row)

    def get_workspace(
        self, *, tenant_id: UUID, workspace_id: UUID
    ) -> dict[str, Any] | None:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT workspace_id, pursuit_ref, opportunity_ref,
                       opportunity_version_digest, subscriber_profile_version,
                       assessment_version, state, created_by, created_at,
                       presented_externally_confirmed_by,
                       presented_externally_confirmed_at
                FROM tenant_private.opportunity_workspaces
                WHERE tenant_id = %s AND workspace_id = %s
                """,
                (tenant_id, workspace_id),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def list_workspaces(self, *, tenant_id: UUID) -> list[dict[str, Any]]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT workspace_id, pursuit_ref, opportunity_ref, state,
                       assessment_version, created_by, created_at
                FROM tenant_private.opportunity_workspaces
                WHERE tenant_id = %s
                ORDER BY created_at DESC
                """,
                (tenant_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    # --- Outcomes and learnings ---------------------------------------------

    def create_outcome(
        self,
        *,
        tenant_id: UUID,
        outcome_ref: str,
        pursuit_ref: str,
        result: str,
        decided_at: datetime,
        evidence_refs: list[str],
        notes: str | None = None,
    ) -> UUID:
        if result not in OUTCOME_RESULTS:
            raise ValueError(f"invalid outcome result {result!r}")
        outcome_id = uuid4()
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                INSERT INTO tenant_private.opportunity_outcomes
                  (outcome_id, tenant_id, outcome_ref, pursuit_ref, result,
                   decided_at, evidence_refs, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (outcome_id, tenant_id, outcome_ref, pursuit_ref, result,
                 decided_at, Jsonb(evidence_refs), notes),
            )
        return outcome_id

    def create_learning(
        self,
        *,
        tenant_id: UUID,
        learning_ref: str,
        outcome_ref: str,
        insight: str,
        evidence_refs: list[str],
    ) -> UUID:
        learning_id = uuid4()
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                INSERT INTO tenant_private.opportunity_learnings
                  (learning_id, tenant_id, learning_ref, outcome_ref, insight,
                   evidence_refs)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (learning_id, tenant_id, learning_ref, outcome_ref, insight,
                 Jsonb(evidence_refs)),
            )
        return learning_id

    def list_outcomes(self, *, tenant_id: UUID) -> list[dict[str, Any]]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT outcome_id, outcome_ref, pursuit_ref, result, decided_at,
                       evidence_refs, notes
                FROM tenant_private.opportunity_outcomes
                WHERE tenant_id = %s
                ORDER BY decided_at DESC
                """,
                (tenant_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def list_learnings(self, *, tenant_id: UUID) -> list[dict[str, Any]]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT learning_id, learning_ref, outcome_ref, insight,
                       evidence_refs, derived_at
                FROM tenant_private.opportunity_learnings
                WHERE tenant_id = %s
                ORDER BY derived_at DESC
                """,
                (tenant_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    # --- Manifest states ----------------------------------------------------

    def upsert_manifest_state(
        self,
        *,
        manifest_kind: str,
        manifest_id: str,
        state: str,
        payload: dict[str, Any],
    ) -> None:
        with self._cursor(role="axignal_worker") as cursor:
            cursor.execute(
                """
                INSERT INTO axignal_global.manifest_states
                  (manifest_kind, manifest_id, state, payload, updated_at)
                VALUES (%s, %s, %s, %s, now())
                ON CONFLICT (manifest_kind, manifest_id)
                DO UPDATE SET state = EXCLUDED.state,
                              payload = EXCLUDED.payload,
                              updated_at = now()
                """,
                (manifest_kind, manifest_id, state, Jsonb(payload)),
            )

    def get_manifest_state(
        self, *, manifest_kind: str, manifest_id: str
    ) -> dict[str, Any] | None:
        with self._cursor(role="axignal_app") as cursor:
            cursor.execute(
                """
                SELECT manifest_kind, manifest_id, state, schema_version,
                       payload, updated_at
                FROM axignal_global.manifest_states
                WHERE manifest_kind = %s AND manifest_id = %s
                """,
                (manifest_kind, manifest_id),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    # --- Portfolio ----------------------------------------------------------

    def add_portfolio_item(
        self,
        *,
        tenant_id: UUID,
        item_ref: str,
        opportunity_ref: str,
        library_id: str,
    ) -> UUID:
        item_id = uuid4()
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                INSERT INTO tenant_private.opportunity_portfolio
                  (item_id, tenant_id, item_ref, opportunity_ref, library_id)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (item_id, tenant_id, item_ref, opportunity_ref, library_id),
            )
        return item_id

    def list_portfolio(self, *, tenant_id: UUID) -> list[dict[str, Any]]:
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

    # --- Pipeline opportunities (Prioridad 2) --------------------------------

    def list_opportunities(self, *, tenant_id: UUID) -> list[dict[str, Any]]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT opportunity_id, opportunity_ref, library_id,
                       publication_number, version, content_hash, source_id,
                       produced_by, produced_at, state, payload
                FROM tenant_private.opportunity_objects
                WHERE tenant_id = %s
                ORDER BY produced_at DESC
                """,
                (tenant_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_opportunity(
        self, *, tenant_id: UUID, opportunity_ref: str
    ) -> dict[str, Any] | None:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT opportunity_id, opportunity_ref, library_id,
                       publication_number, version, content_hash, source_id,
                       produced_by, produced_at, state, payload
                FROM tenant_private.opportunity_objects
                WHERE tenant_id = %s AND opportunity_ref = %s
                """,
                (tenant_id, opportunity_ref),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def record_qualification(
        self,
        *,
        tenant_id: UUID,
        opportunity_ref: str,
        decision: str,
        decided_by: str,
    ) -> None:
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                UPDATE tenant_private.opportunity_objects
                SET state = CASE
                      WHEN %s = 'BID' THEN 'QUALIFIED'
                      WHEN %s = 'NO_BID' THEN 'CLOSED'
                      ELSE 'OPEN'
                    END,
                    payload = jsonb_set(
                      COALESCE(payload, '{}'::jsonb),
                      '{qualification}',
                      jsonb_build_object('decision', %s::text, 'decided_by', %s::text,
                                         'decided_at', now())
                    )
                WHERE tenant_id = %s AND opportunity_ref = %s
                """,
                (
                    decision,
                    decision,
                    decision,
                    decided_by,
                    tenant_id,
                    opportunity_ref,
                ),
            )

    def get_opportunity_claims(
        self, *, tenant_id: UUID, opportunity_ref: str
    ) -> dict[str, Any]:
        """Evidence + canonical claims bound to the opportunity's notices."""
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT publication_number, current_version, current_content_hash,
                       notice_title, buyer_name, notice_type, state
                FROM tenant_private.opportunity_notices
                WHERE tenant_id = %s
                  AND publication_number IN (
                    SELECT publication_number
                    FROM tenant_private.opportunity_objects
                    WHERE tenant_id = %s AND opportunity_ref = %s
                  )
                """,
                (tenant_id, tenant_id, opportunity_ref),
            )
            notices = [dict(row) for row in cursor.fetchall()]
            cursor.execute(
                """
                SELECT evidence_id, subject_id, predicate, title, relationship
                FROM axignal_global.evidence_objects
                WHERE subject_id LIKE 'ted_notice_%'
                ORDER BY evidence_id
                LIMIT 200
                """,
            )
            evidence = [dict(row) for row in cursor.fetchall()]
            cursor.execute(
                """
                SELECT canonical_claim_id, subject_id, predicate, statement
                FROM axignal_global.canonical_claims
                WHERE subject_id LIKE 'ted_notice_%'
                ORDER BY canonical_claim_id
                LIMIT 200
                """,
            )
            claims = [dict(row) for row in cursor.fetchall()]
            return {
                "notices": notices,
                "evidence": evidence,
                "canonical_claims": claims,
            }

    # --- Notices -------------------------------------------------------------

    def list_notices(self, *, tenant_id: UUID) -> list[dict[str, Any]]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT notice_id, publication_number, source_id, current_version,
                       current_content_hash, first_retrieved_at, last_retrieved_at,
                       notice_title, buyer_name, notice_type, state
                FROM tenant_private.opportunity_notices
                WHERE tenant_id = %s
                ORDER BY last_retrieved_at DESC
                """,
                (tenant_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_notice(
        self, *, tenant_id: UUID, publication_number: str
    ) -> dict[str, Any] | None:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT notice_id, publication_number, source_id, current_version,
                       current_content_hash, first_retrieved_at, last_retrieved_at,
                       notice_title, buyer_name, notice_type, state, payload
                FROM tenant_private.opportunity_notices
                WHERE tenant_id = %s AND publication_number = %s
                """,
                (tenant_id, publication_number),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
