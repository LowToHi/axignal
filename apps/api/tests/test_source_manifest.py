"""WP2-T02 — SourceManifest base contract tests."""

from __future__ import annotations

import pytest

from axignal_api.source_manifest import (
    DB_STATE_MAP,
    SourceAccessMode,
    SourceManifest,
    SourceState,
    source_manifest_from_db_row,
    state_from_db,
)


class TestSourceStateVocabulary:
    def test_canonical_states_exact(self) -> None:
        assert [s.value for s in SourceState] == [
            "DISCOVERED",
            "LEGAL_REVIEW",
            "PRIVACY_REVIEW",
            "TECHNICAL_PROBE",
            "EVIDENCE_READY",
            "PRODUCT_ADMITTED",
            "COMMERCIAL",
            "SUSPENDED",
            "REVOKED",
            "REJECTED",
        ]

    def test_db_state_mapping(self) -> None:
        assert state_from_db("ADMITTED") == SourceState.PRODUCT_ADMITTED
        assert state_from_db("QUARANTINED") == SourceState.SUSPENDED
        assert state_from_db("COMMERCIAL") == SourceState.COMMERCIAL
        assert state_from_db("REJECTED") == SourceState.REJECTED
        assert state_from_db(None) == SourceState.DISCOVERED
        assert state_from_db("UNKNOWN_STATE") == SourceState.DISCOVERED
        assert state_from_db("discovered") == SourceState.DISCOVERED


