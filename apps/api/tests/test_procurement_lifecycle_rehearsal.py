from __future__ import annotations

import json
from pathlib import Path

import pytest

from axignal_api.procurement_admission_rehearsal import (
    InMemoryProcurementAdmissionStore,
    ProcurementAdmissionContext,
    ProcurementAdmissionRehearsalError,
)
from axignal_api.procurement_lifecycle_rehearsal import (
    ProcurementLifecycleAssembler,
    ProcurementLifecycleError,
    TEDEFormsLifecycleParser,
)

FIXTURES = Path(__file__).parent / "fixtures"
INITIAL = FIXTURES / "ted_eforms_cn16_synthetic.xml"
CORRECTION = FIXTURES / "ted_eforms_cn16_correction_synthetic.xml"
CANCELLATION = FIXTURES / "ted_eforms_cn16_cancellation_synthetic.xml"
RESULT = FIXTURES / "ted_eforms_can29_result_synthetic.xml"


def frozen_chain(*, include_result: bool = True) -> tuple[bytes, ...]:
    paths = [INITIAL, CORRECTION, CANCELLATION]
    if include_result:
        paths.append(RESULT)
    return tuple(path.read_bytes() for path in paths)


def test_full_lifecycle_builds_evidence_admission_and_awarded_dossier() -> None:
    store = InMemoryProcurementAdmissionStore()
    result = ProcurementLifecycleAssembler(store=store).run(
        raw_notices=frozen_chain(),
        context=ProcurementAdmissionContext.sandbox_rehearsal(),
    )

    assert [item.event_type for item in result.lifecycle_events] == [
        "COMPETITION_INITIAL",
        "COMPETITION_CORRECTION",
        "NOTICE_CANCELLATION",
        "PROCEDURE_RESULT",
    ]
    assert result.dossier.status == "TRACEABLE_SANDBOX_REHEARSAL"
    assert result.dossier.lifecycle_state == "AWARDED"
    assert result.dossier.procedure_identifier == "PROC-SYNTHETIC-001"
    assert result.canonical_claim_writes == 0
    assert result.model_calls == 0
    assert result.reviewer_canonical_writes == 0
    assert result.admission.sandbox_admissible_count > 0
    assert all(
        item.outcome != "ADMITTED_REDERIVED"
        for item in result.admission.decisions
    )

    expected_evidence_count = sum(len(item.claims) for item in result.notices)
    assert len(result.evidence_objects) == expected_evidence_count
    assert len({item.evidence_key for item in result.evidence_objects}) == expected_evidence_count
    assert len({item.content_hash for item in result.evidence_objects}) == expected_evidence_count
    assert all(item.provisional for item in result.evidence_objects)
    assert {item.rights_state for item in result.evidence_objects} == {"SANDBOX_ONLY"}

    result_notice = result.notices[-1]
    assert result_notice.personal_field_element_count == 3
    assert result_notice.winner_organisation_refs == ("ORG-0002",)
    assert result_notice.awarded_values == (("680000.00", "EUR"),)
    assert result_notice.tenders_received_counts == (4,)
    assert result_notice.contract_identifiers == ("CON-0001",)

    serialised = json.dumps(
        {
            "dossier": result.dossier.as_payload(),
            "evidence": [item.__dict__ for item in result.evidence_objects],
        },
        sort_keys=True,
    )
    assert "winner@example.invalid" not in serialised
    assert "+34 000 000 001" not in serialised
    assert store.result_count == 1
    assert store.events[0].event_type == "PROCUREMENT_REHEARSAL_BATCH_STARTED"
    assert store.events[-1].event_type == "PROCUREMENT_REHEARSAL_BATCH_COMMITTED"


def test_actual_ted_state_blocks_all_admission_and_writes_nothing() -> None:
    store = InMemoryProcurementAdmissionStore()
    result = ProcurementLifecycleAssembler(store=store).run(
        raw_notices=frozen_chain(),
        context=ProcurementAdmissionContext.current_ted_state(),
    )

    assert result.admission.batch_id is None
    assert result.admission.sandbox_admissible_count == 0
    assert {item.outcome for item in result.admission.decisions} == {
        "BLOCKED_SOURCE_NOT_PRODUCT_ADMITTED"
    }
    assert store.result_count == 0
    assert store.events == ()
    assert result.canonical_claim_writes == 0


