"""WP4-T12 — Opportunity Operations E2E tests."""

from __future__ import annotations

import pytest

from axignal_api.opportunity_operations_e2e import (
    OpportunityOperationsE2EFailure,
    run_opportunity_operations_e2e,
)


class TestOpportunityOperationsE2E:
    def test_full_journey_passes(self) -> None:
        evidence = run_opportunity_operations_e2e()
        assert evidence["status"] == "PASS"
        assert evidence["f1_opportunity"] == "opp-e2e-1"
        assert evidence["f2_pursuit_states"] == [
            "QUALIFIED",
            "DECISION_REVIEW",
            "ACTIVE",
        ]
        assert evidence["f3_workspace"]
        assert evidence["f4_clarification"] == "clar-e2e-1"
        assert evidence["f5_outcome_learning"]["outcome"] == "WON"
        assert evidence["f6_rollback"] == "v1"

    def test_journey_is_deterministic(self) -> None:
        first = run_opportunity_operations_e2e()
        second = run_opportunity_operations_e2e()
        assert first["f1_opportunity"] == second["f1_opportunity"]
        assert first["f2_pursuit_states"] == second["f2_pursuit_states"]

    def test_failure_contract(self) -> None:
        with pytest.raises(OpportunityOperationsE2EFailure):
            raise OpportunityOperationsE2EFailure("gate failed")
