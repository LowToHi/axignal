from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from axignal_api.connectors.ted_eforms import (
    ProcurementCandidateClaim,
    TEDEFormsCN16Parser,
)
from axignal_api.procurement_admission_rehearsal import (
    InMemoryProcurementAdmissionStore,
    ProcurementAdmissionContext,
    ProcurementAdmissionRehearsal,
    ProcurementAdmissionRehearsalError,
    ProcurementCandidateEnvelope,
)

FIXTURE = Path(__file__).parent / "fixtures" / "ted_eforms_cn16_synthetic.xml"


def xml_bytes() -> bytes:
    return FIXTURE.read_bytes()


def envelopes() -> tuple[ProcurementCandidateEnvelope, ...]:
    claims = TEDEFormsCN16Parser().parse(xml_bytes()).candidate_claims()
    return tuple(ProcurementCandidateEnvelope(candidate=item) for item in claims)


def test_current_ted_state_blocks_every_candidate_and_writes_nothing() -> None:
    store = InMemoryProcurementAdmissionStore()
    result = ProcurementAdmissionRehearsal(store=store).decide(
        raw_xml=xml_bytes(),
        candidates=envelopes(),
        context=ProcurementAdmissionContext.current_ted_state(),
    )

    assert result.batch_id is None
    assert result.sandbox_admissible_count == 0
    assert result.canonical_claim_writes == 0
    assert result.model_calls == 0
    assert result.reviewer_canonical_writes == 0
    assert {item.outcome for item in result.decisions} == {
        "BLOCKED_SOURCE_NOT_PRODUCT_ADMITTED"
    }
    assert store.events == ()
    assert store.result_count == 0


def test_sandbox_rehearsal_rederives_bounded_claims_without_canonical_writes() -> None:
    store = InMemoryProcurementAdmissionStore()
    result = ProcurementAdmissionRehearsal(store=store).decide(
        raw_xml=xml_bytes(),
        candidates=envelopes(),
        context=ProcurementAdmissionContext.sandbox_rehearsal(),
    )

    assert result.batch_id is not None
    assert result.sandbox_admissible_count > 0
    assert result.canonical_claim_writes == 0
    assert result.model_calls == 0
    assert result.reviewer_canonical_writes == 0
    outcomes = {item.outcome for item in result.decisions}
    assert "SANDBOX_ADMISSIBLE_REDERIVED" in outcomes
    assert "HUMAN_REVIEW_REQUIRED_OUTSIDE_PROFILE" in outcomes
    assert all(item.outcome != "ADMITTED_REDERIVED" for item in result.decisions)
    assert store.result_count == 1
    assert store.events[0].event_type == "PROCUREMENT_REHEARSAL_BATCH_STARTED"
    assert store.events[-1].event_type == "PROCUREMENT_REHEARSAL_BATCH_COMMITTED"
    assert [item.sequence for item in store.events] == list(range(1, len(store.events) + 1))


def test_replay_is_idempotent_and_does_not_append_events() -> None:
    store = InMemoryProcurementAdmissionStore()
    rehearsal = ProcurementAdmissionRehearsal(store=store)
    first = rehearsal.decide(
        raw_xml=xml_bytes(),
        candidates=envelopes(),
        context=ProcurementAdmissionContext.sandbox_rehearsal(),
    )
    event_count = len(store.events)
    second = rehearsal.decide(
        raw_xml=xml_bytes(),
        candidates=envelopes(),
        context=ProcurementAdmissionContext.sandbox_rehearsal(),
    )

    assert second.idempotent_replay is True
    assert second.batch_id == first.batch_id
    assert second.decisions == first.decisions
    assert len(store.events) == event_count
    assert store.result_count == 1


def test_forced_failure_rolls_back_batch_decisions_and_events() -> None:
    store = InMemoryProcurementAdmissionStore()
    with pytest.raises(
        ProcurementAdmissionRehearsalError,
        match="TEST_FAILPOINT_AFTER_FIRST_PROCUREMENT_DECISION",
    ):
        ProcurementAdmissionRehearsal(store=store).decide(
            raw_xml=xml_bytes(),
            candidates=envelopes(),
            context=ProcurementAdmissionContext.sandbox_rehearsal(),
            fail_after_first_decision=True,
        )

    assert store.events == ()
    assert store.result_count == 0


def test_tampered_candidate_is_rejected_by_independent_rederivation() -> None:
    original = next(
        item
        for item in envelopes()
        if item.candidate.predicate == "procurement_estimated_value"
    )
    tampered = replace(
        original,
        candidate=replace(
            original.candidate,
            value={"amount": "999999999.00", "currency": "EUR"},
        ),
    )
    result = ProcurementAdmissionRehearsal(
        store=InMemoryProcurementAdmissionStore()
    ).decide(
        raw_xml=xml_bytes(),
        candidates=(tampered,),
        context=ProcurementAdmissionContext.sandbox_rehearsal(),
    )

    assert result.decisions[0].outcome == "REJECTED_REDERIVATION_MISMATCH"
    assert result.decisions[0].rederived_fingerprint is None
    assert result.canonical_claim_writes == 0


def test_model_producer_remains_proposal_only() -> None:
    original = next(
        item
        for item in envelopes()
        if item.candidate.predicate == "procurement_cpv_code"
    )
    model_candidate = replace(original, producer_type="LOCAL_MODEL")
    result = ProcurementAdmissionRehearsal(
        store=InMemoryProcurementAdmissionStore()
    ).decide(
        raw_xml=xml_bytes(),
        candidates=(model_candidate,),
        context=ProcurementAdmissionContext.sandbox_rehearsal(),
    )

    assert result.decisions[0].outcome == "HUMAN_REVIEW_REQUIRED_PROPOSAL_ONLY"
    assert result.decisions[0].gate_results["PRODUCER_AUTHORITY_SEPARATED"] is False
    assert result.canonical_claim_writes == 0


def test_personal_or_prohibited_candidate_is_rejected() -> None:
    personal = ProcurementCandidateEnvelope(
        candidate=ProcurementCandidateClaim(
            predicate="procurement_contact_email",
            subject_key="synthetic",
            value="excluded@example.invalid",
            source_path="/synthetic/contact",
        )
    )
    prohibited = ProcurementCandidateEnvelope(
        candidate=ProcurementCandidateClaim(
            predicate="supplier_probability_of_winning",
            subject_key="synthetic",
            value="0.95",
            source_path="/synthetic/inference",
        )
    )
    result = ProcurementAdmissionRehearsal(
        store=InMemoryProcurementAdmissionStore()
    ).decide(
        raw_xml=xml_bytes(),
        candidates=(personal, prohibited),
        context=ProcurementAdmissionContext.sandbox_rehearsal(),
    )

    assert [item.outcome for item in result.decisions] == [
        "REJECTED_PROHIBITED",
        "REJECTED_PROHIBITED",
    ]
    assert result.sandbox_admissible_count == 0
    assert result.canonical_claim_writes == 0


def test_parser_profile_mismatch_is_quarantined() -> None:
    original = next(
        item
        for item in envelopes()
        if item.candidate.predicate == "procurement_cpv_code"
    )
    mismatched = replace(original, parser_profile="ted-eforms-cn16@9.9.9")
    result = ProcurementAdmissionRehearsal(
        store=InMemoryProcurementAdmissionStore()
    ).decide(
        raw_xml=xml_bytes(),
        candidates=(mismatched,),
        context=ProcurementAdmissionContext.sandbox_rehearsal(),
    )

    assert result.decisions[0].outcome == "QUARANTINED_UNSUPPORTED_PROFILE"
    assert result.canonical_claim_writes == 0
