from __future__ import annotations

from typing import Iterable


def claim_decision(*, evidence_status: str, public_use: str, limitations_present: bool) -> str:
    if evidence_status in {"UNSUPPORTED", "REJECTED"}:
        return "DENY"
    if public_use in {"NOT_YET", "FORBIDDEN"}:
        return "DENY"
    if public_use in {"CONDITIONAL", "ALLOWED_WITH_SCOPE", "ALLOWED_AS_DESIGN_OBJECTIVE"} and not limitations_present:
        return "REVIEW_REQUIRED"
    return "ALLOW_BOUNDED"


def publication_decision(*, gates: dict[str, bool], human_publication_authority: bool) -> str:
    if not gates or not all(gates.values()):
        return "BLOCK"
    return "ALLOW_PUBLICATION" if human_publication_authority else "HUMAN_APPROVAL_REQUIRED"


def analytics_decision(*, event_name: str, allowed_events: Iterable[str], consent: str, purpose: str, contains_private_content: bool) -> str:
    if event_name not in set(allowed_events):
        return "DENY_UNKNOWN_EVENT"
    if contains_private_content:
        return "DENY_PRIVATE_CONTENT"
    if purpose == "marketing" and consent != "GRANTED":
        return "DENY_CONSENT_REQUIRED"
    return "ALLOW_MINIMISED_EVENT"


def experiment_decision(*, surface: str, allowed_surfaces: Iterable[str], forbidden_surfaces: Iterable[str], sample_declared: bool, stopping_rule_declared: bool, human_growth_approval: bool) -> str:
    if surface in set(forbidden_surfaces) or surface not in set(allowed_surfaces):
        return "DENY_SURFACE"
    if not sample_declared or not stopping_rule_declared:
        return "DENY_METHOD"
    return "ALLOW_BOUNDED_EXPERIMENT" if human_growth_approval else "HUMAN_APPROVAL_REQUIRED"


def marketing_scale_decision(*, conversion_validated: bool, contribution_positive: bool, budget_within_limit: bool, human_budget_approval: bool) -> str:
    if not conversion_validated or not contribution_positive or not budget_within_limit:
        return "HOLD"
    return "ALLOW_BOUNDED_SCALE" if human_budget_approval else "HUMAN_APPROVAL_REQUIRED"


def accessibility_release(*, critical_defects: int, keyboard_complete: bool, semantics_verified: bool, human_review_complete: bool) -> str:
    if critical_defects > 0 or not keyboard_complete or not semantics_verified:
        return "BLOCK"
    return "PASS" if human_review_complete else "MANUAL_REVIEW_REQUIRED"


def performance_release(*, lcp_ms: int, cls: float, inp_ms: int, budgets: dict[str, float]) -> str:
    passed = lcp_ms <= budgets["landing_lcp_ms"] and cls <= budgets["landing_cls"] and inp_ms <= budgets["landing_inp_ms"]
    return "PASS" if passed else "BLOCK"


def pricing_presentation(*, server_amount_minor: int, displayed_amount_minor: int, server_currency: str, displayed_currency: str) -> str:
    if server_amount_minor != displayed_amount_minor or server_currency != displayed_currency:
        return "BLOCK_PRICE_MISMATCH"
    return "PASS"
