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
    hardening = (
        ROOT / "infra/postgres/081-entitlement-ledger-hardening.sql"
    ).read_text(encoding="utf-8")
    expiry = (ROOT / "infra/postgres/082-entitlement-expiry-sweep.sql").read_text(
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

    required_hardening = (
        "SECURITY DEFINER",
        "SET search_path TO pg_catalog",
        "REVOKE ALL ON FUNCTION",
        "REVOKE INSERT, UPDATE, DELETE, TRUNCATE",
        "REVOKE UPDATE (state, token_budget_reserved, token_budget_consumed, updated_at)",
        "REVOKE UPDATE (state, actual_tokens, reconciled_at)",
        "FROM PUBLIC",
        "FROM axignal_app",
        "Concurrent retries of the same operation",
    )
    for marker in required_hardening:
        require(marker in hardening, f"Missing authority hardening marker: {marker}")

    required_expiry = (
        "expire_due_trial",
        "SECURITY DEFINER",
        "SET search_path TO pg_catalog",
        "state = 'READ_ONLY'",
        "PRE_AUTHORIZATION_SWEEP",
        "REVOKE ALL ON FUNCTION",
    )
    for marker in required_expiry:
        require(marker in expiry, f"Missing expiry contract marker: {marker}")

    require(
        "trial_runtime_enabled: bool" in config
        and "end_user_ai_enabled: bool" in config,
        "Independent trial and AI flags are required",
    )
    require(
        '_bool_env("AXIGNAL_TRIAL_RUNTIME_ENABLED")' in config
        and '_bool_env("AXIGNAL_END_USER_AI_ENABLED")' in config,
        "Runtime flags must default disabled",
    )
    require("app.include_router(entitlement_router)" in application, "Router not wired")
    require("080-entitlement-token-ledger.sql" in dockerfile, "Ledger migration not installed")
    require(
        "081-entitlement-ledger-hardening.sql" in dockerfile,
        "Authority hardening migration not installed",
    )
    require(
        "082-entitlement-expiry-sweep.sql" in dockerfile,
        "Expiry sweep migration not installed",
    )
    require("stripe" not in combined_runtime.casefold(), "Stripe is outside this runtime cut")
    activation_command = combined_runtime.split("class TrialActivationCommand", 1)[1].split(
        "class AIRequestAuthorizationCommand",
        1,
    )[0]
    require("tenant_id" not in activation_command, "Trial command cannot accept tenant_id")
    require(
        "expire_due_trial" in combined_runtime,
        "Repository must persist expiry before reservation denial",
    )

    result = {
        "schema": "axignal.entitlement-contract-verification.v0.1",
        "status": "PASS",
        "task_state": task["state"],
        "runtime_enabled_by_default": False,
        "trial_duration_days": 7,
        "trial_token_budget_total": 1_000_000,
        "paid_monthly_token_quota": None,
        "token_overage_billing": False,
        "direct_app_table_mutation": False,
        "column_level_mutation_grants": False,
        "security_definer_search_path_fixed": True,
        "expiry_transition_persists_before_denial": True,
        "stripe_wired": False,
    }
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
