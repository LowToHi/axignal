#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import math
from datetime import UTC, datetime
from typing import Any


def canonical_digest(value: Any) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def parse_timestamp(value: str) -> datetime:
    normalised = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalised)
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include timezone")
    return parsed.astimezone(UTC)


def as_of_record_eligible(
    *,
    available_at: str,
    cutoff_at: str,
    revision_available_at: str | None = None,
) -> dict[str, Any]:
    cutoff = parse_timestamp(cutoff_at)
    available = parse_timestamp(available_at)
    if available > cutoff:
        return {"decision": "DENY", "reason": "FUTURE_DATA_LEAKAGE"}
    if revision_available_at is not None:
        revision = parse_timestamp(revision_available_at)
        if revision > cutoff:
            return {"decision": "DENY", "reason": "VINTAGE_LEAKAGE"}
    return {"decision": "ALLOW", "reason": "AS_OF_AVAILABLE"}


def binary_scores(probability: float, outcome: int) -> dict[str, float]:
    if not 0.0 <= probability <= 1.0:
        raise ValueError("probability must be between zero and one")
    if outcome not in {0, 1}:
        raise ValueError("outcome must be binary")
    clipped = min(max(probability, 1e-15), 1.0 - 1e-15)
    brier = (probability - outcome) ** 2
    log_loss = -(
        outcome * math.log(clipped)
        + (1 - outcome) * math.log(1.0 - clipped)
    )
    return {"brier_score": brier, "log_loss": log_loss}


def reconcile_outcome(
    *,
    state: str,
    evidence_complete: bool,
    censored: bool = False,
    contested: bool = False,
) -> dict[str, str]:
    if contested:
        return {"decision": "REVIEW_REQUIRED", "outcome_state": "CONTESTED"}
    if censored:
        return {"decision": "REVIEW_REQUIRED", "outcome_state": "CENSORED"}
    if state in {"PENDING", "UNOBSERVABLE"}:
        return {"decision": "DENY", "outcome_state": state}
    if state == "PARTIAL" or not evidence_complete:
        return {"decision": "REVIEW_REQUIRED", "outcome_state": "PARTIAL"}
    if state in {"REALISED_TRUE", "REALISED_FALSE"}:
        return {"decision": "ALLOW", "outcome_state": state}
    return {"decision": "DENY", "outcome_state": "INVALID"}


def calibration_decision(
    *,
    sample_count: int,
    brier_score: float,
    expected_calibration_error: float,
    thresholds: dict[str, float],
    leakage_detected: bool = False,
) -> dict[str, str]:
    if leakage_detected:
        return {"decision": "DEMOTE", "reason": "LEAKAGE_DETECTED"}
    if sample_count < int(thresholds["minimum_sample_count"]):
        return {"decision": "REVIEW_REQUIRED", "reason": "INSUFFICIENT_SAMPLE"}
    breaches = []
    if brier_score > thresholds["maximum_brier_score"]:
        breaches.append("BRIER_SCORE")
    if expected_calibration_error > thresholds["maximum_ece"]:
        breaches.append("EXPECTED_CALIBRATION_ERROR")
    if breaches:
        return {"decision": "DEGRADED", "reason": "+".join(breaches)}
    return {"decision": "PASS", "reason": "THRESHOLDS_MET"}


def demotion_decision(
    *,
    current_status: str,
    hard_triggers: list[str],
    consecutive_material_breaches: int,
) -> dict[str, str]:
    if hard_triggers:
        return {"decision": "DEMOTED", "reason": sorted(hard_triggers)[0]}
    if current_status in {"DEMOTED", "QUARANTINED", "RETIRED", "BLOCKED"}:
        return {"decision": current_status, "reason": "STATUS_CEILING"}
    if consecutive_material_breaches >= 2:
        return {"decision": "DEMOTED", "reason": "CONSECUTIVE_BREACHES"}
    if consecutive_material_breaches == 1:
        return {"decision": "DEGRADED", "reason": "MATERIAL_BREACH"}
    return {"decision": current_status, "reason": "NO_DEMOTION_TRIGGER"}


def may_promote_model(
    *,
    authority: str,
    current_status: str,
    gates: list[str],
    new_frozen_holdout_passed: bool,
) -> dict[str, str]:
    if authority != "TYPED_HUMAN_APPROVAL":
        return {"decision": "DENY", "reason": "HUMAN_AUTHORITY_REQUIRED"}
    if current_status not in {"DEMOTED", "QUARANTINED", "DEGRADED"}:
        return {"decision": "DENY", "reason": "INVALID_SOURCE_STATUS"}
    if not new_frozen_holdout_passed:
        return {"decision": "DENY", "reason": "NEW_HOLDOUT_REQUIRED"}
    if any(gate != "PASS" for gate in gates):
        return {"decision": "DENY", "reason": "GATE_NOT_PASSED"}
    return {"decision": "ALLOW", "reason": "HUMAN_REACTIVATION_ELIGIBLE"}
