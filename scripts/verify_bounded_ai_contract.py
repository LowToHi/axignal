#!/usr/bin/env python3
"""Fail-closed verifier for bounded AI and token-entitlement authority."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "config" / "ai-assistance-policy.v0.1.json"
CONTRACT_PATH = (
    ROOT / "docs" / "contracts" / "29-bounded-ai-assistance-and-token-entitlements.md"
)
CONTRACT_INDEX_PATH = ROOT / "docs" / "contracts" / "README.md"
ADR_PATH = ROOT / "docs" / "adr" / "ADR-014-bounded-ai-and-token-entitlements.md"
ADR_INDEX_PATH = ROOT / "docs" / "adr" / "README.md"
TASK_PATH = ROOT / "docs" / "roadmap" / "tasks" / "AX-F9-T15.json"
PRICE_BOOK_PATH = (
    ROOT / "apps" / "landing" / "lib" / "canonical-commercial-contract.ts"
)

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


def _normalized(value: str) -> str:
    return " ".join(value.lower().split())


def main() -> None:
    policy = _load_json(POLICY_PATH)
    task = _load_json(TASK_PATH)
    contract = CONTRACT_PATH.read_text(encoding="utf-8")
    contract_index = CONTRACT_INDEX_PATH.read_text(encoding="utf-8")
    adr = ADR_PATH.read_text(encoding="utf-8")
    adr_index = ADR_INDEX_PATH.read_text(encoding="utf-8")
    price_book = PRICE_BOOK_PATH.read_text(encoding="utf-8")

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
    prohibited = set(policy.get("prohibited_capability_classes", []))
    _require(allowed == EXPECTED_ALLOWED, "allowed capability set drifted")
    _require(
        prohibited >= REQUIRED_PROHIBITED,
        "mandatory prohibited capability classes are missing",
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
    _require(trial.get("daily_reset") is False, "trial tokens must not reset")
    _require(trial.get("overage_allowed") is False, "trial overage is prohibited")
    _require(
        trial.get("silent_conversion_allowed") is False,
        "silent trial conversion is prohibited",
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
        "paid no-quota access must retain safety and rights controls",
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

    normalized_contract = _normalized(contract)
    for marker in (
        "token ceiling 1,000,000",
        "the trial belongs to a tenant or economic identity",
        "token and cost reservations are transactional",
        "only `in_scope_axignal` may proceed to an ai model or axignal tool",
        "generate an axignal report in pdf form",
    ):
        _require(marker in normalized_contract, f"contract authority missing: {marker}")
    _require(
        "frontend-only check" in normalized_contract,
        "Contract 29 must reject frontend-only enforcement",
    )

    normalized_adr = _normalized(adr)
    for marker in (
        "exactly `1,000,000` ai tokens per organisation",
        "unlimited monthly ai tokens",
        "psychology, therapy, emotional companionship",
        "code generation or execution",
    ):
        _require(marker in normalized_adr, f"ADR authority missing: {marker}")

    for marker in (
        "durationDays: 7",
        "cumulativeTokens: 1_000_000",
        "automaticConversion: false",
        "cardRequired: false",
    ):
        _require(marker in price_book, f"canonical price book missing: {marker}")

    _require(
        "29-bounded-ai-assistance-and-token-entitlements.md" in contract_index,
        "Contract 29 is not indexed",
    )
    _require(
        "config/ai-assistance-policy.v0.1.json" in contract_index,
        "machine-readable AI policy is not indexed",
    )
    _require(
        "ADR-014-bounded-ai-and-token-entitlements.md" in adr_index,
        "ADR-014 is not indexed",
    )

    contracts = set(task.get("contracts", []))
    _require(
        contracts >= {"29", "ADR-014"},
        "AX-F9-T15 must depend on Contract 29 and ADR-014",
    )
    allowed_scope = _normalized("\n".join(task.get("allowed_scope", [])))
    prohibited_scope = _normalized("\n".join(task.get("prohibited_scope", [])))
    _require(
        "1,000,000 cumulative ai tokens" in allowed_scope,
        "AX-F9-T15 must retain the exact trial token budget",
    )
    _require(
        "unlimited monthly ai tokens" in allowed_scope,
        "AX-F9-T15 must retain paid no-quota AI access",
    )
    _require(
        all(term in prohibited_scope for term in ("general-purpose ai", "psychology", "code generation")),
        "AX-F9-T15 must prohibit general-purpose, psychology and code assistance",
    )

    print(
        json.dumps(
            {
                "contract": "29",
                "adr": "ADR-014",
                "task": task["task_id"],
                "policy_version": policy["policy_version"],
                "status": policy["status"],
                "default_decision": policy["default_decision"],
                "trial_duration_days": trial["duration_days"],
                "trial_token_budget_total": trial["token_budget_total"],
                "trial_budget_semantics": "CUMULATIVE_ORGANISATION_CEILING",
                "paid_monthly_token_quota": paid["monthly_token_quota"],
                "paid_token_overage_billing": paid["token_overage_billing"],
                "runtime_enabled": False,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
