"""F03 — Taxonomies and Classifications (WP3-T03).

Canonical taxonomy model per contract F03:

- supported taxonomies: CPV, NUTS, NACE/ISIC, NAICS/PSC, HS/SITC/CPC,
  COFOG, energy/climate, patents, national classifications;
- codes are versioned and scoped to their taxonomy;
- crosswalks are PROPOSED mappings and never equal canonical equivalence:
  a proposed crosswalk must be validated before it can become canonical;
- canonical equivalence is a separate, audited status.

Rule: crosswalk proposed != canonical equivalence.
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, model_validator

CANONICAL_TAXONOMIES = (
    "CPV",
    "NUTS",
    "NACE",
    "ISIC",
    "NAICS",
    "PSC",
    "HS",
    "SITC",
    "CPC",
    "COFOG",
    "ENERGY_CLIMATE",
    "PATENTS",
    "NATIONAL",
)


class TaxonomyCode(BaseModel):
    """A single versioned code within a taxonomy."""

    schema_version: Literal["axignal.f03.code.v1"] = "axignal.f03.code.v1"
    taxonomy: str = Field(min_length=2, max_length=40)
    code: str = Field(min_length=1, max_length=60)
    label: str = Field(min_length=1, max_length=300)
    label_language: str | None = None
    parent_code: str | None = None
    valid_from: date | None = None
    valid_to: date | None = None
    source_id: str | None = None

    @model_validator(mode="after")
    def validate_code(self) -> TaxonomyCode:
        if self.taxonomy not in CANONICAL_TAXONOMIES:
            raise ValueError(
                f"taxonomy must be one of {CANONICAL_TAXONOMIES}; got {self.taxonomy!r}"
            )
        if self.valid_from and self.valid_to and self.valid_from > self.valid_to:
            raise ValueError("valid_from must be <= valid_to")
        return self

    @property
    def qualified_id(self) -> str:
        return f"{self.taxonomy}:{self.code}"


class TaxonomyCrosswalk(BaseModel):
    """A proposed or canonical mapping between two taxonomy codes."""

    schema_version: Literal["axignal.f03.crosswalk.v1"] = "axignal.f03.crosswalk.v1"
    crosswalk_id: str = Field(min_length=3, max_length=120)
    from_taxonomy: str
    from_code: str
    to_taxonomy: str
    to_code: str
    status: Literal["PROPOSED", "VALIDATED", "CANONICAL_EQUIVALENCE", "REJECTED"] = "PROPOSED"
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    evidence_ref: str | None = None
    proposed_at: date | None = None
    validated_at: date | None = None

    @model_validator(mode="after")
    def validate_crosswalk_rules(self) -> TaxonomyCrosswalk:
        if self.from_taxonomy == self.to_taxonomy and self.from_code == self.to_code:
            raise ValueError("a crosswalk cannot map a code to itself")
        if self.status in ("VALIDATED", "CANONICAL_EQUIVALENCE") and not self.evidence_ref:
            raise ValueError(
                "VALIDATED/CANONICAL_EQUIVALENCE crosswalks require evidence_ref"
            )
        if self.status == "CANONICAL_EQUIVALENCE" and self.confidence < 1.0:
            raise ValueError(
                "CANONICAL_EQUIVALENCE requires confidence=1.0 "
                "(proposed mappings are never canonical equivalence)"
            )
        return self


class TaxonomyRegistry:
    """Versioned taxonomy code and crosswalk registry."""

    def __init__(self) -> None:
        self._codes: dict[str, TaxonomyCode] = {}
        self._crosswalks: dict[str, TaxonomyCrosswalk] = {}

    def register_code(self, code: TaxonomyCode) -> None:
        self._codes[code.qualified_id] = code

    def register_crosswalk(self, crosswalk: TaxonomyCrosswalk) -> None:
        self._crosswalks[crosswalk.crosswalk_id] = crosswalk

    def get_code(self, taxonomy: str, code: str) -> TaxonomyCode | None:
        return self._codes.get(f"{taxonomy}:{code}")

    def get_crosswalk(self, crosswalk_id: str) -> TaxonomyCrosswalk | None:
        return self._crosswalks.get(crosswalk_id)

    def proposed_crosswalks(self) -> tuple[TaxonomyCrosswalk, ...]:
        return tuple(
            c for c in self._crosswalks.values() if c.status == "PROPOSED"
        )

    def canonical_equivalences(self) -> tuple[TaxonomyCrosswalk, ...]:
        return tuple(
            c
            for c in self._crosswalks.values()
            if c.status == "CANONICAL_EQUIVALENCE"
        )

    def __len__(self) -> int:
        return len(self._codes)
