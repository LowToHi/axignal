"""WP8-WP13 — O04-O09 opportunity libraries tests."""

from __future__ import annotations

from datetime import date
from uuid import UUID

import pytest

from axignal_api.opportunity_libraries import (
    ClimateObligation,
    CompanyRecord,
    EnergyAsset,
    InfrastructureProject,
    InnovationWorkspace,
    MacroIndicator,
    OpportunityWorkspace,
    PatentRecord,
    ScenarioBoundary,
    TariffRestriction,
    TemporalMilestone,
    TradeFlow,
    source_admission,
)

TENANT = UUID("11111111-1111-4111-8111-111111111111")
WS_ID = UUID("33333333-3333-4333-8333-333333333333")


class TestSourceAdmissions:
    def test_all_six_libraries(self) -> None:
        for library_id, source_id in (
            ("O04", "src_eib_global_projects"),
            ("O05", "src_official_business_registers"),
            ("O06", "src_eurostat"),
            ("O07", "src_eurostat_comtrade"),
            ("O08", "src_entsoe"),
            ("O09", "src_epo_ops"),
        ):
            manifest = source_admission(library_id, source_id)
            assert manifest["state"] == "DISCOVERED"
            assert manifest["commercial_use"] == "PENDING_HUMAN_DECISION"
            assert manifest["product_shell"] == "AXIGNAL_OPPORTUNITY_INTELLIGENCE"


class TestSharedWorkspace:
    def test_library_pattern(self) -> None:
        for library_id in ("O04", "O05", "O06", "O07", "O08", "O09"):
            workspace = OpportunityWorkspace(
                workspace_id=WS_ID,
                tenant_id=TENANT,
                library_id=library_id,
                subject_id="subj-1",
                created_by="user-1",
            )
            assert workspace.library_id == library_id

    def test_unknown_library_rejected(self) -> None:
        # O10 violates the ^O0[4-9]$ pattern (rejected at pydantic level).
        with pytest.raises(ValueError):
            OpportunityWorkspace(
                workspace_id=WS_ID,
                tenant_id=TENANT,
                library_id="O10",
                subject_id="subj-1",
                created_by="user-1",
            )


class TestTemporalMilestone:
    def test_permit_requires_evidence(self) -> None:
        with pytest.raises(ValueError, match="evidence_ref"):
            TemporalMilestone(
                milestone_id="ms-1",
                subject_id="proj-1",
                milestone_type="PERMIT_GRANTED",
                observed_at=date(2026, 3, 1),
            )

    def test_plain_milestone_ok(self) -> None:
        milestone = TemporalMilestone(
            milestone_id="ms-1",
            subject_id="proj-1",
            milestone_type="STAGE_CHANGED",
            observed_at=date(2026, 3, 1),
        )
        assert milestone.milestone_type == "STAGE_CHANGED"


class TestO04Infrastructure:
    def test_execution_requires_promoters(self) -> None:
        with pytest.raises(ValueError, match="promoters"):
            InfrastructureProject(
                project_id="proj-1",
                title="Highway E-5",
                jurisdiction_id="ES",
                stage="EXECUTION",
            )

    def test_planning_ok(self) -> None:
        project = InfrastructureProject(
            project_id="proj-1",
            title="Highway E-5",
            jurisdiction_id="ES",
        )
        assert project.stage == "PLANNING"


class TestO05Corporate:
    def test_short_registration_number_rejected(self) -> None:
        with pytest.raises(ValueError, match="registration_number"):
            CompanyRecord(
                company_id="co-1",
                legal_name="Acme S.A.",
                jurisdiction_id="ES",
                registration_number="AB",
            )

    def test_valid_company(self) -> None:
        company = CompanyRecord(
            company_id="co-1",
            legal_name="Acme S.A.",
            jurisdiction_id="ES",
            registration_number="A28015865",
        )
        assert company.registration_number == "A28015865"


