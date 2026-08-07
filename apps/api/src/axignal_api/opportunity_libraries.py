"""O04-O09 — Opportunity libraries (WP8-WP13).

Compact implementations of the remaining opportunity libraries, sharing a
common pattern (source admission -> domain ontology -> workspace ->
E2E) without duplicating machinery:

- O04 Infrastructure (WP8): project ontology, promoters/funders,
  stages/milestones, permits, packages/procurement links, Project
  Pursuit Workspace;
- O05 Corporate (WP9): company identifiers, filings, ownership,
  material events, capex/expansion signals, Account Opportunity
  Workspace;
- O06 Sovereign & Macro (WP10): indicators and revisions, budgets,
  policy priorities, country/sector context, scenario boundaries,
  Country & Market Strategy Workspace;
- O07 Trade & Supply (WP11): trade classifications, flows,
  tariffs/restrictions, routes/capacity, dependencies, Supply
  Opportunity Workspace;
- O08 Energy & Climate (WP12): assets/capacity, permits/auctions,
  transition plans, climate obligations, projects/finance, Transition
  Opportunity Workspace;
- O09 Innovation & IP (WP13): patents/families, legal status temporal,
  assignees, R&D projects, research organisations, Innovation
  Opportunity Workspace, legal-limit disclosures.

All source admissions are DISCOVERED with commercial use pending human
decision; no library is declared complete on fixtures.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


def source_admission(library_id: str, source_id: str) -> dict[str, str]:
    """Canonical source admission contract shape for O04-O09."""
    return {
        "source_id": source_id,
        "library_id": library_id,
        "source_type": "INSTITUTIONAL_API",
        "state": "DISCOVERED",
        "commercial_use": "PENDING_HUMAN_DECISION",
        "product_shell": "AXIGNAL_OPPORTUNITY_INTELLIGENCE",
    }


# --- Shared building blocks -------------------------------------------------


class TemporalMilestone(BaseModel):
    """A typed milestone with observation time."""

    schema_version: Literal["axignal.lib.milestone.v1"] = "axignal.lib.milestone.v1"
    milestone_id: str = Field(min_length=3, max_length=120)
    subject_id: str
    milestone_type: str = Field(min_length=2, max_length=80)
    observed_at: date
    evidence_ref: str | None = None

    @model_validator(mode="after")
    def validate_milestone(self) -> TemporalMilestone:
        if (
            self.milestone_type in ("PERMIT_GRANTED", "FILING_FILED", "PATENT_GRANTED")
            and not self.evidence_ref
        ):
            raise ValueError(
                f"{self.milestone_type} milestones require evidence_ref"
            )
        return self


class OpportunityWorkspace(BaseModel):
    """Shared tenant-scoped workspace for O04-O09 libraries."""

    schema_version: Literal["axignal.lib.workspace.v1"] = "axignal.lib.workspace.v1"
    workspace_id: UUID
    tenant_id: UUID
    library_id: str = Field(pattern=r"^O0[4-9]$")
    subject_id: str
    state: Literal["ASSESSING", "ACTIVE", "CLOSED", "WITHDRAWN"] = "ASSESSING"
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def validate_workspace(self) -> OpportunityWorkspace:
        if self.library_id not in ("O04", "O05", "O06", "O07", "O08", "O09"):
            raise ValueError(f"unknown library {self.library_id!r}")
        return self


# --- O04 Infrastructure -----------------------------------------------------


class InfrastructureProject(BaseModel):
    """A public infrastructure project."""

    schema_version: Literal["axignal.o04.project.v1"] = "axignal.o04.project.v1"
    project_id: str = Field(min_length=3, max_length=120)
    title: str = Field(min_length=3, max_length=300)
    jurisdiction_id: str = Field(pattern=r"^[A-Z]{2}$|^EU$")
    stage: Literal["PLANNING", "TENDERING", "EXECUTION", "OPERATION", "CANCELLED"] = "PLANNING"
    promoters: list[str] = Field(default_factory=list)
    estimated_value_eur: float | None = Field(default=None, ge=0.0)
    source_id: str = "src_eib_global_projects"

    @model_validator(mode="after")
    def validate_project(self) -> InfrastructureProject:
        if self.stage == "EXECUTION" and not self.promoters:
            raise ValueError("EXECUTION projects require promoters")
        return self


# --- O05 Corporate ----------------------------------------------------------


class CompanyRecord(BaseModel):
    """A corporate entity with filings and ownership signals."""

    schema_version: Literal["axignal.o05.company.v1"] = "axignal.o05.company.v1"
    company_id: str = Field(min_length=3, max_length=120)
    legal_name: str = Field(min_length=2, max_length=300)
    jurisdiction_id: str = Field(pattern=r"^[A-Z]{2}$")
    registration_number: str | None = None
    ownership_observed_at: date | None = None
    source_id: str = "src_official_business_registers"

    @model_validator(mode="after")
    def validate_company(self) -> CompanyRecord:
        if self.registration_number and len(self.registration_number) < 4:
            raise ValueError("registration_number must be at least 4 characters")
        return self


# --- O06 Sovereign & Macro --------------------------------------------------


class MacroIndicator(BaseModel):
    """A macro indicator with revision awareness."""

    schema_version: Literal["axignal.o06.indicator.v1"] = "axignal.o06.indicator.v1"
    indicator_id: str = Field(min_length=3, max_length=120)
    indicator_code: str = Field(min_length=2, max_length=40)
    jurisdiction_id: str = Field(pattern=r"^[A-Z]{2}$|^EU$")
    value: float
    reference_period: str = Field(min_length=4, max_length=20)
    is_revision: bool = False
    source_id: str = "src_eurostat"

    @model_validator(mode="after")
    def validate_indicator(self) -> MacroIndicator:
        if self.is_revision and not self.indicator_code:
            raise ValueError("revision requires indicator_code")
        return self


class ScenarioBoundary(BaseModel):
    """A scenario boundary: assumptions and uncertainty, never a fact."""

    schema_version: Literal["axignal.o06.scenario.v1"] = "axignal.o06.scenario.v1"
    scenario_id: str = Field(min_length=3, max_length=120)
    horizon: str = Field(min_length=3, max_length=40)
    assumptions: list[str] = Field(default_factory=list)
    uncertainty_note: str | None = None
    status: Literal["HYPOTHESIS", "VALIDATED", "SUPERSEDED"] = "HYPOTHESIS"

    @model_validator(mode="after")
    def validate_scenario(self) -> ScenarioBoundary:
        if not self.assumptions:
            raise ValueError("scenario requires explicit assumptions")
        if self.status == "VALIDATED" and not self.uncertainty_note:
            raise ValueError("VALIDATED scenarios require uncertainty_note")
        return self


# --- O07 Trade & Supply -----------------------------------------------------


class TradeFlow(BaseModel):
    """A trade flow with classification."""

    schema_version: Literal["axignal.o07.flow.v1"] = "axignal.o07.flow.v1"
    flow_id: str = Field(min_length=3, max_length=120)
    origin_jurisdiction: str = Field(pattern=r"^[A-Z]{2}$")
    destination_jurisdiction: str = Field(pattern=r"^[A-Z]{2}$")
    hs_code: str = Field(min_length=2, max_length=20)
    value_eur: float = Field(ge=0.0)
    period: str = Field(min_length=4, max_length=20)
    source_id: str = "src_eurostat_comtrade"

    @model_validator(mode="after")
    def validate_flow(self) -> TradeFlow:
        if self.origin_jurisdiction == self.destination_jurisdiction:
            raise ValueError("trade flow cannot be intra-jurisdiction only")
        return self


class TariffRestriction(BaseModel):
    """A tariff or restriction with evidence."""

    schema_version: Literal["axignal.o07.tariff.v1"] = "axignal.o07.tariff.v1"
    tariff_id: str = Field(min_length=3, max_length=120)
    hs_code: str = Field(min_length=2, max_length=20)
    kind: Literal["TARIFF", "QUOTA", "EMBARGO", "LICENSE"]
    effective_at: date
    evidence_ref: str | None = None

    @model_validator(mode="after")
    def validate_tariff(self) -> TariffRestriction:
        if self.kind == "EMBARGO" and not self.evidence_ref:
            raise ValueError("EMBARGO restrictions require evidence_ref")
        return self


# --- O08 Energy & Climate ---------------------------------------------------


class EnergyAsset(BaseModel):
    """An energy asset with capacity."""

    schema_version: Literal["axignal.o08.asset.v1"] = "axignal.o08.asset.v1"
    asset_id: str = Field(min_length=3, max_length=120)
    asset_type: Literal["WIND", "SOLAR", "HYDRO", "STORAGE", "GRID", "NUCLEAR", "GAS", "HYDROGEN"]
    capacity_mw: float = Field(ge=0.0)
    jurisdiction_id: str = Field(pattern=r"^[A-Z]{2}$|^EU$")
    status: Literal["PLANNED", "UNDER_CONSTRUCTION", "OPERATIONAL", "DECOMMISSIONED"] = "PLANNED"
    source_id: str = "src_entsoe"

    @model_validator(mode="after")
    def validate_asset(self) -> EnergyAsset:
        if self.status == "OPERATIONAL" and self.capacity_mw <= 0:
            raise ValueError("OPERATIONAL assets require positive capacity")
        return self


class ClimateObligation(BaseModel):
    """A climate obligation with target year."""

    schema_version: Literal["axignal.o08.climate.v1"] = "axignal.o08.climate.v1"
    obligation_id: str = Field(min_length=3, max_length=120)
    jurisdiction_id: str = Field(pattern=r"^[A-Z]{2}$|^EU$")
    target_year: int = Field(ge=2020, le=2100)
    reduction_target_pct: float = Field(ge=0.0, le=100.0)
    source_ref: str | None = None

    @model_validator(mode="after")
    def validate_obligation(self) -> ClimateObligation:
        if not self.source_ref:
            raise ValueError("climate obligations require source_ref")
        return self


# --- O09 Innovation & IP ----------------------------------------------------


class PatentRecord(BaseModel):
    """A patent with temporal legal status."""

    schema_version: Literal["axignal.o09.patent.v1"] = "axignal.o09.patent.v1"
    patent_id: str = Field(min_length=3, max_length=120)
    family_id: str | None = None
    legal_status: Literal["APPLIED", "GRANTED", "LAPSED", "REVOKED", "EXPIRED"] = "APPLIED"
    status_observed_at: date
    assignees: list[str] = Field(default_factory=list)
    source_id: str = "src_epo_ops"

    @model_validator(mode="after")
    def validate_patent(self) -> PatentRecord:
        if self.legal_status in ("GRANTED", "REVOKED") and not self.assignees:
            raise ValueError("GRANTED/REVOKED patents require assignees")
        return self


class InnovationWorkspace(BaseModel):
    """An innovation opportunity workspace with legal-limit disclosures."""

    schema_version: Literal["axignal.o09.workspace.v1"] = "axignal.o09.workspace.v1"
    workspace_id: UUID
    tenant_id: UUID
    patent_family_id: str
    state: Literal["ASSESSING", "ACTIVE", "CLOSED"] = "ASSESSING"
    legal_limits_disclosed: bool = False
    created_by: str

    @model_validator(mode="after")
    def validate_workspace(self) -> InnovationWorkspace:
        if self.state == "CLOSED" and not self.legal_limits_disclosed:
            raise ValueError("CLOSED innovation workspaces require legal-limit disclosures")
        return self
