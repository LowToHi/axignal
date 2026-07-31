#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any


AUTHORITY_RANK = {
    "RESTRICTED": 0,
    "REQUEST_ONLY": 1,
    "CANDIDATE_ONLY": 2,
    "PROPOSAL_ONLY": 3,
    "BOUNDED_WORK_MUTATION": 4,
    "TENANT_SCOPED_OPERATION": 5,
    "HUMAN_REVIEW_ONLY": 6,
    "TYPED_HUMAN_APPROVAL": 7,
    "HUMAN_EXTERNAL_ACTION_AUTHORITY": 8,
    "INDEPENDENT_CANONICAL_ADMISSION_RUNTIME": 9,
}

SURFACES = {"GLOBE", "GRAPH", "TIMELINE", "NAVIGATOR"}


def canonical_digest(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def compose_authority(authorities: Sequence[str]) -> str:
    if not authorities:
        return "RESTRICTED"
    if any(authority not in AUTHORITY_RANK for authority in authorities):
        return "RESTRICTED"
    return min(authorities, key=AUTHORITY_RANK.__getitem__)


def dependency_projection_decision(
    *,
    engineering_evidence_ready: bool,
    product_admitted: bool,
    canonical_activation_authorised: bool,
    rights_active: bool,
    kill_switch_active: bool,
) -> str:
    if kill_switch_active or not rights_active:
        return "DENY"
    if product_admitted and canonical_activation_authorised:
        return "PASS"
    if engineering_evidence_ready:
        return "REVIEW_REQUIRED"
    return "NOT_AVAILABLE"


def entity_bridge_decision(
    *,
    exact_identifier: bool,
    scoped_alias: bool,
    tenant_match: bool,
    jurisdiction_compatible: bool,
    human_review_current: bool,
) -> str:
    if not tenant_match:
        return "DENY"
    if exact_identifier and jurisdiction_compatible and human_review_current:
        return "PASS"
    if scoped_alias and jurisdiction_compatible:
        return "REVIEW_REQUIRED"
    return "REVIEW_REQUIRED"


def temporal_alignment_decision(
    *,
    valid_time_present: bool,
    transaction_time_present: bool,
    timezone_resolved: bool,
    vintage_preserved: bool,
    revision_lineage_preserved: bool,
    axes_collapsed: bool,
) -> str:
    if axes_collapsed or not vintage_preserved or not revision_lineage_preserved:
        return "DENY"
    if not valid_time_present or not transaction_time_present:
        return "REVIEW_REQUIRED"
    if not timezone_resolved:
        return "REVIEW_REQUIRED"
    return "PASS"


def surface_projection_decision(
    *,
    surface: str,
    source_authority: str,
    rights_active: bool,
    tenant_match: bool,
    contradiction_preserved: bool,
    traceable: bool,
) -> str:
    if surface not in SURFACES:
        return "DENY"
    if source_authority not in AUTHORITY_RANK:
        return "DENY"
    if not rights_active or not tenant_match:
        return "DENY"
    if not contradiction_preserved or not traceable:
        return "DENY"
    return "PASS"


def cross_library_readiness(
    gates: Mapping[str, str],
    required: Sequence[str],
) -> str:
    if not gates or any(gate not in gates for gate in required):
        return "NOT_READY"
    values = [gates[gate] for gate in required]
    if "DENY" in values or "BLOCK" in values:
        return "DENY"
    if all(value == "PASS" for value in values):
        return "READY"
    return "REVIEW_REQUIRED"


def may_publish_workspace_projection(
    *,
    readiness: str,
    tenant_match: bool,
    rights_active: bool,
    traceable: bool,
    authority_state: str,
) -> bool:
    return all(
        (
            readiness == "READY",
            tenant_match,
            rights_active,
            traceable,
            authority_state in {"CANDIDATE_ONLY", "PROPOSAL_ONLY"},
        )
    )


def may_execute_external_action(
    *,
    actor_type: str,
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
            approvals_current,
            rights_active,
            legal_review_current,
            recipient_verified,
            channel_verified,
            audit_chain_valid,
            not kill_switch_active,
        )
    )


def normalize_cross_library_outcome(
    outcome: str,
    *,
    observed_evidence: bool,
) -> str:
    allowed = {
        "NO_ACTION",
        "PROJECTION_REVIEWED",
        "PROJECTION_PUBLISHED_TO_WORKSPACE",
        "ENTITY_LINK_CONFIRMED",
        "ENTITY_LINK_REJECTED",
        "CONTRADICTION_CONFIRMED",
        "CONTRADICTION_RESOLVED",
        "RESEARCH_RUN_COMPLETED",
        "RESEARCH_RUN_CANCELLED",
        "CLOSED",
    }
    if observed_evidence and outcome in allowed:
        return outcome
    return "UNKNOWN"


def imported_authority(_: str) -> str:
    return "CANDIDATE_ONLY"
