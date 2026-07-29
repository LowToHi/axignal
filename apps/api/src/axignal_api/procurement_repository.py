from __future__ import annotations

import copy
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid4

import psycopg
from psycopg import sql
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from axignal_api.connectors.ted_xml import SOURCE_ID, TEDXMLConnector
from axignal_api.document_proposals import canonical_hash
from axignal_api.procurement_persistent_types import (
    LIFECYCLE_PROFILE,
    PERSISTENT_AUTO_PREDICATES,
    PIPELINE_VERSION,
    POLICY_VERSION,
    PRODUCT_PROFILE,
    SanitisedProcurementLifecycle,
    numeric_projection,
    observed_at,
    sanitise_retrieved_lifecycle,
)
from axignal_api.procurement_queue import (
    ProcurementAdmissionJob,
    ProcurementOutboxEvent,
    ProcurementRetrievalJob,
)


class ProcurementRepositoryError(RuntimeError):
    pass


class ProcurementIntegrityError(ProcurementRepositoryError):
    pass


@dataclass(frozen=True)
class ProcurementPersistenceResult:
    admission_handoff_id: UUID
    package_hash: str
    evidence_ids: tuple[UUID, ...]
    candidate_claim_ids: tuple[UUID, ...]
    dossier_id: UUID
    idempotent_replay: bool


@dataclass(frozen=True)
class ProcurementAdmissionResult:
    admission_batch_id: UUID | None
    canonical_claim_ids: tuple[UUID, ...]
    outcomes: tuple[str, ...]
    idempotent_replay: bool
    model_calls: int = 0


@contextmanager
def _cursor(
    dsn: str,
    *,
    role: str | None = None,
    tenant_id: UUID | None = None,
) -> Iterator[psycopg.Cursor[dict[str, Any]]]:
    with (
        psycopg.connect(dsn, row_factory=dict_row) as connection,
        connection.cursor() as cursor,
    ):
        if role is not None:
            cursor.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(role)))
        if tenant_id is not None:
            cursor.execute(
                "SELECT set_config('app.tenant_id', %s, true)",
                (str(tenant_id),),
            )
        yield cursor


