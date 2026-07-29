from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from hashlib import sha256
from typing import Any
from uuid import UUID, uuid4

from axignal_api.connectors.ted_eforms import (
    ProcurementCandidateClaim,
    TEDEFormsCN16Parser,
)

POLICY_VERSION = "ted-procurement-observed@0.1.0"
PARSER_PROFILE = "ted-eforms-cn16@0.1.0"

AUTO_ADMISSIBLE_PREDICATES = frozenset(
    {
        "procurement_notice_type",
        "procurement_procedure_type",
        "procurement_buyer_official_name",
        "procurement_buyer_identifier",
        "procurement_contract_nature",
        "procurement_cpv_code",
        "procurement_place_of_performance_nuts",
        "procurement_estimated_value",
        "procurement_lot_identifier",
        "procurement_submission_deadline",
        "procurement_eu_funding_indicator",
    }
)
PERSONAL_PREDICATE_TOKENS = frozenset(
    {"contact", "email", "phone", "telephone", "person", "firstname", "familyname"}
)
PROHIBITED_PREDICATES = frozenset(
    {
        "supplier_probability_of_winning",
        "supplier_legal_eligibility",
        "supplier_personal_suitability",
        "expected_contract_profitability",
        "guaranteed_opportunity",
        "bid_submission_or_representation",
        "personalised_investment_recommendation",
        "natural_person_contact_as_opportunity_signal",
    }
)


class ProcurementAdmissionRehearsalError(RuntimeError):
    """Raised when the bounded admission rehearsal fails closed."""


@dataclass(frozen=True)
class ProcurementAdmissionContext:
    source_state: str
    policy_state: str
    rights_valid: bool
    kill_switch_enabled: bool
    sandbox_authorised: bool = False

    @classmethod
    def current_ted_state(cls) -> ProcurementAdmissionContext:
        return cls(
            source_state="TECHNICAL_PROBE",
            policy_state="DISABLED_PENDING_PRODUCT_ADMISSION_AND_XML_PARSER",
            rights_valid=False,
            kill_switch_enabled=True,
            sandbox_authorised=False,
        )

    @classmethod
    def sandbox_rehearsal(cls) -> ProcurementAdmissionContext:
        return cls(
            source_state="SANDBOX",
            policy_state="SANDBOX_REHEARSAL",
            rights_valid=True,
            kill_switch_enabled=False,
            sandbox_authorised=True,
        )

    @property
    def product_admission_ready(self) -> bool:
        return (
            self.source_state == "PRODUCT_ADMITTED"
            and self.policy_state == "ENABLED"
            and self.rights_valid
            and not self.kill_switch_enabled
        )

    @property
    def sandbox_ready(self) -> bool:
        return (
            self.source_state == "SANDBOX"
            and self.policy_state == "SANDBOX_REHEARSAL"
            and self.rights_valid
            and not self.kill_switch_enabled
            and self.sandbox_authorised
        )


@dataclass(frozen=True)
class ProcurementCandidateEnvelope:
    candidate: ProcurementCandidateClaim
    producer_type: str = "DETERMINISTIC_XML_PARSER"
    parser_profile: str = PARSER_PROFILE


@dataclass(frozen=True)
class ProcurementAdmissionDecision:
    candidate_fingerprint: str
    predicate: str
    outcome: str
    reasons: tuple[str, ...]
    gate_results: dict[str, bool]
    rederived_fingerprint: str | None


@dataclass(frozen=True)
class ProcurementAdmissionRehearsalResult:
    batch_id: UUID | None
    decisions: tuple[ProcurementAdmissionDecision, ...]
    idempotent_replay: bool
    sandbox_admissible_count: int
    canonical_claim_writes: int = 0
    model_calls: int = 0
    reviewer_canonical_writes: int = 0

    def as_payload(self) -> dict[str, Any]:
        return {
            "batch_id": str(self.batch_id) if self.batch_id else None,
            "decisions": [
                {
                    "candidate_fingerprint": item.candidate_fingerprint,
                    "predicate": item.predicate,
                    "outcome": item.outcome,
                    "reasons": list(item.reasons),
                    "gate_results": item.gate_results,
                    "rederived_fingerprint": item.rederived_fingerprint,
                }
                for item in self.decisions
            ],
            "idempotent_replay": self.idempotent_replay,
            "sandbox_admissible_count": self.sandbox_admissible_count,
            "canonical_claim_writes": self.canonical_claim_writes,
            "model_calls": self.model_calls,
            "reviewer_canonical_writes": self.reviewer_canonical_writes,
        }


@dataclass(frozen=True)
class ProcurementAdmissionEvent:
    sequence: int
    event_type: str
    batch_id: UUID
    payload_hash: str


