"""F05 — Languages, Terminology and Translation (WP3-T05).

Canonical multilingual content model per contract F05:

Product minimum languages:
  English, Spanish, French, German, Portuguese, Italian.

Must preserve:
- original;
- detected language;
- translation;
- transliteration;
- glossaries;
- provenance;
- confidence;
- human override;
- semantic equivalence of critical actions.

Rule: translation never replaces the original evidence; every derived
text carries provenance, confidence and optional human override.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

PRODUCT_LANGUAGES = ("en", "es", "fr", "de", "pt", "it")


class TranslatedText(BaseModel):
    """A text with its original, language and derived renderings."""

    schema_version: Literal["axignal.f05.text.v1"] = "axignal.f05.text.v1"
    original_text: str = Field(min_length=1, max_length=100_000)
    detected_language: str | None = Field(default=None, pattern=r"^[a-z]{2,3}$")
    translations: dict[str, str] = Field(default_factory=dict)
    transliterations: dict[str, str] = Field(default_factory=dict)
    glossary_ref: str | None = None
    translation_provenance: dict[str, str] = Field(default_factory=dict)
    translation_confidence: dict[str, float] = Field(default_factory=dict)
    human_overrides: dict[str, str] = Field(default_factory=dict)
    source_id: str | None = None
    translated_at: datetime | None = None

    @model_validator(mode="after")
    def validate_text_rules(self) -> TranslatedText:
        # Language codes must be in the product vocabulary.
        for language in (*self.translations, *self.transliterations, *self.human_overrides):
            if language not in PRODUCT_LANGUAGES:
                raise ValueError(
                    f"language {language!r} not in product vocabulary {PRODUCT_LANGUAGES}"
                )
        # Translations require confidence and provenance entries.
        for language in self.translations:
            if language not in self.translation_provenance:
                raise ValueError(
                    f"translation {language!r} requires translation_provenance"
                )
            if language not in self.translation_confidence:
                raise ValueError(
                    f"translation {language!r} requires translation_confidence"
                )
            confidence = self.translation_confidence[language]
            if confidence < 0.0 or confidence > 1.0:
                raise ValueError(f"confidence for {language!r} must be in [0, 1]")
        # Human overrides replace but do not erase the machine translation.
        for language in self.human_overrides:
            if language not in self.translations and language not in self.transliterations:
                raise ValueError(
                    f"human override {language!r} must have a machine rendering to override"
                )
        return self

    def effective_text(self, language: str) -> str:
        """Human override > translation > transliteration > original."""
        if language in self.human_overrides:
            return self.human_overrides[language]
        if language in self.translations:
            return self.translations[language]
        if language in self.transliterations:
            return self.transliterations[language]
        return self.original_text


class GlossaryTerm(BaseModel):
    """A versioned glossary term with provenance and authority."""

    schema_version: Literal["axignal.f05.glossary.v1"] = "axignal.f05.glossary.v1"
    glossary_id: str = Field(min_length=3, max_length=80)
    term: str = Field(min_length=1, max_length=300)
    language: str = Field(pattern=r"^[a-z]{2,3}$")
    equivalents: dict[str, str] = Field(default_factory=dict)
    source_id: str | None = None
    human_approved: bool = False
    approved_by: str | None = None
    approved_at: datetime | None = None

    @model_validator(mode="after")
    def validate_glossary(self) -> GlossaryTerm:
        for language, equivalent in self.equivalents.items():
            if language not in PRODUCT_LANGUAGES:
                raise ValueError(
                    f"language {language!r} not in product vocabulary {PRODUCT_LANGUAGES}"
                )
            if not equivalent.strip():
                raise ValueError(f"equivalent for {language!r} must not be empty")
        if self.human_approved and (not self.approved_by or not self.approved_at):
            raise ValueError(
                "human_approved=true requires approved_by and approved_at"
            )
        return self
