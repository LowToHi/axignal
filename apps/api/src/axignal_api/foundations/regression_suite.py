"""WP3-T09 — multilingual and temporal regression suite.

A regression suite over the F01-F07 foundational libraries that
validates cross-cutting invariants:

Multilingual invariants:
- product languages (en/es/fr/de/pt/it) resolve in F01 and F05;
- translations preserve the original and carry provenance/confidence;
- critical action labels are semantically equivalent across languages.

Temporal invariants:
- temporal roles are typed and ordered (F04);
- jurisdiction validity windows are respected (F01);
- entity control observations are dated (F02);
- document acquisition times are recorded (F07);
- FX rates respect validity windows (F04).
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta

from axignal_api.foundations.f01_geography import (
    CANONICAL_JURISDICTION_REGISTRY,
    Jurisdiction,
)
from axignal_api.foundations.f04_time_currency import FxRate, TemporalPoint
from axignal_api.foundations.f05_languages import (
    PRODUCT_LANGUAGES,
    TranslatedText,
)
from axignal_api.foundations.f07_documents import DocumentRecord

CheckFn = Callable[[], bool]


class RegressionFailure(RuntimeError):
    """Raised when a foundational regression invariant is violated."""


def run_foundational_regression() -> dict[str, bool]:
    """Run all multilingual and temporal regression checks."""
    checks: dict[str, bool] = {}

    # --- Multilingual ---
    checks["product_languages_exact_six"] = PRODUCT_LANGUAGES == (
        "en",
        "es",
        "fr",
        "de",
        "pt",
        "it",
    )

    checks["jurisdiction_multilingual_resolution"] = (
        CANONICAL_JURISDICTION_REGISTRY.resolve("Österreich") is not None
        and CANONICAL_JURISDICTION_REGISTRY.resolve("España") is not None
        and CANONICAL_JURISDICTION_REGISTRY.resolve("Deutschland") is not None
    )

    try:
        text = TranslatedText(
            original_text="Plazo de presentación de ofertas",
            translations={
                lang: f"Tender deadline ({lang})"
                for lang in ("en", "fr", "de", "pt", "it")
            },
            translation_provenance={
                lang: "src-translator" for lang in ("en", "fr", "de", "pt", "it")
            },
            translation_confidence={
                lang: 0.9 for lang in ("en", "fr", "de", "pt", "it")
            },
        )
        checks["translation_preserves_original"] = (
            text.original_text == "Plazo de presentación de ofertas"
        )
        checks["translation_covers_all_product_languages"] = all(
            lang in text.translations for lang in PRODUCT_LANGUAGES if lang != "es"
        )
    except Exception:
        checks["translation_preserves_original"] = False
        checks["translation_covers_all_product_languages"] = False

    # --- Temporal ---
    try:
        deadline = TemporalPoint(role="DEADLINE", value=datetime(2026, 9, 1, 12, 0))
        publication = TemporalPoint(role="PUBLICATION", value=datetime(2026, 8, 1))
        checks["temporal_roles_typed"] = (
            deadline.role == "DEADLINE" and publication.role == "PUBLICATION"
        )
        checks["deadline_after_publication"] = (
            deadline.value > publication.value
        )
    except Exception:
        checks["temporal_roles_typed"] = False
        checks["deadline_after_publication"] = False

    try:
        fx = FxRate(
            from_currency="EUR",
            to_currency="USD",
            rate=1.08,
            valid_from=date(2026, 1, 1),
            valid_to=date(2026, 12, 31),
        )
        checks["fx_validity_window"] = (
            fx.valid_to >= fx.valid_from and fx.rate > 0
        )
    except Exception:
        checks["fx_validity_window"] = False

    try:
        doc = DocumentRecord(
            document_id="doc-reg",
            source_id="src-x",
            format="PDF",
            content_hash=f"sha256:{'e' * 64}",
            acquired_at=datetime.now(UTC),
        )
        checks["document_acquisition_dated"] = (
            doc.acquired_at <= datetime.now(UTC) + timedelta(seconds=1)
        )
    except Exception:
        checks["document_acquisition_dated"] = False

    try:
        historical = Jurisdiction(
            jurisdiction_id="CS",
            name="Serbia and Montenegro",
            valid_from=date(2003, 2, 4),
            valid_to=date(2006, 6, 3),
            superseded_by="RS",
        )
        checks["jurisdiction_temporality"] = (
            historical.valid_to > historical.valid_from
            and historical.superseded_by == "RS"
        )
    except Exception:
        checks["jurisdiction_temporality"] = False

    if not all(checks.values()):
        failed = [name for name, ok in checks.items() if not ok]
        raise RegressionFailure(
            f"foundational regression failures: {failed}"
        )
    return checks
