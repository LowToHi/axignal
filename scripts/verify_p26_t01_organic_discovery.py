#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "data/growth/organic-discovery-runtime.v0.1.json"
MODULE_LABELS = {
    "OVERVIEW": "Overview",
    "ORGANIC_SEO": "Organic SEO",
    "PAGES_AND_SITEMAPS": "Pages & Sitemaps",
    "AI_CITATIONS": "AI Citations",
    "TENDER_ALERTS": "Tender Alerts",
    "CRM": "CRM",
    "CUSTOMERS_AND_TRIALS": "Customers & Trials",
    "BILLING": "Billing",
    "RISK_AND_ABUSE": "Risk & Abuse",
    "SOURCES_AND_COVERAGE": "Sources & Coverage",
    "OPERATIONS": "Operations",
    "SETTINGS": "Settings",
    "AUDIT": "Audit",
}


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def main() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["task"] == "AX-GE2E-P26-T01"
    assert contract["status"] == "CANDIDATE_ONLY"
    assert contract["public_indexing_authorised"] is False
    assert contract["public_tender_alerts_authorised"] is False
    assert contract["founder_admin_publicly_exposed"] is False
    assert contract["policy_versions"]["indexability"] == (
        "indexability-gate@1.0.0"
    )
    assert contract["indexability_thresholds"]["minimum_demand_score"] == 0.55
    assert contract["indexability_thresholds"]["maximum_age_hours"] == 48
    assert contract["founder_admin_authority"] == {
        "authentication": "RECENT_AAL2_PASSKEY",
        "server_allowlist_required": True,
        "database_principal_required": True,
        "tenant_seat_required": False,
        "browser_supplied_role_authoritative": False,
        "all_mutations_audited": True,
    }

    migration = read("infra/postgres/130-organic-discovery-founder-admin.sql")
    alert_migration = read(
        "infra/postgres/131-organic-discovery-alert-lifecycle.sql"
    )
    required_relations = (
        "seo_page_candidates",
        "seo_indexability_decisions",
        "seo_page_snapshots",
        "seo_sitemap_entries",
        "ai_citation_events",
        "crm_contacts",
        "tender_alert_subscriptions",
        "founder_admin_audit_events",
    )
    for relation in required_relations:
        assert relation in migration
    for function in (
        "evaluate_indexability",
        "publish_page_snapshot",
        "public_discovery_page",
        "public_sitemap_entries",
        "founder_overview",
        "subscribe_tender_alert",
    ):
        assert f"FUNCTION growth_private.{function}" in migration
    for function in (
        "confirm_tender_alert",
        "fail_tender_alert_delivery",
        "unsubscribe_tender_alert",
    ):
        assert f"FUNCTION growth_private.{function}" in alert_migration
    assert (
        "REVOKE ALL ON ALL TABLES IN SCHEMA growth_private FROM axignal_app"
        in migration
    )
    assert "SECURITY DEFINER" in migration
    assert "append_only_relation" in migration

    routes = read("apps/api/src/axignal_api/organic_routes.py")
    assert "require_recent_aal2" in routes
    assert "require_founder_identity" in routes
    assert "settings.require_public_indexing()" in routes
    assert "settings.require_public_alerts()" in routes
    assert "repository.fail_alert_delivery" in routes
    assert '"trial_created": False' in routes
    assert '"tenant_created": False' in routes

    founder_identity = read("apps/api/src/axignal_api/founder_identity.py")
    assert "verify_identity_assertion" in founder_identity
    assert "SeatRepository" not in founder_identity

    admin = read("apps/web/app/admin/founder-admin-dashboard.tsx")
    for module in contract["founder_admin_modules"]:
        assert MODULE_LABELS[module] in admin

    robots = read("apps/web/app/robots.ts")
    assert 'userAgent: "OAI-SearchBot"' in robots
    assert 'userAgent: "GPTBot", disallow: "/"' in robots
    assert '"/admin/"' in robots
    assert '"/alerts/confirm/"' in robots

    sitemap = read("apps/web/app/sitemap.ts")
    assert "fetchDiscoverySitemap" in sitemap
    assert "isPublicOrganicIndexingEnabled" in sitemap

    llms = read("apps/web/app/llms.txt/route.ts")
    assert "Every listed page has passed indexability-gate@1.0.0" in llms
    assert "Citation of AXIGNAL content does not imply endorsement" in llms

    workspace = read("apps/web/app/page.tsx")
    assert "index: false" in workspace
    assert "Private AXIGNAL B2G investigation workspace" in workspace

    alert_form = read("apps/web/components/tender-alert-form.tsx")
    assert "tender_alert_signup" in alert_form
    assert "turnstile" in alert_form.casefold()
    assert "does not create an AXIGNAL account" in alert_form

    organic_compose = read("infra/pilot/compose.organic-test.yaml")
    canonical_origin = (
        "${AXIGNAL_ORGANIC_PUBLIC_ORIGIN:-http://127.0.0.1:18080}"
    )
    assert organic_compose.count(
        f"AXIGNAL_PUBLIC_SITE_URL: {canonical_origin}"
    ) == 2
    assert f"AXIGNAL_PUBLIC_ORIGIN: {canonical_origin}" in organic_compose
    assert "http://localhost:18080" not in organic_compose

    print("P26-T01 organic discovery contract: PASS")


if __name__ == "__main__":
    main()
