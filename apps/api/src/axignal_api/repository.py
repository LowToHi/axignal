from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal
from uuid import UUID, uuid4

import psycopg
from psycopg import sql
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from axignal_api.admission import AdmissionDecision, CandidateArtifact, EvidenceArtifact
from axignal_api.connectors.world_bank import WorldBankObservation

DatabaseRole = Literal["axignal_app", "axignal_worker"]


@dataclass(frozen=True)
class OutboxEvent:
    outbox_event_id: UUID
    aggregate_id: UUID
    event_type: str
    payload: dict[str, Any]
    attempts: int


class ResearchRepository:
    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    @contextmanager
    def _cursor(
        self,
        *,
        role: DatabaseRole,
        tenant_id: UUID | None = None,
    ) -> Iterator[psycopg.Cursor[dict[str, Any]]]:
        with (
            psycopg.connect(self.dsn, row_factory=dict_row) as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(role)))
            if tenant_id is not None:
                cursor.execute(
                    "SELECT set_config('app.tenant_id', %s, true)",
                    (str(tenant_id),),
                )
            yield cursor

    def create_run(
        self,
        *,
        tenant_id: UUID,
        context_id: str,
        opportunity_id: str,
        question: str,
        include_private_knowledge: bool,
    ) -> UUID:
        run_id = uuid4()
        source_plan = [
            {
                "source_id": "world-bank-wdi",
                "indicator": "FP.CPI.TOTL.ZG",
                "country": "RUS",
                "priority": 1,
                "purpose": "Country-level inflation context for the selected opportunity",
            }
        ]
        budgets = {
            "max_api_requests": 1,
            "max_documents": 1,
            "max_response_bytes": 524_288,
            "max_duration_seconds": 30,
            "max_model_calls": 0,
        }
        event_payload = {
            "schema_version": 1,
            "tenant_id": str(tenant_id),
            "research_run_id": str(run_id),
            "source_id": "world-bank-wdi",
        }
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                INSERT INTO tenant_private.research_runs (
                  research_run_id,
                  tenant_id,
                  context_id,
                  opportunity_id,
                  question,
                  state,
                  private_knowledge_authorised,
                  source_plan,
                  budgets
                ) VALUES (%s, %s, %s, %s, %s, 'QUEUED', %s, %s, %s)
                """,
                (
                    run_id,
                    tenant_id,
                    context_id,
                    opportunity_id,
                    question,
                    include_private_knowledge,
                    Jsonb(source_plan),
                    Jsonb(budgets),
                ),
            )
            cursor.execute(
                """
                INSERT INTO axignal_global.outbox_events (
                  aggregate_type,
                  aggregate_id,
                  event_type,
                  payload
                ) VALUES ('RESEARCH_RUN', %s, 'research.run.requested', %s)
                """,
                (run_id, Jsonb(event_payload)),
            )
        return run_id

    def get_run_view(self, *, tenant_id: UUID, run_id: UUID) -> dict[str, Any] | None:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT *
                FROM tenant_private.research_runs
                WHERE research_run_id = %s
                """,
                (run_id,),
            )
            run = cursor.fetchone()
            if run is None:
                return None

            evidence = self._fetch_many(
                cursor,
                "axignal_global.evidence_objects",
                "evidence_id",
                run["evidence_ids"],
            )
            candidates = self._fetch_many(
                cursor,
                "axignal_global.candidate_claims",
                "candidate_claim_id",
                run["candidate_claim_ids"],
            )
            canonical = self._fetch_many(
                cursor,
                "axignal_global.canonical_claims",
                "canonical_claim_id",
                run["canonical_claim_ids"],
            )
            dossier = None
            if run["dossier_id"] is not None:
                cursor.execute(
                    "SELECT * FROM tenant_private.dossiers WHERE dossier_id = %s",
                    (run["dossier_id"],),
                )
                dossier = cursor.fetchone()

        return {
            "research_run_id": run["research_run_id"],
            "context_id": run["context_id"],
            "opportunity_id": run["opportunity_id"],
            "question": run["question"],
            "state": run["state"],
            "private_knowledge_authorised": run["private_knowledge_authorised"],
            "source_plan": run["source_plan"],
            "budgets": run["budgets"],
            "actual_usage": run["actual_usage"],
            "evidence": [self._evidence_view(row) for row in evidence],
            "candidate_claims": [self._candidate_view(row) for row in candidates],
            "canonical_claims": [self._canonical_view(row) for row in canonical],
            "dossier": self._dossier_view(dossier) if dossier else None,
            "admission_batch_id": run["admission_batch_id"],
            "error_code": run["error_code"],
            "error_detail": run["error_detail"],
            "created_at": run["created_at"],
            "updated_at": run["updated_at"],
            "synthetic": False,
        }

    @staticmethod
    def _fetch_many(
        cursor: psycopg.Cursor[dict[str, Any]],
        table: str,
        id_column: str,
        identifiers: list[UUID],
    ) -> list[dict[str, Any]]:
        if not identifiers:
            return []
        query = sql.SQL("SELECT * FROM {} WHERE {} = ANY(%s)").format(
            sql.SQL(table),
            sql.Identifier(id_column),
        )
        cursor.execute(query, (identifiers,))
        rows = cursor.fetchall()
        order = {identifier: index for index, identifier in enumerate(identifiers)}
        return sorted(rows, key=lambda row: order.get(row[id_column], len(order)))

    @staticmethod
    def _evidence_view(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "evidence_id": row["evidence_id"],
            "source_id": row["source_id"],
            "title": row["title"],
            "relationship": row["relationship"],
            "subject_id": row["subject_id"],
            "predicate": row["predicate"],
            "observed_at": row["observed_at"],
            "numeric_value": (
                str(row["numeric_value"]) if row["numeric_value"] is not None else None
            ),
            "unit": row["unit"],
            "rights_status": row["rights_status"],
            "provisional": row["provisional"],
            "payload": row["payload"],
        }

    @staticmethod
    def _candidate_view(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "candidate_claim_id": row["candidate_claim_id"],
            "fingerprint": row["fingerprint"],
            "statement": row["statement"],
            "kind": row["kind"],
            "state": row["state"],
            "producer_type": row["producer_type"],
            "method_version": row["method_version"],
            "canonical_claim_id": row["canonical_claim_id"],
            "rejection_reasons": row["rejection_reasons"],
        }

    @staticmethod
    def _canonical_view(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "canonical_claim_id": row["canonical_claim_id"],
            "fingerprint": row["fingerprint"],
            "statement": row["statement"],
            "subject_id": row["subject_id"],
            "predicate": row["predicate"],
            "object_value": row["object_value"],
            "observed_at": row["observed_at"],
            "epistemic_class": row["epistemic_class"],
            "state": row["state"],
            "admitted_by": row["admitted_by"],
            "admitted_at": row["admitted_at"],
        }

    @staticmethod
    def _dossier_view(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "dossier_id": row["dossier_id"],
            "status": row["status"],
            "title": row["title"],
            "summary": row["summary"],
            "sections": row["sections"],
            "attribution": row["attribution"],
        }

    def get_source(self, source_id: str) -> dict[str, Any] | None:
        with self._cursor(role="axignal_worker") as cursor:
            cursor.execute(
                "SELECT * FROM axignal_global.sources WHERE source_id = %s",
                (source_id,),
            )
            return cursor.fetchone()

    def get_run_for_worker(self, *, tenant_id: UUID, run_id: UUID) -> dict[str, Any] | None:
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                "SELECT * FROM tenant_private.research_runs WHERE research_run_id = %s",
                (run_id,),
            )
            return cursor.fetchone()

    def transition_run(
        self,
        *,
        tenant_id: UUID,
        run_id: UUID,
        state: str,
    ) -> None:
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                UPDATE tenant_private.research_runs
                SET state = %s, updated_at = now()
                WHERE research_run_id = %s
                """,
                (state, run_id),
            )
            if cursor.rowcount != 1:
                raise LookupError("ResearchRun not found for tenant")

    def pending_outbox(self, *, limit: int = 10) -> list[OutboxEvent]:
        with self._cursor(role="axignal_worker") as cursor:
            cursor.execute(
                """
                SELECT outbox_event_id, aggregate_id, event_type, payload, attempts
                FROM axignal_global.outbox_events
                WHERE status = 'PENDING' AND available_at <= now()
                ORDER BY created_at
                LIMIT %s
                """,
                (limit,),
            )
            rows = cursor.fetchall()
        return [
            OutboxEvent(
                outbox_event_id=row["outbox_event_id"],
                aggregate_id=row["aggregate_id"],
                event_type=row["event_type"],
                payload=row["payload"],
                attempts=row["attempts"],
            )
            for row in rows
        ]

    def mark_outbox_published(self, event_id: UUID) -> None:
        with self._cursor(role="axignal_worker") as cursor:
            cursor.execute(
                """
                UPDATE axignal_global.outbox_events
                SET status = 'PUBLISHED', published_at = now(), attempts = attempts + 1
                WHERE outbox_event_id = %s AND status = 'PENDING'
                """,
                (event_id,),
            )

    def mark_outbox_failed(self, event_id: UUID, error: str) -> None:
        with self._cursor(role="axignal_worker") as cursor:
            cursor.execute(
                """
                UPDATE axignal_global.outbox_events
                SET attempts = attempts + 1,
                    last_error = %s,
                    status = CASE WHEN attempts >= 4 THEN 'FAILED' ELSE 'PENDING' END,
                    available_at = now() + interval '30 seconds'
                WHERE outbox_event_id = %s AND status = 'PENDING'
                """,
                (error[:500], event_id),
            )

    def complete_world_bank_run(
        self,
        *,
        tenant_id: UUID,
        run_id: UUID,
        source: dict[str, Any],
        observation: WorldBankObservation,
        evidence: EvidenceArtifact,
        candidate: CandidateArtifact,
        decision: AdmissionDecision,
    ) -> dict[str, UUID | None]:
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT state, opportunity_id
                FROM tenant_private.research_runs
                WHERE research_run_id = %s
                """,
                (run_id,),
            )
            run = cursor.fetchone()
            if run is None:
                raise LookupError("ResearchRun not found for worker")

            source_object_id = self._upsert_source_object(
                cursor=cursor,
                source=source,
                observation=observation,
            )
            evidence_id = self._upsert_evidence(
                cursor=cursor,
                source_object_id=source_object_id,
                source_id=observation.source_id,
                evidence=evidence,
            )
            candidate_claim_id = self._upsert_candidate(
                cursor=cursor,
                candidate=candidate,
                evidence_id=evidence_id,
            )
            admission_batch_id = uuid4()
            cursor.execute(
                """
                INSERT INTO axignal_global.admission_batches (
                  admission_batch_id,
                  policy_version,
                  state,
                  candidate_claim_ids
                ) VALUES (%s, %s, 'PENDING', %s)
                """,
                (
                    admission_batch_id,
                    decision.policy_version,
                    [candidate_claim_id],
                ),
            )

            canonical_claim_id: UUID | None = None
            canonical_was_created = False
            if decision.admitted:
                canonical_claim_id, canonical_was_created = self._admit_candidate(
                    cursor=cursor,
                    candidate_claim_id=candidate_claim_id,
                    candidate=candidate,
                    evidence=evidence,
                    evidence_id=evidence_id,
                    admission_batch_id=admission_batch_id,
                    epistemic_class=decision.epistemic_class or "OBSERVED_FACT",
                )
            else:
                cursor.execute(
                    """
                    UPDATE axignal_global.candidate_claims
                    SET state = 'REJECTED', rejection_reasons = %s, updated_at = now()
                    WHERE candidate_claim_id = %s
                    """,
                    (Jsonb(list(decision.reasons)), candidate_claim_id),
                )

            decision_summary = decision.as_json() | {
                "canonical_claim_id": str(canonical_claim_id) if canonical_claim_id else None,
                "canonical_claim_created": canonical_was_created,
            }
            cursor.execute(
                """
                UPDATE axignal_global.admission_batches
                SET state = 'DECIDED', decision_summary = %s, decided_at = now()
                WHERE admission_batch_id = %s
                """,
                (Jsonb(decision_summary), admission_batch_id),
            )

            dossier_id = uuid4()
            sections = [
                {
                    "section_id": "institutional_observation",
                    "title": "Contexto macroeconómico institucional",
                    "text": candidate.statement,
                    "evidence_ids": [str(evidence_id)],
                    "candidate_claim_ids": [str(candidate_claim_id)],
                    "canonical_claim_ids": (
                        [str(canonical_claim_id)] if canonical_claim_id else []
                    ),
                },
                {
                    "section_id": "methodology",
                    "title": "Metodología y autoridad",
                    "text": (
                        "El dato fue extraído de forma determinista del World Bank Indicators API. "
                        "No se utilizó un modelo generativo para producir ni admitir el hecho."
                    ),
                    "policy_version": decision.policy_version,
                    "retrieval_mode": observation.retrieval_mode,
                },
                {
                    "section_id": "limitations",
                    "title": "Limitaciones",
                    "text": (
                        "El indicador es anual y nacional. Aporta contexto para la oportunidad de "
                        "Moscú, pero no demuestra causalidad ni condiciones inmobiliarias locales."
                    ),
                },
            ]
            attribution = {
                "source_id": source["source_id"],
                "source_name": source["name"],
                "license_id": source["license_id"],
                "attribution_text": source["attribution_text"],
                "dataset_url": source["dataset_url"],
                "changes": "AXIGNAL selected, normalised and contextualised the observation.",
            }
            dossier_status = (
                "TRACEABLE_WITH_ADMITTED_FACTS" if canonical_claim_id else "TRACEABLE_PROVISIONAL"
            )
            cursor.execute(
                """
                INSERT INTO tenant_private.dossiers (
                  dossier_id,
                  tenant_id,
                  research_run_id,
                  status,
                  title,
                  summary,
                  sections,
                  attribution
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    dossier_id,
                    tenant_id,
                    run_id,
                    dossier_status,
                    "Contexto de inflación · Federación Rusa",
                    (
                        "AXIGNAL recuperó un indicador institucional con derechos admitidos y "
                        "ejecutó la admisión determinista del hecho observado."
                        if canonical_claim_id
                        else "La observación fue conservada, pero no superó los gates de admisión."
                    ),
                    Jsonb(sections),
                    Jsonb(attribution),
                ),
            )
            cursor.execute(
                """
                INSERT INTO tenant_private.research_evidence_links (
                  tenant_id,
                  research_run_id,
                  evidence_id,
                  visibility
                ) VALUES (%s, %s, %s, 'GLOBAL_PUBLIC')
                ON CONFLICT DO NOTHING
                """,
                (tenant_id, run_id, evidence_id),
            )
            canonical_ids = [canonical_claim_id] if canonical_claim_id else []
            usage = {
                "api_requests": 1 if observation.retrieval_mode == "LIVE_API" else 0,
                "fixture_reads": 1 if observation.retrieval_mode == "FROZEN_FIXTURE" else 0,
                "documents": 1,
                "model_calls": 0,
                "source_content_hash": observation.content_hash,
            }
            cursor.execute(
                """
                UPDATE tenant_private.research_runs
                SET state = 'COMPLETED',
                    actual_usage = %s,
                    evidence_ids = %s,
                    candidate_claim_ids = %s,
                    canonical_claim_ids = %s,
                    dossier_id = %s,
                    admission_batch_id = %s,
                    updated_at = now()
                WHERE research_run_id = %s
                """,
                (
                    Jsonb(usage),
                    [evidence_id],
                    [candidate_claim_id],
                    canonical_ids,
                    dossier_id,
                    admission_batch_id,
                    run_id,
                ),
            )
            cursor.execute(
                """
                INSERT INTO axignal_global.outbox_events (
                  aggregate_type,
                  aggregate_id,
                  event_type,
                  payload
                ) VALUES ('RESEARCH_RUN', %s, 'research.run.completed', %s)
                """,
                (
                    run_id,
                    Jsonb(
                        {
                            "schema_version": 1,
                            "tenant_id": str(tenant_id),
                            "research_run_id": str(run_id),
                            "evidence_ids": [str(evidence_id)],
                            "candidate_claim_ids": [str(candidate_claim_id)],
                            "canonical_claim_ids": [str(item) for item in canonical_ids],
                            "dossier_id": str(dossier_id),
                            "admission_batch_id": str(admission_batch_id),
                        }
                    ),
                ),
            )

        return {
            "source_object_id": source_object_id,
            "evidence_id": evidence_id,
            "candidate_claim_id": candidate_claim_id,
            "canonical_claim_id": canonical_claim_id,
            "dossier_id": dossier_id,
            "admission_batch_id": admission_batch_id,
        }

    @staticmethod
    def _upsert_source_object(
        *,
        cursor: psycopg.Cursor[dict[str, Any]],
        source: dict[str, Any],
        observation: WorldBankObservation,
    ) -> UUID:
        source_updated_at = None
        if observation.source_updated_at:
            try:
                source_updated_at = datetime.fromisoformat(observation.source_updated_at).replace(
                    tzinfo=UTC
                )
            except ValueError:
                source_updated_at = None
        rights_snapshot = {
            "rights_status": source["rights_status"],
            "license_id": source["license_id"],
            "attribution_text": source["attribution_text"],
            "terms_url": source["terms_url"],
            "dataset_url": source["dataset_url"],
            "last_reviewed_at": source["last_reviewed_at"].isoformat(),
        }
        cursor.execute(
            """
            INSERT INTO axignal_global.source_objects (
              source_id,
              retrieval_key,
              request_url,
              retrieved_at,
              source_updated_at,
              http_status,
              content_type,
              content_hash,
              raw_payload,
              rights_snapshot,
              lineage
            ) VALUES (%s, %s, %s, %s, %s, 200, 'application/json', %s, %s, %s, %s)
            ON CONFLICT (retrieval_key) DO NOTHING
            RETURNING source_object_id
            """,
            (
                observation.source_id,
                observation.retrieval_key,
                observation.request_url,
                observation.retrieved_at,
                source_updated_at,
                observation.content_hash,
                Jsonb(observation.raw_payload),
                Jsonb(rights_snapshot),
                Jsonb(
                    {
                        "connector": "world-bank-wdi@1.0.0",
                        "retrieval_mode": observation.retrieval_mode,
                        "country_code": observation.country_code,
                        "indicator_code": observation.indicator_code,
                    }
                ),
            ),
        )
        row = cursor.fetchone()
        if row:
            return row["source_object_id"]
        cursor.execute(
            "SELECT source_object_id FROM axignal_global.source_objects WHERE retrieval_key = %s",
            (observation.retrieval_key,),
        )
        existing = cursor.fetchone()
        if existing is None:
            raise RuntimeError("Source object upsert failed")
        return existing["source_object_id"]

    @staticmethod
    def _upsert_evidence(
        *,
        cursor: psycopg.Cursor[dict[str, Any]],
        source_object_id: UUID,
        source_id: str,
        evidence: EvidenceArtifact,
    ) -> UUID:
        cursor.execute(
            """
            INSERT INTO axignal_global.evidence_objects (
              source_object_id,
              source_id,
              evidence_key,
              title,
              relationship,
              subject_id,
              predicate,
              observed_at,
              valid_from,
              valid_to,
              numeric_value,
              unit,
              payload,
              content_hash,
              rights_status,
              provisional
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, true)
            ON CONFLICT (evidence_key) DO NOTHING
            RETURNING evidence_id
            """,
            (
                source_object_id,
                source_id,
                evidence.evidence_key,
                evidence.title,
                evidence.relationship,
                evidence.subject_id,
                evidence.predicate,
                evidence.observed_at,
                evidence.valid_from,
                evidence.valid_to,
                evidence.numeric_value,
                evidence.unit,
                Jsonb(evidence.payload),
                evidence.content_hash,
                evidence.rights_status,
            ),
        )
        row = cursor.fetchone()
        if row:
            return row["evidence_id"]
        cursor.execute(
            "SELECT evidence_id FROM axignal_global.evidence_objects WHERE evidence_key = %s",
            (evidence.evidence_key,),
        )
        existing = cursor.fetchone()
        if existing is None:
            raise RuntimeError("Evidence upsert failed")
        return existing["evidence_id"]

    @staticmethod
    def _upsert_candidate(
        *,
        cursor: psycopg.Cursor[dict[str, Any]],
        candidate: CandidateArtifact,
        evidence_id: UUID,
    ) -> UUID:
        cursor.execute(
            """
            INSERT INTO axignal_global.candidate_claims (
              fingerprint,
              opportunity_id,
              subject_id,
              predicate,
              object_value,
              statement,
              kind,
              state,
              evidence_ids,
              producer_type,
              producer_id,
              method_version
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'ADMISSION_QUEUED', %s, %s, %s, %s)
            ON CONFLICT (fingerprint) DO UPDATE SET updated_at = now()
            RETURNING candidate_claim_id
            """,
            (
                candidate.fingerprint,
                candidate.opportunity_id,
                candidate.subject_id,
                candidate.predicate,
                Jsonb(candidate.object_value),
                candidate.statement,
                candidate.kind,
                [evidence_id],
                candidate.producer_type,
                candidate.producer_id,
                candidate.method_version,
            ),
        )
        row = cursor.fetchone()
        if row is None:
            raise RuntimeError("Candidate upsert failed")
        return row["candidate_claim_id"]

    @staticmethod
    def _admit_candidate(
        *,
        cursor: psycopg.Cursor[dict[str, Any]],
        candidate_claim_id: UUID,
        candidate: CandidateArtifact,
        evidence: EvidenceArtifact,
        evidence_id: UUID,
        admission_batch_id: UUID,
        epistemic_class: str,
    ) -> tuple[UUID, bool]:
        cursor.execute(
            """
            INSERT INTO axignal_global.canonical_claims (
              fingerprint,
              subject_id,
              predicate,
              object_value,
              statement,
              evidence_ids,
              valid_from,
              valid_to,
              observed_at,
              epistemic_class,
              admitted_by,
              admission_batch_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'DETERMINISTIC_RUNTIME', %s)
            ON CONFLICT (fingerprint) DO NOTHING
            RETURNING canonical_claim_id
            """,
            (
                candidate.fingerprint,
                candidate.subject_id,
                candidate.predicate,
                Jsonb(candidate.object_value),
                candidate.statement,
                [evidence_id],
                evidence.valid_from,
                evidence.valid_to,
                evidence.observed_at,
                epistemic_class,
                admission_batch_id,
            ),
        )
        row = cursor.fetchone()
        created = row is not None
        if row:
            canonical_claim_id = row["canonical_claim_id"]
        else:
            cursor.execute(
                """
                SELECT canonical_claim_id
                FROM axignal_global.canonical_claims
                WHERE fingerprint = %s
                """,
                (candidate.fingerprint,),
            )
            existing = cursor.fetchone()
            if existing is None:
                raise RuntimeError("Canonical claim admission failed")
            canonical_claim_id = existing["canonical_claim_id"]
        cursor.execute(
            """
            UPDATE axignal_global.candidate_claims
            SET state = 'ADMITTED',
                canonical_claim_id = %s,
                rejection_reasons = '[]'::jsonb,
                updated_at = now()
            WHERE candidate_claim_id = %s
            """,
            (canonical_claim_id, candidate_claim_id),
        )
        if created:
            cursor.execute(
                """
                INSERT INTO axignal_global.claim_state_events (
                  canonical_claim_id,
                  from_state,
                  to_state,
                  reason,
                  admission_batch_id
                ) VALUES (%s, NULL, 'ADMITTED', 'all_deterministic_gates_passed', %s)
                """,
                (canonical_claim_id, admission_batch_id),
            )
        return canonical_claim_id, created

    def fail_run(
        self,
        *,
        tenant_id: UUID,
        run_id: UUID,
        error_code: str,
        error_detail: str,
    ) -> None:
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                UPDATE tenant_private.research_runs
                SET state = 'FAILED',
                    error_code = %s,
                    error_detail = %s,
                    updated_at = now()
                WHERE research_run_id = %s
                """,
                (error_code[:100], error_detail[:1_000], run_id),
            )

    def add_private_knowledge_fixture(
        self,
        *,
        tenant_id: UUID,
        title: str,
        body: str,
        content_hash: str,
    ) -> UUID:
        item_id = uuid4()
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                INSERT INTO tenant_private.knowledge_items (
                  knowledge_item_id,
                  tenant_id,
                  item_type,
                  title,
                  body,
                  content_hash
                ) VALUES (%s, %s, 'NOTE', %s, %s, %s)
                """,
                (item_id, tenant_id, title, body, content_hash),
            )
        return item_id

    def record_intent_event(
        self,
        *,
        tenant_id: UUID,
        event_type: str,
        subject_key: str,
        payload: dict[str, Any],
        occurred_at: datetime,
        expires_at: datetime,
    ) -> UUID:
        event_id = uuid4()
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                INSERT INTO intent_intelligence.intent_events (
                  intent_event_id,
                  tenant_id,
                  event_type,
                  subject_key,
                  payload,
                  occurred_at,
                  expires_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    event_id,
                    tenant_id,
                    event_type,
                    subject_key,
                    Jsonb(payload),
                    occurred_at,
                    expires_at,
                ),
            )
        return event_id

    def debug_count_for_tenant(
        self,
        *,
        tenant_id: UUID,
        table: Literal["research_runs", "knowledge_items"],
    ) -> int:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                sql.SQL("SELECT count(*) AS count FROM tenant_private.{}").format(
                    sql.Identifier(table)
                )
            )
            row = cursor.fetchone()
            return int(row["count"] if row else 0)

    def dump_run_json(self, *, tenant_id: UUID, run_id: UUID) -> str:
        view = self.get_run_view(tenant_id=tenant_id, run_id=run_id)
        if view is None:
            raise LookupError("ResearchRun not found")
        return json.dumps(view, default=str, sort_keys=True)
