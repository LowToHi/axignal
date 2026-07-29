from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> int:
    policy = json.loads(
        (ROOT / "config/ai-assistance-policy.v0.1.json").read_text(encoding="utf-8")
    )
    task = json.loads(
        (ROOT / "docs/roadmap/tasks/AX-F9-T15.json").read_text(encoding="utf-8")
    )
    migration = (ROOT / "infra/postgres/080-entitlement-token-ledger.sql").read_text(
        encoding="utf-8"
    )
    config = (ROOT / "apps/api/src/axignal_api/entitlement_config.py").read_text(
        encoding="utf-8"
    )
    application = (ROOT / "apps/api/src/axignal_api/application.py").read_text(
        encoding="utf-8"
    )
    dockerfile = (ROOT / "infra/postgres/Dockerfile").read_text(encoding="utf-8")
    combined_runtime = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            ROOT / "apps/api/src/axignal_api/entitlements.py",
            ROOT / "apps/api/src/axignal_api/entitlement_repository.py",
            ROOT / "apps/api/src/axignal_api/capability_tokens.py",
        )
    )

    require(policy["status"] == "CANDIDATE_DISABLED", "AI policy must remain disabled")
    require(policy["default_decision"] == "OUT_OF_SCOPE", "Default must fail closed")
    require(policy["trial"]["duration_days"] == 7, "Trial must be exactly seven days")
    require(
        policy["trial"]["token_budget_total"] == 1_000_000,
        "Trial budget must be exactly one million tokens",
    )
    require(policy["trial"]["daily_reset"] is False, "Trial cannot reset daily")
    require(policy["trial"]["overage_allowed"] is False, "Trial overage is forbidden")
    require(
        policy["trial"]["silent_conversion_allowed"] is False,
        "Silent conversion is forbidden",
    )
    require(
        policy["paid_monthly"]["monthly_token_quota"] is None,
        "Paid plans cannot have a monthly token quota",
    )
    require(
        policy["paid_monthly"]["token_overage_billing"] is False,
        "Paid token overage billing is forbidden",
    )
    require(task["state"] in {"PROPOSED", "IN_PROGRESS"}, "F9 cannot be accepted yet")

    required_sql = (
        "organisation_entitlements",
        "ai_token_reservations",
        "entitlement_events",
        "activate_controlled_trial",
        "reserve_ai_tokens",
        "reconcile_ai_tokens",
        "release_ai_token_reservation",
        "expire_current_trial",
        "FORCE ROW LEVEL SECURITY",
        "token_budget_total = 1000000",
        "expires_at = starts_at + interval '7 days'",
        "entitlement_kind = 'PAID_MONTHLY'",
        "token_budget_total IS NULL",
    )
    for marker in required_sql:
        require(marker in migration, f"Missing SQL contract marker: {marker}")

    require(
        'trial_runtime_enabled: bool' in config
        and 'end_user_ai_enabled: bool' in config,
        "Independent trial and AI flags are required",
    )
    require(
        '_bool_env("AXIGNAL_TRIAL_RUNTIME_ENABLED")' in config
        and '_bool_env("AXIGNAL_END_USER_AI_ENABLED")' in config,
        "Runtime flags must default disabled",
    )
    require("app.include_router(entitlement_router)" in application, "Router not wired")
    require("080-entitlement-token-ledger.sql" in dockerfile, "Migration not installed")
    require("stripe" not in combined_runtime.casefold(), "Stripe is outside this runtime cut")
    require("tenant_id" not in combined_runtime.split("class TrialActivationCommand", 1)[1].split(
        "class AIRequestAuthorizationCommand", 1
    )[0], "Trial command cannot accept tenant_id")

    result = {
        "schema": "axignal.entitlement-contract-verification.v0.1",
        "status": "PASS",
        "task_state": task["state"],
        "runtime_enabled_by_default": False,
        "trial_duration_days": 7,
        "trial_token_budget_total": 1_000_000,
        "paid_monthly_token_quota": None,
        "token_overage_billing": False,
        "stripe_wired": False,
    }
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
