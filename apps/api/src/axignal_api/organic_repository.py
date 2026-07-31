from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb


class OrganicDiscoveryRepository:
    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    @contextmanager
    def _cursor(self, *, application_role: bool = True) -> Iterator[psycopg.Cursor]:
        with (
            psycopg.connect(self.dsn, row_factory=dict_row) as connection,
            connection.cursor() as cursor,
        ):
            if application_role:
                cursor.execute("SET LOCAL ROLE axignal_app")
            yield cursor

    def founder_authorized(self, *, subject: str) -> bool:
        try:
            with self._cursor() as cursor:
                cursor.execute(
                    "SELECT growth_private.assert_founder_admin(%s)",
                    (subject,),
                )
            return True
        except psycopg.Error:
            return False

    def overview(self, *, actor_subject: str) -> dict[str, Any]:
        with self._cursor() as cursor:
            cursor.execute(
                "SELECT growth_private.founder_overview(%s) AS result",
                (actor_subject,),
            )
            row = cursor.fetchone()
        return dict(row["result"]) if row and isinstance(row["result"], dict) else {}

    def pages(self, *, actor_subject: str) -> list[dict[str, Any]]:
        with self._cursor() as cursor:
            cursor.execute(
                "SELECT * FROM growth_private.admin_pages(%s)",
                (actor_subject,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def evaluate(self, *, page_id: UUID, actor_subject: str) -> dict[str, Any]:
        with self._cursor() as cursor:
            cursor.execute(
                "SELECT growth_private.evaluate_indexability(%s, %s, now()) AS result",
                (page_id, actor_subject),
            )
            row = cursor.fetchone()
        if not row or not isinstance(row["result"], dict):
            raise RuntimeError("Indexability evaluation returned no result")
        return dict(row["result"])

    def publish(
        self,
        *,
        page_id: UUID,
        actor_subject: str,
        content_hash: str,
        ttl_hours: int,
    ) -> dict[str, Any]:
        now = datetime.now(UTC)
        with self._cursor() as cursor:
            cursor.execute(
                """
                SELECT growth_private.publish_page_snapshot(
                  %s, %s, %s, %s, %s
                ) AS result
                """,
                (
                    page_id,
                    actor_subject,
                    content_hash,
                    now + timedelta(hours=ttl_hours),
                    now,
                ),
            )
            row = cursor.fetchone()
        if not row or not isinstance(row["result"], dict):
            raise RuntimeError("SEO publication returned no result")
        return dict(row["result"])

    def public_page(
        self,
        *,
        country_slug: str,
        sector_slug: str,
        page_kind: str,
        locale: str,
    ) -> dict[str, Any] | None:
        with self._cursor() as cursor:
            cursor.execute(
                """
                SELECT growth_private.public_discovery_page(
                  %s, %s, %s, %s, now()
                ) AS result
                """,
                (country_slug, sector_slug, page_kind, locale),
            )
            row = cursor.fetchone()
        if not row or not isinstance(row["result"], dict):
            return None
        return dict(row["result"])

    def sitemap(self) -> list[dict[str, Any]]:
        with self._cursor() as cursor:
            cursor.execute(
                "SELECT * FROM growth_private.public_sitemap_entries(now())"
            )
            return [dict(row) for row in cursor.fetchall()]

    def subscribe_alert(
        self,
        *,
        email: str,
        email_hmac: str,
        confirmation_token_digest: str,
        country_code: str,
        sector_slug: str,
        locale: str,
        cadence: str,
        source_path: str,
    ) -> dict[str, Any]:
        with self._cursor() as cursor:
            cursor.execute(
                """
                SELECT growth_private.subscribe_tender_alert(
                  %s, %s, %s, %s, %s, %s, %s, %s, now()
                ) AS result
                """,
                (
                    email,
                    email_hmac,
                    confirmation_token_digest,
                    country_code,
                    sector_slug,
                    locale,
                    cadence,
                    source_path,
                ),
            )
            row = cursor.fetchone()
        if not row or not isinstance(row["result"], dict):
            raise RuntimeError("Tender alert subscription returned no result")
        return dict(row["result"])

    def contacts(self, *, actor_subject: str) -> list[dict[str, Any]]:
        with self._cursor() as cursor:
            cursor.execute(
                "SELECT * FROM growth_private.admin_contacts(%s)",
                (actor_subject,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def alerts(self, *, actor_subject: str) -> list[dict[str, Any]]:
        with self._cursor() as cursor:
            cursor.execute(
                "SELECT * FROM growth_private.admin_alerts(%s)",
                (actor_subject,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def record_citation(
        self,
        *,
        actor_subject: str,
        provider: str,
        surface: str,
        cited_url: str,
        query_hmac: str,
        source: str,
        metadata: dict[str, Any],
        observed_at: datetime,
    ) -> UUID:
        with self._cursor() as cursor:
            cursor.execute(
                """
                SELECT growth_private.record_ai_citation(
                  %s, %s, %s, %s, %s, %s, %s, %s
                ) AS citation_event_id
                """,
                (
                    actor_subject,
                    provider,
                    surface,
                    cited_url,
                    query_hmac,
                    source,
                    Jsonb(metadata),
                    observed_at,
                ),
            )
            row = cursor.fetchone()
        if not row:
            raise RuntimeError("Citation event was not recorded")
        return UUID(str(row["citation_event_id"]))

    def test_bootstrap_founder(self, *, subject: str) -> None:
        with self._cursor(application_role=False) as cursor:
            cursor.execute(
                """
                INSERT INTO growth_private.founder_admin_principals (
                  subject, status, provisioned_by
                ) VALUES (%s, 'ACTIVE', 'P26_TEST_RUNTIME')
                ON CONFLICT (subject) DO UPDATE SET
                  status = 'ACTIVE', revoked_at = NULL
                """,
                (subject,),
            )
