#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

_ALLOWED_TRANSITIONS = {
    "DETECTED": {"QUALIFYING", "REJECTED"},
    "QUALIFYING": {"QUALIFIED", "REJECTED"},
    "QUALIFIED": {"PURSUIT_OPEN", "REJECTED"},
    "PURSUIT_OPEN": {"DECISION_PENDING"},
    "DECISION_PENDING": {"APPROVED", "DECLINED"},
    "APPROVED": {"IN_EXECUTION", "DECLINED"},
    "IN_EXECUTION": {"DECISION_PENDING", "SUBMITTED_OR_ACTIVATED", "LOST_OR_CLOSED"},
    "SUBMITTED_OR_ACTIVATED": {"WON_OR_REALIZED", "LOST_OR_CLOSED"},
    "WON_OR_REALIZED": {"LEARNING_CAPTURED"},
    "LOST_OR_CLOSED": {"LEARNING_CAPTURED"},
    "REJECTED": {"LEARNING_CAPTURED"},
    "DECLINED": {"LEARNING_CAPTURED"},
}

_EXTERNAL_ACTORS = {
    "HUMAN_SUBMISSION_AUTHORITY",
    "HUMAN_ACTIVATION_AUTHORITY",
}


def transition_allowed(current: str, target: str) -> bool:
    return target in _ALLOWED_TRANSITIONS.get(current, set())


def qualification_decision(
    required_context_complete: bool,
    disqualifier_present: bool,
    evidence_current: bool,
) -> str:
    if disqualifier_present:
        return "REJECTED"
    if not required_context_complete or not evidence_current:
        return "REVIEW_REQUIRED"
    return "QUALIFIED"


def work_readiness(dependency_states: Sequence[str]) -> str:
    if not dependency_states:
        return "BLOCKED"
    allowed = {"SATISFIED", "WAIVED_BY_HUMAN"}
    return "READY" if all(state in allowed for state in dependency_states) else "BLOCKED"


def approval_valid(
    state: str,
    requester_ref: str,
    approver_ref: str,
    subject_version_matches: bool,
    rights_active: bool,
    document_current: bool,
) -> bool:
    return all(
        (
            state == "APPROVED",
            bool(requester_ref),
            bool(approver_ref),
            requester_ref != approver_ref,
            subject_version_matches,
            rights_active,
            document_current,
        )
    )


def may_execute_external_action(
    actor_type: str,
    granted_approvals: set[str],
    required_approvals: set[str],
    rights_active: bool,
    document_current: bool,
    audit_chain_valid: bool,
) -> bool:
    return all(
        (
            actor_type in _EXTERNAL_ACTORS,
            required_approvals.issubset(granted_approvals),
            rights_active,
            document_current,
            audit_chain_valid,
        )
    )


def normalize_outcome(observed: bool, state: str | None) -> str:
    allowed = {
        "WON",
        "LOST",
        "NO_BID",
        "WITHDRAWN",
        "EXPIRED",
        "REALIZED",
        "NOT_REALIZED",
        "UNKNOWN",
    }
    if not observed or state is None:
        return "UNKNOWN"
    if state not in allowed:
        raise ValueError("unsupported outcome state")
    return state


def learning_state(actor_type: str, human_reviewed: bool) -> str:
    if actor_type == "MODEL":
        return "PROPOSED"
    if human_reviewed and actor_type == "HUMAN_LEARNING_AUTHORITY":
        return "REVIEWED"
    return "PROPOSED"


def canonical_digest(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def audit_event_hash(previous_hash: str, event: Mapping[str, Any]) -> str:
    return canonical_digest({"previous_event_hash": previous_hash, "event": event})


def import_authority(hash_valid: bool, schema_known: bool) -> str:
    if not hash_valid or not schema_known:
        return "QUARANTINE"
    return "CANDIDATE_ONLY"
