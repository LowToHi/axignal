from __future__ import annotations

from typing import Any
from uuid import UUID

from psycopg.types.json import Jsonb

from axignal_api.admission_queue import POLICY_VERSION, AdmissionReviewJob
from axignal_api.admission_types import (
    AdmissionIntegrityError,
    AdmissionPolicyError,
    AdmissionRunResult,
)


class AdmissionDecisionFlowMixin:
    def decide(
        self,
        job: AdmissionReviewJob,
        *,
        fail_after_canonical_insert: bool = False,
    ) -> AdmissionRunResult:
        if job.policy_version != POLICY_VERSION:
            raise AdmissionPolicyError("Admission policy version mismatch")
        with self._cursor("axignal_admission_runtime", job.tenant_id) as cursor:
            handoff = self._load_handoff(cursor, job)
            if handoff["state"] != "PENDING":
                return self._existing_result(cursor, job.admission_handoff_id)

            package = self._validate_package(handoff, job)
            run = self._load_run(cursor, job)
            source, source_object, fragments = self._load_authoritative_inputs(
                cursor,
                package,
            )
            candidates = self._load_candidates(cursor, handoff["candidate_claim_ids"])
            self._validate_candidate_set(
                package,
                handoff["candidate_claim_ids"],
            )
            evidence = self._load_evidence(cursor, candidates)
            self._validate_all_evidence(
                package=package,
                fragments=fragments,
                evidence=evidence,
                source=source,
            )
            batch_id = self._create_batch(cursor, handoff["candidate_claim_ids"])

            decisions: list[dict[str, Any]] = []
            canonical_ids: list[UUID] = []
            for packaged_candidate in package["candidate_claims"]:
                candidate_id = UUID(packaged_candidate["persistent_candidate_claim_id"])
                candidate = candidates.get(candidate_id)
                if candidate is None:
                    raise AdmissionIntegrityError("Candidate Claim is absent from persistence")
                self._validate_candidate_record(candidate, packaged_candidate)
                decision = self._evaluate_candidate(
                    package=package,
                    candidate=candidate,
                    packaged_candidate=packaged_candidate,
                    source=source,
                    source_object=source_object,
                    fragments=fragments,
                    evidence=evidence,
                )
                canonical_id = None
                if decision["outcome"] == "ADMITTED_REDERIVED":
                    canonical_id, duplicate = self._write_canonical(
                        cursor,
                        batch_id=batch_id,
                        decision=decision,
                    )
                    if duplicate:
                        decision["outcome"] = "DUPLICATE"
                    canonical_ids.append(canonical_id)
                    if fail_after_canonical_insert:
                        raise RuntimeError("TEST_FAILPOINT_AFTER_CANONICAL_INSERT")
                    cursor.execute(
                        """
                        UPDATE axignal_global.candidate_claims
                        SET state = 'ADMITTED', canonical_claim_id = %s,
                            rejection_reasons = '[]'::jsonb, updated_at = now()
                        WHERE candidate_claim_id = %s
                        """,
                        (canonical_id, candidate_id),
                    )
                else:
                    candidate_state = {
                        "HUMAN_REVIEW_REQUIRED": "HUMAN_REVIEW_REQUIRED",
                        "CONTESTED": "CONTESTED",
                    }.get(decision["outcome"], "REJECTED")
                    cursor.execute(
                        """
                        UPDATE axignal_global.candidate_claims
                        SET state = %s, rejection_reasons = %s, updated_at = now()
                        WHERE candidate_claim_id = %s
                        """,
                        (
                            candidate_state,
                            Jsonb(decision["reasons"]),
                            candidate_id,
                        ),
                    )
                self._record_decision(
                    cursor,
                    batch_id=batch_id,
                    handoff_id=job.admission_handoff_id,
                    candidate_id=candidate_id,
                    canonical_id=canonical_id,
                    decision=decision,
                )
                decisions.append(decision)

            summary = self._decision_summary(decisions, canonical_ids)
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
            run_state = "COMPLETED" if canonical_ids else "HUMAN_REVIEW_REQUIRED"
            usage = dict(run["actual_usage"] or {}) | {
                "admission_runtime_calls": 1,
                "admission_model_calls": 0,
                "admission_decisions": len(decisions),
                "canonical_claims": len(set(canonical_ids)),
            }
            cursor.execute(
                """
                UPDATE tenant_private.research_runs
                SET state = %s, canonical_claim_ids = %s,
                    admission_batch_id = %s, actual_usage = %s,
                    error_code = NULL, error_detail = NULL, updated_at = now()
                WHERE research_run_id = %s
                """,
                (
                    run_state,
                    list(dict.fromkeys(canonical_ids)),
                    batch_id,
                    Jsonb(usage),
                    job.research_run_id,
                ),
            )
            if canonical_ids and run["dossier_id"] is not None:
                cursor.execute(
                    """
                    UPDATE tenant_private.dossiers
                    SET status = 'TRACEABLE_WITH_ADMITTED_FACTS'
                    WHERE dossier_id = %s
                    """,
                    (run["dossier_id"],),
                )
            return AdmissionRunResult(
                admission_batch_id=batch_id,
                canonical_claim_ids=tuple(dict.fromkeys(canonical_ids)),
                outcomes=tuple(item["outcome"] for item in decisions),
                idempotent_replay=False,
            )
