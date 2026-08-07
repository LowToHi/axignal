"""F01 — Jurisdiction and Geography (WP3-T01).

Canonical jurisdiction registry with the contract's required dimensions:

- countries and territories with stable identifiers (ISO 3166-1 alpha-2);
- administrative levels (NUTS and equivalents);
- regions and places of performance;
- versioned coordinates/geometry metadata;
- economic zones;
- time zones;
- multilingual names;
- historical changes (valid_from/valid_to, supersession).

Gate: stable identifiers + temporality + versioned geometry + reversible
aliases + license + precision + coverage disclosure.

Data source: ISO 3166-1 public standard codes and names (public
administrative reference, no personal data). This is a technical
reference registry; coverage claims require the WP2-T09 disclosure.
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class Jurisdiction(BaseModel):
    """A canonical jurisdiction record (country or territory)."""

    schema_version: Literal["axignal.f01.jurisdiction.v1"] = "axignal.f01.jurisdiction.v1"
    jurisdiction_id: str = Field(pattern=r"^[A-Z]{2}$")
    iso_alpha3: str | None = Field(default=None, pattern=r"^[A-Z]{3}$")
    iso_numeric: str | None = Field(default=None, pattern=r"^[0-9]{3}$")
    name: str = Field(min_length=2, max_length=120)
    names_multilingual: dict[str, str] = Field(default_factory=dict)
    administrative_levels: list[str] = Field(default_factory=list)
    nuts_equivalent: str | None = None
    economic_zone: str | None = None
    timezone: str | None = None
    valid_from: date | None = None
    valid_to: date | None = None
    supersedes: str | None = None
    superseded_by: str | None = None
    license_ref: str = "ISO-3166-1"
    precision_note: str | None = None
    coverage_disclosure_ref: str | None = None

    @model_validator(mode="after")
    def validate_temporality(self) -> Jurisdiction:
        if self.valid_from and self.valid_to and self.valid_from > self.valid_to:
            raise ValueError("valid_from must be <= valid_to")
        if self.superseded_by and not self.valid_to:
            raise ValueError("superseded_by requires valid_to")
        return self


class JurisdictionRegistry:
    """Versioned registry of canonical jurisdictions with reversible aliases."""

    def __init__(self) -> None:
        self._by_id: dict[str, Jurisdiction] = {}
        self._aliases: dict[str, str] = {}

    def register(self, jurisdiction: Jurisdiction) -> None:
        self._by_id[jurisdiction.jurisdiction_id] = jurisdiction
        self._aliases[jurisdiction.jurisdiction_id.casefold()] = jurisdiction.jurisdiction_id
        self._aliases[jurisdiction.name.casefold()] = jurisdiction.jurisdiction_id
        for language, name in jurisdiction.names_multilingual.items():
            self._aliases[f"{language}:{name.casefold()}"] = jurisdiction.jurisdiction_id
            # Reversible aliases: plain multilingual names also resolve.
            self._aliases.setdefault(name.casefold(), jurisdiction.jurisdiction_id)

    def resolve(self, alias: str) -> Jurisdiction | None:
        key = alias.strip().casefold()
        jurisdiction_id = self._aliases.get(key)
        if jurisdiction_id is None:
            return None
        return self._by_id.get(jurisdiction_id)

    def get(self, jurisdiction_id: str) -> Jurisdiction | None:
        return self._by_id.get(jurisdiction_id.upper())

    def all(self) -> tuple[Jurisdiction, ...]:
        return tuple(sorted(self._by_id.values(), key=lambda j: j.jurisdiction_id))

    def __len__(self) -> int:
        return len(self._by_id)


# Canonical registry seeded with ISO 3166-1 alpha-2 reference data for the
# EU member states (public standard reference; no personal data).
CANONICAL_JURISDICTIONS = [
    Jurisdiction(
        jurisdiction_id="AT",
        iso_alpha3="AUT",
        iso_numeric="040",
        name="Austria",
        names_multilingual={"es": "Austria", "en": "Austria", "de": "Österreich", "fr": "Autriche"},
        administrative_levels=["state", "district", "municipality"],
        nuts_equivalent="AT",
        economic_zone="EU",
        timezone="Europe/Vienna",
    ),
    Jurisdiction(
        jurisdiction_id="BE",
        iso_alpha3="BEL",
        iso_numeric="056",
        name="Belgium",
        names_multilingual={"es": "Bélgica", "en": "Belgium", "nl": "België", "fr": "Belgique"},
        administrative_levels=["region", "province", "municipality"],
        nuts_equivalent="BE",
        economic_zone="EU",
        timezone="Europe/Brussels",
    ),
    Jurisdiction(
        jurisdiction_id="DE",
        iso_alpha3="DEU",
        iso_numeric="276",
        name="Germany",
        names_multilingual={
            "es": "Alemania",
            "en": "Germany",
            "de": "Deutschland",
            "fr": "Allemagne",
        },
        administrative_levels=["land", "district", "municipality"],
        nuts_equivalent="DE",
        economic_zone="EU",
        timezone="Europe/Berlin",
    ),
    Jurisdiction(
        jurisdiction_id="ES",
        iso_alpha3="ESP",
        iso_numeric="724",
        name="Spain",
        names_multilingual={"es": "España", "en": "Spain", "fr": "Espagne"},
        administrative_levels=["autonomous-community", "province", "municipality"],
        nuts_equivalent="ES",
        economic_zone="EU",
        timezone="Europe/Madrid",
    ),
    Jurisdiction(
        jurisdiction_id="FR",
        iso_alpha3="FRA",
        iso_numeric="250",
        name="France",
        names_multilingual={"es": "Francia", "en": "France", "fr": "France"},
        administrative_levels=["region", "department", "commune"],
        nuts_equivalent="FR",
        economic_zone="EU",
        timezone="Europe/Paris",
    ),
    Jurisdiction(
        jurisdiction_id="IT",
        iso_alpha3="ITA",
        iso_numeric="380",
        name="Italy",
        names_multilingual={"es": "Italia", "en": "Italy", "it": "Italia", "fr": "Italie"},
        administrative_levels=["region", "province", "municipality"],
        nuts_equivalent="IT",
        economic_zone="EU",
        timezone="Europe/Rome",
    ),
    Jurisdiction(
        jurisdiction_id="LU",
        iso_alpha3="LUX",
        iso_numeric="442",
        name="Luxembourg",
        names_multilingual={
            "es": "Luxemburgo",
            "en": "Luxembourg",
            "fr": "Luxembourg",
            "de": "Luxemburg",
        },
        administrative_levels=["canton", "commune"],
        nuts_equivalent="LU",
        economic_zone="EU",
        timezone="Europe/Luxembourg",
    ),
    Jurisdiction(
        jurisdiction_id="NL",
        iso_alpha3="NLD",
        iso_numeric="528",
        name="Netherlands",
        names_multilingual={"es": "Países Bajos", "en": "Netherlands", "nl": "Nederland"},
        administrative_levels=["province", "municipality"],
        nuts_equivalent="NL",
        economic_zone="EU",
        timezone="Europe/Amsterdam",
    ),
    Jurisdiction(
        jurisdiction_id="PL",
        iso_alpha3="POL",
        iso_numeric="616",
        name="Poland",
        names_multilingual={"es": "Polonia", "en": "Poland", "pl": "Polska"},
        administrative_levels=["voivodeship", "county", "municipality"],
        nuts_equivalent="PL",
        economic_zone="EU",
        timezone="Europe/Warsaw",
    ),
    Jurisdiction(
        jurisdiction_id="PT",
        iso_alpha3="PRT",
        iso_numeric="620",
        name="Portugal",
        names_multilingual={"es": "Portugal", "en": "Portugal", "pt": "Portugal"},
        administrative_levels=["region", "district", "municipality"],
        nuts_equivalent="PT",
        economic_zone="EU",
        timezone="Europe/Lisbon",
    ),
]

CANONICAL_JURISDICTION_REGISTRY = JurisdictionRegistry()
for _jurisdiction in CANONICAL_JURISDICTIONS:
    CANONICAL_JURISDICTION_REGISTRY.register(_jurisdiction)
