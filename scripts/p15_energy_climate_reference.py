#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import Any

OPERATIONAL_PROJECT_STATES = {
    "COMMISSIONING",
    "OPERATIONAL",
}


def canonical_digest(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def project_status_decision(
    *,
    state: str,
    evidence_current: bool,
    announced_only: bool,
    rights_active: bool,
) -> str:
    if not rights_active or state in {"CANCELLED", "SUSPENDED"}:
        return "DENY"
    if announced_only or not evidence_current:
        return "REVIEW_REQUIRED"
    if state in OPERATIONAL_PROJECT_STATES:
        return "PASS"
    if state in {
        "ANNOUNCED",
        "DEVELOPMENT",
        "PERMITTING",
        "FINANCING",
        "PROCUREMENT",
        "CONSTRUCTION",
    }:
        return "REVIEW_REQUIRED"
    return "DENY"


def capacity_decision(
    *,
    capacity_type: str,
    value: Decimal | None,
    unit_known: bool,
    period_known: bool,
    observed: bool,
    grid_connected: bool,
) -> str:
    if value is None or value < 0 or not unit_known:
        return "DENY"
    if capacity_type in {
        "OPERATIONAL_CAPACITY",
        "AVAILABLE_CAPACITY",
        "GENERATED_ENERGY",
        "CURTAILED_ENERGY",
    }:
        if observed and period_known and grid_connected:
            return "PASS"
        return "REVIEW_REQUIRED"
    if capacity_type in {
        "ANNOUNCED_NAMEPLATE",
        "PERMITTED_NAMEPLATE",
        "CONTRACTED_NAMEPLATE",
        "INSTALLED_NAMEPLATE",
        "CONNECTED_CAPACITY",
        "UNKNOWN",
    }:
        return "REVIEW_REQUIRED"
    return "DENY"


def grid_connection_decision(
    *,
    state: str,
    observed: bool,
    current: bool,
    energised: bool,
) -> str:
    if state in {"REJECTED", "WITHDRAWN", "EXPIRED"}:
        return "DENY"
    if not observed or not current:
        return "REVIEW_REQUIRED"
    if state == "ENERGISED":
        return "PASS" if energised else "REVIEW_REQUIRED"
    if state in {
        "APPLICATION_SUBMITTED",
        "QUEUE_ASSIGNED",
        "OFFER_ISSUED",
        "AGREEMENT_SIGNED",
        "CONSTRUCTION_PENDING",
    }:
        return "REVIEW_REQUIRED"
    return "DENY"


def support_mechanism_decision(
    *,
    state: str,
    jurisdiction_resolved: bool,
    effective_date_current: bool,
    award_observed: bool,
    legal_review_current: bool,
) -> str:
    if state in {"EXPIRED", "REPEALED", "EXHAUSTED", "WITHDRAWN"}:
        return "DENY"
    if not jurisdiction_resolved or not effective_date_current:
        return "REVIEW_REQUIRED"
    if state == "AWARDED" and award_observed and legal_review_current:
        return "PASS"
    return "REVIEW_REQUIRED"


def emissions_decision(
    *,
    value_class: str,
    value: Decimal | None,
    method_present: bool,
    boundary_present: bool,
    period_present: bool,
    observed: bool,
) -> str:
    if value is None or value < 0:
        return "DENY"
    if not method_present or not boundary_present or not period_present:
        return "REVIEW_REQUIRED"
    if value_class in {"MEASURED", "REPORTED"} and observed:
        return "PASS"
    if value_class in {
        "CALCULATED",
        "ESTIMATED",
        "MODELLED",
        "EMISSION_FACTOR",
        "AVOIDED_ESTIMATE",
        "OFFSET_QUANTITY",
        "TARGET",
        "UNKNOWN",
    }:
        return "REVIEW_REQUIRED"
    return "DENY"


def transition_readiness(
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


def normalize_transition_outcome(
    outcome: str,
    *,
    observed_evidence: bool,
) -> str:
    allowed = {
        "NO_ACTION",
        "MONITORING_CONTINUES",
        "CONTACTED",
        "INFORMATION_RECEIVED",
        "SUPPORT_APPLICATION_SUBMITTED",
        "GRID_APPLICATION_SUBMITTED",
        "GRID_CONNECTION_GRANTED",
        "OFFTAKE_SIGNED",
        "FINANCIAL_CLOSE_REACHED",
        "CONSTRUCTION_STARTED",
        "CAPACITY_COMMISSIONED",
        "COMMERCIAL_OPERATION",
        "DECLINED",
        "LOST_OR_CLOSED",
    }
    if observed_evidence and outcome in allowed:
        return outcome
    return "UNKNOWN"


def imported_authority(_: str) -> str:
    return "CANDIDATE_ONLY"
