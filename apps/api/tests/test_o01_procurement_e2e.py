"""WP5-T12 — O01 Procurement E2E tests."""

from __future__ import annotations

import pytest

from axignal_api.o01_procurement_e2e import (
    ProcurementE2EFailure,
    run_o01_e2e,
)


class TestO01E2E:
    def test_full_journey_passes(self) -> None:
        evidence = run_o01_e2e()
        assert evidence["status"] == "PASS"
        assert evidence["f1_source_contract"]["source"] == "src_ted_search_api_v3"
        assert evidence["f1_source_contract"]["state"] == "PRODUCT_ADMITTED"
        assert evidence["f1_source_contract"]["profiles"] == 4
        assert evidence["f2_notice"]["amendments"] == 1
        assert evidence["f3_lots"]["amendment"] == "lot-2"
        assert evidence["f4_buyer"]["entity"] == "ent_ministerio_fomento_es"
        assert evidence["f5_qualification"] == "GO"
        assert evidence["f6_bid_workspace"] == "SUBMITTED"
        assert evidence["f7_award"]["value_eur"] == 1_450_000.0
        assert evidence["f8_rollback"] == "READY_FOR_APPROVAL"

    def test_journey_is_deterministic(self) -> None:
        first = run_o01_e2e()
        second = run_o01_e2e()
        assert first["f2_notice"] == second["f2_notice"]
        assert first["f5_qualification"] == second["f5_qualification"]
        assert first["f6_bid_workspace"] == second["f6_bid_workspace"]

    def test_failure_contract(self) -> None:
        with pytest.raises(ProcurementE2EFailure):
            raise ProcurementE2EFailure("gate failed")
