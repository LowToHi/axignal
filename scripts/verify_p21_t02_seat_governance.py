#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PATH = ROOT / "data/commercial/seat-governance-runtime.v0.1.json"
PRICE_PATH = ROOT / "data/commercial/commercial-runtime-pricing-stripe-runtime.v0.1.json"
MIGRATION_PATH = ROOT / "infra/postgres/110-seat-governance.sql"


def require_text(path: Path, markers: tuple[str, ...]) -> str:
    text = path.read_text(encoding="utf-8")
    for marker in markers:
        assert marker in text, (path, marker)
    return text


def main() -> None:
    runtime = json.loads(RUNTIME_PATH.read_text(encoding="utf-8"))
    commercial = json.loads(PRICE_PATH.read_text(encoding="utf-8"))
    plans = {
        plan["plan_code"]: plan
        for plan in commercial["pricing_contract"]["plans"]
    }

    assert runtime["task_id"] == "AX-GE2E-P21-T02"
    assert runtime["billing_model"] == "FLAT_TIER"
    assert runtime["stripe_subscription_quantity"] == 1
    assert runtime["commercial_activation_authorised"] is False
    assert runtime["public_launch_authorised"] is False
    assert plans["PROFESSIONAL_MONTHLY"]["seat_floor"] == 1
    assert plans["PROFESSIONAL_MONTHLY"]["seat_ceiling"] == 3
    assert plans["TEAM_MONTHLY"]["seat_floor"] == 4
    assert plans["TEAM_MONTHLY"]["seat_ceiling"] == 15
    assert (
        runtime["price_book_binding"]["plans"]["PROFESSIONAL_MONTHLY"]["seat_capacity"]
        == plans["PROFESSIONAL_MONTHLY"]["seat_ceiling"]
    )
    assert (
        runtime["price_book_binding"]["plans"]["TEAM_MONTHLY"]["seat_capacity"]
        == plans["TEAM_MONTHLY"]["seat_ceiling"]
    )
    assert (
        runtime["price_book_binding"]["plans"]["CONTROLLED_TRIAL_7D"]["seat_capacity"]
        == 2
    )

    migration = require_text(
        MIGRATION_PATH,
        (
            "organisation_seat_entitlements",
            "organisation_memberships",
            "organisation_invitations",
            "organisation_seat_allocations",
            "membership_role_bindings",
            "membership_audit_events",
            "FORCE ROW LEVEL SECURITY",
            "seat_capacity_exhausted",
            "seat_downgrade_capacity_conflict",
            "last_owner_revocation_forbidden",
            "seat_access_decision",
            "membership_audit_events_are_append_only",
        ),
    )
    assert "('PROFESSIONAL_MONTHLY', 'FLAT_TIER', 3" in migration
    assert "('TEAM_MONTHLY', 'FLAT_TIER', 15" in migration
    assert "('TRIAL_7D', 'FLAT_TIER', 2" in migration
    assert "token_digest text NOT NULL" in migration
    assert "UNIQUE (tenant_id, operation_id)" in migration
    assert "state IN ('RESERVED', 'ACTIVE')" in migration

    require_text(
        ROOT / "infra/postgres/Dockerfile",
        ("110-seat-governance.sql",),
    )
    require_text(
        ROOT / "apps/api/src/axignal_api/identity.py",
        (
            "SeatSettings.from_env()",
            "seat_settings.enabled",
            "seat_access_decision",
            "SEAT_GOVERNANCE_BOOTSTRAP_PATHS",
        ),
    )
    require_text(
        ROOT / "apps/api/src/axignal_api/seat_delivery.py",
        (
            "token_urlsafe",
            "sha256",
            "Test invitation provider is restricted",
            "smtplib.SMTP",
        ),
    )
    require_text(
        ROOT / "apps/api/src/axignal_api/seat_routes.py",
        (
            "/v1/organisation/seats",
            "confirm_owner_bootstrap",
            "confirm_acceptance",
            "test_acceptance_token",
        ),
    )
    require_text(
        ROOT / "apps/web/components/seat-governance-bridge.tsx",
        (
            "Reserve seat and send invitation",
            "Seat capacity exhausted",
            "Stripe bills one package unit",
        ),
    )
    require_text(
        ROOT / "apps/web/app/accept-invitation/page.tsx",
        ("AcceptInvitationClient",),
    )

    assert len(runtime["invariants"]) >= 30
    assert len(runtime["readiness_gates"]) >= 14
    assert len(runtime["roles"]) == 8

    print(
        json.dumps(
            {
                "status": "PASS",
                "task_id": runtime["task_id"],
                "billing_model": runtime["billing_model"],
                "professional_capacity": 3,
                "team_capacity": 15,
                "trial_capacity": 2,
                "roles": len(runtime["roles"]),
                "invariants": len(runtime["invariants"]),
                "readiness_gates": len(runtime["readiness_gates"]),
                "commercial_activation_authorised": False,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