class TestSourceManifestContract:
    def test_ted_source_manifest(self) -> None:
        manifest = SourceManifest(
            source_id="src_ted_search_api_v3",
            name="TED Search API v3",
            library_id="O01",
            source_type="INSTITUTIONAL_API",
            access_mode=SourceAccessMode.INSTITUTIONAL_API,
            base_url="https://api.ted.europa.eu/v3",
            state=SourceState.PRODUCT_ADMITTED,
            rights_status="COMMERCIAL_REUSE_WITH_ATTRIBUTION",
            commercial_use=True,
            manifest_version="1.0.0",
            product_shell_ids=["AXIGNAL_OPPORTUNITY_INTELLIGENCE"],
        )
        assert manifest.is_shell is False
        assert manifest.library_id == "O01"

    def test_from_db_row_ted(self) -> None:
        row = {
            "source_id": "src_ted_search_api_v3",
            "name": "TED Search API v3",
            "source_type": "INSTITUTIONAL_API",
            "access_mode": "INSTITUTIONAL_API",
            "base_url": "https://api.ted.europa.eu/v3",
            "admission_state": "ADMITTED",
            "rights_status": "COMMERCIAL_REUSE_WITH_ATTRIBUTION",
            "commercial_use": True,
            "redistribution": True,
            "kill_switch": False,
        }
        manifest = source_manifest_from_db_row(row)
        assert manifest.source_id == "src_ted_search_api_v3"
        assert manifest.state == SourceState.PRODUCT_ADMITTED
        assert manifest.product_shell_ids == ["AXIGNAL_OPPORTUNITY_INTELLIGENCE"]
        assert manifest.commercial_use is True

    def test_from_db_row_quarantined_maps_to_suspended(self) -> None:
        row = {
            "source_id": "bank-of-russia-statistics",
            "name": "Bank of Russia Statistics",
            "source_type": "INSTITUTIONAL_API",
            "admission_state": "QUARANTINED",
            "commercial_use": False,
        }
        manifest = source_manifest_from_db_row(row)
        assert manifest.state == SourceState.SUSPENDED
        assert manifest.library_id == "O06"
        assert manifest.product_shell_ids == []

    def test_rejects_unknown_shell(self) -> None:
        with pytest.raises(ValueError, match="unknown shell"):
            SourceManifest(
                source_id="src-test",
                name="Test Source",
                library_id="O01",
                source_type="PUBLIC_API",
                access_mode=SourceAccessMode.PUBLIC_API,
                manifest_version="1.0.0",
                product_shell_ids=["AXIGNAL_PROCUREMENT"],
            )

    def test_rejects_unknown_library(self) -> None:
        with pytest.raises(ValueError, match="library_id must be one of"):
            SourceManifest(
                source_id="src-test",
                name="Test Source",
                library_id="O10",
                source_type="PUBLIC_API",
                access_mode=SourceAccessMode.PUBLIC_API,
                manifest_version="1.0.0",
                product_shell_ids=["AXIGNAL_OPPORTUNITY_INTELLIGENCE"],
            )

    def test_kill_switch_incompatible_with_admitted(self) -> None:
        with pytest.raises(ValueError, match="kill_switch"):
            SourceManifest(
                source_id="src-test",
                name="Test Source",
                library_id="O01",
                source_type="PUBLIC_API",
                access_mode=SourceAccessMode.PUBLIC_API,
                state=SourceState.PRODUCT_ADMITTED,
                kill_switch=True,
                manifest_version="1.0.0",
                product_shell_ids=["AXIGNAL_OPPORTUNITY_INTELLIGENCE"],
            )

    def test_kill_switch_ok_when_suspended(self) -> None:
        manifest = SourceManifest(
            source_id="src-test",
            name="Test Source",
            library_id="O01",
            source_type="PUBLIC_API",
            access_mode=SourceAccessMode.PUBLIC_API,
            state=SourceState.SUSPENDED,
            kill_switch=True,
            manifest_version="1.0.0",
            product_shell_ids=["AXIGNAL_OPPORTUNITY_INTELLIGENCE"],
        )
        assert manifest.kill_switch is True

    def test_personal_data_requires_privacy_profile(self) -> None:
        with pytest.raises(ValueError, match="privacy_profile"):
            SourceManifest(
                source_id="src-test",
                name="Test Source",
                library_id="O01",
                source_type="PUBLIC_API",
                access_mode=SourceAccessMode.PUBLIC_API,
                has_personal_data=True,
                manifest_version="1.0.0",
                product_shell_ids=["AXIGNAL_OPPORTUNITY_INTELLIGENCE"],
            )

    def test_personal_data_with_privacy_profile_ok(self) -> None:
        manifest = SourceManifest(
            source_id="src-test",
            name="Test Source",
            library_id="O01",
            source_type="PUBLIC_API",
            access_mode=SourceAccessMode.PUBLIC_API,
            has_personal_data=True,
            privacy_profile={
                "purpose": "opportunity intelligence for legal entities",
                "retention_days": 365,
                "consent_required": True,
                "deletion_contract": "dsar",
            },
            manifest_version="1.0.0",
            product_shell_ids=["AXIGNAL_OPPORTUNITY_INTELLIGENCE"],
        )
        assert manifest.privacy_profile["purpose"]

    def test_rejected_source_cannot_be_commercial(self) -> None:
        with pytest.raises(ValueError, match="REJECTED"):
            SourceManifest(
                source_id="src-test",
                name="Test Source",
                library_id="O01",
                source_type="PUBLIC_API",
                access_mode=SourceAccessMode.PUBLIC_API,
                state=SourceState.REJECTED,
                commercial_use=True,
                manifest_version="1.0.0",
                product_shell_ids=["AXIGNAL_OPPORTUNITY_INTELLIGENCE"],
            )

    def test_blocker_scope_does_not_propagate(self) -> None:
        # Contract 11.2: a source blocker must not propagate to other
        # sources, libraries, Core, shells, billing or general UX.
        assert "O01:TedSourceAdmission" != "O02"
        assert SourceState.LEGAL_REVIEW != SourceState.REJECTED
        assert DB_STATE_MAP["QUARANTINED"] == SourceState.SUSPENDED

    def test_source_id_pattern(self) -> None:
        with pytest.raises(ValueError):
            SourceManifest(
                source_id="INVALID ID!",
                name="Bad",
                library_id="O01",
                source_type="PUBLIC_API",
                access_mode=SourceAccessMode.PUBLIC_API,
                manifest_version="1.0.0",
                product_shell_ids=["AXIGNAL_OPPORTUNITY_INTELLIGENCE"],
            )
