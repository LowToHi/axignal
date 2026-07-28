from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any, Literal
from uuid import UUID, uuid4

import psycopg
from psycopg import sql
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from axignal_api.document_proposals import LocalDocumentPipelineResult, canonical_hash
from axignal_api.proposal_queue import (
    DocumentProposalBudget,
    DocumentProposalJob,
    ProposalOutboxEvent,
)

DatabaseRole = Literal["axignal_app", "axignal_proposal_worker"]
SOURCE_ID = "world-bank-rer41"
DOCUMENT_ID = "doc_world_bank_rer41"
PIPELINE_VERSION = "local-document-proposal-pipeline@0.1.0"


class DocumentProposalRepository:
    def __init__(
        self,
        *,
        app_dsn: str | None = None,
        proposal_dsn: str | None = None,
    ) -> None:
        self.app_dsn = app_dsn
        self.proposal_dsn = proposal_dsn

    @contextmanager
    def _cursor(
        self,
        role: DatabaseRole,
        tenant_id: UUID | None = None,
    ) -> Iterator[psycopg.Cursor[dict[str, Any]]]:
        dsn = self.app_dsn if role == "axignal_app" else self.proposal_dsn
        if not dsn:
            raise RuntimeError(f"No database credential configured for role {role}")
        with (
            psycopg.connect(dsn, row_factory=dict_row) as connection,
            connection.cursor() as cursor,
        ):
            if role == "axignal_app":
                cursor.execute(
                    sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(role))
                )
            if tenant_id:
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
    ) -> UUID:
        run_id = uuid4()
        budget = DocumentProposalBudget()
        job = DocumentProposalJob(
            tenant_id=tenant_id,
            research_run_id=run_id,
            source_id=SOURCE_ID,
            document_id=DOCUMENT_ID,
            pipeline_version=PIPELINE_VERSION,
            budget=budget,
        )
        plan = [{
            "source_id": SOURCE_ID,
            "document_id": DOCUMENT_ID,
            "processing": "LOCAL_MODEL_PROPOSAL_ONLY",
        }]
        budgets = budget.as_payload() | {
            "max_duration_seconds": 60,
            "max_cost_minor_units": 0,
            "currency": "EUR",
        }
        with self._cursor("axignal_app", tenant_id) as cursor:
            cursor.execute(
                """
                INSERT INTO tenant_private.research_runs (
                  research_run_id, tenant_id, context_id, opportunity_id,
                  question, state, private_knowledge_authorised, source_plan,
                  budgets, job_kind, document_id
                ) VALUES (%s, %s, %s, %s, %s, 'QUEUED', false, %s, %s,
                          'DOCUMENT_PROPOSAL', %s)
                """,
                (
                    run_id,
                    tenant_id,
                    context_id,
                    opportunity_id,
                    question,
                    Jsonb(plan),
                    Jsonb(budgets),
                    DOCUMENT_ID,
                ),
            )
            cursor.execute(
                """
                INSERT INTO axignal_global.proposal_outbox_events
                  (aggregate_id, event_type, payload)
                VALUES (%s, 'research.document_proposal.requested', %s)
                """,
                (run_id, Jsonb(job.as_payload())),
            )
        return run_id

    def pending_proposal_outbox(self, limit: int = 10) -> list[ProposalOutboxEvent]:
        with self._cursor("axignal_app") as cursor:
            cursor.execute(
                """
                SELECT proposal_outbox_event_id, aggregate_id, event_type,
                       payload, attempts
                FROM axignal_global.proposal_outbox_events
                WHERE status = 'PENDING' AND available_at <= now()
                ORDER BY created_at LIMIT %s
                """,
                (limit,),
            )
            return [
                ProposalOutboxEvent(
                    event_id=row["proposal_outbox_event_id"],
                    aggregate_id=row["aggregate_id"],
                    event_type=row["event_type"],
                    payload=row["payload"],
                    attempts=row["attempts"],
                )
                for row in cursor.fetchall()
            ]

    def mark_proposal_outbox_published(self, event_id: UUID) -> None:
        with self._cursor("axignal_app") as cursor:
            cursor.execute(
                """
                UPDATE axignal_global.proposal_outbox_events
                SET status = 'PUBLISHED', published_at = now(),
                    attempts = attempts + 1
                WHERE proposal_outbox_event_id = %s AND status = 'PENDING'
                """,
                (event_id,),
            )

    def mark_proposal_outbox_failed(self, event_id: UUID, error: str) -> None:
        with self._cursor("axignal_app") as cursor:
            cursor.execute(
                """
                UPDATE axignal_global.proposal_outbox_events
                SET attempts = attempts + 1, last_error = %s,
                    status = CASE WHEN attempts >= 4
                                  THEN 'FAILED' ELSE 'PENDING' END,
                    available_at = now() + interval '30 seconds'
                WHERE proposal_outbox_event_id = %s AND status = 'PENDING'
                """,
                (error[:500], event_id),
            )

    def get_source(self, source_id: str) -> dict[str, Any] | None:
        with self._cursor("axignal_proposal_worker") as cursor:
            cursor.execute(
                "SELECT * FROM axignal_global.sources WHERE source_id = %s",
                (source_id,),
            )
            return cursor.fetchone()

    def get_run_for_worker(
        self,
        *,
        tenant_id: UUID,
        run_id: UUID,
    ) -> dict[str, Any] | None:
        with self._cursor("axignal_proposal_worker", tenant_id) as cursor:
            cursor.execute(
                "SELECT * FROM tenant_private.research_runs "
                "WHERE research_run_id = %s",
                (run_id,),
            )
            return cursor.fetchone()

    def transition_run(self, *, tenant_id: UUID, run_id: UUID, state: str) -> None:
        with self._cursor("axignal_proposal_worker", tenant_id) as cursor:
            cursor.execute(
                "UPDATE tenant_private.research_runs "
                "SET state = %s, updated_at = now() "
                "WHERE research_run_id = %s",
                (state, run_id),
            )
            if cursor.rowcount != 1:
                raise LookupError("Document ResearchRun not found for tenant")

    def persist_result(
        self,
        *,
        tenant_id: UUID,
        run_id: UUID,
        source: dict[str, Any],
        result: LocalDocumentPipelineResult,
    ) -> dict[str, Any]:
        with self._cursor("axignal_proposal_worker", tenant_id) as cursor:
            cursor.execute(
                "SELECT state FROM tenant_private.research_runs "
                "WHERE research_run_id = %s "
                "AND job_kind = 'DOCUMENT_PROPOSAL'",
                (run_id,),
            )
            run = cursor.fetchone()
            if not run:
                raise LookupError("Document ResearchRun not found for persistence")
            if run["state"] == "COMPLETED_PROVISIONAL":
                return {"idempotent_replay": True}

            source_object_id = self._source_object(cursor, source, result)
            self._fragments(cursor, source_object_id, result)
            by_evidence = {
                key: candidate
                for candidate in result.candidate_claims
                for key in candidate.evidence_keys
            }
            evidence_ids = {
                evidence.evidence_key: self._evidence(
                    cursor,
                    source_object_id,
                    evidence,
                    by_evidence[evidence.evidence_key],
                    result,
                )
                for evidence in result.evidence
            }
            candidate_ids = {
                candidate.candidate_claim_id: self._candidate(
                    cursor,
                    candidate,
                    [evidence_ids[key] for key in candidate.evidence_keys],
                )
                for candidate in result.candidate_claims
            }
            package = self._package(
                tenant_id,
                run_id,
                source,
                result,
                evidence_ids,
                candidate_ids,
            )
            package_hash = canonical_hash(package)
            handoff_id = self._handoff(
                cursor,
                tenant_id,
                run_id,
                list(candidate_ids.values()),
                package,
                package_hash,
            )
            dossier_id = self._dossier(
                cursor,
                tenant_id,
                run_id,
                result,
                evidence_ids,
                candidate_ids,
            )
            for evidence_id in evidence_ids.values():
                cursor.execute(
                    """
                    INSERT INTO tenant_private.research_evidence_links
                      (tenant_id, research_run_id, evidence_id, visibility)
                    VALUES (%s, %s, %s, 'GLOBAL_PUBLIC')
                    ON CONFLICT DO NOTHING
                    """,
                    (tenant_id, run_id, evidence_id),
                )
            usage = dict(result.actual_usage) | {
                "documents": 1,
                "model_calls": 1,
                "candidate_claims": len(candidate_ids),
                "evidence_objects": len(evidence_ids),
                "admission_handoffs": 1,
                "canonical_claims": 0,
            }
            cursor.execute(
                """
                UPDATE tenant_private.research_runs
                SET state = 'COMPLETED_PROVISIONAL', actual_usage = %s,
                    evidence_ids = %s, candidate_claim_ids = %s,
                    canonical_claim_ids = '{}'::uuid[], dossier_id = %s,
                    admission_handoff_id = %s, error_code = NULL,
                    error_detail = NULL, updated_at = now()
                WHERE research_run_id = %s
                """,
                (
                    Jsonb(usage),
                    list(evidence_ids.values()),
                    list(candidate_ids.values()),
                    dossier_id,
                    handoff_id,
                    run_id,
                ),
            )
            cursor.execute(
                """
                INSERT INTO axignal_global.outbox_events
                  (aggregate_type, aggregate_id, event_type, payload)
                VALUES ('RESEARCH_RUN', %s,
                        'research.document_proposal.completed', %s)
                """,
                (
                    run_id,
                    Jsonb({
                        "schema_version": 1,
                        "tenant_id": str(tenant_id),
                        "research_run_id": str(run_id),
                        "admission_handoff_id": str(handoff_id),
                        "candidate_claim_ids": [
                            str(item) for item in candidate_ids.values()
                        ],
                        "evidence_ids": [
                            str(item) for item in evidence_ids.values()
                        ],
                        "canonical_claim_ids": [],
                    }),
                ),
            )
        return {
            "source_object_id": source_object_id,
            "evidence_ids": list(evidence_ids.values()),
            "candidate_claim_ids": list(candidate_ids.values()),
            "dossier_id": dossier_id,
            "admission_handoff_id": handoff_id,
            "package_hash": package_hash,
        }

    def record_failure(
        self,
        *,
        job: DocumentProposalJob,
        error_code: str,
        error_detail: str,
        quarantined: bool,
    ) -> None:
        state = "QUARANTINED" if quarantined else "FAILED"
        with self._cursor("axignal_proposal_worker", job.tenant_id) as cursor:
            cursor.execute(
                """
                INSERT INTO axignal_global.proposal_job_failures (
                  tenant_id, research_run_id, job_payload, error_code,
                  error_detail, quarantined
                ) VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    job.tenant_id,
                    job.research_run_id,
                    Jsonb(job.as_payload()),
                    error_code,
                    error_detail[:2_000],
                    quarantined,
                ),
            )
            cursor.execute(
                """
                UPDATE tenant_private.research_runs
                SET state = %s, error_code = %s, error_detail = %s,
                    updated_at = now()
                WHERE research_run_id = %s
                """,
                (state, error_code, error_detail[:2_000], job.research_run_id),
            )

    @staticmethod
    def _source_object(cursor: Any, source: dict[str, Any], result: Any) -> UUID:
        document = result.document
        key = f"document:{document.source_id}:{document.content_hash}"
        cursor.execute(
            """
            INSERT INTO axignal_global.source_objects (
              source_id, retrieval_key, request_url, retrieved_at,
              source_updated_at, http_status, content_type, content_hash,
              raw_payload, rights_snapshot, lineage
            ) VALUES (%s, %s, %s, %s, %s, 200, %s, %s, %s, %s, %s)
            ON CONFLICT (retrieval_key) DO NOTHING
            RETURNING source_object_id
            """,
            (
                document.source_id,
                key,
                document.source_url,
                document.retrieved_at,
                document.published_at,
                document.mime_type,
                document.content_hash,
                Jsonb(document.model_dump(mode="json")),
                Jsonb({
                    "rights_status": source["rights_status"],
                    "license_id": source["license_id"],
                    "attribution_text": source["attribution_text"],
                    "terms_url": source["terms_url"],
                    "dataset_url": source["dataset_url"],
                }),
                Jsonb({
                    "document_id": document.document_id,
                    "pipeline": PIPELINE_VERSION,
                    "retrieval_mode": "FROZEN_FIXTURE",
                }),
            ),
        )
        row = cursor.fetchone()
        if row:
            return row["source_object_id"]
        cursor.execute(
            "SELECT source_object_id FROM axignal_global.source_objects "
            "WHERE retrieval_key = %s",
            (key,),
        )
        return cursor.fetchone()["source_object_id"]

    @staticmethod
    def _fragments(cursor: Any, source_object_id: UUID, result: Any) -> None:
        for item in result.fragments:
            cursor.execute(
                """
                INSERT INTO axignal_global.document_fragments (
                  fragment_id, source_object_id, document_id, ordinal,
                  start_char, end_char, text_content, content_hash,
                  parser_version, security_scan_state
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'CLEAR')
                ON CONFLICT (fragment_id) DO NOTHING
                """,
                (
                    item.fragment_id,
                    source_object_id,
                    item.document_id,
                    item.ordinal,
                    item.start_char,
                    item.end_char,
                    item.text,
                    item.content_hash,
                    item.parser_version,
                ),
            )

    @staticmethod
    def _evidence(
        cursor: Any,
        source_object_id: UUID,
        evidence: Any,
        candidate: Any,
        result: Any,
    ) -> UUID:
        relationship = {
            "SUPPORTING": "SUPPORT",
            "ADVERSE": "CONTRADICT",
            "CONTEXT": "CONTEXT",
        }[candidate.relationship]
        cursor.execute(
            """
            INSERT INTO axignal_global.evidence_objects (
              source_object_id, source_id, evidence_key, title, relationship,
              subject_id, predicate, observed_at, unit, payload,
              content_hash, rights_status, provisional
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, true)
            ON CONFLICT (evidence_key) DO NOTHING RETURNING evidence_id
            """,
            (
                source_object_id,
                evidence.source_id,
                evidence.evidence_key,
                evidence.title,
                relationship,
                candidate.subject_id,
                candidate.predicate,
                result.document.published_at,
                candidate.object_value.get("unit"),
                Jsonb({
                    "document_id": evidence.document_id,
                    "fragment_id": evidence.fragment_id,
                    "text": evidence.text,
                    "quote_hash": evidence.quote_hash,
                    "content_hash": evidence.content_hash,
                }),
                evidence.content_hash,
                evidence.rights_status,
            ),
        )
        row = cursor.fetchone()
        if row:
            return row["evidence_id"]
        cursor.execute(
            "SELECT evidence_id FROM axignal_global.evidence_objects "
            "WHERE evidence_key = %s",
            (evidence.evidence_key,),
        )
        return cursor.fetchone()["evidence_id"]

    @staticmethod
    def _candidate(cursor: Any, candidate: Any, evidence_ids: list[UUID]) -> UUID:
        cursor.execute(
            """
            INSERT INTO axignal_global.candidate_claims (
              fingerprint, opportunity_id, subject_id, predicate, object_value,
              statement, kind, state, evidence_ids, producer_type, producer_id,
              method_version, relationship, model_version, prompt_version,
              extraction_confidence, assumptions, unknowns
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'ADMISSION_QUEUED', %s,
                      'LOCAL_MODEL', %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (fingerprint) DO NOTHING RETURNING candidate_claim_id
            """,
            (
                candidate.fingerprint,
                candidate.opportunity_id,
                candidate.subject_id,
                candidate.predicate,
                Jsonb(candidate.object_value),
                candidate.statement,
                candidate.kind,
                evidence_ids,
                candidate.producer_id,
                candidate.method_version,
                candidate.relationship,
                candidate.model_version,
                candidate.prompt_version,
                candidate.extraction_confidence,
                Jsonb(candidate.assumptions),
                Jsonb(candidate.unknowns),
            ),
        )
        row = cursor.fetchone()
        if row:
            return row["candidate_claim_id"]
        cursor.execute(
            "SELECT candidate_claim_id FROM axignal_global.candidate_claims "
            "WHERE fingerprint = %s",
            (candidate.fingerprint,),
        )
        return cursor.fetchone()["candidate_claim_id"]

    @staticmethod
    def _package(
        tenant_id: UUID,
        run_id: UUID,
        source: dict[str, Any],
        result: Any,
        evidence_ids: dict[str, UUID],
        candidate_ids: dict[str, UUID],
    ) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "tenant_id": str(tenant_id),
            "research_run_id": str(run_id),
            "pipeline_version": result.pipeline_version,
            "document": result.document.model_dump(mode="json"),
            "source": {
                key: source[key]
                for key in (
                    "source_id",
                    "rights_status",
                    "license_id",
                    "admission_state",
                    "kill_switch",
                )
            },
            "fragments": [
                item.model_dump(mode="json") for item in result.fragments
            ],
            "evidence": [
                item.model_dump(mode="json")
                | {"persistent_evidence_id": str(evidence_ids[item.evidence_key])}
                for item in result.evidence
            ],
            "candidate_claims": [
                item.model_dump(mode="json")
                | {
                    "persistent_candidate_claim_id": str(
                        candidate_ids[item.candidate_claim_id]
                    )
                }
                for item in result.candidate_claims
            ],
            "admission_boundary_results": [
                item.model_dump(mode="json") for item in result.admission_results
            ],
            "dossier": result.dossier.model_dump(mode="json"),
            "actual_usage": result.actual_usage,
            "human_review_state": "NOT_REQUESTED",
            "canonical_claim_ids": [],
        }

    @staticmethod
    def _handoff(
        cursor: Any,
        tenant_id: UUID,
        run_id: UUID,
        candidate_ids: list[UUID],
        package: dict[str, Any],
        package_hash: str,
    ) -> UUID:
        cursor.execute(
            """
            INSERT INTO axignal_global.admission_handoffs (
              tenant_id, research_run_id, state, candidate_claim_ids,
              package, package_hash
            ) VALUES (%s, %s, 'PENDING', %s, %s, %s)
            ON CONFLICT (package_hash) DO NOTHING
            RETURNING admission_handoff_id
            """,
            (tenant_id, run_id, candidate_ids, Jsonb(package), package_hash),
        )
        row = cursor.fetchone()
        if row:
            return row["admission_handoff_id"]
        cursor.execute(
            "SELECT admission_handoff_id "
            "FROM axignal_global.admission_handoffs WHERE package_hash = %s",
            (package_hash,),
        )
        return cursor.fetchone()["admission_handoff_id"]

    @staticmethod
    def _dossier(
        cursor: Any,
        tenant_id: UUID,
        run_id: UUID,
        result: Any,
        evidence_ids: dict[str, UUID],
        candidate_ids: dict[str, UUID],
    ) -> UUID:
        dossier_id = uuid4()
        sections = [
            {
                "section_id": item.section_id,
                "title": item.title,
                "text": item.text,
                "status": item.status,
                "evidence_ids": [
                    str(evidence_ids[key])
                    for key in item.evidence_keys
                    if key in evidence_ids
                ],
                "candidate_claim_ids": [
                    str(candidate_ids[key])
                    for key in item.candidate_claim_ids
                    if key in candidate_ids
                ],
                "canonical_claim_ids": [],
            }
            for item in result.dossier.sections
        ]
        cursor.execute(
            """
            INSERT INTO tenant_private.dossiers (
              dossier_id, tenant_id, research_run_id, status, title,
              summary, sections, attribution
            ) VALUES (%s, %s, %s, 'TRACEABLE_PROVISIONAL', %s, %s, %s, %s)
            ON CONFLICT (research_run_id) DO NOTHING RETURNING dossier_id
            """,
            (
                dossier_id,
                tenant_id,
                run_id,
                result.dossier.title,
                result.dossier.summary,
                Jsonb(sections),
                Jsonb(result.dossier.attribution),
            ),
        )
        row = cursor.fetchone()
        if row:
            return row["dossier_id"]
        cursor.execute(
            "SELECT dossier_id FROM tenant_private.dossiers "
            "WHERE research_run_id = %s",
            (run_id,),
        )
        return cursor.fetchone()["dossier_id"]
