"""WP3-T06 — F06 Rights/Provenance tests."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from axignal_api.foundations.f06_rights_provenance import (
    EvidenceProvenance,
    SourceRightsRecord,
)


class TestSourceRightsRecord:
    def test_ted_record(self) -> None:
        record = SourceRightsRecord(
            source_id="src_ted_search_api_v3",
            owner="Publications Office of the EU",
            access_endpoint="https://api.ted.europa.eu/v3/notices/search",
            access_mechanism="INSTITUTIONAL_API",
            tos_license_ref="TED-OJEU-REUSE",
            commercial_use=True,
            redistribution=True,
            attribution_required=True,
            attribution_text="Source: Publications Office of the EU",
            rate_limit_note="TED API v3 rate limits apply",
            revocable=True,
            last_reviewed_at=__import__("datetime").date(2026, 7, 27),
            legal_decision="PENDING",
            privacy_decision="PENDING",
        )
        assert record.kill_switch is False
        assert record.quarantined is False

    def test_attribution_required_needs_text(self) -> None:
        with pytest.raises(ValueError, match="attribution_text"):
            SourceRightsRecord(
                source_id="src-x",
                owner="Owner",
                attribution_required=True,
            )

    def test_personal_data_requires_privacy_approval(self) -> None:
        with pytest.raises(ValueError, match="privacy_decision"):
            SourceRightsRecord(
                source_id="src-x",
                owner="Owner",
                attribution_required=False,
                has_personal_data=True,
                retention_days=365,
                privacy_decision="PENDING",
            )

    def test_personal_data_requires_retention(self) -> None:
        with pytest.raises(ValueError, match="retention_days"):
            SourceRightsRecord(
                source_id="src-x",
                owner="Owner",
                attribution_required=False,
                has_personal_data=True,
                privacy_decision="APPROVED",
            )

    def test_personal_data_approved_ok(self) -> None:
        record = SourceRightsRecord(
            source_id="src-x",
            owner="Owner",
            attribution_required=False,
            has_personal_data=True,
            retention_days=365,
            privacy_decision="APPROVED",
        )
        assert record.privacy_decision == "APPROVED"

    def test_quarantine_requires_kill_switch(self) -> None:
        with pytest.raises(ValueError, match="kill_switch"):
            SourceRightsRecord(
                source_id="src-x",
                owner="Owner",
                attribution_required=False,
                quarantined=True,
            )

    def test_quarantined_with_kill_switch_ok(self) -> None:
        record = SourceRightsRecord(
            source_id="src-x",
            owner="Owner",
            attribution_required=False,
            kill_switch=True,
            quarantined=True,
        )
        assert record.quarantined is True

    def test_legal_decision_vocabulary(self) -> None:
        with pytest.raises(ValueError):
            SourceRightsRecord(
                source_id="src-x",
                owner="Owner",
                attribution_required=False,
                legal_decision="MAYBE",
            )


class TestEvidenceProvenance:
    def test_live_probe_provenance(self) -> None:
        provenance = EvidenceProvenance(
            evidence_id="ev-1",
            source_id="src_ted_search_api_v3",
            source_version="v3",
            retrieved_at=datetime.now(UTC),
            retrieved_by="research-worker",
            retrieval_mode="LIVE_API_TECHNICAL_PROBE",
            content_hash=f"sha256:{'a' * 64}",
            request_hash="req-hash-0001",
            original_url="https://api.ted.europa.eu/v3/notices/search",
        )
        assert provenance.record_version == 1

    def test_content_hash_pattern(self) -> None:
        with pytest.raises(ValueError):
            EvidenceProvenance(
                evidence_id="ev-1",
                source_id="src-x",
                retrieved_at=datetime.now(UTC),
                content_hash="md5:abc",
                request_hash="req-hash-0001",
            )

    def test_fixture_requires_original_url(self) -> None:
        with pytest.raises(ValueError, match="original_url"):
            EvidenceProvenance(
                evidence_id="ev-1",
                source_id="src-x",
                retrieved_at=datetime.now(UTC),
                retrieval_mode="FROZEN_FIXTURE",
                content_hash=f"sha256:{'b' * 64}",
                request_hash="req-hash-0001",
            )

    def test_fixture_with_original_url_ok(self) -> None:
        provenance = EvidenceProvenance(
            evidence_id="ev-1",
            source_id="src-x",
            retrieved_at=datetime.now(UTC),
            retrieval_mode="FROZEN_FIXTURE",
            content_hash=f"sha256:{'c' * 64}",
            request_hash="req-hash-0001",
            original_url="https://example.org/real-source",
        )
        assert provenance.retrieval_mode == "FROZEN_FIXTURE"

    def test_record_versioning(self) -> None:
        provenance = EvidenceProvenance(
            evidence_id="ev-1",
            source_id="src-x",
            retrieved_at=datetime.now(UTC),
            content_hash=f"sha256:{'d' * 64}",
            request_hash="req-hash-0001",
            record_version=3,
        )
        assert provenance.record_version == 3
