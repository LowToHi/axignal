#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import Any


def canonical_digest(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def filing_current(
    *,
    status: str,
    version_current: bool,
    withdrawn: bool,
    superseded: bool,
) -> str:
    if withdrawn or status in {"WITHDRAWN", "REVOKED", "REJECTED"}:
        return "DENY"
    if superseded or not version_current:
        return "REVIEW_REQUIRED"
    if status in {"PUBLISHED", "ACCEPTED", "CURRENT"}:
        return "PASS"
    return "REVIEW_REQUIRED"


def ownership_decision(
    *,
    observed: bool,
    rights_active: bool,
    percentage: Decimal | None,
    chain_complete: bool,
    contested: bool,
    beneficial_owner: bool,
    beneficial_owner_authorised: bool,
) -> str:
    if not rights_active:
        return "DENY"
    if beneficial_owner and not beneficial_owner_authorised:
        return "DENY"
    if contested:
        return "REVIEW_REQUIRED"
    if not observed or not chain_complete or percentage is None:
        return "REVIEW_REQUIRED"
    if percentage < Decimal("0") or percentage > Decimal("100"):
        return "DENY"
    return "PASS"


def control_decision(
    *,
    basis: str,
    observed: bool,
    contested: bool,
) -> str:
    if contested:
        return "REVIEW_REQUIRED"
    if basis in {"UNKNOWN", "INFERRED_ONLY", "OWNERSHIP_ONLY"}:
        return "REVIEW_REQUIRED"
    if observed and basis in {
        "VOTING_MAJORITY",
        "AGREEMENT",
        "BOARD_APPOINTMENT_RIGHT",
        "REGISTRY_DECLARATION",
    }:
        return "PASS"
    return "REVIEW_REQUIRED"


def personal_data_decision(
    *,
    purpose_bound: bool,
    legal_basis_recorded: bool,
    minimised: bool,
    rights_active: bool,
) -> str:
    if not rights_active:
        return "DENY"
    if all((purpose_bound, legal_basis_recorded, minimised)):
        return "PASS"
    return "DENY"


def corporate_action_decision(
    *,
    state: str,
    observed_evidence: bool,
    required_approvals_observed: bool,
) -> str:
    if state in {"CANCELLED", "TERMINATED", "REJECTED"}:
        return "DENY"
    if state == "COMPLETED":
        if observed_evidence and required_approvals_observed:
            return "PASS"
        return "REVIEW_REQUIRED"
    if state in {"ANNOUNCED", "RUMOURED", "PROPOSED", "AGREED", "PENDING"}:
        return "REVIEW_REQUIRED"
    return "REVIEW_REQUIRED"


def account_readiness(
    gate_results: Mapping[str, str],
    required_gates: Sequence[str],
) -> str:
    if not gate_results or any(gate not in gate_results for gate in required_gates):
        return "NOT_READY"
    values = [gate_results[gate] for gate in required_gates]
    if any(value == "DENY" for value in values):
        return "DENY"
    if any(value != "PASS" for value in values):
        return "REVIEW_REQUIRED"
    return "READY"


def may_execute_external_action(
    *,
    actor_type: str,
    readiness: str,
    approvals_current: bool,
    rights_active: bool,
    privacy_cleared: bool,
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
            privacy_cleared,
            recipient_verified,
            channel_verified,
            audit_chain_valid,
            not kill_switch_active,
        )
    )


def normalize_account_outcome(
    outcome: str,
    *,
    observed_evidence: bool,
) -> str:
    allowed = {
        "NO_ACTION",
        "MONITORING_CONTINUES",
        "CONTACTED",
        "MEETING_HELD",
        "QUALIFIED_INTEREST",
        "OPPORTUNITY_OPENED",
        "DUE_DILIGENCE_STARTED",
        "NON_BINDING_INDICATION_SUBMITTED",
        "TRANSACTION_SIGNED",
        "TRANSACTION_COMPLETED",
        "DECLINED",
        "LOST_OR_CLOSED",
    }
    if observed_evidence and outcome in allowed:
        return outcome
    return "UNKNOWN"


def imported_authority(_: str) -> str:
    return "CANDIDATE_ONLY"