class InMemoryProcurementAdmissionStore:
    """Transactional CI-only store; never a replacement for the canonical ledger."""

    def __init__(self) -> None:
        self._results: dict[str, ProcurementAdmissionRehearsalResult] = {}
        self._events: list[ProcurementAdmissionEvent] = []

    @property
    def events(self) -> tuple[ProcurementAdmissionEvent, ...]:
        return tuple(self._events)

    @property
    def result_count(self) -> int:
        return len(self._results)

    def existing(self, idempotency_key: str) -> ProcurementAdmissionRehearsalResult | None:
        result = self._results.get(idempotency_key)
        if result is None:
            return None
        return ProcurementAdmissionRehearsalResult(
            batch_id=result.batch_id,
            decisions=result.decisions,
            idempotent_replay=True,
            sandbox_admissible_count=result.sandbox_admissible_count,
        )

    def commit(
        self,
        *,
        idempotency_key: str,
        decisions: tuple[ProcurementAdmissionDecision, ...],
        fail_after_first_decision: bool = False,
    ) -> ProcurementAdmissionRehearsalResult:
        existing = self.existing(idempotency_key)
        if existing is not None:
            return existing

        snapshot_results = copy.deepcopy(self._results)
        snapshot_events = list(self._events)
        batch_id = uuid4()
        try:
            self._append_event(
                event_type="PROCUREMENT_REHEARSAL_BATCH_STARTED",
                batch_id=batch_id,
                payload={"idempotency_key": idempotency_key},
            )
            for index, decision in enumerate(decisions):
                self._append_event(
                    event_type="PROCUREMENT_REHEARSAL_DECISION_RECORDED",
                    batch_id=batch_id,
                    payload={
                        "candidate_fingerprint": decision.candidate_fingerprint,
                        "outcome": decision.outcome,
                    },
                )
                if fail_after_first_decision and index == 0:
                    raise ProcurementAdmissionRehearsalError(
                        "TEST_FAILPOINT_AFTER_FIRST_PROCUREMENT_DECISION"
                    )
            result = ProcurementAdmissionRehearsalResult(
                batch_id=batch_id,
                decisions=decisions,
                idempotent_replay=False,
                sandbox_admissible_count=sum(
                    item.outcome == "SANDBOX_ADMISSIBLE_REDERIVED" for item in decisions
                ),
            )
            self._results[idempotency_key] = result
            self._append_event(
                event_type="PROCUREMENT_REHEARSAL_BATCH_COMMITTED",
                batch_id=batch_id,
                payload=result.as_payload(),
            )
            return result
        except Exception:
            self._results = snapshot_results
            self._events = snapshot_events
            raise

    def _append_event(self, *, event_type: str, batch_id: UUID, payload: Any) -> None:
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        self._events.append(
            ProcurementAdmissionEvent(
                sequence=len(self._events) + 1,
                event_type=event_type,
                batch_id=batch_id,
                payload_hash=f"sha256:{sha256(encoded.encode('utf-8')).hexdigest()}",
            )
        )


