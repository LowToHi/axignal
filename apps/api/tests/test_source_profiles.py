"""WP2-T05..T08 — source profiles tests (quality, rights, privacy, outage)."""

from __future__ import annotations

import pytest

from axignal_api.source_profiles import (
    OutageProfile,
    PrivacyProfile,
    QualityProfile,
    RightsProfile,
)


class TestQualityProfile:
    def test_valid_profile(self) -> None:
        profile = QualityProfile(
            source_id="src_ted_search_api_v3",
            freshness_max_age_days=7,
            completeness_score=0.9,
            latency_observed_seconds=1.2,
            reliability_pct=99.5,
            evidence_refs=["probe-2026-08-07"],
        )
        assert profile.deduplication == "CONTENT_HASH"
        assert profile.provenance_traceable is True

    def test_score_requires_evidence(self) -> None:
        with pytest.raises(ValueError, match="evidence_refs"):
            QualityProfile(
                source_id="src-x",
                freshness_max_age_days=7,
                completeness_score=0.8,
                latency_observed_seconds=1.0,
                reliability_pct=99.0,
            )

    def test_zero_score_without_evidence_ok(self) -> None:
        profile = QualityProfile(
            source_id="src-x",
            freshness_max_age_days=30,
            completeness_score=0.0,
            latency_observed_seconds=0.0,
            reliability_pct=0.0,
        )
        assert profile.completeness_score == 0.0

    def test_bounded_values(self) -> None:
        with pytest.raises(ValueError):
            QualityProfile(
                source_id="src-x",
                freshness_max_age_days=99999,
                completeness_score=1.5,
                latency_observed_seconds=1.0,
                reliability_pct=100.0,
            )

    def test_deduplication_vocabulary(self) -> None:
        with pytest.raises(ValueError):
            QualityProfile(
                source_id="src-x",
                freshness_max_age_days=1,
                completeness_score=0.0,
                latency_observed_seconds=1.0,
                reliability_pct=0.0,
                deduplication="FUZZY",
            )


class TestRightsProfile:
    def test_valid_rights(self) -> None:
        profile = RightsProfile(
            source_id="src_ted_search_api_v3",
            license_id="TED-OJEU-REUSE",
            attribution_text="Source: Publications Office of the EU",
            commercial_use=True,
            redistribution=True,
            derivative_reuse="ATTRIBUTION",
            retention_days=3650,
        )
        assert profile.kill_switch_available is True

    def test_attribution_required_needs_text(self) -> None:
        with pytest.raises(ValueError, match="attribution_text"):
            RightsProfile(
                source_id="src-x",
                license_id="MIT",
                attribution_required=True,
            )

    def test_attribution_not_required_ok(self) -> None:
        profile = RightsProfile(
            source_id="src-x",
            license_id="CC0",
            attribution_required=False,
        )
        assert profile.attribution_required is False

    def test_derivative_vocabulary(self) -> None:
        with pytest.raises(ValueError):
            RightsProfile(
                source_id="src-x",
                license_id="MIT",
                derivative_reuse="WHATEVER",
            )


class TestPrivacyProfile:
    def test_non_personal_ok(self) -> None:
        profile = PrivacyProfile(
            source_id="src_x",
            has_personal_data=False,
        )
        assert profile.cross_shell_sharing == "FORBIDDEN"

    def test_personal_requires_purpose_and_deletion(self) -> None:
        with pytest.raises(ValueError, match="purpose_limitation"):
            PrivacyProfile(
                source_id="src-x",
                has_personal_data=True,
                deletion_contract="DSAR",
                retention_days=365,
            )
        with pytest.raises(ValueError, match="deletion_contract"):
            PrivacyProfile(
                source_id="src-x",
                has_personal_data=True,
                purpose_limitation="processing applications",
                retention_days=365,
            )
        with pytest.raises(ValueError, match="retention_days"):
            PrivacyProfile(
                source_id="src-x",
                has_personal_data=True,
                purpose_limitation="processing applications",
                deletion_contract="DSAR",
            )

    def test_personal_complete_ok(self) -> None:
        profile = PrivacyProfile(
            source_id="src-x",
            has_personal_data=True,
            data_categories=["candidate_name"],
            purpose_limitation="public employment application processing",
            retention_days=365,
            consent_required=True,
            deletion_contract="DSAR_AND_EXPIRY",
        )
        assert profile.data_minimisation is True

    def test_categories_require_minimisation(self) -> None:
        with pytest.raises(ValueError, match="data_minimisation"):
            PrivacyProfile(
                source_id="src-x",
                has_personal_data=True,
                data_categories=["x"],
                purpose_limitation="p",
                retention_days=30,
                deletion_contract="DSAR",
                data_minimisation=False,
            )

    def test_cross_shell_sharing_default_forbidden(self) -> None:
        assert PrivacyProfile(source_id="src-x").cross_shell_sharing == "FORBIDDEN"


class TestOutageProfile:
    def test_valid_profile(self) -> None:
        profile = OutageProfile(
            source_id="src_x",
            retry_max_attempts=3,
            backoff_base_seconds=2.0,
            backoff_max_seconds=300.0,
            request_timeout_seconds=15.0,
        )
        assert profile.outage_escalation == "QUARANTINE"
        assert profile.partial_failure_policy == "PARTIAL_RESULT"

    def test_backoff_ordering(self) -> None:
        with pytest.raises(ValueError, match="backoff_max_seconds"):
            OutageProfile(
                source_id="src-x",
                backoff_base_seconds=300.0,
                backoff_max_seconds=2.0,
            )

    def test_retry_bounds(self) -> None:
        with pytest.raises(ValueError):
            OutageProfile(source_id="src-x", retry_max_attempts=100)

    def test_escalation_vocabulary(self) -> None:
        with pytest.raises(ValueError):
            OutageProfile(source_id="src-x", outage_escalation="PANIC")
