#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from decimal import Decimal
from typing import Iterable, Mapping


def canonical_digest(payload: object) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def call_current(
    state: str,
    withdrawn: bool,
    amendment_reconciled: bool,
    source_active: bool,
) -> bool:
    return (
        state in {"OPEN", "AMENDED"}
        and not withdrawn
        and amendment_reconciled
        and source_active
    )


def deadline_open(
    now: datetime,
    deadline: datetime,
    timezone_known: bool,
    calendar_known: bool,
) -> bool:
    if not timezone_known or not calendar_known:
        return False
    if now.tzinfo is None or deadline.tzinfo is None:
        return False
    return now < deadline


def eligibility_decision(
    mandatory_states: Iterable[str],
    active_exclusions: Iterable[str],
) -> str:
    states = list(mandatory_states)
    exclusions = list(active_exclusions)
    if exclusions:
        return "DENY"
    if any(state == "FAIL" for state in states):
        return "DENY"
    if any(state in {"UNKNOWN", "PENDING_EVIDENCE", "CONTESTED"} for state in states):
        return "REVIEW_REQUIRED"
    if states and all(state in {"PASS", "NOT_APPLICABLE"} for state in states):
        return "PASS"
    return "NOT_READY"


def consortium_decision(
    required_roles: set[str],
    assigned_roles: set[str],
    partner_count: int,
    minimum_partners: int,
    maximum_partners: int | None,
    jurisdictions_satisfied: bool,
    independence_known: bool,
) -> str:
    if not required_roles.issubset(assigned_roles):
        return "DENY"
    if partner_count < minimum_partners:
        return "DENY"
    if maximum_partners is not None and partner_count > maximum_partners:
        return "DENY"
    if not jurisdictions_satisfied:
        return "DENY"
    if not independence_known:
        return "REVIEW_REQUIRED"
    return "PASS"


def validate_funding_request(
    eligible_cost: Decimal,
    requested_grant: Decimal,
    maximum_rate: Decimal,
    call_ceiling: Decimal,
    cofinancing_confirmed: bool,
) -> str:
    if min(eligible_cost, requested_grant, maximum_rate, call_ceiling) < Decimal("0"):
        return "DENY"
    if requested_grant > eligible_cost:
        return "DENY"
    if requested_grant > call_ceiling:
        return "DENY"
    if eligible_cost and requested_grant / eligible_cost > maximum_rate:
        return "DENY"
    if not cofinancing_confirmed:
        return "REVIEW_REQUIRED"
    return "PASS"


def application_readiness(gates: Mapping[str, str], required_gates: set[str]) -> str:
    if set(gates) != required_gates:
        return "NOT_READY"
    values = set(gates.values())
    if "DENY" in values:
        return "DENY"
    if values & {"UNKNOWN", "INDETERMINATE", "CONTESTED"}:
        return "REVIEW_REQUIRED"
    if values == {"PASS"}:
        return "READY"
    return "NOT_READY"


def may_submit_application(
    actor_type: str,
    readiness: str,
    approvals_present: set[str],
    approvals_required: set[str],
    rights_permit: bool,
    call_current_state: bool,
    channel_verified: bool,
    kill_switch_active: bool,
    audit_chain_valid: bool,
) -> bool:
    return (
        actor_type == "HUMAN_SUBMISSION_AUTHORITY"
        and readiness == "READY"
        and approvals_required.issubset(approvals_present)
        and rights_permit
        and call_current_state
        and channel_verified
        and not kill_switch_active
        and audit_chain_valid
    )


def normalize_award(observed: bool, state: str) -> str:
    allowed = {
        "REJECTED",
        "RESERVE_LIST",
        "AWARDED",
        "AGREEMENT_PENDING",
        "AGREEMENT_SIGNED",
        "PAYMENT_PENDING",
        "PAID",
        "TERMINATED",
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
