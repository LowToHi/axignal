"""WP3-T01 — F01 Geography jurisdiction registry tests."""

from __future__ import annotations

import pytest

from axignal_api.foundations.f01_geography import (
    CANONICAL_JURISDICTION_REGISTRY,
    Jurisdiction,
    JurisdictionRegistry,
)


class TestJurisdictionModel:
    def test_stable_identifiers(self) -> None:
        jurisdiction = Jurisdiction(
            jurisdiction_id="ES",
            iso_alpha3="ESP",
            iso_numeric="724",
            name="Spain",
        )
        assert jurisdiction.jurisdiction_id == "ES"
        assert jurisdiction.license_ref == "ISO-3166-1"

    def test_multilingual_names(self) -> None:
        jurisdiction = Jurisdiction(
            jurisdiction_id="DE",
            name="Germany",
            names_multilingual={"es": "Alemania", "de": "Deutschland"},
        )
        assert jurisdiction.names_multilingual["de"] == "Deutschland"

    def test_temporality_ordering(self) -> None:
        with pytest.raises(ValueError, match="valid_from"):
            Jurisdiction(
                jurisdiction_id="XX",
                name="Test",
                valid_from=__import__("datetime").date(2026, 1, 1),
                valid_to=__import__("datetime").date(2020, 1, 1),
            )

    def test_superseded_requires_valid_to(self) -> None:
        with pytest.raises(ValueError, match="superseded_by requires valid_to"):
            Jurisdiction(
                jurisdiction_id="XX",
                name="Test",
                superseded_by="YY",
            )

    def test_historical_change_supported(self) -> None:
        jurisdiction = Jurisdiction(
            jurisdiction_id="CS",
            name="Serbia and Montenegro",
            valid_from=__import__("datetime").date(2003, 2, 4),
            valid_to=__import__("datetime").date(2006, 6, 3),
            superseded_by="RS",
        )
        assert jurisdiction.superseded_by == "RS"

    def test_invalid_id_rejected(self) -> None:
        with pytest.raises(ValueError):
            Jurisdiction(jurisdiction_id="españa", name="Spain")


class TestJurisdictionRegistry:
    def test_canonical_registry_has_eu_reference_set(self) -> None:
        registry = CANONICAL_JURISDICTION_REGISTRY
        assert len(registry) >= 10
        assert registry.get("ES") is not None
        assert registry.get("LU") is not None

    def test_resolve_by_id(self) -> None:
        assert CANONICAL_JURISDICTION_REGISTRY.resolve("es").jurisdiction_id == "ES"
        assert CANONICAL_JURISDICTION_REGISTRY.resolve("DE").jurisdiction_id == "DE"

    def test_resolve_by_name(self) -> None:
        assert CANONICAL_JURISDICTION_REGISTRY.resolve("Spain").jurisdiction_id == "ES"
        assert CANONICAL_JURISDICTION_REGISTRY.resolve("España").jurisdiction_id == "ES"

    def test_resolve_by_multilingual_name(self) -> None:
        assert CANONICAL_JURISDICTION_REGISTRY.resolve("es:Alemania").jurisdiction_id == "DE"
        assert CANONICAL_JURISDICTION_REGISTRY.resolve("de:Österreich").jurisdiction_id == "AT"

    def test_resolve_unknown_returns_none(self) -> None:
        assert CANONICAL_JURISDICTION_REGISTRY.resolve("Atlantis") is None

    def test_reversible_aliases(self) -> None:
        # Reversibility: alias -> id -> same jurisdiction object.
        jurisdiction = CANONICAL_JURISDICTION_REGISTRY.resolve("Francia")
        assert jurisdiction is not None
        assert CANONICAL_JURISDICTION_REGISTRY.get(jurisdiction.jurisdiction_id) is jurisdiction

    def test_registry_accepts_custom_entries(self) -> None:
        registry = JurisdictionRegistry()
        registry.register(Jurisdiction(jurisdiction_id="AD", name="Andorra"))
        assert len(registry) == 1
        assert registry.resolve("andorra").jurisdiction_id == "AD"

    def test_economic_zone_and_timezone(self) -> None:
        es = CANONICAL_JURISDICTION_REGISTRY.get("ES")
        assert es.economic_zone == "EU"
        assert es.timezone == "Europe/Madrid"
        assert es.nuts_equivalent == "ES"

    def test_no_personal_data(self) -> None:
        for jurisdiction in CANONICAL_JURISDICTION_REGISTRY.all():
            assert jurisdiction.schema_version == "axignal.f01.jurisdiction.v1"