class ProcurementAdmissionRehearsal:
    """Independent deterministic policy rehearsal over frozen XML evidence."""

    def __init__(
        self,
        *,
        store: InMemoryProcurementAdmissionStore,
        parser: TEDEFormsCN16Parser | None = None,
    ) -> None:
        self.store = store
        self.parser = parser or TEDEFormsCN16Parser()

    def decide(
        self,
        *,
        raw_xml: bytes,
        candidates: tuple[ProcurementCandidateEnvelope, ...],
        context: ProcurementAdmissionContext,
        fail_after_first_decision: bool = False,
    ) -> ProcurementAdmissionRehearsalResult:
        parsed = self.parser.parse(raw_xml)
        rederived = {item.fingerprint: item for item in parsed.candidate_claims()}
        idempotency_key = self._idempotency_key(
            raw_content_hash=parsed.raw_content_hash,
            candidates=candidates,
            context=context,
        )
        existing = self.store.existing(idempotency_key)
        if existing is not None:
            return existing

        if not context.product_admission_ready and not context.sandbox_ready:
            decisions = tuple(
                ProcurementAdmissionDecision(
                    candidate_fingerprint=item.candidate.fingerprint,
                    predicate=item.candidate.predicate,
                    outcome="BLOCKED_SOURCE_NOT_PRODUCT_ADMITTED",
                    reasons=("source_or_policy_gate_not_admitted",),
                    gate_results={
                        "SOURCE_PRODUCT_ADMITTED": context.source_state == "PRODUCT_ADMITTED",
                        "POLICY_ENABLED": context.policy_state == "ENABLED",
                        "RIGHTS_VALID": context.rights_valid,
                        "SOURCE_KILL_SWITCH_OFF": not context.kill_switch_enabled,
                        "SANDBOX_AUTHORISED": context.sandbox_ready,
                    },
                    rederived_fingerprint=None,
                )
                for item in candidates
            )
            return ProcurementAdmissionRehearsalResult(
                batch_id=None,
                decisions=decisions,
                idempotent_replay=False,
                sandbox_admissible_count=0,
            )

        decisions = tuple(
            self._evaluate_candidate(envelope, rederived=rederived, context=context)
            for envelope in candidates
        )
        return self.store.commit(
            idempotency_key=idempotency_key,
            decisions=decisions,
            fail_after_first_decision=fail_after_first_decision,
        )

    @staticmethod
    def _evaluate_candidate(
        envelope: ProcurementCandidateEnvelope,
        *,
        rederived: dict[str, ProcurementCandidateClaim],
        context: ProcurementAdmissionContext,
    ) -> ProcurementAdmissionDecision:
        candidate = envelope.candidate
        predicate_lower = candidate.predicate.casefold()
        personal_predicate = any(token in predicate_lower for token in PERSONAL_PREDICATE_TOKENS)
        gate_results = {
            "SOURCE_PRODUCT_ADMITTED": context.product_admission_ready,
            "SANDBOX_REHEARSAL_AUTHORISED": context.sandbox_ready,
            "PARSER_PROFILE_PINNED": envelope.parser_profile == PARSER_PROFILE,
            "PRODUCER_AUTHORITY_SEPARATED": (
                envelope.producer_type == "DETERMINISTIC_XML_PARSER"
            ),
            "PERSONAL_DATA_EXCLUDED": not personal_predicate,
            "PREDICATE_NOT_PROHIBITED": candidate.predicate not in PROHIBITED_PREDICATES,
            "PREDICATE_AUTO_ADMISSIBLE": candidate.predicate in AUTO_ADMISSIBLE_PREDICATES,
            "REEDERIVATION_EXACT_MATCH": candidate.fingerprint in rederived,
        }
        if personal_predicate or candidate.predicate in PROHIBITED_PREDICATES:
            return ProcurementAdmissionDecision(
                candidate_fingerprint=candidate.fingerprint,
                predicate=candidate.predicate,
                outcome="REJECTED_PROHIBITED",
                reasons=("personal_or_prohibited_procurement_predicate",),
                gate_results=gate_results,
                rederived_fingerprint=None,
            )
        if envelope.parser_profile != PARSER_PROFILE:
            return ProcurementAdmissionDecision(
                candidate_fingerprint=candidate.fingerprint,
                predicate=candidate.predicate,
                outcome="QUARANTINED_UNSUPPORTED_PROFILE",
                reasons=("parser_profile_mismatch",),
                gate_results=gate_results,
                rederived_fingerprint=None,
            )
        if envelope.producer_type != "DETERMINISTIC_XML_PARSER":
            return ProcurementAdmissionDecision(
                candidate_fingerprint=candidate.fingerprint,
                predicate=candidate.predicate,
                outcome="HUMAN_REVIEW_REQUIRED_PROPOSAL_ONLY",
                reasons=("producer_has_no_auto_admission_authority",),
                gate_results=gate_results,
                rederived_fingerprint=None,
            )
        if candidate.predicate not in AUTO_ADMISSIBLE_PREDICATES:
            return ProcurementAdmissionDecision(
                candidate_fingerprint=candidate.fingerprint,
                predicate=candidate.predicate,
                outcome="HUMAN_REVIEW_REQUIRED_OUTSIDE_PROFILE",
                reasons=("predicate_outside_auto_admission_profile",),
                gate_results=gate_results,
                rederived_fingerprint=None,
            )
        if candidate.fingerprint not in rederived:
            return ProcurementAdmissionDecision(
                candidate_fingerprint=candidate.fingerprint,
                predicate=candidate.predicate,
                outcome="REJECTED_REDERIVATION_MISMATCH",
                reasons=("candidate_does_not_match_independent_xml_rederivation",),
                gate_results=gate_results,
                rederived_fingerprint=None,
            )
        return ProcurementAdmissionDecision(
            candidate_fingerprint=candidate.fingerprint,
            predicate=candidate.predicate,
            outcome=(
                "ADMITTED_REDERIVED"
                if context.product_admission_ready
                else "SANDBOX_ADMISSIBLE_REDERIVED"
            ),
            reasons=("all_bounded_deterministic_gates_passed",),
            gate_results=gate_results,
            rederived_fingerprint=candidate.fingerprint,
        )

    @staticmethod
    def _idempotency_key(
        *,
        raw_content_hash: str,
        candidates: tuple[ProcurementCandidateEnvelope, ...],
        context: ProcurementAdmissionContext,
    ) -> str:
        material = {
            "policy_version": POLICY_VERSION,
            "parser_profile": PARSER_PROFILE,
            "raw_content_hash": raw_content_hash,
            "candidate_fingerprints": sorted(item.candidate.fingerprint for item in candidates),
            "source_state": context.source_state,
            "policy_state": context.policy_state,
            "sandbox_authorised": context.sandbox_authorised,
        }
        encoded = json.dumps(material, sort_keys=True, separators=(",", ":"))
        return f"sha256:{sha256(encoded.encode('utf-8')).hexdigest()}"
