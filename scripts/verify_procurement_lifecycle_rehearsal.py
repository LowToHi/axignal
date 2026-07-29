from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from axignal_api.procurement_admission_rehearsal import (
    InMemoryProcurementAdmissionStore,
    ProcurementAdmissionContext,
    ProcurementAdmissionRehearsalError,
)
from axignal_api.procurement_lifecycle_rehearsal import (
    LIFECYCLE_PROFILE,
    ProcurementLifecycleAssembler,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "apps" / "api" / "tests" / "fixtures"
OUTPUT = ROOT / "procurement-lifecycle-rehearsal-evidence.json"
PATHS = (
    FIXTURES / "ted_eforms_cn16_synthetic.xml",
    FIXTURES / "ted_eforms_cn16_correction_synthetic.xml",
    FIXTURES / "ted_eforms_cn16_cancellation_synthetic.xml",
    FIXTURES / "ted_eforms_can29_result_synthetic.xml",
)
raw_notices = tuple(path.read_bytes() for path in PATHS)

actual_store = InMemoryProcurementAdmissionStore()
actual = ProcurementLifecycleAssembler(store=actual_store).run(
    raw_notices=raw_notices,
    context=ProcurementAdmissionContext.current_ted_state(),
)
assert actual_store.result_count == 0
assert actual_store.events == ()
assert {item.outcome for item in actual.admission.decisions} == {
    "BLOCKED_SOURCE_NOT_PRODUCT_ADMITTED"
}

sandbox_store = InMemoryProcurementAdmissionStore()
assembler = ProcurementLifecycleAssembler(store=sandbox_store)
sandbox = assembler.run(
    raw_notices=raw_notices,
    context=ProcurementAdmissionContext.sandbox_rehearsal(),
)
replay = assembler.run(
    raw_notices=raw_notices,
    context=ProcurementAdmissionContext.sandbox_rehearsal(),
)
assert replay.admission.idempotent_replay is True
assert replay.dossier.content_hash == sandbox.dossier.content_hash

rollback_store = InMemoryProcurementAdmissionStore()
try:
    ProcurementLifecycleAssembler(store=rollback_store).run(
        raw_notices=raw_notices,
        context=ProcurementAdmissionContext.sandbox_rehearsal(),
        fail_after_first_decision=True,
    )
except ProcurementAdmissionRehearsalError:
    pass
else:
    raise AssertionError("Expected lifecycle admission failpoint did not fire")
assert rollback_store.result_count == 0
assert rollback_store.events == ()

outcomes = Counter(item.outcome for item in sandbox.admission.decisions)
evidence = {
    "profile": LIFECYCLE_PROFILE,
    "fixture_classification": "SYNTHETIC_OFFICIAL_STRUCTURE",
    "notice_count": len(sandbox.notices),
    "event_types": [item.event_type for item in sandbox.lifecycle_events],
    "event_hashes": [item.event_hash for item in sandbox.lifecycle_events],
    "candidate_claim_count": sum(len(item.claims) for item in sandbox.notices),
    "evidence_object_count": len(sandbox.evidence_objects),
    "unique_evidence_key_count": len(
        {item.evidence_key for item in sandbox.evidence_objects}
    ),
    "unique_evidence_hash_count": len(
        {item.content_hash for item in sandbox.evidence_objects}
    ),
    "actual_source_blocked_decision_count": len(actual.admission.decisions),
    "sandbox_outcome_counts": dict(sorted(outcomes.items())),
    "dossier_status": sandbox.dossier.status,
    "dossier_lifecycle_state": sandbox.dossier.lifecycle_state,
    "dossier_hash": sandbox.dossier.content_hash,
    "idempotent_replay": replay.admission.idempotent_replay,
    "rollback_residue_count": rollback_store.result_count + len(rollback_store.events),
    "personal_field_elements_observed": sum(
        item.personal_field_element_count for item in sandbox.notices
    ),
    "personal_values_emitted": False,
    "raw_xml_persisted_in_artifact": False,
    "notice_values_persisted_in_artifact": False,
    "canonical_claim_writes": sandbox.canonical_claim_writes,
    "model_calls": sandbox.model_calls,
    "reviewer_canonical_writes": sandbox.reviewer_canonical_writes,
    "source_state": "TECHNICAL_PROBE",
    "product_admitted": False,
    "runtime_enabled": False,
    "universe_supported": False,
}
assert evidence["notice_count"] == 4
assert evidence["event_types"] == [
    "COMPETITION_INITIAL",
    "COMPETITION_CORRECTION",
    "NOTICE_CANCELLATION",
    "PROCEDURE_RESULT",
]
assert evidence["evidence_object_count"] == evidence["candidate_claim_count"]
assert evidence["unique_evidence_key_count"] == evidence["evidence_object_count"]
assert evidence["unique_evidence_hash_count"] == evidence["evidence_object_count"]
assert evidence["dossier_lifecycle_state"] == "AWARDED"
assert evidence["rollback_residue_count"] == 0
assert evidence["canonical_claim_writes"] == 0

OUTPUT.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(evidence, indent=2, sort_keys=True))
