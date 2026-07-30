#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any


def notice_currentness(
    state: str,
    amendment_pending: bool,
    rights_active: bool,
) -> str:
    if state in {"WITHDRAWN", "CANCELLED", "SUPERSEDED"} or not rights_active:
        return "DENY"
    if amendment_pending or state in {"AMENDED", "CONTESTED"}:
        return "REVIEW_REQUIRED"
    return "PASS" if state == "CURRENT" else "REVIEW_REQUIRED"


def deadline_decision(
    now_iso: str,
    deadline_iso: str | None,
    timezone_known: bool,
    amendment_pending: bool,
) -> str:
    if deadline_iso is None or not timezone_known:
        return "REVIEW_REQUIRED"
    if amendment_pending:
        return "REVIEW_REQUIRED"
    now = datetime.fromisoformat(now_iso)
    deadline = datetime.fromisoformat(deadline_iso)
    if now.tzinfo is None or deadline.tzinfo is None:
        return "REVIEW_REQUIRED"
    return "PASS" if now < deadline else "DENY"


def eligibility_decision(
    mandatory_total: int,
    satisfied_total: int,
    unknown_total: int,
    active_exclusion_ground: bool,
) -> str:
    if active_exclusion_ground:
        return "FAIL"
    if unknown_total > 0:
        return "REVIEW_REQUIRED"
    return "PASS" if satisfied_total == mandatory_total else "FAIL"


def lot_selection_decision(
    selected: set[str],
    available: set[str],
    exclusive_pairs: set[frozenset[str]],
) -> str:
    if not selected or not selected <= available:
        return "DENY"
    for pair in exclusive_pairs:
        if pair <= selected:
            return "DENY"
    return "PASS"


def requirement_coverage(
    mandatory: set[str],
    covered: set[str],
    contradicted: set[str],
    unknown: set[str],
) -> str:
    if mandatory & contradicted:
        return "DENY"
    if mandatory & unknown:
        return "REVIEW_REQUIRED"
    return "PASS" if mandatory <= covered else "NOT_READY"


def readiness_decision(gates: dict[str, str]) -> str:
    if not gates:
        return "DENY"
    values = set(gates.values())
    if "DENY" in values:
        return "DENY"
    if "REVIEW_REQUIRED" in values or "INDETERMINATE" in values:
        return "REVIEW_REQUIRED"
    return "READY" if values == {"PASS"} else "NOT_READY"


def commercial_validation(
    amount_known: bool,
    currency_known: bool,
    tax_known: bool,
    conversion_required: bool,
    rate_ref_present: bool,
) -> str:
    if not amount_known or not currency_known or not tax_known:
        return "DENY"
    if conversion_required and not rate_ref_present:
        return "DENY"
    return "PASS"


def may_submit(
    actor: str,
    readiness: str,
    approvals_current: bool,
    notice_current: bool,
    deadline_valid: bool,
    channel_verified: bool,
) -> bool:
    return (
        actor == "HUMAN_SUBMISSION_AUTHORITY"
        and readiness == "READY"
        and approvals_current
        and notice_current
        and deadline_valid
        and channel_verified
    )


def normalize_award(observed: bool, state: str) -> str:
    if not observed:
        return "UNKNOWN"
    allowed = {"AWARD_OBSERVED", "CONTRACT_OBSERVED", "CLOSED"}
    return state if state in allowed else "UNKNOWN"


def canonical_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
