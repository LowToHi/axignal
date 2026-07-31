#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any


def canonical_digest(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def event_eligibility(data: Mapping[str, Any]) -> str:
    if data.get("deleted"):
        return "DENY"
    if data.get("bot_or_internal"):
        return "DENY"
    if data.get("direct_identifier"):
        return "DENY"
    aggregate = bool(data.get("aggregate_tides"))
    private = bool(data.get("private_memory"))
    if aggregate and private:
        return "ALLOW_BOTH"
    if aggregate:
        return "ALLOW_AGGREGATE"
    if private:
        return "ALLOW_PRIVATE"
    return "DENY"


def purpose_decision(data: Mapping[str, Any]) -> str:
    if data.get("implied"):
        return "DENY"
    if data.get("revoked"):
        return "DENY"
    if not data.get("permission"):
        return "DENY"
    return "ALLOW"


def preference_decision(data: Mapping[str, Any]) -> str:
    if data.get("deleted"):
        return "DELETE"
    if not data.get("memory_enabled"):
        return "DENY"
    if data.get("user_confirmed"):
        return "CONFIRMED_PREFERENCE"
    repetitions = int(data.get("repetitions", 0))
    distinct_days = int(data.get("distinct_days", 0))
    if repetitions >= 3 and distinct_days >= 2:
        return "INFERRED_PREFERENCE"
    return "OBSERVED_INTEREST"


def cohort_privacy_decision(data: Mapping[str, Any]) -> str:
    if data.get("row_level_output"):
        return "DENY"
    if int(data.get("unique_users", 0)) < 20:
        return "PRIVACY_SUPPRESSED"
    if int(data.get("unique_organisations", 0)) < 5:
        return "PRIVACY_SUPPRESSED"
    if float(data.get("dominant_organisation_share", 1.0)) > 0.25:
        return "PRIVACY_SUPPRESSED"
    if int(data.get("active_days", 0)) < 3:
        return "PRIVACY_SUPPRESSED"
    if data.get("reidentification_risk") != "LOW":
        return "PRIVACY_SUPPRESSED"
    return "AGGREGATE_ALLOWED"


def tide_decision(data: Mapping[str, Any]) -> str:
    if not data.get("privacy_allowed"):
        return "PRIVACY_SUPPRESSED"
    if not data.get("cohort_sufficient"):
        return "INSUFFICIENT_COHORT"
    if float(data.get("manipulation_risk", 1.0)) >= 0.7:
        return "COORDINATION_SUSPECTED"
    velocity = float(data.get("intent_velocity", 0.0))
    share = float(data.get("intent_share", 0.0))
    persistence = float(data.get("persistence", 0.0))
    diversity = float(data.get("organisation_diversity", 0.0))
    if velocity > 0.2:
        return "ACCELERATING_ATTENTION"
    if velocity < -0.15:
        return "DECLINING_ATTENTION"
    if persistence >= 0.7 and share >= 0.1:
        return "PERSISTENT_ATTENTION"
    if diversity >= 0.7 and share >= 0.15:
        return "BROAD_ATTENTION"
    return "EMERGING_ATTENTION"


def manipulation_decision(data: Mapping[str, Any]) -> str:
    if float(data.get("bot_or_internal_share", 0.0)) > 0.0:
        return "COORDINATION_SUSPECTED"
    if float(data.get("campaign_share", 0.0)) > 0.5:
        return "COORDINATION_SUSPECTED"
    if float(data.get("dominant_organisation_share", 0.0)) > 0.25:
        return "COORDINATION_SUSPECTED"
    if float(data.get("burst_score", 0.0)) > 0.8:
        return "COORDINATION_SUSPECTED"
    return "CLEAR"


def research_candidate_decision(data: Mapping[str, Any]) -> str:
    state = str(data.get("tide_state"))
    if state == "PRIVACY_SUPPRESSED":
        return "PRIVACY_SUPPRESSED"
    if state == "INSUFFICIENT_COHORT":
        return "PRIVACY_SUPPRESSED"
    if state == "COORDINATION_SUSPECTED":
        return "MANIPULATION_SUSPECTED"
    if float(data.get("rights_confidence", 0.0)) < 0.7:
        return "RIGHTS_BLOCKED"
    if float(data.get("source_feasibility", 0.0)) < 0.5:
        return "INSUFFICIENT_VALUE"
    if data.get("privacy_scope") not in {
        "GLOBAL_AGGREGATE",
        "TENANT_PRIVATE",
        "USER_PRIVATE",
        "INTERNAL_ONLY",
    }:
        return "DENY"
    if data.get("human_review_current"):
        return "PRIORITISATION_READY"
    return "PROPOSED"


def retention_decision(data: Mapping[str, Any]) -> str:
    if data.get("deleted"):
        return "DELETE_AND_INVALIDATE"
    if data.get("expired"):
        return "EXPIRE_AND_INVALIDATE"
    if data.get("retention_class") == "AUDIT":
        if data.get("raw_content"):
            return "DENY"
        return "RETAIN_METADATA_ONLY"
    return "RETAIN"


def adversarial_decision(threat_class: str) -> str:
    decisions = {
        "IMPLIED_CONSENT": "DENY",
        "SMALL_COHORT_REIDENTIFICATION": "PRIVACY_SUPPRESSED",
        "CROSS_TENANT_AGGREGATION": "DENY",
        "RAW_MESSAGE_LEAK": "DENY",
        "CAMPAIGN_OR_BOT_AS_ORGANIC": "QUARANTINE",
        "DELETION_OR_OPTOUT_BYPASS": "DENY",
        "INFERRED_PREFERENCE_AS_CONFIRMED": "DENY",
        "TIDE_AS_MARKET_DEMAND": "DENY",
        "RESEARCH_CANDIDATE_AS_AUTHORISED_RUN": "DENY",
    }
    return decisions.get(threat_class, "DENY")


def readiness(gates: Mapping[str, str], required: Sequence[str]) -> str:
    if set(gates) != set(required):
        return "DENY"
    if any(gates[gate] != "PASS" for gate in required):
        return "DENY"
    return "READY_FOR_HUMAN_REVIEW"
