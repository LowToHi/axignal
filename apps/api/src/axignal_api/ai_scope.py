from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ScopeDecision = Literal[
    "IN_SCOPE_AXIGNAL",
    "CLARIFICATION_REQUIRED",
    "OUT_OF_SCOPE",
    "BLOCKED_SAFETY_OR_AUTHORITY",
]

ALLOWED_CAPABILITIES = frozenset(
    {
        "NAVIGATE_AXIGNAL",
        "READ_INVESTIGATION_CONTEXT",
        "UPDATE_INVESTIGATION_CONTEXT",
        "SEARCH_ADMITTED_AXIGNAL_DATA",
        "COMPARE_ADMITTED_AXIGNAL_DATA",
        "EXPLAIN_CLAIMS_AND_EVIDENCE",
        "SHOW_CONTRADICTIONS_AND_UNKNOWNS",
        "REQUEST_BOUNDED_RESEARCH_RUN",
        "READ_RESEARCH_RUN_PROGRESS",
        "ASSEMBLE_EVIDENCE_LINKED_DOSSIER",
        "GENERATE_GROUNDED_PDF_REPORT",
        "EXPLAIN_AXIGNAL_PRODUCT_AND_METHOD",
    }
)

_BLOCKED_MARKERS = (
    "ignore previous",
    "ignore system",
    "bypass",
    "system prompt",
    "developer message",
    "admit this claim",
    "admit this source",
    "submit the bid",
    "send the application",
    "make the payment",
    "issue a refund",
    "execute shell",
    "run command",
    "impersonate",
)

_OUT_OF_SCOPE_MARKERS = (
    "therapy",
    "therapist",
    "psychologist",
    "medical diagnosis",
    "write code",
    "debug code",
    "weather forecast",
    "recipe",
    "horoscope",
    "general knowledge",
)


@dataclass(frozen=True)
class ScopeResult:
    decision: ScopeDecision
    reason: str
    capability: str


def classify_axignal_request(*, capability: str, user_intent: str) -> ScopeResult:
    """Classify a typed request before any model or tool invocation."""
    if capability not in ALLOWED_CAPABILITIES:
        return ScopeResult("OUT_OF_SCOPE", "capability_not_allowlisted", capability)

    normalised = " ".join(user_intent.casefold().split())
    if len(normalised) < 3:
        return ScopeResult(
            "CLARIFICATION_REQUIRED",
            "intent_is_not_specific_enough",
            capability,
        )
    if any(marker in normalised for marker in _BLOCKED_MARKERS):
        return ScopeResult(
            "BLOCKED_SAFETY_OR_AUTHORITY",
            "prompt_injection_or_external_authority_request",
            capability,
        )
    if any(marker in normalised for marker in _OUT_OF_SCOPE_MARKERS):
        return ScopeResult("OUT_OF_SCOPE", "request_is_not_an_axignal_task", capability)
    return ScopeResult("IN_SCOPE_AXIGNAL", "typed_axignal_capability_allowed", capability)