class TestO06SovereignMacro:
    def test_revision_requires_code(self) -> None:
        with pytest.raises(ValueError, match="indicator_code"):
            MacroIndicator(
                indicator_id="ind-1",
                indicator_code="",
                jurisdiction_id="EU",
                value=2.5,
                reference_period="2026-Q2",
                is_revision=True,
            )

    def test_valid_indicator(self) -> None:
        indicator = MacroIndicator(
            indicator_id="ind-1",
            indicator_code="GDP",
            jurisdiction_id="EU",
            value=2.5,
            reference_period="2026-Q2",
        )
        assert indicator.value == 2.5

    def test_scenario_requires_assumptions(self) -> None:
        with pytest.raises(ValueError, match="assumptions"):
            ScenarioBoundary(scenario_id="scn-1", horizon="2030")

    def test_validated_scenario_requires_uncertainty(self) -> None:
        with pytest.raises(ValueError, match="uncertainty_note"):
            ScenarioBoundary(
                scenario_id="scn-1",
                horizon="2030",
                assumptions=["X"],
                status="VALIDATED",
            )

    def test_scenario_is_hypothesis_by_default(self) -> None:
        scenario = ScenarioBoundary(
            scenario_id="scn-1",
            horizon="2030",
            assumptions=["Fiscal policy stable"],
        )
        assert scenario.status == "HYPOTHESIS"


class TestO07TradeSupply:
    def test_intra_jurisdiction_rejected(self) -> None:
        with pytest.raises(ValueError, match="intra-jurisdiction"):
            TradeFlow(
                flow_id="flow-1",
                origin_jurisdiction="ES",
                destination_jurisdiction="ES",
                hs_code="8703",
                value_eur=100_000.0,
                period="2026-Q2",
            )

    def test_valid_flow(self) -> None:
        flow = TradeFlow(
            flow_id="flow-1",
            origin_jurisdiction="ES",
            destination_jurisdiction="DE",
            hs_code="8703",
            value_eur=100_000.0,
            period="2026-Q2",
        )
        assert flow.value_eur == 100_000.0

    def test_embargo_requires_evidence(self) -> None:
        with pytest.raises(ValueError, match="evidence_ref"):
            TariffRestriction(
                tariff_id="tar-1",
                hs_code="8703",
                kind="EMBARGO",
                effective_at=date(2026, 1, 1),
            )

    def test_valid_tariff(self) -> None:
        tariff = TariffRestriction(
            tariff_id="tar-1",
            hs_code="8703",
            kind="TARIFF",
            effective_at=date(2026, 1, 1),
        )
        assert tariff.kind == "TARIFF"


class TestO08EnergyClimate:
    def test_operational_requires_capacity(self) -> None:
        with pytest.raises(ValueError, match="capacity"):
            EnergyAsset(
                asset_id="ast-1",
                asset_type="WIND",
                capacity_mw=0.0,
                jurisdiction_id="ES",
                status="OPERATIONAL",
            )

    def test_planned_asset_ok(self) -> None:
        asset = EnergyAsset(
            asset_id="ast-1",
            asset_type="SOLAR",
            capacity_mw=50.0,
            jurisdiction_id="ES",
        )
        assert asset.status == "PLANNED"

    def test_climate_obligation_requires_source(self) -> None:
        with pytest.raises(ValueError, match="source_ref"):
            ClimateObligation(
                obligation_id="obl-1",
                jurisdiction_id="EU",
                target_year=2030,
                reduction_target_pct=55.0,
            )

    def test_valid_climate_obligation(self) -> None:
        obligation = ClimateObligation(
            obligation_id="obl-1",
            jurisdiction_id="EU",
            target_year=2030,
            reduction_target_pct=55.0,
            source_ref="src_ec_climate_law",
        )
        assert obligation.reduction_target_pct == 55.0


class TestO09InnovationIP:
    def test_granted_requires_assignees(self) -> None:
        with pytest.raises(ValueError, match="assignees"):
            PatentRecord(
                patent_id="pat-1",
                legal_status="GRANTED",
                status_observed_at=date(2026, 1, 1),
            )

    def test_applied_ok(self) -> None:
        patent = PatentRecord(
            patent_id="pat-1",
            status_observed_at=date(2026, 1, 1),
        )
        assert patent.legal_status == "APPLIED"

    def test_closed_requires_legal_disclosure(self) -> None:
        with pytest.raises(ValueError, match="legal-limit"):
            InnovationWorkspace(
                workspace_id=WS_ID,
                tenant_id=TENANT,
                patent_family_id="fam-1",
                state="CLOSED",
                created_by="user-1",
            )

    def test_assessing_ok(self) -> None:
        workspace = InnovationWorkspace(
            workspace_id=WS_ID,
            tenant_id=TENANT,
            patent_family_id="fam-1",
            created_by="user-1",
        )
        assert workspace.state == "ASSESSING"
        assert workspace.legal_limits_disclosed is False