class ProcurementAppRepository:
    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    def create_run(
        self,
        *,
        tenant_id: UUID,
        context_id: str,
        opportunity_id: str,
        question: str,
        publication_numbers: tuple[str, ...],
    ) -> UUID:
        run_id = uuid4()
        source_plan = [
            {
                "source_id": SOURCE_ID,
                "publication_numbers": list(publication_numbers),
                "priority": 1,
                "purpose": "Official TED eForms lifecycle evidence",
                "rights_scope": "DERIVED_NON_PERSONAL_ONLY",
            }
        ]
        budgets = {
            "max_api_requests": len(publication_numbers),
            "max_documents": len(publication_numbers),
            "max_response_bytes": 2_097_152 * len(publication_numbers),
            "max_duration_seconds": 90,
            "max_model_calls": 0,
        }
        payload = ProcurementRetrievalJob(
            tenant_id=tenant_id,
            research_run_id=run_id,
            publication_numbers=publication_numbers,
        ).as_payload()
        with _cursor(self.dsn, role="axignal_app", tenant_id=tenant_id) as cursor:
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
                  budgets,
                  job_kind
                ) VALUES (%s, %s, %s, %s, %s, 'QUEUED', false, %s, %s, 'PROCUREMENT_TED')
                """,
                (
                    run_id,
                    tenant_id,
                    context_id,
                    opportunity_id,
                    question,
                    Jsonb(source_plan),
                    Jsonb(budgets),
                ),
            )
            cursor.execute(
                """
                INSERT INTO axignal_global.procurement_retrieval_outbox_events (
                  aggregate_id,
                  event_type,
                  payload
                ) VALUES (%s, 'research.procurement.requested', %s)
                """,
                (run_id, Jsonb(payload)),
            )
        return run_id

    def pending_retrieval_outbox(self, *, limit: int) -> list[ProcurementOutboxEvent]:
        with _cursor(self.dsn, role="axignal_app") as cursor:
            return _pending_outbox(
                cursor,
                table="axignal_global.procurement_retrieval_outbox_events",
                id_column="procurement_retrieval_outbox_event_id",
                limit=limit,
            )

    def mark_retrieval_outbox_published(self, event_id: UUID) -> None:
        with _cursor(self.dsn, role="axignal_app") as cursor:
            _mark_outbox_published(
                cursor,
                table="axignal_global.procurement_retrieval_outbox_events",
                id_column="procurement_retrieval_outbox_event_id",
                event_id=event_id,
            )

    def mark_retrieval_outbox_failed(self, event_id: UUID, error: str) -> None:
        with _cursor(self.dsn, role="axignal_app") as cursor:
            _mark_outbox_failed(
                cursor,
                table="axignal_global.procurement_retrieval_outbox_events",
                id_column="procurement_retrieval_outbox_event_id",
                event_id=event_id,
                error=error,
            )


class ProcurementRetrievalRepository:
    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    def pending_retrieval_outbox(self, *, limit: int) -> list[ProcurementOutboxEvent]:
        with _cursor(self.dsn) as cursor:
            return _pending_outbox(
                cursor,
                table="axignal_global.procurement_retrieval_outbox_events",
                id_column="procurement_retrieval_outbox_event_id",
                limit=limit,
            )

    def mark_retrieval_outbox_published(self, event_id: UUID) -> None:
        with _cursor(self.dsn) as cursor:
            _mark_outbox_published(
                cursor,
                table="axignal_global.procurement_retrieval_outbox_events",
                id_column="procurement_retrieval_outbox_event_id",
                event_id=event_id,
            )

    def mark_retrieval_outbox_failed(self, event_id: UUID, error: str) -> None:
        with _cursor(self.dsn) as cursor:
            _mark_outbox_failed(
                cursor,
                table="axignal_global.procurement_retrieval_outbox_events",
                id_column="procurement_retrieval_outbox_event_id",
                event_id=event_id,
                error=error,
            )

    def load_run(self, job: ProcurementRetrievalJob) -> dict[str, Any] | None:
        with _cursor(self.dsn, tenant_id=job.tenant_id) as cursor:
            cursor.execute(
                """
                SELECT * FROM tenant_private.research_runs
                WHERE research_run_id = %s AND tenant_id = %s
                """,
                (job.research_run_id, job.tenant_id),
            )
            return cursor.fetchone()

    def load_source(self) -> dict[str, Any] | None:
        with _cursor(self.dsn) as cursor:
            cursor.execute(
                "SELECT * FROM axignal_global.sources WHERE source_id = %s",
                (SOURCE_ID,),
            )
            return cursor.fetchone()

    def transition(self, job: ProcurementRetrievalJob, state: str) -> None:
        with _cursor(self.dsn, tenant_id=job.tenant_id) as cursor:
            cursor.execute(
                """
                UPDATE tenant_private.research_runs
                SET state = %s, updated_at = now()
                WHERE research_run_id = %s AND tenant_id = %s
                """,
                (state, job.research_run_id, job.tenant_id),
            )
            if cursor.rowcount != 1:
                raise LookupError("Procurement ResearchRun is absent")

    def persist_lifecycle(
        self,
        *,
        job: ProcurementRetrievalJob,
        lifecycle: SanitisedProcurementLifecycle,
        source: dict[str, Any],
        fail_after_first_evidence: bool = False,
    ) -> ProcurementPersistenceResult:
        with _cursor(self.dsn, tenant_id=job.tenant_id) as cursor:
            cursor.execute(
                """
                SELECT * FROM tenant_private.research_runs
                WHERE research_run_id = %s AND tenant_id = %s
                FOR UPDATE
                """,
                (job.research_run_id, job.tenant_id),
            )
            run = cursor.fetchone()
            if run is None or run["job_kind"] != "PROCUREMENT_TED":
                raise ProcurementIntegrityError("Procurement ResearchRun boundary differs")
            if run["admission_handoff_id"] is not None:
                return self._existing_persistence(cursor, run["admission_handoff_id"])
            if tuple(job.publication_numbers) != tuple(
                run["source_plan"][0]["publication_numbers"]
            ):
                raise ProcurementIntegrityError("Procurement source plan differs from job")

            source_config = source.get("config") or {}
            _assert_product_source(source, source_config)
            source_object_ids: dict[str, UUID] = {}
            for notice in lifecycle.notices:
                retrieval_key = (
                    f"ted:{notice.publication_number}:"
                    f"{notice.raw_content_hash.removeprefix('sha256:')}"
                )
                rights_snapshot = {
                    "source_id": source["source_id"],
                    "rights_status": source["rights_status"],
                    "license_id": source["license_id"],
                    "attribution_text": source["attribution_text"],
                    "terms_url": source["terms_url"],
                    "dataset_url": source["dataset_url"],
                    "last_reviewed_at": source["last_reviewed_at"].isoformat(),
                    "rights_scope": "DERIVED_NON_PERSONAL_ONLY",
                    "raw_xml_persistence": False,
                    "raw_xml_redistribution": False,
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
                    ) VALUES (%s, %s, %s, now(), %s, 200, 'application/xml', %s, %s, %s, %s)
                    ON CONFLICT (retrieval_key) DO NOTHING
                    RETURNING source_object_id
                    """,
                    (
                        SOURCE_ID,
                        retrieval_key,
                        notice.request_url,
                        observed_at(notice.issue_date),
                        notice.raw_content_hash,
                        Jsonb(notice.payload()),
                        Jsonb(rights_snapshot),
                        Jsonb(
                            {
                                "notice_reference": notice.notice_reference,
                                "previous_notice_reference": notice.previous_notice_reference,
                                "procedure_identifier": notice.procedure_identifier,
                                "lifecycle_kind": notice.lifecycle_kind,
                                "parser_profile": LIFECYCLE_PROFILE,
                                "raw_xml_persisted": False,
                            }
                        ),
                    ),
                )
                row = cursor.fetchone()
                if row is None:
                    cursor.execute(
                        """
                        SELECT source_object_id FROM axignal_global.source_objects
                        WHERE retrieval_key = %s
                        """,
                        (retrieval_key,),
                    )
                    row = cursor.fetchone()
                if row is None:
                    raise ProcurementIntegrityError("TED Source Object upsert failed")
                source_object_id = row["source_object_id"]
                source_object_ids[notice.notice_reference] = source_object_id
                cursor.execute(
                    """
                    INSERT INTO axignal_global.procurement_notice_versions (
                      source_object_id,
                      source_id,
                      publication_number,
                      notice_reference,
                      procedure_identifier,
                      lifecycle_kind,
                      previous_notice_reference,
                      issue_date,
                      raw_content_hash,
                      parser_profile,
                      sanitised_payload,
                      personal_field_element_count,
                      raw_xml_persisted
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, false)
                    ON CONFLICT (notice_reference) DO NOTHING
                    """,
                    (
                        source_object_id,
                        SOURCE_ID,
                        notice.publication_number,
                        notice.notice_reference,
                        notice.procedure_identifier,
                        notice.lifecycle_kind,
                        notice.previous_notice_reference,
                        notice.issue_date,
                        notice.raw_content_hash,
                        LIFECYCLE_PROFILE,
                        Jsonb(notice.payload()),
                        notice.personal_field_element_count,
                    ),
                )

            evidence_ids: list[UUID] = []
            candidate_ids: list[UUID] = []
            evidence_package: list[dict[str, Any]] = []
            candidate_package: list[dict[str, Any]] = []
            for index, claim in enumerate(lifecycle.claims):
                source_object_id = source_object_ids[claim.notice_reference]
                numeric_value, unit = numeric_projection(claim)
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
                    ) VALUES (%s, %s, %s, %s, 'SUPPORT', %s, %s, %s, NULL, NULL,
                              %s, %s, %s, %s, 'CC0_DERIVED_NON_PERSONAL', true)
                    ON CONFLICT (evidence_key) DO NOTHING
                    RETURNING evidence_id
                    """,
                    (
                        source_object_id,
                        SOURCE_ID,
                        claim.evidence_key,
                        f"TED observed fact · {claim.predicate}",
                        f"procurement:{claim.subject_key}",
                        claim.predicate,
                        observed_at(claim.issue_date),
                        numeric_value,
                        unit,
                        Jsonb(claim.evidence_payload()),
                        claim.evidence_content_hash,
                    ),
                )
                evidence_row = cursor.fetchone()
                if evidence_row is None:
                    cursor.execute(
                        "SELECT evidence_id FROM axignal_global.evidence_objects "
                        "WHERE evidence_key = %s",
                        (claim.evidence_key,),
                    )
                    evidence_row = cursor.fetchone()
                if evidence_row is None:
                    raise ProcurementIntegrityError("TED Evidence Object upsert failed")
                evidence_id = evidence_row["evidence_id"]
                evidence_ids.append(evidence_id)
                if fail_after_first_evidence and index == 0:
                    raise RuntimeError("TEST_FAILPOINT_AFTER_FIRST_TED_EVIDENCE")

                object_value = claim.candidate_object_value()
                statement = claim.deterministic_statement()
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
                      method_version,
                      relationship,
                      assumptions,
                      unknowns
                    ) VALUES (%s, %s, %s, %s, %s, %s, 'FACT', 'ADMISSION_QUEUED',
                              %s, 'DETERMINISTIC_PARSER', 'ted-eforms-parser', %s,
                              'SUPPORT', '[]'::jsonb, '[]'::jsonb)
                    ON CONFLICT (fingerprint) DO UPDATE SET updated_at = now()
                    RETURNING candidate_claim_id
                    """,
                    (
                        claim.fingerprint,
                        run["opportunity_id"],
                        f"procurement:{claim.subject_key}",
                        claim.predicate,
                        Jsonb(object_value),
                        statement,
                        [evidence_id],
                        LIFECYCLE_PROFILE,
                    ),
                )
                candidate_id = cursor.fetchone()["candidate_claim_id"]
                candidate_ids.append(candidate_id)
                evidence_package.append(
                    {
                        "persistent_evidence_id": str(evidence_id),
                        "evidence_key": claim.evidence_key,
                        "claim_fingerprint": claim.fingerprint,
                        "predicate": claim.predicate,
                        "subject_id": f"procurement:{claim.subject_key}",
                        "source_path": claim.source_path,
                        "value_hash": claim.value_hash,
                        "content_hash": claim.evidence_content_hash,
                        "notice_reference": claim.notice_reference,
                        "raw_content_hash": claim.raw_content_hash,
                    }
                )
                candidate_package.append(
                    {
                        "persistent_candidate_claim_id": str(candidate_id),
                        "fingerprint": claim.fingerprint,
                        "predicate": claim.predicate,
                        "subject_id": f"procurement:{claim.subject_key}",
                        "object_value": object_value,
                        "statement": statement,
                        "evidence_id": str(evidence_id),
                        "producer_type": "DETERMINISTIC_PARSER",
                        "method_version": LIFECYCLE_PROFILE,
                    }
                )

            dossier_id = uuid4()
            sections = _build_dossier_sections(lifecycle, evidence_ids, candidate_ids)
            attribution = {
                "source_id": SOURCE_ID,
                "source_name": source["name"],
                "license_id": source["license_id"],
                "attribution_text": source["attribution_text"],
                "terms_url": source["terms_url"],
                "changes": (
                    "AXIGNAL parsed the official XML, removed personal and identity values, "
                    "normalised bounded fields and preserved notice lineage."
                ),
                "raw_xml_redistributed": False,
            }
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
                ) VALUES (%s, %s, %s, 'TRACEABLE_PROVISIONAL', %s, %s, %s, %s)
                """,
                (
                    dossier_id,
                    job.tenant_id,
                    job.research_run_id,
                    "Expediente TED no personal",
                    (
                        "AXIGNAL conservó una proyección no personal del ciclo oficial TED; "
                        "la admisión canónica permanece pendiente de rederivación independiente."
                    ),
                    Jsonb(sections),
                    Jsonb(attribution),
                ),
            )
            for evidence_id in evidence_ids:
                cursor.execute(
                    """
                    INSERT INTO tenant_private.research_evidence_links (
                      tenant_id, research_run_id, evidence_id, visibility
                    ) VALUES (%s, %s, %s, 'GLOBAL_PUBLIC')
                    ON CONFLICT DO NOTHING
                    """,
                    (job.tenant_id, job.research_run_id, evidence_id),
                )

            usage = {
                "api_requests": sum(
                    item.retrieval_mode == "LIVE_DIRECT_XML" for item in lifecycle.notices
                ),
                "fixture_reads": sum(
                    item.retrieval_mode == "FROZEN_FIXTURE" for item in lifecycle.notices
                ),
                "documents": len(lifecycle.notices),
                "model_calls": 0,
                "personal_field_elements_observed": lifecycle.personal_field_element_count,
                "personal_values_persisted": False,
                "raw_xml_persisted": False,
                "excluded_claims": lifecycle.excluded_claim_count,
                "lineage_hash": lifecycle.lineage_hash,
            }
            package = {
                "schema_version": 1,
                "tenant_id": str(job.tenant_id),
                "research_run_id": str(job.research_run_id),
                "pipeline_version": PIPELINE_VERSION,
                "policy_version": POLICY_VERSION,
                "source": {
                    "source_id": SOURCE_ID,
                    "product_profile": PRODUCT_PROFILE,
                    "rights_status": source["rights_status"],
                    "license_id": source["license_id"],
                    "rights_scope": "DERIVED_NON_PERSONAL_ONLY",
                    "kill_switch": source["kill_switch"],
                },
                "publication_numbers": list(job.publication_numbers),
                "notices": [item.payload() for item in lifecycle.notices],
                "lineage_hash": lifecycle.lineage_hash,
                "evidence": evidence_package,
                "candidate_claims": candidate_package,
                "dossier": {
                    "dossier_id": str(dossier_id),
                    "status": "TRACEABLE_PROVISIONAL",
                },
                "actual_usage": usage,
                "canonical_claim_ids": [],
                "personal_values_persisted": False,
                "raw_xml_persisted": False,
            }
            package_hash = canonical_hash(package)
            cursor.execute(
                """
                INSERT INTO axignal_global.admission_handoffs (
                  tenant_id,
                  research_run_id,
                  state,
                  candidate_claim_ids,
                  package,
                  package_hash
                ) VALUES (%s, %s, 'PENDING', %s, %s, %s)
                RETURNING admission_handoff_id
                """,
                (
                    job.tenant_id,
                    job.research_run_id,
                    candidate_ids,
                    Jsonb(package),
                    package_hash,
                ),
            )
            handoff_id = cursor.fetchone()["admission_handoff_id"]
            cursor.execute(
                """
                UPDATE tenant_private.research_runs
                SET state = 'HANDOFF_PENDING',
                    actual_usage = %s,
                    evidence_ids = %s,
                    candidate_claim_ids = %s,
                    canonical_claim_ids = '{}'::uuid[],
                    dossier_id = %s,
                    admission_handoff_id = %s,
                    error_code = NULL,
                    error_detail = NULL,
                    updated_at = now()
                WHERE research_run_id = %s AND tenant_id = %s
                """,
                (
                    Jsonb(usage),
                    evidence_ids,
                    candidate_ids,
                    dossier_id,
                    handoff_id,
                    job.research_run_id,
                    job.tenant_id,
                ),
            )
            return ProcurementPersistenceResult(
                admission_handoff_id=handoff_id,
                package_hash=package_hash,
                evidence_ids=tuple(evidence_ids),
                candidate_claim_ids=tuple(candidate_ids),
                dossier_id=dossier_id,
                idempotent_replay=False,
            )

    @staticmethod
    def _existing_persistence(
        cursor: psycopg.Cursor[dict[str, Any]], handoff_id: UUID
    ) -> ProcurementPersistenceResult:
        cursor.execute(
            "SELECT * FROM axignal_global.admission_handoffs WHERE admission_handoff_id = %s",
            (handoff_id,),
        )
        handoff = cursor.fetchone()
        if handoff is None:
            raise ProcurementIntegrityError("Existing TED handoff is absent")
        package = handoff["package"]
        return ProcurementPersistenceResult(
            admission_handoff_id=handoff_id,
            package_hash=handoff["package_hash"],
            evidence_ids=tuple(
                UUID(item["persistent_evidence_id"]) for item in package["evidence"]
            ),
            candidate_claim_ids=tuple(handoff["candidate_claim_ids"]),
            dossier_id=UUID(package["dossier"]["dossier_id"]),
            idempotent_replay=True,
        )

    def fail(self, job: ProcurementRetrievalJob, exc: Exception) -> None:
        with _cursor(self.dsn, tenant_id=job.tenant_id) as cursor:
            cursor.execute(
                """
                INSERT INTO axignal_global.procurement_job_failures (
                  stage, tenant_id, research_run_id, job_payload,
                  error_code, error_detail, quarantined
                ) VALUES ('RETRIEVAL', %s, %s, %s, %s, %s, true)
                """,
                (
                    job.tenant_id,
                    job.research_run_id,
                    Jsonb(job.as_payload()),
                    exc.__class__.__name__.upper(),
                    str(exc)[:2000],
                ),
            )
            cursor.execute(
                """
                UPDATE tenant_private.research_runs
                SET state = 'QUARANTINED', error_code = %s, error_detail = %s,
                    updated_at = now()
                WHERE research_run_id = %s AND tenant_id = %s
                """,
                (
                    exc.__class__.__name__.upper(),
                    str(exc)[:2000],
                    job.research_run_id,
                    job.tenant_id,
                ),
            )


class ProcurementAdmissionRepository:
    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    def pending_admission_outbox(self, *, limit: int) -> list[ProcurementOutboxEvent]:
        with _cursor(self.dsn) as cursor:
            return _pending_outbox(
                cursor,
                table="axignal_global.procurement_admission_outbox_events",
                id_column="procurement_admission_outbox_event_id",
                limit=limit,
            )

    def mark_admission_outbox_published(self, event_id: UUID) -> None:
        with _cursor(self.dsn) as cursor:
            _mark_outbox_published(
                cursor,
                table="axignal_global.procurement_admission_outbox_events",
                id_column="procurement_admission_outbox_event_id",
                event_id=event_id,
            )

    def mark_admission_outbox_failed(self, event_id: UUID, error: str) -> None:
        with _cursor(self.dsn) as cursor:
            _mark_outbox_failed(
                cursor,
                table="axignal_global.procurement_admission_outbox_events",
                id_column="procurement_admission_outbox_event_id",
                event_id=event_id,
                error=error,
            )

    def decide(
        self,
        *,
        job: ProcurementAdmissionJob,
        connector: TEDXMLConnector,
        fail_after_first_canonical: bool = False,
    ) -> ProcurementAdmissionResult:
        retrieved = tuple(connector.fetch(item) for item in job.publication_numbers)
        rederived = sanitise_retrieved_lifecycle(retrieved)
        rederived_claims = {item.fingerprint: item for item in rederived.claims}
        with _cursor(self.dsn, tenant_id=job.tenant_id) as cursor:
            cursor.execute(
                """
                SELECT * FROM axignal_global.admission_handoffs
                WHERE admission_handoff_id = %s AND tenant_id = %s
                  AND research_run_id = %s
                FOR UPDATE
                """,
                (job.admission_handoff_id, job.tenant_id, job.research_run_id),
            )
            handoff = cursor.fetchone()
            if handoff is None:
                raise ProcurementIntegrityError("TED admission handoff is absent")
            if handoff["state"] != "PENDING":
                return self._existing_admission(cursor, job.admission_handoff_id)
            package = handoff["package"]
            self._validate_package(package, handoff["package_hash"], job, rederived)
            cursor.execute(
                """
                SELECT * FROM tenant_private.research_runs
                WHERE research_run_id = %s AND tenant_id = %s
                FOR UPDATE
                """,
                (job.research_run_id, job.tenant_id),
            )
            run = cursor.fetchone()
            if run is None or run["job_kind"] != "PROCUREMENT_TED":
                raise ProcurementIntegrityError("TED admission ResearchRun boundary differs")
            if run["admission_handoff_id"] != job.admission_handoff_id:
                raise ProcurementIntegrityError("TED admission handoff reference differs")
            cursor.execute(
                "SELECT * FROM axignal_global.sources WHERE source_id = %s",
                (SOURCE_ID,),
            )
            source = cursor.fetchone()
            if source is None:
                raise ProcurementIntegrityError("TED source record is absent")
            _assert_product_source(source, source.get("config") or {})

            candidate_ids = list(handoff["candidate_claim_ids"])
            cursor.execute(
                """
                SELECT * FROM axignal_global.candidate_claims
                WHERE candidate_claim_id = ANY(%s)
                """,
                (candidate_ids,),
            )
            candidate_rows = {
                row["candidate_claim_id"]: row for row in cursor.fetchall()
            }
            cursor.execute(
                """
                SELECT * FROM axignal_global.evidence_objects
                WHERE evidence_id = ANY(%s)
                """,
                (
                    [
                        UUID(item["persistent_evidence_id"])
                        for item in package["evidence"]
                    ],
                ),
            )
            evidence_rows = {row["evidence_id"]: row for row in cursor.fetchall()}
            if len(candidate_rows) != len(candidate_ids):
                raise ProcurementIntegrityError("TED persisted candidate set is incomplete")
            if len(evidence_rows) != len(package["evidence"]):
                raise ProcurementIntegrityError("TED persisted evidence set is incomplete")

            batch_id = uuid4()
            cursor.execute(
                """
                INSERT INTO axignal_global.admission_batches (
                  admission_batch_id, policy_version, state, candidate_claim_ids
                ) VALUES (%s, %s, 'PENDING', %s)
                """,
                (batch_id, POLICY_VERSION, candidate_ids),
            )
            canonical_ids: list[UUID] = []
            outcomes: list[str] = []
            for index, packaged in enumerate(package["candidate_claims"]):
                candidate_id = UUID(packaged["persistent_candidate_claim_id"])
                candidate = candidate_rows.get(candidate_id)
                if candidate is None:
                    raise ProcurementIntegrityError("TED candidate is missing")
                claim = rederived_claims.get(packaged["fingerprint"])
                if claim is None:
                    raise ProcurementIntegrityError("TED candidate failed independent rederivation")
                self._validate_candidate(candidate, packaged, claim)
                evidence_id = UUID(packaged["evidence_id"])
                evidence = evidence_rows.get(evidence_id)
                if evidence is None:
                    raise ProcurementIntegrityError("TED candidate evidence is missing")
                self._validate_evidence(evidence, packaged, claim)
                canonical_id, duplicate = self._write_canonical(
                    cursor,
                    batch_id=batch_id,
                    candidate=candidate,
                    evidence=evidence,
                )
                outcome = "DUPLICATE" if duplicate else "ADMITTED_REDERIVED"
                canonical_ids.append(canonical_id)
                outcomes.append(outcome)
                cursor.execute(
                    """
                    UPDATE axignal_global.candidate_claims
                    SET state = 'ADMITTED', canonical_claim_id = %s,
                        rejection_reasons = '[]'::jsonb, updated_at = now()
                    WHERE candidate_claim_id = %s
                    """,
                    (canonical_id, candidate_id),
                )
                cursor.execute(
                    """
                    INSERT INTO axignal_global.admission_decisions (
                      admission_batch_id,
                      admission_handoff_id,
                      candidate_claim_id,
                      outcome,
                      policy_version,
                      gate_results,
                      rejection_reasons,
                      canonical_claim_id,
                      rederived_fingerprint,
                      human_review_required
                    ) VALUES (%s, %s, %s, %s, %s, %s, '[]'::jsonb, %s, %s, false)
                    """,
                    (
                        batch_id,
                        job.admission_handoff_id,
                        candidate_id,
                        outcome,
                        POLICY_VERSION,
                        Jsonb(
                            {
                                "SOURCE_PRODUCT_ADMITTED": True,
                                "SOURCE_KILL_SWITCH_OFF": True,
                                "RIGHTS_DERIVED_NON_PERSONAL": True,
                                "RAW_XML_HASH_MATCH": True,
                                "INDEPENDENT_REPARSE": True,
                                "LINEAGE_MATCH": True,
                                "PERSONAL_VALUES_EXCLUDED": True,
                                "PREDICATE_ALLOWED": True,
                                "CANDIDATE_EXACT_MATCH": True,
                            }
                        ),
                        canonical_id,
                        claim.fingerprint,
                    ),
                )
                if fail_after_first_canonical and index == 0:
                    raise RuntimeError("TEST_FAILPOINT_AFTER_FIRST_TED_CANONICAL")

            unique_canonical = list(dict.fromkeys(canonical_ids))
            summary = {
                "policy_version": POLICY_VERSION,
                "decision_count": len(outcomes),
                "outcomes": outcomes,
                "canonical_claim_ids": [str(item) for item in unique_canonical],
                "model_calls": 0,
                "personal_values_persisted": False,
                "raw_xml_persisted": False,
                "independent_redownload": True,
            }
            cursor.execute(
                """
                UPDATE axignal_global.admission_batches
                SET state = 'DECIDED', decision_summary = %s, decided_at = now()
                WHERE admission_batch_id = %s
                """,
                (Jsonb(summary), batch_id),
            )
            cursor.execute(
                """
                UPDATE axignal_global.admission_handoffs
                SET state = 'CONSUMED', consumed_at = now()
                WHERE admission_handoff_id = %s AND state = 'PENDING'
                """,
                (job.admission_handoff_id,),
            )
            usage = copy.deepcopy(run["actual_usage"] or {})
            usage.update(
                {
                    "admission_runtime_calls": 1,
                    "admission_model_calls": 0,
                    "admission_decisions": len(outcomes),
                    "canonical_claims": len(unique_canonical),
                    "independent_xml_redownloads": len(retrieved),
                    "raw_xml_persisted": False,
                    "personal_values_persisted": False,
                }
            )
            cursor.execute(
                """
                UPDATE tenant_private.research_runs
                SET state = 'COMPLETED', canonical_claim_ids = %s,
                    admission_batch_id = %s, actual_usage = %s,
                    error_code = NULL, error_detail = NULL, updated_at = now()
                WHERE research_run_id = %s AND tenant_id = %s
                """,
                (
                    unique_canonical,
                    batch_id,
                    Jsonb(usage),
                    job.research_run_id,
                    job.tenant_id,
                ),
            )
            if run["dossier_id"] is not None:
                cursor.execute(
                    """
                    UPDATE tenant_private.dossiers
                    SET status = 'TRACEABLE_WITH_ADMITTED_FACTS'
                    WHERE dossier_id = %s
                    """,
                    (run["dossier_id"],),
                )
            return ProcurementAdmissionResult(
                admission_batch_id=batch_id,
                canonical_claim_ids=tuple(unique_canonical),
                outcomes=tuple(outcomes),
                idempotent_replay=False,
            )

    @staticmethod
    def _validate_package(
        package: dict[str, Any],
        stored_hash: str,
        job: ProcurementAdmissionJob,
        rederived: SanitisedProcurementLifecycle,
    ) -> None:
        expected_keys = {
            "schema_version",
            "tenant_id",
            "research_run_id",
            "pipeline_version",
            "policy_version",
            "source",
            "publication_numbers",
            "notices",
            "lineage_hash",
            "evidence",
            "candidate_claims",
            "dossier",
            "actual_usage",
            "canonical_claim_ids",
            "personal_values_persisted",
            "raw_xml_persisted",
        }
        if set(package) != expected_keys or package.get("schema_version") != 1:
            raise ProcurementIntegrityError("TED admission package schema differs")
        if canonical_hash(package) != stored_hash or stored_hash != job.expected_package_hash:
            raise ProcurementIntegrityError("TED admission package hash differs")
        if package["tenant_id"] != str(job.tenant_id):
            raise ProcurementIntegrityError("TED admission package tenant differs")
        if package["research_run_id"] != str(job.research_run_id):
            raise ProcurementIntegrityError("TED admission package ResearchRun differs")
        if package["pipeline_version"] != PIPELINE_VERSION:
            raise ProcurementIntegrityError("TED pipeline version differs")
        if package["policy_version"] != POLICY_VERSION:
            raise ProcurementIntegrityError("TED policy version differs")
        if package["publication_numbers"] != list(job.publication_numbers):
            raise ProcurementIntegrityError("TED publication-number set differs")
        if package["lineage_hash"] != rederived.lineage_hash:
            raise ProcurementIntegrityError("TED lifecycle hash differs after redownload")
        if package["canonical_claim_ids"] != []:
            raise ProcurementIntegrityError("TED handoff already contains canonical claims")
        if package["personal_values_persisted"] is not False:
            raise ProcurementIntegrityError("TED handoff claims personal values were persisted")
        if package["raw_xml_persisted"] is not False:
            raise ProcurementIntegrityError("TED handoff claims raw XML was persisted")
        expected_hashes = {
            item.publication_number: item.raw_content_hash for item in rederived.notices
        }
        for notice in package["notices"]:
            if expected_hashes.get(notice["publication_number"]) != notice["raw_content_hash"]:
                raise ProcurementIntegrityError("TED raw XML hash differs after redownload")

    @staticmethod
    def _validate_candidate(
        candidate: dict[str, Any],
        packaged: dict[str, Any],
        claim: Any,
    ) -> None:
        checks = {
            candidate["fingerprint"] == packaged["fingerprint"] == claim.fingerprint,
            candidate["predicate"] == packaged["predicate"] == claim.predicate,
            candidate["subject_id"] == packaged["subject_id"],
            candidate["object_value"]
            == packaged["object_value"]
            == claim.candidate_object_value(),
            candidate["statement"]
            == packaged["statement"]
            == claim.deterministic_statement(),
            candidate["producer_type"] == "DETERMINISTIC_PARSER",
            candidate["method_version"] == LIFECYCLE_PROFILE,
            candidate["predicate"] in PERSISTENT_AUTO_PREDICATES,
        }
        if False in checks:
            raise ProcurementIntegrityError("TED Candidate Claim differs from rederivation")

    @staticmethod
    def _validate_evidence(
        evidence: dict[str, Any],
        packaged: dict[str, Any],
        claim: Any,
    ) -> None:
        if UUID(packaged["evidence_id"]) != evidence["evidence_id"]:
            raise ProcurementIntegrityError("TED Evidence Object ID differs")
        if evidence["evidence_key"] != claim.evidence_key:
            raise ProcurementIntegrityError("TED Evidence Object key differs")
        if evidence["content_hash"] != claim.evidence_content_hash:
            raise ProcurementIntegrityError("TED Evidence Object hash differs")
        if evidence["payload"] != claim.evidence_payload():
            raise ProcurementIntegrityError("TED Evidence Object payload differs")
        if evidence["rights_status"] != "CC0_DERIVED_NON_PERSONAL":
            raise ProcurementIntegrityError("TED Evidence Object rights scope differs")

    @staticmethod
    def _write_canonical(
        cursor: psycopg.Cursor[dict[str, Any]],
        *,
        batch_id: UUID,
        candidate: dict[str, Any],
        evidence: dict[str, Any],
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
              state,
              admitted_by,
              admission_batch_id
            ) VALUES (%s, %s, %s, %s, %s, %s, NULL, NULL, %s,
                      'OBSERVED_FACT', 'ADMITTED', 'DETERMINISTIC_RUNTIME', %s)
            ON CONFLICT (fingerprint) DO NOTHING
            RETURNING canonical_claim_id
            """,
            (
                candidate["fingerprint"],
                candidate["subject_id"],
                candidate["predicate"],
                Jsonb(candidate["object_value"]),
                candidate["statement"],
                [evidence["evidence_id"]],
                evidence["observed_at"],
                batch_id,
            ),
        )
        row = cursor.fetchone()
        if row is not None:
            canonical_id = row["canonical_claim_id"]
            cursor.execute(
                """
                INSERT INTO axignal_global.claim_state_events (
                  canonical_claim_id, from_state, to_state, reason, admission_batch_id
                ) VALUES (%s, NULL, 'ADMITTED', %s, %s)
                """,
                (
                    canonical_id,
                    "TED non-personal fact independently redownloaded and rederived",
                    batch_id,
                ),
            )
            return canonical_id, False
        cursor.execute(
            "SELECT canonical_claim_id FROM axignal_global.canonical_claims WHERE fingerprint = %s",
            (candidate["fingerprint"],),
        )
        existing = cursor.fetchone()
        if existing is None:
            raise ProcurementIntegrityError("TED canonical convergence failed")
        return existing["canonical_claim_id"], True

    @staticmethod
    def _existing_admission(
        cursor: psycopg.Cursor[dict[str, Any]], handoff_id: UUID
    ) -> ProcurementAdmissionResult:
        cursor.execute(
            """
            SELECT admission_batch_id, outcome, canonical_claim_id
            FROM axignal_global.admission_decisions
            WHERE admission_handoff_id = %s
            ORDER BY created_at, admission_decision_id
            """,
            (handoff_id,),
        )
        rows = cursor.fetchall()
        if not rows:
            raise ProcurementIntegrityError("Consumed TED handoff has no decisions")
        return ProcurementAdmissionResult(
            admission_batch_id=rows[0]["admission_batch_id"],
            canonical_claim_ids=tuple(
                dict.fromkeys(
                    row["canonical_claim_id"]
                    for row in rows
                    if row["canonical_claim_id"] is not None
                )
            ),
            outcomes=tuple(row["outcome"] for row in rows),
            idempotent_replay=True,
        )

    def fail(self, job: ProcurementAdmissionJob, exc: Exception) -> None:
        with _cursor(self.dsn, tenant_id=job.tenant_id) as cursor:
            cursor.execute(
                """
                INSERT INTO axignal_global.procurement_job_failures (
                  stage, tenant_id, research_run_id, admission_handoff_id,
                  job_payload, error_code, error_detail, quarantined
                ) VALUES ('ADMISSION', %s, %s, %s, %s, %s, %s, true)
                """,
                (
                    job.tenant_id,
                    job.research_run_id,
                    job.admission_handoff_id,
                    Jsonb(job.as_payload()),
                    exc.__class__.__name__.upper(),
                    str(exc)[:2000],
                ),
            )
            cursor.execute(
                """
                UPDATE axignal_global.admission_handoffs
                SET state = 'QUARANTINED'
                WHERE admission_handoff_id = %s AND state = 'PENDING'
                """,
                (job.admission_handoff_id,),
            )
            cursor.execute(
                """
                UPDATE tenant_private.research_runs
                SET state = 'QUARANTINED', error_code = %s, error_detail = %s,
                    updated_at = now()
                WHERE research_run_id = %s AND tenant_id = %s
                """,
                (
                    exc.__class__.__name__.upper(),
                    str(exc)[:2000],
                    job.research_run_id,
                    job.tenant_id,
                ),
            )


