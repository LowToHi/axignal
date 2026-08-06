#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import Any

OBSERVED_VALUE_CLASSES = {
    "OBSERVED",
    "PROVISIONAL",
    "ESTIMATED",
    "REVISED",
    "BENCHMARK",
    "DERIVED",
}
NON_OBSERVED_VALUE_CLASSES = {"FORECAST", "SCENARIO", "TARGET", "UNKNOWN"}
OBSERVED_OUTCOMES = {
    "NO_ACTION",
    "MONITORING",
    "STRATEGY_APPROVED",
    "BRIEF_PUBLISHED",
    "MEETING_HELD",
    "MARKET_REVIEW_OPENED",
    "PILOT_AUTHORISED",
    "BUDGET_ALLOCATED",
    "CAPITAL_COMMITTED",
    "MARKET_ENTRY_STARTED",
    "DECLINED",
    "CLOSED",
}


def canonical_digest(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def indicator_current(
    *,
    value_class: str,
    vintage_current: bool,
    withdrawn: bool,
    rights_active: bool,
) -> str:
    if withdrawn or not rights_active:
        return "DENY"
    if not vintage_current or value_class in NON_OBSERVED_VALUE_CLASSES:
        return "REVIEW_REQUIRED"
    if value_class in OBSERVED_VALUE_CLASSES:
        return "PASS"
    return "DENY"


def comparability_decision(
    *,
    unit: bool,
    scale: bool,
    currency: bool,
    price_basis: bool,
    frequency: bool,
    lineage: bool,
) -> str:
    if not lineage:
        return "DENY"
    if all((unit, scale, currency, price_basis, frequency)):
        return "PASS"
    return "REVIEW_REQUIRED"


def public_finance_decision(
    *,
    state: str,
    amount: Decimal | None,
    observed: bool,
    rights_active: bool,
) -> str:
    if not rights_active or state == "CANCELLED":
        return "DENY"
    if amount is not None and amount < 0:
        return "DENY"
    if state in {"DISBURSED", "PAID"} and observed and amount is not None:
        return "PASS"
    return "REVIEW_REQUIRED"


def strategy_readiness(
    gates: Mapping[str, str],
    required: Sequence[str],
) -> str:
    if not gates or any(gate not in gates for gate in required):
        return "NOT_READY"
    values = [gates[gate] for gate in required]
    if "DENY" in values:
        return "DENY"
    if all(value == "PASS" for value in values):
        return "READY"
    return "REVIEW_REQUIRED"


def may_execute_external_action(
    *,
    actor_type: str,
    readiness: str,
    approvals: bool,
    rights: bool,
    document: bool,
    recipient: bool,
    channel: bool,
    audit: bool,
    kill_switch: bool,
) -> bool:
    return all(
        (
            actor_type == "HUMAN_EXTERNAL_ACTION_AUTHORITY",
            readiness == "READY",
            approvals,
            rights,
            document,
            recipient,
            channel,
            audit,
            not kill_switch,
        )
    )


def normalize_outcome(outcome: str, *, observed: bool) -> str:
    if observed and outcome in OBSERVED_OUTCOMES:
        return outcome
    return "UNKNOWN"


def imported_authority(_: str) -> str:
    return "CANDIDATE_ONLY"
