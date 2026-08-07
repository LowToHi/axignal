"""WP14-T12 — mandatory cross-library E2E tests."""

from __future__ import annotations

import pytest

from axignal_api.cross_library_e2e import (
    CrossLibraryE2EFailure,
    run_cross_library_e2e,
)


class TestCrossLibraryE2E:
    def test_mandatory_journey_passes(self) -> None:
        evidence = run_cross_library_e2e()
        assert evidence["status"] == "PASS"
        assert evidence["f1_regulatory_change"]["sectors"] == ["construction", "transport"]
        assert evidence["f2_infrastructure"] == "National transport corridor"
        assert evidence["f3_notices"] == "PROCURES"
        assert evidence["f4_corporate"] == "EXPANSION"
        assert evidence["f5_trade_dependency"] == "steel"
        assert evidence["f6_energy"] == "OBSERVATION"
        assert evidence["f7_opportunity_graph"]["nodes"] == 2
        assert evidence["f7_opportunity_graph"]["hypothesis"] == "HYPOTHESIS"
        assert evidence["f8_pursuit"] == "DECISION_REVIEW"
        assert evidence["f9_outcome"]["result"] == "WITHDRAWN"
        assert evidence["f9_outcome"]["hypothesis_stayed_hypothesis"] is True
        assert evidence["f10_views"]["navigator_libraries"] == 2
        assert evidence["f11_entitlements"]["submit_denied_by_default"] is True
        assert evidence["f12_portfolio"] == 1

    def test_journey_is_deterministic(self) -> None:
        first = run_cross_library_e2e()
        second = run_cross_library_e2e()
        assert first["f3_notices"] == second["f3_notices"]
        assert first["f7_opportunity_graph"] == second["f7_opportunity_graph"]
        assert first["f9_outcome"] == second["f9_outcome"]

    def test_failure_contract(self) -> None:
        with pytest.raises(CrossLibraryE2EFailure):
            raise CrossLibraryE2EFailure("gate failed")
