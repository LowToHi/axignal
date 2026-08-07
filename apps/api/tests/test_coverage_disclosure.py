"""WP2-T09 — coverage disclosure tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from axignal_api.coverage_disclosure import (
    CoverageDisclosure,
    library_coverage_disclosure,
)


class TestCoverageDisclosure:
    def test_valid_source_disclosure(self) -> None:
        disclosure = CoverageDisclosure(
            scope_type="SOURCE",
            scope_id="src_ted_search_api_v3",
            countries=["LU"],
            languages=["EN"],
            sectors=["public-procurement"],
            time_depth_from=datetime(2020, 1, 1).date(),
            time_depth_to=datetime(2026, 12, 31).date(),
            update_cadence="DAILY",
            source_scope="TED Search API v3 notices",
            evidence_refs=["probe-2026-08-07"],
            expires_at=datetime.now(UTC) + timedelta(days=30),
        )
        assert disclosure.claims_global_coverage is False
        assert disclosure.disclosure_status == "ACTIVE"

    def test_active_coverage_requires_evidence(self) -> None:
        with pytest.raises(ValueError, match="evidence_refs"):
            CoverageDisclosure(
                scope_type="LIBRARY",
                scope_id="O01",
                countries=["LU"],
                languages=["EN"],
                expires_at=datetime.now(UTC) + timedelta(days=30),
            )

    def test_active_coverage_requires_expiry(self) -> None:
        with pytest.raises(ValueError, match="expires_at"):
            CoverageDisclosure(
                scope_type="LIBRARY",
                scope_id="O01",
                countries=["LU"],
                languages=["EN"],
                evidence_refs=["probe-1"],
            )

    def test_global_coverage_claim_rejected(self) -> None:
        with pytest.raises(ValueError, match="claims_global_coverage"):
            CoverageDisclosure(
                scope_type="LIBRARY",
                scope_id="O01",
                claims_global_coverage=True,
            )

    def test_empty_disclosure_ok(self) -> None:
        disclosure = CoverageDisclosure(
            scope_type="SOURCE",
            scope_id="src-new",
            update_cadence="STATIC",
        )
        assert disclosure.disclosure_status == "ACTIVE"
        assert disclosure.countries == []

    def test_suspended_disclosure_needs_no_evidence(self) -> None:
        disclosure = CoverageDisclosure(
            scope_type="SOURCE",
            scope_id="src-x",
            countries=["LU"],
            disclosure_status="SUSPENDED",
        )
        assert disclosure.disclosure_status == "SUSPENDED"

    def test_time_depth_ordering(self) -> None:
        with pytest.raises(ValueError, match="time_depth_from"):
            CoverageDisclosure(
                scope_type="SOURCE",
                scope_id="src-x",
                time_depth_from=datetime(2026, 1, 1).date(),
                time_depth_to=datetime(2020, 1, 1).date(),
            )

    def test_library_helper(self) -> None:
        disclosure = library_coverage_disclosure(
            library_id="O01",
            countries=["LU"],
            languages=["EN", "FR"],
            sectors=["procurement"],
            evidence_refs=["coverage-probe-1"],
            expires_at=datetime.now(UTC) + timedelta(days=90),
        )
        assert disclosure.scope_type == "LIBRARY"
        assert disclosure.scope_id == "O01"
        assert disclosure.claims_global_coverage is False

    def test_cadence_vocabulary(self) -> None:
        with pytest.raises(ValueError):
            CoverageDisclosure(
                scope_type="SOURCE",
                scope_id="src-x",
                update_cadence="WHENEVER",
            )
