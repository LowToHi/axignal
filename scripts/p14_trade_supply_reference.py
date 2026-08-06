#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import Any

OBSERVED_FLOW_CLASSES = {
    "REPORTED_VALUE",
    "REPORTED_QUANTITY",
    "NET_WEIGHT",
    "GROSS_WEIGHT",
    "UNIT_VALUE",
    "INDEX",
    "SHARE",
    "GROWTH_RATE",
}


def canonical_digest(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def flow_observation_decision(
    *,
    value_class: str,
    period_known: bool,
    vintage_current: bool,
    unit_known: bool,
    missing: bool,
    rights_active: bool,
) -> str:
    if not rights_active:
        return "DENY"
    if missing:
        return "REVIEW_REQUIRED"
    if not period_known or not vintage_current or not unit_known:
        return "REVIEW_REQUIRED"
    if value_class in OBSERVED_FLOW_CLASSES:
        return "PASS"
    if value_class in {"ESTIMATE", "UNKNOWN"}:
        return "REVIEW_REQUIRED"
    return "DENY"


def classification_decision(
    *,
    source_code_present: bool,
    taxonomy_version_present: bool,
    mapping_observed: bool,
    ambiguous: bool,
) -> str:
    if not source_code_present or not taxonomy_version_present:
        return "DENY"
    if ambiguous or not mapping_observed:
        return "REVIEW_REQUIRED"
    return "PASS"


def customs_measure_decision(
    *,
    state: str,
    jurisdiction_resolved: bool,
    effective_date_current: bool,
    observed: bool,
    legal_review_current: bool,
) -> str:
    if state in {"REPEALED", "EXPIRED", "WITHDRAWN"}:
        return "DENY"
    if not jurisdiction_resolved or not effective_date_current:
        return "REVIEW_REQUIRED"
    if observed and legal_review_current and state == "IN_FORCE":
        return "PASS"
    return "REVIEW_REQUIRED"


def route_event_decision(
    *,
    event_type: str,
    observed: bool,
    status_current: bool,
    closure_confirmed: bool,
) -> str:
    if not observed or not status_current:
        return "REVIEW_REQUIRED"
    if event_type == "PORT_CLOSURE":
        return "PASS" if closure_confirmed else "REVIEW_REQUIRED"
    if event_type in {
        "PORT_DISRUPTION",
        "CANAL_DISRUPTION",
        "BORDER_DELAY",
        "RAIL_DISRUPTION",
        "ROAD_DISRUPTION",
        "AIR_CARGO_DISRUPTION",
        "CAPACITY_CONSTRAINT",
        "ROUTE_CHANGE",
        "EVENT_RESOLVED",
    }:
        return "PASS"
    return "REVIEW_REQUIRED"


def flow_value_valid(
    *,
    value: Decimal | None,
    missing: bool,
    suppressed: bool,
) -> str:
    if missing or suppressed or value is None:
        return "UNKNOWN"
    if value < 0:
        return "REVIEW_REQUIRED"
    return "OBSERVED"


def supply_readiness(
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


def normalize_supply_outcome(outcome: str, *, observed_evidence: bool) -> str:
    allowed = {
        "NO_ACTION",
        "MONITORING_CONTINUES",
        "CONTACTED",
        "QUOTATION_RECEIVED",
        "MEETING_HELD",
        "DUE_DILIGENCE_STARTED",
        "SUPPLY_OPTION_OPENED",
        "PILOT_ORDER_APPROVED",
        "ORDER_PLACED",
        "CAPACITY_BOOKED",
        "CUSTOMS_FILING_SUBMITTED",
        "DECLINED",
        "LOST_OR_CLOSED",
    }
    if observed_evidence and outcome in allowed:
        return outcome
    return "UNKNOWN"


def imported_authority(_: str) -> str:
    return "CANDIDATE_ONLY"
