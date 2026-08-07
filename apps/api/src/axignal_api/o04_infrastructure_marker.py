"""O04-O07 cross-library E2E markers (WP14-T12).

Minimal typed markers used by the mandatory cross-library journey; the
full domain models live in opportunity_libraries (O04/O07). These
markers exist only to keep the E2E self-contained and typed.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class InfrastructureProjectMarker(BaseModel):
    """O04 project marker for the cross-library E2E."""

    project_id: str = Field(min_length=3, max_length=120)
    title: str = Field(min_length=3, max_length=300)
    jurisdiction_id: str = Field(pattern=r"^[A-Z]{2}$|^EU$")
    stage: str = Field(pattern=r"^(PLANNING|TENDERING|EXECUTION|OPERATION|CANCELLED)$")
    budget_eur: float = Field(ge=0.0)

    @model_validator(mode="after")
    def validate_marker(self) -> InfrastructureProjectMarker:
        if self.stage == "EXECUTION" and self.budget_eur <= 0:
            raise ValueError("EXECUTION projects require a positive budget")
        return self


class TradeDependencyMarker(BaseModel):
    """O07 trade dependency marker for the cross-library E2E."""

    dependency_id: str = Field(min_length=3, max_length=120)
    origin_jurisdiction: str = Field(pattern=r"^[A-Z]{2}$")
    destination_jurisdiction: str = Field(pattern=r"^[A-Z]{2}$")
    commodity: str = Field(min_length=2, max_length=80)
    critical: bool = False

    @model_validator(mode="after")
    def validate_marker(self) -> TradeDependencyMarker:
        if self.origin_jurisdiction == self.destination_jurisdiction:
            raise ValueError("dependency must be cross-jurisdiction")
        if self.critical and not self.commodity:
            raise ValueError("critical dependencies require a commodity")
        return self