def test_notice_cancellation_does_not_imply_procedure_cancellation() -> None:
    result = ProcurementLifecycleAssembler().run(
        raw_notices=frozen_chain(include_result=False),
        context=ProcurementAdmissionContext.sandbox_rehearsal(),
    )

    assert result.dossier.lifecycle_state == "NOTICE_CANCELLED_PROCEDURE_UNRESOLVED"
    assert any(
        "procedure cancellation is not established" in item
        for item in result.dossier.unknowns
    )


def test_replay_is_idempotent_and_dossier_hash_is_stable() -> None:
    store = InMemoryProcurementAdmissionStore()
    assembler = ProcurementLifecycleAssembler(store=store)
    first = assembler.run(
        raw_notices=frozen_chain(),
        context=ProcurementAdmissionContext.sandbox_rehearsal(),
    )
    event_count = len(store.events)
    second = assembler.run(
        raw_notices=frozen_chain(),
        context=ProcurementAdmissionContext.sandbox_rehearsal(),
    )

    assert second.admission.idempotent_replay is True
    assert second.admission.batch_id == first.admission.batch_id
    assert second.dossier.content_hash == first.dossier.content_hash
    assert second.dossier.dossier_id == first.dossier.dossier_id
    assert second.evidence_objects == first.evidence_objects
    assert second.lifecycle_events == first.lifecycle_events
    assert len(store.events) == event_count


def test_forced_failure_rolls_back_admission_store() -> None:
    store = InMemoryProcurementAdmissionStore()
    with pytest.raises(
        ProcurementAdmissionRehearsalError,
        match="TEST_FAILPOINT_AFTER_FIRST_PROCUREMENT_DECISION",
    ):
        ProcurementLifecycleAssembler(store=store).run(
            raw_notices=frozen_chain(),
            context=ProcurementAdmissionContext.sandbox_rehearsal(),
            fail_after_first_decision=True,
        )

    assert store.result_count == 0
    assert store.events == ()


def test_dangling_change_reference_fails_closed() -> None:
    bad = CORRECTION.read_bytes().replace(
        b"123e4567-e89b-42d3-a456-426614174000-01",
        b"923e4567-e89b-42d3-a456-426614174009-01",
    )
    with pytest.raises(ProcurementLifecycleError, match="dangling"):
        ProcurementLifecycleAssembler().run(
            raw_notices=(INITIAL.read_bytes(), bad),
            context=ProcurementAdmissionContext.sandbox_rehearsal(),
        )


def test_change_after_cancelled_notice_fails_closed() -> None:
    later_correction = CORRECTION.read_bytes()
    later_correction = later_correction.replace(
        b"223e4567-e89b-42d3-a456-426614174001",
        b"523e4567-e89b-42d3-a456-426614174004",
        1,
    )
    later_correction = later_correction.replace(
        b"123e4567-e89b-42d3-a456-426614174000-01",
        b"323e4567-e89b-42d3-a456-426614174002-01",
    )
    later_correction = later_correction.replace(
        b"2026-08-01+02:00",
        b"2026-08-10+02:00",
    )
    with pytest.raises(ProcurementLifecycleError, match="cancelled notice"):
        ProcurementLifecycleAssembler().run(
            raw_notices=(*frozen_chain(include_result=False), later_correction),
            context=ProcurementAdmissionContext.sandbox_rehearsal(),
        )


def test_result_for_unknown_lot_fails_closed() -> None:
    bad_result = RESULT.read_bytes().replace(b"LOT-0001", b"LOT-9999")
    with pytest.raises(ProcurementLifecycleError, match="unknown lot"):
        ProcurementLifecycleAssembler().run(
            raw_notices=(*frozen_chain(include_result=False), bad_result),
            context=ProcurementAdmissionContext.sandbox_rehearsal(),
        )


def test_result_parser_rejects_profile_drift() -> None:
    bad_result = RESULT.read_bytes().replace(
        b"eforms-sdk-1.14",
        b"eforms-sdk-1.15",
    )
    with pytest.raises(ProcurementLifecycleError, match="customization"):
        TEDEFormsLifecycleParser().parse(bad_result)
