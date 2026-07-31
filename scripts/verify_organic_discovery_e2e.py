#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

DSN = os.environ["AXIGNAL_DATABASE_URL"]
EVIDENCE_DIR = Path(os.environ.get("AXIGNAL_ORGANIC_EVIDENCE_DIR", "artifacts"))
NOW = datetime(2026, 7, 31, 18, 0, tzinfo=UTC)
FOUNDER = "usr_p26_founder_e2e"


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def call(
    query: str,
    params: tuple[object, ...] = (),
    *,
    application_role: bool = False,
) -> dict | None:
    with (
        psycopg.connect(DSN, row_factory=dict_row) as connection,
        connection.cursor() as cursor,
    ):
        if application_role:
            cursor.execute("SET LOCAL ROLE axignal_app")
        cursor.execute(query, params)
        if cursor.description is None:
            return None
        return cursor.fetchone()


def app_call(query: str, params: tuple[object, ...] = ()) -> dict | None:
    return call(query, params, application_role=True)


def expect_failure(marker: str, operation) -> str:
    try:
        operation()
    except Exception as exc:
        assert marker in str(exc), f"Expected {marker!r}, got {exc!r}"
        return marker
    raise AssertionError(f"Expected failure {marker}")


def scalar(query: str, params: tuple[object, ...] = ()) -> int:
    row = call(query, params)
    assert row is not None
    return int(next(iter(row.values())))


def seed_candidate(
    *,
    path: str,
    synthetic: bool,
    demand: float,
    opportunities: int,
    buyers: int,
) -> UUID:
    metrics = {
        "country_name": "Germany",
        "sector_name": "Cybersecurity",
        "currency": "EUR",
        "coverage_label": "3 declared libraries",
        "opportunities": [
            {
                "title": "Secure cloud infrastructure services",
                "buyer": "Federal Digital Administration",
                "value_label": "€2.4M",
                "deadline": "2026-09-18",
                "source_url": "https://example.test/notices/secure-cloud",
            },
            {
                "title": "Managed security operations centre",
                "buyer": "Regional Public IT Agency",
                "value_label": "Value not declared",
                "deadline": "2026-09-24",
                "source_url": "https://example.test/notices/soc",
            },
        ],
    }
    row = call(
        """
        INSERT INTO growth_private.seo_page_candidates (
          page_kind, locale, country_code, country_slug, sector_slug,
          canonical_path, title, description, state,
          active_opportunity_count, unique_buyer_count,
          known_value_microunits, demand_score, data_quality_score,
          uniqueness_score, source_coverage_score, content_depth_score,
          freshness_at, source_count, methodology_version,
          is_synthetic, metrics, source_urls, created_at, updated_at
        ) VALUES (
          'TENDER_HUB', 'en', 'DE', 'germany',
          CASE WHEN %s THEN 'synthetic-cybersecurity' ELSE 'cybersecurity' END,
          %s,
          CASE WHEN %s THEN 'Synthetic Germany cybersecurity tenders'
               ELSE 'Cybersecurity government tenders in Germany' END,
          'Current opportunities with buyer, value, deadline and provenance.',
          'CANDIDATE', %s, %s, 2400000000000, %s, 0.91,
          0.82, 0.86, 0.88, %s, 3,
          'public-intelligence-snapshot@1.0.0', %s, %s, %s, %s, %s
        )
        RETURNING page_id
        """,
        (
            synthetic,
            path,
            synthetic,
            opportunities,
            buyers,
            demand,
            NOW - timedelta(hours=2),
            synthetic,
            Jsonb(metrics),
            Jsonb(
                [
                    "https://example.test/source-a",
                    "https://example.test/source-b",
                    "https://example.test/source-c",
                ]
            ),
            NOW,
            NOW,
        ),
    )
    assert row is not None
    return UUID(str(row["page_id"]))


