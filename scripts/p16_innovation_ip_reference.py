#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any


CURRENT_PATENT_STATES = {
    "APPLICATION_FILED",
    "APPLICATION_PUBLISHED",
    "SEARCH_REPORT_ISSUED",
    "EXAMINATION_PENDING",
    "PATENT_GRANTED",
    "OPPOSITION_PENDING",
    "PATENT_MAINTAINED",
}

TERMINAL_PATENT_STATES = {
    "PATENT_LAPSED",
    "PATENT_EXPIRED",
    "PATENT_REVOKED",
}

OBSERVED_RELATIONSHIPS = {
    "OBSERVED_APPLICANT",
    "OBSERVED_ASSIGNEE",
    "OBSERVED_INVENTOR",
    "OBSERVED_AUTHOR",
    "OBSERVED_AFFILIATION",
    "OBSERVED_FUNDER",
}


def canonical_digest(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def patent_status_decision(
    *,
    state: str,
    jurisdiction_resolved: bool,
    status_current: bool,
    observed: bool,
    rights_active: bool,
) -> str:
    if not rights_active:
        return "DENY"
    if state in TERMINAL_PATENT_STATES:
        return "DENY" if observed and status_current else "REVIEW_REQUIRED"
    if not jurisdiction_resolved or not status_current or not observed:
        return "REVIEW_REQUIRED"
    if state in CURRENT_PATENT_STATES:
        return "PASS"
    return "REVIEW_REQUIRED"


def grant_claim_decision(
    *,
    source_state: str,
    grant_event_observed: bool,
    jurisdiction_resolved: bool,
    status_current: bool,
) -> str:
    if source_state != "PATENT_GRANTED":
        return "DENY"
    if not grant_event_observed:
        return "REVIEW_REQUIRED"
    if not jurisdiction_resolved or not status_current:
        return "REVIEW_REQUIRED"
    return "PASS"


def relationship_decision(
    *,
    relationship_class: str,
    exact_entity: bool,
    time_current: bool,
    lawful_scope: bool,
) -> str:
    if not lawful_scope:
        return "DENY"
    if not exact_entity or not time_current:
        return "REVIEW_REQUIRED"
    if relationship_class in OBSERVED_RELATIONSHIPS:
        return "PASS"
    if relationship_class.startswith("PROPOSED_"):
        return "REVIEW_REQUIRED"
    return "REVIEW_REQUIRED"


def citation_decision(
    *,
    citation_observed: bool,
    source_current: bool,
    legal_conclusion_requested: bool,
) -> str:
    if legal_conclusion_requested:
        return "DENY"
    if not citation_observed or not source_current:
        return "REVIEW_REQUIRED"
    return "PASS"


def research_output_decision(
    *,
    output_type: str,
    published: bool,
    withdrawn: bool,
    rights_active: bool,
    peer_reviewed_claim: bool,
) -> str:
    if not rights_active or withdrawn:
        return "DENY"
    if not published:
        return "REVIEW_REQUIRED"
    if output_type == "PREPRINT" and peer_reviewed_claim:
        return "DENY"
    return "PASS"


def licence_signal_decision(
    *,
    state: str,
    observed: bool,
    terms_current: bool,
    executed_evidence: bool,
) -> str:
    if state == "EXECUTED":
        if observed and terms_current and executed_evidence:
            return "PASS"
        return "REVIEW_REQUIRED"
    if state in {"EXPIRED", "TERMINATED", "WITHDRAWN"}:
        return "DENY"
    if observed and terms_current:
        return "REVIEW_REQUIRED"
    return "REVIEW_REQUIRED"


def innovation_readiness(
    gates: Mapping[str, str],
    required: Sequence[str],
) -> str:
    if not gates or any(gate not in gates for gate in required):
        return "NOT_READY"
    values = [gates[gate] for gate in required]
    if "DENY" in values or "BLOCK" in values:
        return "DENY"
    if all(value == "PASS" for value in values):
        return "READY"
    return "REVIEW_REQUIRED"


def may_execute_external_action(
    *,
    actor_type: str,
    readiness: str,
    approvals_current: bool,
    rights_active: bool,
    legal_review_current: bool,
    recipient_verified: bool,
    channel_verified: bool,
    audit_chain_valid: bool,
    kill_switch_active: bool,
) -> bool:
    return all(
        (
            actor_type == "HUMAN_EXTERNAL_ACTION_AUTHORITY",
            readiness == "READY",
            approvals_current,
            rights_active,
            legal_review_current,
            recipient_verified,
            channel_verified,
            audit_chain_valid,
            not kill_switch_active,
        )
    )


def normalize_innovation_outcome(
    outcome: str,
    *,
    observed_evidence: bool,
) -> str:
    allowed = {
        "NO_ACTION",
        "MONITORING_CONTINUES",
        "BRIEF_PUBLISHED",
        "DOSSIER_SHARED",
        "INSTITUTION_CONTACTED",
        "DISCUSSION_OPENED",
        "LICENSING_ENQUIRY_SUBMITTED",
        "DUE_DILIGENCE_STARTED",
        "PILOT_APPROVED",
        "LICENCE_NEGOTIATION_OPENED",
        "DECLINED",
        "CLOSED",
    }
    if observed_evidence and outcome in allowed:
        return outcome
    return "UNKNOWN"


def imported_authority(_: str) -> str:
    return "CANDIDATE_ONLY"
