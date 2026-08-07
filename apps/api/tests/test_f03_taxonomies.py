"""WP3-T03 — F03 Taxonomies tests."""

from __future__ import annotations

import pytest

from axignal_api.foundations.f03_taxonomies import (
    CANONICAL_TAXONOMIES,
    TaxonomyCode,
    TaxonomyCrosswalk,
    TaxonomyRegistry,
)


class TestTaxonomyCode:
    def test_valid_cpv_code(self) -> None:
        code = TaxonomyCode(
            taxonomy="CPV",
            code="45233100",
            label="Construction work for highways, roads",
            parent_code="45230000",
        )
        assert code.qualified_id == "CPV:45233100"

    def test_valid_nuts_code(self) -> None:
        code = TaxonomyCode(taxonomy="NUTS", code="ES30", label="Comunidad de Madrid")
        assert code.qualified_id == "NUTS:ES30"

    def test_unknown_taxonomy_rejected(self) -> None:
        with pytest.raises(ValueError, match="taxonomy must be one of"):
            TaxonomyCode(taxonomy="MADEUP", code="1", label="x")

    def test_canonical_taxonomies_exact(self) -> None:
        assert CANONICAL_TAXONOMIES == (
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

    def test_temporality(self) -> None:
        with pytest.raises(ValueError, match="valid_from"):
            TaxonomyCode(
                taxonomy="NACE",
                code="A",
                label="x",
                valid_from=__import__("datetime").date(2026, 1, 1),
                valid_to=__import__("datetime").date(2020, 1, 1),
            )

    def test_versioned_code_supersession(self) -> None:
        old = TaxonomyCode(
            taxonomy="NACE",
            code="55.1",
            label="Hotels",
            valid_to=__import__("datetime").date(2024, 12, 31),
        )
        new = TaxonomyCode(
            taxonomy="NACE",
            code="55.10",
            label="Hotels and similar accommodation",
            valid_from=__import__("datetime").date(2025, 1, 1),
        )
        assert old.qualified_id != new.qualified_id
        assert new.code.startswith(old.code)


class TestTaxonomyCrosswalk:
    def test_proposed_crosswalk_default(self) -> None:
        crosswalk = TaxonomyCrosswalk(
            crosswalk_id="cw-1",
            from_taxonomy="NACE",
            from_code="62.0",
            to_taxonomy="ISIC",
            to_code="62",
        )
        assert crosswalk.status == "PROPOSED"
        # Proposed != canonical equivalence.
        assert crosswalk.status != "CANONICAL_EQUIVALENCE"

    def test_crosswalk_cannot_map_to_itself(self) -> None:
        with pytest.raises(ValueError, match="itself"):
            TaxonomyCrosswalk(
                crosswalk_id="cw-2",
                from_taxonomy="NACE",
                from_code="62.0",
                to_taxonomy="NACE",
                to_code="62.0",
            )

    def test_validated_requires_evidence(self) -> None:
        with pytest.raises(ValueError, match="evidence_ref"):
            TaxonomyCrosswalk(
                crosswalk_id="cw-3",
                from_taxonomy="NACE",
                from_code="62.0",
                to_taxonomy="ISIC",
                to_code="62",
                status="VALIDATED",
            )

    def test_canonical_equivalence_requires_full_confidence(self) -> None:
        with pytest.raises(ValueError, match="confidence=1.0"):
            TaxonomyCrosswalk(
                crosswalk_id="cw-4",
                from_taxonomy="NACE",
                from_code="62.0",
                to_taxonomy="ISIC",
                to_code="62",
                status="CANONICAL_EQUIVALENCE",
                confidence=0.9,
                evidence_ref="evidence-1",
            )

    def test_canonical_equivalence_ok_with_evidence(self) -> None:
        crosswalk = TaxonomyCrosswalk(
            crosswalk_id="cw-5",
            from_taxonomy="NACE",
            from_code="62.0",
            to_taxonomy="ISIC",
            to_code="62",
            status="CANONICAL_EQUIVALENCE",
            confidence=1.0,
            evidence_ref="evidence-1",
        )
        assert crosswalk.status == "CANONICAL_EQUIVALENCE"


class TestTaxonomyRegistry:
    def test_register_and_lookup_codes(self) -> None:
        registry = TaxonomyRegistry()
        registry.register_code(
            TaxonomyCode(taxonomy="CPV", code="45233100", label="Roads")
        )
        assert registry.get_code("CPV", "45233100") is not None
        assert registry.get_code("CPV", "999") is None

    def test_proposed_vs_canonical_separated(self) -> None:
        registry = TaxonomyRegistry()
        registry.register_crosswalk(
            TaxonomyCrosswalk(
                crosswalk_id="cw-proposed",
                from_taxonomy="NACE",
                from_code="62.0",
                to_taxonomy="ISIC",
                to_code="62",
            )
        )
        registry.register_crosswalk(
            TaxonomyCrosswalk(
                crosswalk_id="cw-canonical",
                from_taxonomy="HS",
                from_code="0101",
                to_taxonomy="SITC",
                to_code="0011",
                status="CANONICAL_EQUIVALENCE",
                confidence=1.0,
                evidence_ref="evidence-2",
            )
        )
        assert len(registry.proposed_crosswalks()) == 1
        assert len(registry.canonical_equivalences()) == 1
