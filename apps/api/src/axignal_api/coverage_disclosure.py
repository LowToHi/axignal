"""Coverage disclosure — WP2-T09.

A CoverageDisclosure is the machine-readable, versioned declaration of
what a source/library actually covers, with explicit limits. It exists so
that no claim of "global" or "total" coverage can be made without a
disclosure backing it (contract 2.3, 2.5, 18.22, 18.24 and Anexo E).

Rules:
- coverage claims are bounded: countries, languages, sectors, time
  depth, update cadence and source scope;
- "global" is a multijurisdictional architecture descriptor, never a
  demonstrated-total-coverage claim;
- any quantitative/comparative/coverage claim must link evidence_refs
  and an expiry date;
- a coverage change can suspend the disclosure automatically.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class CoverageDisclosure(BaseModel):
    """Declared coverage and limits of a source or library."""

    schema_version: Literal["axignal.coverage-disclosure.v1"] = "axignal.coverage-disclosure.v1"
    scope_type: Literal["SOURCE", "LIBRARY"]
    scope_id: str = Field(min_length=2, max_length=120)
    countries: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    sectors: list[str] = Field(default_factory=list)
    time_depth_from: date | None = None
    time_depth_to: date | None = None
    update_cadence: Literal[
        "REALTIME", "DAILY", "WEEKLY", "MONTHLY", "QUARTERLY", "YEARLY", "STATIC"
    ] = "STATIC"
    source_scope: str | None = None
    completeness_note: str | None = None
    claims_global_coverage: Literal[False] = False
    evidence_refs: list[str] = Field(default_factory=list)
    expires_at: datetime | None = None
    disclosure_status: Literal["ACTIVE", "SUSPENDED", "SUPERSEDED"] = "ACTIVE"
    exact_head: str | None = None

    @model_validator(mode="after")
    def validate_disclosure_rules(self) -> CoverageDisclosure:
        if (
            self.time_depth_from
            and self.time_depth_to
            and self.time_depth_from > self.time_depth_to
        ):
            raise ValueError("time_depth_from must be <= time_depth_to")
        if self.claims_global_coverage:
            raise ValueError(
                "claims_global_coverage must always be false; 'global' describes "
                "architecture, not demonstrated total coverage"
            )
        if self.disclosure_status != "ACTIVE":
            return self
        if self.countries or self.languages or self.sectors:
            if not self.evidence_refs:
                raise ValueError(
                    "active coverage declarations require evidence_refs"
                )
            if self.expires_at is None:
                raise ValueError(
                    "active coverage declarations require expires_at"
                )
        return self


def library_coverage_disclosure(
    *,
    library_id: str,
    countries: list[str],
    languages: list[str],
    sectors: list[str],
    evidence_refs: list[str],
    expires_at: datetime,
) -> CoverageDisclosure:
    """Build an ACTIVE library coverage disclosure with bounded claims."""
    return CoverageDisclosure(
        scope_type="LIBRARY",
        scope_id=library_id,
        countries=countries,
        languages=languages,
        sectors=sectors,
        evidence_refs=evidence_refs,
        expires_at=expires_at,
        disclosure_status="ACTIVE",
    )
