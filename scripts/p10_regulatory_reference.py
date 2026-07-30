#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from datetime import datetime


def canonical_digest(payload: object) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def instrument_current(
    legal_status: str,
    repealed: bool,
    amendment_reconciled: bool,
    source_active: bool,
) -> bool:
    return (
        legal_status in {"PUBLISHED", "EFFECTIVE", "APPLICABLE"}
        and not repealed
        and amendment_reconciled
        and source_active
    )


def legal_effect_decision(
    adopted: bool,
    published: bool,
    effective_at: datetime | None,
    applicable_at: datetime | None,
    now: datetime,
    binding_authority_verified: bool,
) -> str:
    if not binding_authority_verified:
        return "REVIEW_REQUIRED"
    if not adopted or not published:
        return "NOT_BINDING"
    if effective_at is None or applicable_at is None:
        return "REVIEW_REQUIRED"
    if any(value.tzinfo is None for value in (effective_at, applicable_at, now)):
        return "REVIEW_REQUIRED"
    if now < effective_at:
        return "NOT_YET_EFFECTIVE"
    if now < applicable_at:
        return "TRANSITION"
    return "APPLICABLE"


def applicability_decision(
    mandatory_states: Iterable[str],
    hierarchy_conflict: bool,
    verified_exemption: bool,
) -> str:
    states = list(mandatory_states)
    if hierarchy_conflict:
        return "REVIEW_REQUIRED"
    if any(state == "FAIL" for state in states):
        return "DOES_NOT_APPLY"
    if any(
        state in {"UNKNOWN", "PENDING_EVIDENCE", "CONTESTED"}
        for state in states
    ):
        return "REVIEW_REQUIRED"
    if verified_exemption:
        return "EXEMPT"
    if states and all(
        state in {"PASS", "NOT_APPLICABLE"} for state in states
    ):
        return "APPLIES"
    return "NOT_READY"


def control_coverage_decision(
    requirement_states: Mapping[str, str],
    required_requirements: set[str],
) -> str:
    if set(requirement_states) != required_requirements:
        return "NOT_READY"
    values = set(requirement_states.values())
    if "INEFFECTIVE" in values or "DENY" in values:
        return "DENY"
    if values & {"UNKNOWN", "NOT_MAPPED", "PROPOSED", "CONTESTED"}:
        return "REVIEW_REQUIRED"
    if values <= {"IMPLEMENTED", "TESTED", "EFFECTIVE"}:
        return "PASS"
    return "NOT_READY"


def market_entry_readiness(
    gates: Mapping[str, str],
    required_gates: set[str],
) -> str:
    if set(gates) != required_gates:
        return "NOT_READY"
    values = set(gates.values())
    if "DENY" in values:
        return "DENY"
    if values & {"UNKNOWN", "INDETERMINATE", "CONTESTED", "STALE"}:
        return "REVIEW_REQUIRED"
    if values == {"PASS"}:
        return "READY"
    return "NOT_READY"


def may_file_regulatory_action(
    actor_type: str,
    readiness: str,
    approvals_present: set[str],
    approvals_required: set[str],
    instrument_current_state: bool,
    rights_permit: bool,
    recipient_authority_verified: bool,
    channel_verified: bool,
    kill_switch_active: bool,
    audit_chain_valid: bool,
) -> bool:
    return (
        actor_type == "HUMAN_FILING_AUTHORITY"
        and readiness == "READY"
        and approvals_required.issubset(approvals_present)
        and instrument_current_state
        and rights_permit
        and recipient_authority_verified
        and channel_verified
        and not kill_switch_active
        and audit_chain_valid
    )


def normalize_enforcement_outcome(observed: bool, state: str) -> str:
    allowed = {
        "AUTHORISED",
        "CONDITIONALLY_AUTHORISED",
        "REJECTED",
        "INSPECTION_OPEN",
        "NON_COMPLIANCE_FOUND",
        "SANCTIONED",
        "REMEDIATED",
        "CLOSED",
    }
    if not observed or state not in allowed:
        return "UNKNOWN"
    return state


def imported_authority(
    hashes_valid: bool,
    schema_known: bool,
    rights_permit: bool,
) -> str:
    if not hashes_valid or not schema_known or not rights_permit:
        return "QUARANTINE"
    return "CANDIDATE_ONLY"
