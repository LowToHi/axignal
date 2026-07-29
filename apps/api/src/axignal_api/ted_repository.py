from __future__ import annotations

from collections import defaultdict
from typing import Any
from uuid import UUID, uuid4

from psycopg.types.json import Jsonb

from axignal_api.connectors.ted import FIXED_FIELDS, SOURCE_ID, TEDSearchPage
from axignal_api.repository import ResearchRepository
from axignal_api.ted_runtime import (
    PROFILE_ID,
    TEDAdmissionDecision,
    TEDCandidateArtifact,
    TEDEvidenceArtifact,
    canonical_hash,
    sanitised_projection,
)

ATTRIBUTION = (
    "Source: TED (Tenders Electronic Daily), Supplement to the Official Journal "
    "of the European Union. AXIGNAL selected and normalised the allowlisted fields; "
    "changes are indicated in the dossier methodology."
)


class TEDResearchRepository(ResearchRepository):
    def create_ted_run(
        self,
        *,
        tenant_id: UUID,
        context_id: str,
        opportunity_id: str,
        question: str,
    ) -> UUID:
        run_id = uuid4()
        source_plan = [
            {
                "source_id": SOURCE_ID,
                "profile_id": PROFILE_ID,
                "query": "place-of-performance IN (LUX)",
                "fields": list(FIXED_FIELDS),
                "limit": 3,
                "priority": 1,
                "purpose": "Bounded European public procurement discovery",
            }
        ]
        budgets = {
            "max_api_requests": 1,
            "max_notices": 3,
            "max_response_bytes": 1_048_576,
            "max_duration_seconds": 30,
            "max_model_calls": 0,
        }
        event_payload = {
            "schema_version": 1,
            "tenant_id": str(tenant_id),
            "research_run_id": str(run_id),
            "source_id": SOURCE_ID,
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
                  budgets,
                  job_kind
                ) VALUES (%s, %s, %s, %s, %s, 'QUEUED', false, %s, %s, 'TED_PROCUREMENT')
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

    def complete_ted_run(
        self,
        *,
        tenant_id: UUID,
        run_id: UUID,
        source: dict[str, Any],
        page: TEDSearchPage,
        evidence: tuple[TEDEvidenceArtifact, ...],
        candidates: tuple[TEDCandidateArtifact, ...],
        decisions: tuple[TEDAdmissionDecision, ...],
    ) -> dict[str, Any]:
        if not evidence or len(evidence) != len(candidates) or len(candidates) != len(decisions):
            raise ValueError("TED artifact and decision cardinality differs")

        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT state, opportunity_id, job_kind
                FROM tenant_private.research_runs
                WHERE research_run_id = %s
                FOR UPDATE
                """,
                (run_id,),
            )
            run = cursor.fetchone()
            if run is None:
                raise LookupError("ResearchRun not found for TED worker")
            if run["job_kind"] != "TED_PROCUREMENT":
                raise ValueError("ResearchRun is not a TED procurement run")
            if run["state"] == "COMPLETED":
                return {"idempotent_replay": True}

            source_object_id = self._upsert_ted_source_object(
                cursor=cursor,
                source=source,
                page=page,
            )
            evidence_ids: list[UUID] = []
            candidate_ids: list[UUID] = []
            for evidence_item, candidate in zip(evidence, candidates, strict=True):
                evidence_id = self._upsert_ted_evidence(
                    cursor=cursor,
                    source_object_id=source_object_id,
                    evidence=evidence_item,
                )
                candidate_id = self._upsert_ted_candidate(
                    cursor=cursor,
                    candidate=candidate,
                    evidence_id=evidence_id,
                )
                evidence_ids.append(evidence_id)
                candidate_ids.append(candidate_id)

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
                    decisions[0].policy_version,
                    candidate_ids,
                ),
            )

            canonical_ids: list[UUID] = []
            canonical_by_candidate: dict[UUID, UUID] = {}
            decision_rows: list[dict[str, Any]] = []
            for candidate_id, evidence_id, candidate, decision in zip(
                candidate_ids,
                evidence_ids,
                candidates,
                decisions,
                strict=True,
            ):
                canonical_id: UUID | None = None
                created = False
                if decision.admitted:
                    canonical_id, created = self._admit_ted_candidate(
                        cursor=cursor,
                        candidate_id=candidate_id,
                        evidence_id=evidence_id,
                        candidate=candidate,
                        admission_batch_id=admission_batch_id,
                        observed_at=page.retrieved_at,
                    )
                    canonical_ids.append(canonical_id)
                    canonical_by_candidate[candidate_id] = canonical_id
                else:
                    cursor.execute(
                        """
                        UPDATE axignal_global.candidate_claims
                        SET state = 'REJECTED', rejection_reasons = %s, updated_at = now()
                        WHERE candidate_claim_id = %s
                        """,
                        (Jsonb(list(decision.reasons)), candidate_id),
                    )
                decision_rows.append(
                    decision.as_json()
                    | {
                        "candidate_claim_id": str(candidate_id),
                        "canonical_claim_id": str(canonical_id) if canonical_id else None,
                        "canonical_claim_created": created,
                    }
                )

            cursor.execute(
                """
                UPDATE axignal_global.admission_batches
                SET state = 'DECIDED', decision_summary = %s, decided_at = now()
                WHERE admission_batch_id = %s
                """,
                (
                    Jsonb(
                        {
                            "profile_id": PROFILE_ID,
                            "source_id": SOURCE_ID,
                            "decisions": decision_rows,
                        }
                    ),
                    admission_batch_id,
                ),
            )

            dossier_id = uuid4()
            sections = self._dossier_sections(
                candidates=candidates,
                candidate_ids=candidate_ids,
                evidence_ids=evidence_ids,
                canonical_by_candidate=canonical_by_candidate,
            )
            admitted_count = len(canonical_ids)
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
                    "TRACEABLE_WITH_ADMITTED_FACTS"
                    if admitted_count
                    else "TRACEABLE_PROVISIONAL",
                    "TED · European public procurement discovery",
                    (
                        f"AXIGNAL processed {len(page.notices)} bounded TED notices and "
                        f"admitted {admitted_count} exact observed fields."
                    ),
                    Jsonb(sections),
                    Jsonb(
                        {
                            "source_id": SOURCE_ID,
                            "profile_id": PROFILE_ID,
                            "attribution_text": ATTRIBUTION,
                            "source_url": page.request_url,
                            "changes": (
                                "AXIGNAL retained only allowlisted fields and generated "
                                "deterministic evidence bindings."
                            ),
                            "api_redistribution": false,
                        }
                    ),
                ),
            )

            for evidence_id in evidence_ids:
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

            usage = {
                "api_requests": 1 if page.retrieval_mode.startswith("LIVE_API") else 0,
                "fixture_reads": 1 if page.retrieval_mode == "FROZEN_FIXTURE" else 0,
                "notices": len(page.notices),
                "documents": len(page.notices),
                "model_calls": 0,
                "source_envelope_content_hash": page.content_hash,
                "projection_content_hash": canonical_hash(sanitised_projection(page)),
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
                    evidence_ids,
                    candidate_ids,
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
                            "source_id": SOURCE_ID,
                            "profile_id": PROFILE_ID,
                            "evidence_ids": [str(item) for item in evidence_ids],
                            "candidate_claim_ids": [str(item) for item in candidate_ids],
                            "canonical_claim_ids": [str(item) for item in canonical_ids],
                            "dossier_id": str(dossier_id),
                            "admission_batch_id": str(admission_batch_id),
                        }
                    ),
                ),
            )

        return {
            "source_object_id": source_object_id,
            "evidence_ids": evidence_ids,
            "candidate_claim_ids": candidate_ids,
            "canonical_claim_ids": canonical_ids,
            "dossier_id": dossier_id,
            "admission_batch_id": admission_batch_id,
            "idempotent_replay": False,
        }

    @staticmethod
    def _upsert_ted_source_object(
        *,
        cursor: Any,
        source: dict[str, Any],
        page: TEDSearchPage,
    ) -> UUID:
        projection = sanitised_projection(page)
        projection_hash = canonical_hash(projection)
        retrieval_key = canonical_hash(
            {
                "source_id": SOURCE_ID,
                "request_hash": page.request_hash,
                "projection_content_hash": projection_hash,
            }
        )
        rights_snapshot = {
            "rights_status": source["rights_status"],
            "license_id": source["license_id"],
            "attribution_text": source["attribution_text"],
            "terms_url": source["terms_url"],
            "dataset_url": source["dataset_url"],
            "profile_id": PROFILE_ID,
            "api_redistribution": false,
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
            ) VALUES (%s, %s, %s, %s, NULL, 200, 'application/json', %s, %s, %s, %s)
            ON CONFLICT (source_id, content_hash) DO NOTHING
            RETURNING source_object_id
            """,
            (
                SOURCE_ID,
                retrieval_key,
                page.request_url,
                page.retrieved_at,
                projection_hash,
                Jsonb(projection),
                Jsonb(rights_snapshot),
                Jsonb(
                    {
                        "source_envelope_content_hash": page.content_hash,
                        "request_hash": page.request_hash,
                        "retrieval_mode": page.retrieval_mode,
                        "sanitised_projection": true,
                    }
                ),
            ),
        )
        row = cursor.fetchone()
        if row is not None:
            return row["source_object_id"]
        cursor.execute(
            """
            SELECT source_object_id
            FROM axignal_global.source_objects
            WHERE source_id = %s AND content_hash = %s
            """,
            (SOURCE_ID, projection_hash),
        )
        existing = cursor.fetchone()
        if existing is None:
            raise RuntimeError("TED source object upsert failed")
        return existing["source_object_id"]

    @staticmethod
    def _upsert_ted_evidence(
        *,
        cursor: Any,
        source_object_id: UUID,
        evidence: TEDEvidenceArtifact,
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
              numeric_value,
              unit,
              payload,
              content_hash,
              rights_status,
              provisional
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NULL, NULL, %s, %s, %s, true)
            ON CONFLICT (evidence_key) DO NOTHING
            RETURNING evidence_id
            """,
            (
                source_object_id,
                SOURCE_ID,
                evidence.evidence_key,
                evidence.title,
                evidence.relationship,
                evidence.subject_id,
                evidence.predicate,
                evidence.observed_at,
                Jsonb(evidence.payload),
                evidence.content_hash,
                evidence.rights_status,
            ),
        )
        row = cursor.fetchone()
        if row is not None:
            return row["evidence_id"]
        cursor.execute(
            "SELECT evidence_id FROM axignal_global.evidence_objects WHERE evidence_key = %s",
            (evidence.evidence_key,),
        )
        existing = cursor.fetchone()
        if existing is None:
            raise RuntimeError("TED evidence upsert failed")
        return existing["evidence_id"]

    @staticmethod
    def _upsert_ted_candidate(
        *,
        cursor: Any,
        candidate: TEDCandidateArtifact,
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
            ON CONFLICT (fingerprint) DO NOTHING
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
        if row is not None:
            return row["candidate_claim_id"]
        cursor.execute(
            """
            SELECT candidate_claim_id
            FROM axignal_global.candidate_claims
            WHERE fingerprint = %s
            """,
            (candidate.fingerprint,),
        )
        existing = cursor.fetchone()
        if existing is None:
            raise RuntimeError("TED candidate upsert failed")
        return existing["candidate_claim_id"]

    @staticmethod
    def _admit_ted_candidate(
        *,
        cursor: Any,
        candidate_id: UUID,
        evidence_id: UUID,
        candidate: TEDCandidateArtifact,
        admission_batch_id: UUID,
        observed_at: Any,
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
              observed_at,
              epistemic_class,
              state,
              admitted_by,
              admission_batch_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'OBSERVED_FACT', 'ADMITTED',
                      'DETERMINISTIC_RUNTIME', %s)
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
                observed_at,
                admission_batch_id,
            ),
        )
        row = cursor.fetchone()
        created = row is not None
        if row is None:
            cursor.execute(
                """
                SELECT canonical_claim_id
                FROM axignal_global.canonical_claims
                WHERE fingerprint = %s
                """,
                (candidate.fingerprint,),
            )
            row = cursor.fetchone()
        if row is None:
            raise RuntimeError("TED canonical admission failed")
        canonical_id = row["canonical_claim_id"]
        cursor.execute(
            """
            UPDATE axignal_global.candidate_claims
            SET state = 'ADMITTED', canonical_claim_id = %s,
                rejection_reasons = '[]'::jsonb, updated_at = now()
            WHERE candidate_claim_id = %s
            """,
            (canonical_id, candidate_id),
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
                ) VALUES (%s, NULL, 'ADMITTED', 'all_ted_projection_gates_passed', %s)
                """,
                (canonical_id, admission_batch_id),
            )
        return canonical_id, created

    @staticmethod
    def _dossier_sections(
        *,
        candidates: tuple[TEDCandidateArtifact, ...],
        candidate_ids: list[UUID],
        evidence_ids: list[UUID],
        canonical_by_candidate: dict[UUID, UUID],
    ) -> list[dict[str, Any]]:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for candidate, candidate_id, evidence_id in zip(
            candidates,
            candidate_ids,
            evidence_ids,
            strict=True,
        ):
            publication_number = str(candidate.object_value["publication_number"])
            canonical_id = canonical_by_candidate.get(candidate_id)
            grouped[publication_number].append(
                {
                    "predicate": candidate.predicate,
                    "statement": candidate.statement,
                    "value": candidate.object_value["value"],
                    "evidence_id": str(evidence_id),
                    "candidate_claim_id": str(candidate_id),
                    "canonical_claim_id": str(canonical_id) if canonical_id else None,
                }
            )
        sections = [
            {
                "section_id": f"ted_notice_{publication_number.replace('-', '_')}",
                "title": f"TED notice {publication_number}",
                "status": "TRACEABLE",
                "facts": facts,
            }
            for publication_number, facts in sorted(grouped.items())
        ]
        sections.append(
            {
                "section_id": "methodology",
                "title": "Methodology and authority",
                "status": "TRACEABLE",
                "text": (
                    "The official TED Search API was queried through a fixed non-personal "
                    "profile. AXIGNAL persisted only allowlisted fields. A deterministic "
                    "parser created Candidate Claims and only the deterministic admission "
                    "runtime could write canonical Claims. No model call was made."
                ),
                "profile_id": PROFILE_ID,
            }
        )
        return sections
