"""WP5 — O01 Procurement tests (T01, T04-T07)."""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from axignal_api.o01_procurement import (
    AwardRecord,
    BuyerResolution,
    Lot,
    NoticeLifecycle,
    NoticeState,
    ted_coverage_disclosure,
    ted_profiles,
    ted_source_manifest,
)


def notice(**overrides: object) -> NoticeLifecycle:
    base: dict[str, object] = {
        "notice_id": "123456-2026",
        "published_at": datetime(2026, 8, 1, tzinfo=UTC),
        "content_hash": f"sha256:{'a' * 64}",
    }
    base.update(overrides)
    return NoticeLifecycle(**base)


class TestTedSourceAdmission:
    def test_manifest_complete(self) -> None:
        manifest = ted_source_manifest()
        assert manifest.source_id == "src_ted_search_api_v3"
        assert manifest.library_id == "O01"
        assert manifest.state.value == "PRODUCT_ADMITTED"
        assert manifest.rights_status == "COMMERCIAL_REUSE_WITH_ATTRIBUTION"
        assert manifest.commercial_use is True
        assert manifest.product_shell_ids == ["AXIGNAL_OPPORTUNITY_INTELLIGENCE"]
        assert manifest.manifest_version == "1.1.0"

    def test_all_profiles_present(self) -> None:
        profiles = ted_profiles()
        assert set(profiles) == {"quality", "rights", "privacy", "outage"}
        assert profiles["quality"].source_id == "src_ted_search_api_v3"
        assert profiles["rights"].commercial_use is True
        assert profiles["privacy"].has_personal_data is False
        assert profiles["outage"].outage_escalation == "QUARANTINE"

    def test_coverage_disclosure(self) -> None:
        disclosure = ted_coverage_disclosure()
        assert disclosure.scope_id == "src_ted_search_api_v3"
        assert disclosure.expires_at is not None


class TestNoticeLifecycle:
    def test_published_initial(self) -> None:
        assert notice().state == NoticeState.PUBLISHED

    def test_corrected_requires_timestamp(self) -> None:
        with pytest.raises(ValueError, match="corrected_at"):
            notice(state="CORRECTED")

    def test_cancelled_requires_timestamp(self) -> None:
        with pytest.raises(ValueError, match="cancelled_at"):
            notice(state="CANCELLED")

    def test_correction_transition(self) -> None:
        result = notice().transition(
            NoticeState.CORRECTED, at=datetime(2026, 8, 2, tzinfo=UTC)
        )
        assert result.state == NoticeState.CORRECTED
        assert result.amendment_count == 1
        assert result.corrected_at is not None

    def test_second_correction_increments(self) -> None:
        once = notice().transition(
            NoticeState.CORRECTED, at=datetime(2026, 8, 2, tzinfo=UTC)
        )
        twice = once.transition(
            NoticeState.CORRECTED, at=datetime(2026, 8, 3, tzinfo=UTC)
        )
        assert twice.amendment_count == 2

    def test_cancellation_transition(self) -> None:
        result = notice().transition(
            NoticeState.CANCELLED, at=datetime(2026, 8, 3, tzinfo=UTC)
        )
        assert result.state == NoticeState.CANCELLED

    def test_cancelled_is_terminal(self) -> None:
        cancelled = notice().transition(
            NoticeState.CANCELLED, at=datetime(2026, 8, 3, tzinfo=UTC)
        )
        with pytest.raises(ValueError, match="illegal notice transition"):
            cancelled.transition(
                NoticeState.CORRECTED, at=datetime(2026, 8, 4, tzinfo=UTC)
            )

    def test_notice_id_pattern(self) -> None:
        with pytest.raises(ValueError):
            notice(notice_id="bad-id")


class TestLotAndAmendment:
    def test_plain_lot(self) -> None:
        lot = Lot(lot_id="lot-1", notice_id="123456-2026", title="Roads")
        assert lot.is_amendment is False

    def test_amendment_requires_source_lot(self) -> None:
        with pytest.raises(ValueError, match="amended_lot_id"):
            Lot(lot_id="lot-2", notice_id="123456-2026", title="Roads v2", is_amendment=True)

    def test_amendment_with_source_ok(self) -> None:
        lot = Lot(
            lot_id="lot-2",
            notice_id="123456-2026",
            title="Roads v2",
            is_amendment=True,
            amended_lot_id="lot-1",
        )
        assert lot.amended_lot_id == "lot-1"

    def test_cpv_codes(self) -> None:
        lot = Lot(lot_id="lot-1", notice_id="123456-2026", title="Roads", cpv_codes=["45233100"])
        assert lot.cpv_codes == ["45233100"]


class TestBuyerSupplierResolution:
    def test_native_identifier_resolution(self) -> None:
        resolution = BuyerResolution(
            party_id="pty-1",
            role="BUYER",
            entity_id="ent_ministerio_fomento_es",
            entity_fingerprint="fp:abc",
            resolution_method="NATIVE_IDENTIFIER",
            resolved_at=datetime(2026, 8, 7, tzinfo=UTC),
        )
        assert resolution.role == "BUYER"

    def test_name_match_requires_fingerprint(self) -> None:
        with pytest.raises(ValueError, match="entity_fingerprint"):
            BuyerResolution(
                party_id="pty-1",
                role="BUYER",
                entity_id="ent_x",
                entity_fingerprint="",
                resolution_method="NAME_MATCH",
                resolved_at=datetime(2026, 8, 7, tzinfo=UTC),
            )

    def test_manual_resolution_ok(self) -> None:
        resolution = BuyerResolution(
            party_id="pty-2",
            role="SUPPLIER",
            entity_id="ent_y",
            entity_fingerprint="fp:def",
            resolution_method="MANUAL",
            resolved_at=datetime(2026, 8, 7, tzinfo=UTC),
        )
        assert resolution.resolution_method == "MANUAL"


class TestAwardRecord:
    def test_award_without_signed_contract(self) -> None:
        award = AwardRecord(
            award_id="award-1",
            notice_id="123456-2026",
            lot_id="lot-1",
            supplier_entity_id="ent_y",
            award_value_eur=500_000.0,
            awarded_at=date(2026, 9, 15),
        )
        assert award.contract_signed is False

    def test_signed_contract_requires_evidence(self) -> None:
        with pytest.raises(ValueError, match="evidence_ref"):
            AwardRecord(
                award_id="award-1",
                notice_id="123456-2026",
                lot_id="lot-1",
                supplier_entity_id="ent_y",
                award_value_eur=500_000.0,
                awarded_at=date(2026, 9, 15),
                contract_signed=True,
            )

    def test_signed_contract_with_evidence_ok(self) -> None:
        award = AwardRecord(
            award_id="award-1",
            notice_id="123456-2026",
            lot_id="lot-1",
            supplier_entity_id="ent_y",
            award_value_eur=500_000.0,
            awarded_at=date(2026, 9, 15),
            contract_signed=True,
            evidence_ref="evidence-award-1",
        )
        assert award.evidence_ref == "evidence-award-1"