def _assert_product_source(source: dict[str, Any], config: dict[str, Any]) -> None:
    gates = {
        source.get("source_id") == SOURCE_ID,
        source.get("admission_state") == "ADMITTED",
        source.get("kill_switch") is False,
        source.get("rights_status") == "COMMERCIAL_REUSE_WITH_ATTRIBUTION",
        source.get("commercial_use") is True,
        source.get("redistribution") is True,
        config.get("product_profile_id") == PRODUCT_PROFILE,
        config.get("rights_scope") == "DERIVED_NON_PERSONAL_ONLY",
        config.get("raw_xml_persistence") is False,
        config.get("raw_xml_redistribution") is False,
        config.get("personal_values_persistence") is False,
        config.get("model_training") is False,
    }
    if False in gates:
        raise ProcurementIntegrityError("TED source admission or rights gate is not satisfied")


def _build_dossier_sections(
    lifecycle: SanitisedProcurementLifecycle,
    evidence_ids: list[UUID],
    candidate_ids: list[UUID],
) -> list[dict[str, Any]]:
    lifecycle_facts = [
        {
            "publication_number": item.publication_number,
            "notice_reference": item.notice_reference,
            "lifecycle_kind": item.lifecycle_kind,
            "previous_notice_reference": item.previous_notice_reference,
            "issue_date": item.issue_date,
            "raw_content_hash": item.raw_content_hash,
        }
        for item in lifecycle.notices
    ]
    return [
        {
            "section_id": "official_notice_lifecycle",
            "title": "Ciclo oficial de anuncios",
            "facts": lifecycle_facts,
            "lineage_hash": lifecycle.lineage_hash,
        },
        {
            "section_id": "non_personal_observations",
            "title": "Hechos observados no personales",
            "evidence_ids": [str(item) for item in evidence_ids],
            "candidate_claim_ids": [str(item) for item in candidate_ids],
            "claim_count": len(candidate_ids),
        },
        {
            "section_id": "privacy_and_rights",
            "title": "Privacidad, derechos y límites",
            "rights_scope": "DERIVED_NON_PERSONAL_ONLY",
            "personal_field_elements_observed": lifecycle.personal_field_element_count,
            "personal_values_persisted": False,
            "identity_claims_excluded": lifecycle.excluded_claim_count,
            "raw_xml_persisted": False,
            "raw_xml_redistributed": False,
        },
        {
            "section_id": "authority",
            "title": "Autoridad",
            "text": (
                "El worker TED solo propone. La admisión canónica exige una segunda "
                "descarga oficial y rederivación bajo una credencial independiente."
            ),
            "model_calls": 0,
        },
    ]


