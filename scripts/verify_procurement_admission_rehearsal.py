from __future__ import annotations

import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

import httpx

from axignal_api.connectors.ted_eforms import TEDEFormsCN16Parser
from axignal_api.procurement_admission_rehearsal import (
    InMemoryProcurementAdmissionStore,
    ProcurementAdmissionContext,
    ProcurementAdmissionRehearsal,
    ProcurementAdmissionRehearsalError,
    ProcurementCandidateEnvelope,
)

SOURCE_URL = (
    "https://raw.githubusercontent.com/OP-TED/eForms-SDK/1.14.2/"
    "examples/notices/cn_24_minimal.xml"
)
OUTPUT = Path("procurement-admission-rehearsal-evidence.json")


def fetch_pinned_xml() -> bytes:
    parsed = urlparse(SOURCE_URL)
    expected_path = "/OP-TED/eForms-SDK/1.14.2/examples/notices/cn_24_minimal.xml"
    if (
        parsed.scheme != "https"
        or parsed.hostname != "raw.githubusercontent.com"
        or parsed.path != expected_path
        or parsed.query
        or parsed.fragment
        or parsed.username
        or parsed.password
        or parsed.port not in {None, 443}
    ):
        raise RuntimeError("Pinned official XML URL left the allowlist")
    with httpx.Client(timeout=20.0, follow_redirects=False) as client:
        response = client.get(
            SOURCE_URL,
            headers={"user-agent": "AXIGNAL/0.1 procurement-admission-rehearsal"},
        )
    if response.is_redirect or response.status_code != 200:
        raise RuntimeError("Pinned official XML retrieval failed closed")
    return response.content


def main() -> int:
    raw_xml = fetch_pinned_xml()
    parsed = TEDEFormsCN16Parser().parse(raw_xml)
    candidates = tuple(
        ProcurementCandidateEnvelope(candidate=item)
        for item in parsed.candidate_claims()
    )

    real_store = InMemoryProcurementAdmissionStore()
    real_result = ProcurementAdmissionRehearsal(store=real_store).decide(
        raw_xml=raw_xml,
        candidates=candidates,
        context=ProcurementAdmissionContext.current_ted_state(),
    )
    real_outcomes = Counter(item.outcome for item in real_result.decisions)
    if set(real_outcomes) != {"BLOCKED_SOURCE_NOT_PRODUCT_ADMITTED"}:
        raise RuntimeError("Current TED state produced an unblocked decision")
    if real_store.result_count or real_store.events:
        raise RuntimeError("Blocked source state wrote rehearsal persistence")

    sandbox_store = InMemoryProcurementAdmissionStore()
    sandbox = ProcurementAdmissionRehearsal(store=sandbox_store)
    first = sandbox.decide(
        raw_xml=raw_xml,
        candidates=candidates,
        context=ProcurementAdmissionContext.sandbox_rehearsal(),
    )
    event_count = len(sandbox_store.events)
    replay = sandbox.decide(
        raw_xml=raw_xml,
        candidates=candidates,
        context=ProcurementAdmissionContext.sandbox_rehearsal(),
    )
    if not replay.idempotent_replay or replay.batch_id != first.batch_id:
        raise RuntimeError("Procurement rehearsal replay was not idempotent")
    if len(sandbox_store.events) != event_count:
        raise RuntimeError("Idempotent replay appended duplicate events")

    rollback_store = InMemoryProcurementAdmissionStore()
    try:
        ProcurementAdmissionRehearsal(store=rollback_store).decide(
            raw_xml=raw_xml,
            candidates=candidates,
            context=ProcurementAdmissionContext.sandbox_rehearsal(),
            fail_after_first_decision=True,
        )
    except ProcurementAdmissionRehearsalError:
        pass
    else:
        raise RuntimeError("Forced procurement failpoint did not fire")
    if rollback_store.result_count or rollback_store.events:
        raise RuntimeError("Forced procurement failure left transaction residue")

    outcomes = Counter(item.outcome for item in first.decisions)
    if "ADMITTED_REDERIVED" in outcomes:
        raise RuntimeError("Sandbox emitted a canonical admission outcome")
    if first.canonical_claim_writes or first.model_calls or first.reviewer_canonical_writes:
        raise RuntimeError("Rehearsal authority boundary was violated")
    if first.sandbox_admissible_count < 1:
        raise RuntimeError("Official XML produced no sandbox-admissible claims")

    evidence = {
        "goal_id": "AXIGNAL-GOAL-001",
        "task_id": "AX-F8-T12",
        "profile_id": "ted-procurement-admission-rehearsal@0.1.0",
        "source_release": "OP-TED/eForms-SDK@1.14.2",
        "raw_content_hash": parsed.raw_content_hash,
        "raw_xml_persisted": False,
        "notice_values_persisted": False,
        "candidate_count": len(candidates),
        "current_source_state": "TECHNICAL_PROBE",
        "current_source_outcomes": dict(sorted(real_outcomes.items())),
        "current_source_store_writes": 0,
        "sandbox_outcomes": dict(sorted(outcomes.items())),
        "sandbox_admissible_count": first.sandbox_admissible_count,
        "sandbox_event_count": len(sandbox_store.events),
        "event_sequences_contiguous": [item.sequence for item in sandbox_store.events]
        == list(range(1, len(sandbox_store.events) + 1)),
        "idempotent_replay": replay.idempotent_replay,
        "replay_appended_events": False,
        "forced_rollback_residue_count": 0,
        "personal_values_emitted": False,
        "canonical_claim_writes": 0,
        "model_calls": 0,
        "reviewer_canonical_writes": 0,
        "source_product_admitted": False,
        "policy_production_enabled": False,
        "runtime_production_enabled": False,
        "universe_supported": False,
        "verified_at": datetime.now(UTC).isoformat(),
    }
    OUTPUT.write_text(json.dumps(evidence, indent=2, sort_keys=True), encoding="utf-8")
    print(
        "PASS procurement admission rehearsal",
        len(candidates),
        first.sandbox_admissible_count,
        dict(sorted(outcomes.items())),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
