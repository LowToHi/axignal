"""WP3-T05 — F05 Languages tests."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from axignal_api.foundations.f05_languages import (
    PRODUCT_LANGUAGES,
    GlossaryTerm,
    TranslatedText,
)


class TestTranslatedText:
    def test_original_preserved(self) -> None:
        text = TranslatedText(original_text="Licitación pública")
        assert text.original_text == "Licitación pública"
        assert text.effective_text("en") == "Licitación pública"

    def test_product_languages_exact(self) -> None:
        assert PRODUCT_LANGUAGES == ("en", "es", "fr", "de", "pt", "it")

    def test_translation_requires_provenance_and_confidence(self) -> None:
        with pytest.raises(ValueError, match="translation_provenance"):
            TranslatedText(
                original_text="Hola",
                translations={"en": "Hello"},
                translation_confidence={"en": 0.9},
            )
        with pytest.raises(ValueError, match="translation_confidence"):
            TranslatedText(
                original_text="Hola",
                translations={"en": "Hello"},
                translation_provenance={"en": "src-model-1"},
            )

    def test_valid_translation(self) -> None:
        text = TranslatedText(
            original_text="Licitación pública",
            translations={"en": "Public tender"},
            translation_provenance={"en": "src-translator-1"},
            translation_confidence={"en": 0.95},
            source_id="src_es_boe",
        )
        assert text.effective_text("en") == "Public tender"

    def test_unknown_language_rejected(self) -> None:
        with pytest.raises(ValueError, match="product vocabulary"):
            TranslatedText(
                original_text="Hola",
                translations={"xx": "Hello"},
                translation_provenance={"xx": "src"},
                translation_confidence={"xx": 0.9},
            )

    def test_confidence_bounds(self) -> None:
        with pytest.raises(ValueError, match="confidence"):
            TranslatedText(
                original_text="Hola",
                translations={"en": "Hello"},
                translation_provenance={"en": "src"},
                translation_confidence={"en": 1.5},
            )

    def test_human_override_precedence(self) -> None:
        text = TranslatedText(
            original_text="Contrato",
            translations={"fr": "Contrat (machine)"},
            translation_provenance={"fr": "src-model-1"},
            translation_confidence={"fr": 0.8},
            human_overrides={"fr": "Marché public (reviewed)"},
        )
        assert text.effective_text("fr") == "Marché public (reviewed)"
        # Machine rendering is preserved, not erased.
        assert text.translations["fr"] == "Contrat (machine)"

    def test_human_override_requires_machine_rendering(self) -> None:
        with pytest.raises(ValueError, match="machine rendering"):
            TranslatedText(
                original_text="Contrato",
                human_overrides={"fr": "Marché"},
            )

    def test_transliteration_used_when_no_translation(self) -> None:
        text = TranslatedText(
            original_text="Договор",
            transliterations={"en": "Dogovor"},
        )
        assert text.effective_text("en") == "Dogovor"

    def test_translation_never_replaces_original(self) -> None:
        text = TranslatedText(
            original_text="Documento original",
            translations={"en": "Original document"},
            translation_provenance={"en": "src"},
            translation_confidence={"en": 0.99},
        )
        # The original remains authoritative evidence.
        assert text.original_text == "Documento original"
        assert text.original_text != text.translations["en"]


class TestGlossaryTerm:
    def test_valid_term(self) -> None:
        term = GlossaryTerm(
            glossary_id="procurement-es",
            term="Licitación",
            language="es",
            equivalents={"en": "Tender", "fr": "Appel d'offres"},
            source_id="src_es_boe",
        )
        assert term.human_approved is False

    def test_unknown_language_rejected(self) -> None:
        with pytest.raises(ValueError, match="product vocabulary"):
            GlossaryTerm(
                glossary_id="glo-1",
                term="Tender",
                language="en",
                equivalents={"xx": "Licitación"},
            )

    def test_empty_equivalent_rejected(self) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            GlossaryTerm(
                glossary_id="glo-1",
                term="Tender",
                language="en",
                equivalents={"es": "   "},
            )

    def test_human_approval_requires_actor_and_time(self) -> None:
        with pytest.raises(ValueError, match="approved_by"):
            GlossaryTerm(
                glossary_id="glo-1",
                term="Tender",
                language="en",
                human_approved=True,
            )

    def test_human_approval_complete(self) -> None:
        term = GlossaryTerm(
            glossary_id="glo-1",
            term="Tender",
            language="en",
            human_approved=True,
            approved_by="Rafael López",
            approved_at=datetime.now(UTC),
        )
        assert term.approved_by == "Rafael López"