def _pending_outbox(
    cursor: psycopg.Cursor[dict[str, Any]],
    *,
    table: str,
    id_column: str,
    limit: int,
) -> list[ProcurementOutboxEvent]:
    query = sql.SQL(
        """
        SELECT {id_column} AS event_id, aggregate_id, event_type, payload, attempts
        FROM {table}
        WHERE status = 'PENDING' AND available_at <= now()
        ORDER BY created_at
        LIMIT %s
        """
    ).format(id_column=sql.Identifier(id_column), table=sql.SQL(table))
    cursor.execute(query, (limit,))
    return [
        ProcurementOutboxEvent(
            event_id=row["event_id"],
            aggregate_id=row["aggregate_id"],
            event_type=row["event_type"],
            payload=row["payload"],
            attempts=row["attempts"],
        )
        for row in cursor.fetchall()
    ]


def _mark_outbox_published(
    cursor: psycopg.Cursor[dict[str, Any]],
    *,
    table: str,
    id_column: str,
    event_id: UUID,
) -> None:
    query = sql.SQL(
        """
        UPDATE {table}
        SET status = 'PUBLISHED', published_at = now(), attempts = attempts + 1
        WHERE {id_column} = %s AND status = 'PENDING'
        """
    ).format(table=sql.SQL(table), id_column=sql.Identifier(id_column))
    cursor.execute(query, (event_id,))


def _mark_outbox_failed(
    cursor: psycopg.Cursor[dict[str, Any]],
    *,
    table: str,
    id_column: str,
    event_id: UUID,
    error: str,
) -> None:
    query = sql.SQL(
        """
        UPDATE {table}
        SET attempts = attempts + 1,
            last_error = %s,
            status = CASE WHEN attempts >= 4 THEN 'FAILED' ELSE 'PENDING' END,
            available_at = now() + interval '30 seconds'
        WHERE {id_column} = %s AND status = 'PENDING'
        """
    ).format(table=sql.SQL(table), id_column=sql.Identifier(id_column))
    cursor.execute(query, (error[:500], event_id))
