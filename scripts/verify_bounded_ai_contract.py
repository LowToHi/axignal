#!/usr/bin/env python3
"""Fail-closed verifier for AXIGNAL bounded AI and token entitlements."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "config" / "ai-assistance-policy.v0.1.json"
CONTRACT_PATH = (
    ROOT / "docs" / "contracts" / "29-bounded-ai-assistance-and-token-entitlements.md"
)
INDEX_PATH = ROOT / "docs" / "contracts" / "README.md"

EXPECTED_ALLOWED = {
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

REQUIRED_PROHIBITED = {
    "PSYCHOLOGY_OR_THERAPY",
    "EMOTIONAL_COMPANIONSHIP",
    "CODE_GENERATION_REVIEW_DEBUG_OR_EXECUTION",
    "GENERAL_KNOWLEDGE_ASSISTANCE",
    "UNRESTRICTED_WEB_BROWSING",
    "SHELL_OR_OS_EXECUTION",
    "ARBITRARY_SQL",
    "EXTERNAL_COMMUNICATION",
    "USER_SELECTED_MCP_SKILL_OR_PLUGIN_EXECUTION",
    "CANONICAL_CLAIM_OR_SOURCE_ADMISSION",
}

REQUIRED_CONTRACT_MARKERS = (
    "1,000,000 tokens maximum per trial organisation",
    "Unlimited monthly AI tokens",
    "act as a psychologist, therapist, counsellor",
    "generate, debug, review or execute software code",
    "Only `IN_SCOPE_AXIGNAL` MAY proceed to an AI model or AXIGNAL tool",
    "No frontend-only check, system prompt or model self-refusal satisfies this contract",
    "GENERATE_GROUNDED_PDF_REPORT",
)


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"cannot load {path.relative_to(ROOT)}: {exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit(f"{path.relative_to(ROOT)} must contain a JSON object")
    return value


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> None:
    policy = _load_json(POLICY_PATH)
    contract = CONTRACT_PATH.read_text(encoding="utf-8")
    index = INDEX_PATH.read_text(encoding="utf-8")

    _require(
        policy.get("schema") == "axignal.ai-assistance-policy.v0.1",
        "unexpected bounded AI policy schema",
    )
    _require(
        policy.get("status") == "CANDIDATE_DISABLED",
        "bounded AI policy must remain disabled until implementation gates pass",
    )
    _require(
        policy.get("default_decision") == "OUT_OF_SCOPE",
        "bounded AI policy must default to OUT_OF_SCOPE",
    )

    allowed = set(policy.get("allowed_capabilities", []))
    _require(allowed == EXPECTED_ALLOWED, "allowed capability set drifted")

    prohibited = set(policy.get("prohibited_capability_classes", []))
    _require(
        REQUIRED_PROHIBITED <= prohibited,
        "one or more mandatory prohibited capability classes are missing",
    )

    trial = policy.get("trial")
    _require(isinstance(trial, dict), "trial policy must be an object")
    _require(trial.get("duration_days") == 7, "trial duration must be seven days")
    _require(
        trial.get("token_budget_scope") == "ORGANISATION",
        "trial token budget must be organisation-scoped",
    )
    _require(
        trial.get("token_budget_total") == 1_000_000,
        "trial token budget must be exactly 1,000,000",
    )
    _require(trial.get("daily_reset") is False, "trial tokens must not reset daily")
    _require(trial.get("overage_allowed") is False, "trial token overage is prohibited")
    _require(
        trial.get("silent_conversion_allowed") is False,
        "silent trial conversion is prohibited",
    )
    exhaustion_message = trial.get("exhaustion_message_es", "")
    _require(
        "1.000.000" in exhaustion_message
        and "suscripciones mensuales de pago" in exhaustion_message
        and "tokens son ilimitados" in exhaustion_message,
        "trial exhaustion message must disclose the cap and unlimited paid tokens",
    )

    paid = policy.get("paid_monthly")
    _require(isinstance(paid, dict), "paid_monthly policy must be an object")
    _require(
        paid.get("monthly_token_quota") is None,
        "paid monthly subscriptions must not have a token quota",
    )
    _require(
        paid.get("token_overage_billing") is False,
        "paid monthly subscriptions must not bill token overages",
    )
    _require(
        paid.get("safety_reliability_rights_controls_remain") is True,
        "paid unlimited tokens must retain safety, reliability and rights controls",
    )

    authority = policy.get("authority")
    _require(isinstance(authority, dict), "authority policy must be an object")
    for key in (
        "model_can_write_canonical_claims",
        "model_can_admit_sources",
        "model_can_admit_claims",
        "model_can_execute_external_actions",
        "frontend_is_enforcement_boundary",
    ):
        _require(authority.get(key) is False, f"{key} must be false")
    for key in (
        "server_pre_model_scope_gate_required",
        "server_post_model_output_gate_required",
    ):
        _require(authority.get(key) is True, f"{key} must be true")

    for marker in REQUIRED_CONTRACT_MARKERS:
        _require(marker in contract, f"contract marker missing: {marker}")

    _require(
        "29-bounded-ai-assistance-and-token-entitlements.md" in index,
        "contract 29 is not indexed",
    )
    _require(
        "config/ai-assistance-policy.v0.1.json" in index,
        "machine-readable AI policy is not indexed",
    )

    print(
        json.dumps(
            {
                "contract": "29",
                "policy_version": policy["policy_version"],
                "status": policy["status"],
                "default_decision": policy["default_decision"],
                "allowed_capability_count": len(allowed),
                "trial_duration_days": trial["duration_days"],
                "trial_token_budget_total": trial["token_budget_total"],
                "paid_monthly_token_quota": paid["monthly_token_quota"],
                "paid_token_overage_billing": paid["token_overage_billing"],
                "general_assistant_enabled": False,
                "psychology_enabled": False,
                "code_generation_enabled": False,
                "grounded_pdf_enabled_by_contract": True,
                "runtime_enabled": False,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
