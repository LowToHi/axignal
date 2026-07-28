from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from psycopg.types.json import Jsonb

from axignal_api.admission_queue import POLICY_VERSION
from axignal_api.admission_types import AdmissionIntegrityError, AdmissionRunResult


class AdmissionLedgerStoreMixin:
    @staticmethod
    def _create_batch(cursor: Any, candidate_ids: list[UUID]) -> UUID:
        batch_id = uuid4()
        cursor.execute(
            """
            INSERT INTO axignal_global.admission_batches (
              admission_batch_id, policy_version, state, candidate_claim_ids
            ) VALUES (%s, %s, 'PENDING', %s)
            """,
            (batch_id, POLICY_VERSION, candidate_ids),
        )
        return batch_id

    @staticmethod
    def _write_canonical(
        cursor: Any,
        *,
        batch_id: UUID,
        decision: dict[str, Any],
    ) -> tuple[UUID, bool]:
        rederived = decision["rederived"]
        fingerprint = decision["rederived_fingerprint"]
        canonical_id = uuid4()
        period = rederived["object_value"]["period"]
        statement = (
            "The World Bank report states that real GDP growth in the Russian "
            f"Federation reached {rederived['object_value']['value']} percent in {period}."
        )
        cursor.execute(
            """
            INSERT INTO axignal_global.canonical_claims (
              canonical_claim_id, fingerprint, subject_id, predicate,
              object_value, statement, evidence_ids, valid_from, valid_to,
              observed_at, epistemic_class, state, admitted_by,
              admission_batch_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                      'OBSERVED_FACT', 'ADMITTED', 'DETERMINISTIC_RUNTIME', %s)
            ON CONFLICT (fingerprint) DO NOTHING
            RETURNING canonical_claim_id
            """,
            (
                canonical_id,
                fingerprint,
                rederived["subject_id"],
                rederived["predicate"],
                Jsonb(rederived["object_value"]),
                statement,
                [UUID(item) for item in rederived["evidence_ids"]],
                datetime(int(period), 1, 1, tzinfo=UTC),
                datetime(int(period), 12, 31, 23, 59, 59, tzinfo=UTC),
                datetime(int(period), 12, 31, 23, 59, 59, tzinfo=UTC),
                batch_id,
            ),
        )
        inserted = cursor.fetchone()
        if inserted is None:
            cursor.execute(
                "SELECT canonical_claim_id FROM axignal_global.canonical_claims "
                "WHERE fingerprint = %s",
                (fingerprint,),
            )
            existing = cursor.fetchone()
            if existing is None:
                raise AdmissionIntegrityError("Canonical fingerprint conflict unresolved")
            return existing["canonical_claim_id"], True
        canonical_id = inserted["canonical_claim_id"]
        cursor.execute(
            """
            INSERT INTO axignal_global.claim_state_events (
              canonical_claim_id, from_state, to_state, reason,
              admission_batch_id
            ) VALUES (%s, NULL, 'ADMITTED', %s, %s)
            """,
            (
                canonical_id,
                "deterministically_rederived_from_immutable_document_evidence",
                batch_id,
            ),
        )
        return canonical_id, False

    @staticmethod
    def _record_decision(
        cursor: Any,
        *,
        batch_id: UUID,
        handoff_id: UUID,
        candidate_id: UUID,
        canonical_id: UUID | None,
        decision: dict[str, Any],
    ) -> None:
        cursor.execute(
            """
            INSERT INTO axignal_global.admission_decisions (
              admission_batch_id, admission_handoff_id, candidate_claim_id,
              outcome, policy_version, gate_results, rejection_reasons,
              canonical_claim_id, rederived_fingerprint,
              human_review_required
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                batch_id,
                handoff_id,
                candidate_id,
                decision["outcome"],
                POLICY_VERSION,
                Jsonb(decision["gate_results"]),
                Jsonb(decision["reasons"]),
                canonical_id,
                decision["rederived_fingerprint"],
                decision["outcome"] == "HUMAN_REVIEW_REQUIRED",
            ),
        )

    @staticmethod
    def _decision_summary(
        decisions: list[dict[str, Any]],
        canonical_ids: list[UUID],
    ) -> dict[str, Any]:
        counts: dict[str, int] = {}
        for item in decisions:
            counts[item["outcome"]] = counts.get(item["outcome"], 0) + 1
        return {
            "policy_version": POLICY_VERSION,
            "decision_counts": counts,
            "canonical_claim_ids": [str(item) for item in dict.fromkeys(canonical_ids)],
            "model_calls": 0,
        }

    @staticmethod
    def _existing_result(cursor: Any, handoff_id: UUID) -> AdmissionRunResult:
        cursor.execute(
            """
            SELECT admission_batch_id, outcome, canonical_claim_id
            FROM axignal_global.admission_decisions
            WHERE admission_handoff_id = %s
            ORDER BY created_at
            """,
            (handoff_id,),
        )
        rows = cursor.fetchall()
        if not rows:
            raise AdmissionIntegrityError("Non-pending handoff has no durable decisions")
        canonical_ids = tuple(dict.fromkeys(
            row["canonical_claim_id"]
            for row in rows
            if row["canonical_claim_id"] is not None
        ))
        return AdmissionRunResult(
            admission_batch_id=rows[0]["admission_batch_id"],
            canonical_claim_ids=canonical_ids,
            outcomes=tuple(row["outcome"] for row in rows),
            idempotent_replay=True,
        )