def main() -> None:
    call(
        """
        INSERT INTO growth_private.founder_admin_principals (
          subject, status, provisioned_by, provisioned_at
        ) VALUES (%s, 'ACTIVE', 'P26_E2E', %s)
        ON CONFLICT (subject) DO UPDATE SET
          status = 'ACTIVE', revoked_at = NULL
        """,
        (FOUNDER, NOW),
    )

    identity_organisations_before = scalar(
        "SELECT count(*) FROM identity_private.organisations"
    )
    trial_grants_before = scalar(
        "SELECT count(*) FROM identity_private.trial_grants"
    )

    admitted_id = seed_candidate(
        path="/tenders/germany/cybersecurity",
        synthetic=False,
        demand=0.82,
        opportunities=28,
        buyers=9,
    )
    rejected_id = seed_candidate(
        path="/tenders/germany/synthetic-cybersecurity",
        synthetic=True,
        demand=0.2,
        opportunities=2,
        buyers=1,
    )

    unauthorized = expect_failure(
        "founder_admin_required",
        lambda: app_call(
            "SELECT growth_private.evaluate_indexability(%s, %s, %s)",
            (admitted_id, "usr_not_founder", NOW),
        ),
    )

    rejected = app_call(
        "SELECT growth_private.evaluate_indexability(%s, %s, %s) AS result",
        (rejected_id, FOUNDER, NOW),
    )
    assert rejected is not None
    assert rejected["result"]["decision"] == "NOINDEX"
    assert "SYNTHETIC_DATA" in rejected["result"]["reason_codes"]

    admitted = app_call(
        "SELECT growth_private.evaluate_indexability(%s, %s, %s) AS result",
        (admitted_id, FOUNDER, NOW),
    )
    assert admitted is not None
    assert admitted["result"]["decision"] == "INDEX"

    publish = app_call(
        """
        SELECT growth_private.publish_page_snapshot(
          %s, %s, %s, %s, %s
        ) AS result
        """,
        (
            admitted_id,
            FOUNDER,
            digest("p26-public-snapshot-v1"),
            NOW + timedelta(hours=24),
            NOW,
        ),
    )
    assert publish is not None
    assert publish["result"]["state"] == "PUBLISHED"
    assert publish["result"]["snapshot_version"] == 1

    public_page = app_call(
        """
        SELECT growth_private.public_discovery_page(
          'germany', 'cybersecurity', 'TENDER_HUB', 'en', %s
        ) AS result
        """,
        (NOW + timedelta(minutes=1),),
    )
    assert public_page is not None
    assert public_page["result"]["canonical_path"] == (
        "/tenders/germany/cybersecurity"
    )
    assert public_page["result"]["active_opportunity_count"] == 28

    sitemap = app_call(
        """
        SELECT count(*) AS included
        FROM growth_private.public_sitemap_entries(%s)
        """,
        (NOW + timedelta(minutes=1),),
    )
    assert sitemap is not None and sitemap["included"] == 1

    token = "p26-alert-confirmation-token-0000000001"
    alert = app_call(
        """
        SELECT growth_private.subscribe_tender_alert(
          'buyer.p26@example.test', %s, %s, 'DE', 'cybersecurity',
          'en', 'DAILY', '/tenders/germany/cybersecurity', %s
        ) AS result
        """,
        (digest("buyer-email"), digest(token), NOW),
    )
    assert alert is not None
    assert alert["result"]["state"] == "PENDING_CONFIRMATION"
    assert alert["result"]["trial_created"] is False
    assert alert["result"]["tenant_created"] is False

    confirmation = app_call(
        "SELECT growth_private.confirm_tender_alert(%s, %s) AS result",
        (digest(token), NOW + timedelta(minutes=2)),
    )
    assert confirmation is not None
    assert confirmation["result"]["state"] == "ACTIVE"
    assert confirmation["result"]["trial_created"] is False
    assert confirmation["result"]["tenant_created"] is False

    citation = app_call(
        """
        SELECT growth_private.record_ai_citation(
          %s, 'CHATGPT', 'SEARCH',
          'https://axignal.com/tenders/germany/cybersecurity',
          %s, 'MANUAL', '{"utm_source":"chatgpt.com"}'::jsonb, %s
        ) AS citation_event_id
        """,
        (FOUNDER, digest("find cybersecurity tenders germany"), NOW),
    )
    assert citation is not None

    identity_organisations_after = scalar(
        "SELECT count(*) FROM identity_private.organisations"
    )
    trial_grants_after = scalar(
        "SELECT count(*) FROM identity_private.trial_grants"
    )
    assert identity_organisations_after == identity_organisations_before
    assert trial_grants_after == trial_grants_before

    direct_table_access = expect_failure(
        "permission denied",
        lambda: app_call(
            "SELECT count(*) FROM growth_private.crm_contacts"
        ),
    )
    append_only_decisions = expect_failure(
        "append_only_relation",
        lambda: call(
            "UPDATE growth_private.seo_indexability_decisions SET score = 0"
        ),
    )
    append_only_citations = expect_failure(
        "append_only_relation",
        lambda: call("DELETE FROM growth_private.ai_citation_events"),
    )
    append_only_audit = expect_failure(
        "append_only_relation",
        lambda: call(
            "DELETE FROM growth_private.founder_admin_audit_events"
        ),
    )

    evidence = {
        "status": "PASS",
        "task": "AX-GE2E-P26-T01",
        "indexability_policy": "indexability-gate@1.0.0",
        "high_quality_candidate": "INDEX",
        "synthetic_candidate": "NOINDEX",
        "synthetic_in_sitemap": False,
        "published_snapshot_version": 1,
        "public_page_path": "/tenders/germany/cybersecurity",
        "public_sitemap_entries": 1,
        "unauthorized_founder": unauthorized,
        "alert_initial_state": "PENDING_CONFIRMATION",
        "alert_confirmed_state": "ACTIVE",
        "alert_created_tenant": False,
        "alert_created_trial": False,
        "identity_organisation_delta": (
            identity_organisations_after - identity_organisations_before
        ),
        "trial_grant_delta": trial_grants_after - trial_grants_before,
        "citation_recorded": True,
        "direct_growth_table_access": direct_table_access,
        "indexability_ledger": append_only_decisions,
        "citation_ledger": append_only_citations,
        "founder_audit_ledger": append_only_audit,
        "external_search_provider_calls": 0,
        "model_calls": 0,
        "public_indexing_authorised_by_ci": False,
    }
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    output = EVIDENCE_DIR / "organic-discovery-e2e.json"
    output.write_text(
        json.dumps(evidence, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(json.dumps(evidence, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
