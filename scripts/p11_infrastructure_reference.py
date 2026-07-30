#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from decimal import Decimal
from typing import Any


def canonical_digest(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def project_current(
    *,
    status: str,
    version_current: bool,
    withdrawn: bool,
) -> str:
    if withdrawn or status in {"CANCELLED", "SUSPENDED", "CLOSED"}:
        return "DENY"
    if not version_current or status in {"UNKNOWN", "CONTESTED"}:
        return "REVIEW_REQUIRED"
    return "PASS"


def stage_evidence_decision(states: list[str]) -> str:
    if not states:
        return "REVIEW_REQUIRED"
    if any(state in {"SUPERSEDED", "WITHDRAWN"} for state in states):
        return "DENY"
    if any(
        state in {"UNKNOWN", "REPORTED", "EVIDENCED", "CONTESTED"}
        for state in states
    ):
        return "REVIEW_REQUIRED"
    if all(state == "VERIFIED" for state in states):
        return "PASS"
    return "REVIEW_REQUIRED"


def financing_decision(
    *,
    project_cost: Decimal,
    committed_debt: Decimal,
    committed_equity: Decimal,
    grant_support: Decimal,
    state: str,
    observed_evidence: bool,
) -> str:
    values = (
        project_cost,
        committed_debt,
        committed_equity,
        grant_support,
    )
    if any(value < 0 for value in values) or project_cost <= 0:
        return "DENY"
    committed = committed_debt + committed_equity + grant_support
    if committed > project_cost:
        return "DENY"
    if state == "WITHDRAWN":
        return "DENY"
    if state in {"COMMITTED", "FINANCIAL_CLOSE"} and observed_evidence:
        return "PASS"
    return "REVIEW_REQUIRED"


def permit_land_decision(required_states: Mapping[str, str]) -> str:
    if not required_states:
        return "REVIEW_REQUIRED"
    denied = {"REJECTED", "EXPIRED_OR_REVOKED"}
    pending = {
        "NOT_IDENTIFIED",
        "REQUIRED",
        "APPLIED",
        "UNDER_REVIEW",
    }
    if any(state in denied for state in required_states.values()):
        return "DENY"
    if any(state in pending for state in required_states.values()):
        return "REVIEW_REQUIRED"
    if all(
        state in {"GRANTED", "SECURED"}
        for state in required_states.values()
    ):
        return "PASS"
    return "REVIEW_REQUIRED"


def project_readiness(
    gates: Mapping[str, str],
    required_gates: list[str],
) -> str:
    if any(gate not in gates for gate in required_gates):
        return "NOT_READY"
    values = [gates[gate] for gate in required_gates]
    if any(value in {"DENY", "BLOCK"} for value in values):
        return "DENY"
    if any(
        value in {
            "UNKNOWN",
            "INDETERMINATE",
            "CONTESTED",
            "STALE",
            "REVIEW_REQUIRED",
        }
        for value in values
    ):
        return "REVIEW_REQUIRED"
    if all(value == "PASS" for value in values):
        return "READY"
    return "NOT_READY"


def may_execute_external_action(
    *,
    actor_type: str,
    readiness: str,
    approvals_current: bool,
    rights_active: bool,
    project_is_current: bool,
    channel_verified: bool,
    audit_chain_valid: bool,
    kill_switch_active: bool,
) -> bool:
    return (
        actor_type == "HUMAN_EXTERNAL_ACTION_AUTHORITY"
        and readiness == "READY"
        and approvals_current
        and rights_active
        and project_is_current
        and channel_verified
        and audit_chain_valid
        and not kill_switch_active
    )


def normalize_project_outcome(
    state: str,
    *,
    observed_evidence: bool,
) -> str:
    allowed = {
        "ANNOUNCED",
        "APPROVED",
        "FINANCED",
        "FINANCIAL_CLOSE",
        "TENDER_PUBLISHED",
        "CONTRACT_AWARDED",
        "CONTRACT_SIGNED",
        "CONSTRUCTION_STARTED",
        "OPERATIONAL",
        "SUSPENDED",
        "CANCELLED",
        "COMPLETED",
    }
    if not observed_evidence or state not in allowed:
        return "UNKNOWN"
    return state


def imported_authority(_: str) -> str:
    return "CANDIDATE_ONLY"
