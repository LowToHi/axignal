#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

_AUTHORITY_RANK = {
    "REVOKED": 0,
    "SUPERSEDED": 1,
    "CONTESTED": 2,
    "CANDIDATE": 3,
    "REVIEWED": 4,
    "ADMITTED": 5,
}


def preserve_value_state(value: Any, state: str) -> tuple[Any, str]:
    allowed = {"KNOWN", "UNKNOWN", "UNAVAILABLE", "NOT_APPLICABLE", "ZERO"}
    if state not in allowed:
        raise ValueError("unsupported value state")
    if state == "ZERO" and value not in (0, Decimal("0")):
        raise ValueError("ZERO state requires a zero value")
    if state != "KNOWN" and state != "ZERO" and value is not None:
        raise ValueError("non-known value states cannot carry a value")
    return value, state


def resolve_interval(
    valid_from: datetime | None,
    valid_to: datetime | None,
    at: datetime,
) -> bool | None:
    if valid_from is None and valid_to is None:
        return None
    if valid_from is not None and at < valid_from:
        return False
    return not (valid_to is not None and at >= valid_to)


def convert_money(
    amount: Decimal,
    rate: Decimal | None,
    rate_at: datetime | None,
) -> Decimal:
    if rate is None or rate_at is None:
        raise ValueError("currency conversion requires rate and rate timestamp")
    if rate <= 0:
        raise ValueError("currency conversion rate must be positive")
    return amount * rate


def evaluate_rights(state: str, kill_switch: bool) -> str:
    if kill_switch:
        return "DENY"
    if state != "ALLOW":
        return "DENY"
    return "ALLOW"


def resolve_document_anchor(document_version: str, anchor_version: str) -> bool:
    if not document_version or not anchor_version:
        return False
    return document_version == anchor_version


def least_authority(states: list[str]) -> str:
    if not states:
        raise ValueError("at least one authority state is required")
    unknown = set(states) - set(_AUTHORITY_RANK)
    if unknown:
        raise ValueError(f"unknown authority states: {sorted(unknown)}")
    return min(states, key=_AUTHORITY_RANK.__getitem__)


def may_write_canonical(actor_type: str, human_approved: bool) -> bool:
    if not human_approved:
        return False
    return actor_type in {"HUMAN_DATA_AUTHORITY", "INDEPENDENT_ADMISSION_RUNTIME"}


def classify_entity_match(score: Decimal, deterministic_identifier_match: bool) -> str:
    if deterministic_identifier_match:
        return "CANDIDATE_MATCH"
    if score >= Decimal("0.95"):
        return "CANDIDATE_MATCH"
    return "UNRESOLVED"


def mapping_cardinality(source_count: int, target_count: int) -> str:
    if source_count < 1 or target_count < 1:
        raise ValueError("mapping sides cannot be empty")
    if source_count == 1 and target_count == 1:
        return "ONE_TO_ONE"
    if source_count == 1:
        return "ONE_TO_MANY"
    if target_count == 1:
        return "MANY_TO_ONE"
    return "MANY_TO_MANY"
