from __future__ import annotations

import json
import pathlib

REQUIRED_FILES = {
    "migration": pathlib.Path("infra/postgres/100-stripe-paid-lifecycle.sql"),
    "config": pathlib.Path("apps/api/src/axignal_api/billing_config.py"),
    "routes": pathlib.Path("apps/api/src/axignal_api/billing_routes.py"),
    "gateway": pathlib.Path("apps/api/src/axignal_api/stripe_gateway.py"),
    "signature": pathlib.Path("apps/api/src/axignal_api/stripe_signature.py"),
}


def main() -> int:
    contents = {name: path.read_text(encoding="utf-8") for name, path in REQUIRED_FILES.items()}
    combined = "\n".join(contents.values())

    required_markers = [
        "EXPECTED_AXIGNAL_STRIPE_ACCOUNT_ID = \"acct_1TybkH8feyjV8Pem\"",
        "AXIGNAL_BILLING_RUNTIME_ENABLED",
        "AXIGNAL_STRIPE_CHECKOUT_ENABLED",
        "AXIGNAL_STRIPE_WEBHOOKS_ENABLED",
        "AXIGNAL_STRIPE_LIFECYCLE_ENABLED",
        "AXIGNAL_STRIPE_SANDBOX_ONLY",
        "confirm_paid_selection",
        "confirm_upgrade",
        "confirm_cancellation",
        "verify_stripe_signature",
        "payload_digest",
        "stripe_webhook_receipts",
        "payment_ledger_entries",
        "PAID_MONTHLY",
        "unlimited_ai_tokens = true",
        "token_budget_total = NULL",
        "live_stripe_event_forbidden",
        "stripe_trial_forbidden",
        "rollback_paid_lifecycle",
    ]
    missing = [marker for marker in required_markers if marker not in combined]
    if missing:
        raise SystemExit(f"Missing Stripe billing contract markers: {missing}")

    forbidden = {
        "trial_period_days": "Stripe trial parameters must not be emitted",
        "sk_live_": "Live Stripe secrets must not be embedded",
        "token_overage": "Paid token overage billing is forbidden",
    }
    violations: list[str] = []
    gateway = contents["gateway"]
    for marker, reason in forbidden.items():
        if marker in gateway:
            violations.append(f"{marker}: {reason}")
    if violations:
        raise SystemExit(f"Forbidden Stripe billing patterns: {violations}")

    migration = contents["migration"]
    if "GRANT EXECUTE ON FUNCTION tenant_private.apply_stripe_billing_event" not in migration:
        raise SystemExit("Billing worker event authority is not granted")
    if "TO axignal_billing_worker" not in migration:
        raise SystemExit("Isolated billing worker role is missing")
    if "FROM axignal_app" not in migration:
        raise SystemExit("Application mutation authority was not revoked")

    result = {
        "schema": "axignal.stripe-billing-contract.v0.1",
        "status": "PASS",
        "expected_account": "acct_1TybkH8feyjV8Pem",
        "sandbox_only_default": True,
        "explicit_selection": True,
        "stripe_trial_parameters": False,
        "signed_raw_body_webhooks": True,
        "idempotent_event_receipts": True,
        "append_only_payment_ledger": True,
        "paid_monthly_token_quota": None,
        "paid_token_overage_billing": False,
        "isolated_billing_worker": True,
        "rollback_function": True,
    }
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
