"""WP3-T10 — foundational E2E.

End-to-end journey across all foundational libraries (F01-F07):

1. a jurisdiction is resolved (F01);
2. an entity is registered with native identifiers (F02);
3. taxonomy codes are attached (F03);
4. a monetary value and temporal points are typed (F04);
5. a translated text carries provenance and confidence (F05);
6. the source rights record and evidence provenance are created (F06);
7. a document moves through the acquisition pipeline (F07);
8. the cross-foundation resolution composes everything (WP3-T08);
9. the regression suite still passes (WP3-T09).

The E2E is deterministic: it uses reference data and fixtures, never
live sources, and asserts every gate.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

from axignal_api.foundations.cross_foundation_resolution import (
    CrossFoundationResolution,
    ResolutionContext,
)
from axignal_api.foundations.f01_geography import CANONICAL_JURISDICTION_REGISTRY
from axignal_api.foundations.f02_entities import (
    Entity,
    EntityFact,
    EntityIdentifier,
    EntityName,
    EntityRegistry,
)
from axignal_api.foundations.f03_taxonomies import TaxonomyCode, TaxonomyRegistry
from axignal_api.foundations.f04_time_currency import MonetaryValue, TemporalPoint
from axignal_api.foundations.f05_languages import TranslatedText
from axignal_api.foundations.f06_rights_provenance import (
    EvidenceProvenance,
    SourceRightsRecord,
)
from axignal_api.foundations.f07_documents import (
    DocumentRecord,
    run_acquisition_pipeline,
)
from axignal_api.foundations.regression_suite import run_foundational_regression


class FoundationalE2EFailure(RuntimeError):
    """Raised when the foundational E2E journey fails a gate."""


def run_foundational_e2e() -> dict[str, Any]:
    """Run the full F01-F07 E2E journey and return the evidence dict."""
    evidence: dict[str, Any] = {}

    # 1. F01 jurisdiction.
    jurisdiction = CANONICAL_JURISDICTION_REGISTRY.resolve("España")
    assert jurisdiction is not None, "F01: Spain must resolve"
    evidence["f01_jurisdiction"] = {
        "id": jurisdiction.jurisdiction_id,
        "nuts": jurisdiction.nuts_equivalent,
        "timezone": jurisdiction.timezone,
    }

    # 2. F02 entity.
    registry = EntityRegistry()
    buyer = Entity(
        entity_id="ent_ministerio_fomento_es",
        entity_type="PUBLIC_BODY",
        names=[EntityName(name="Ministerio de Fomento", language="es")],
        identifiers=[
            EntityIdentifier(
                scheme="es-registry", value="S2800135B", source_id="src_es_boe"
            )
        ],
        facts=[
            EntityFact(
                fact_type="registered_name",
                value="Ministerio de Fomento",
                provenance="OBSERVED",
                source_id="src_es_boe",
                observed_at=date(2026, 1, 1),
            )
        ],
    )
    registry.register(buyer)
    resolved_entity = registry.get("ent_ministerio_fomento_es")
    assert resolved_entity is not None, "F02: entity must register"
    assert resolved_entity.resolution_fingerprint, "F02: fingerprint required"
    evidence["f02_entity"] = {
        "id": resolved_entity.entity_id,
        "fingerprint": resolved_entity.resolution_fingerprint[:16],
    }

    # 3. F03 taxonomies.
    taxonomies = TaxonomyRegistry()
    cpv = TaxonomyCode(taxonomy="CPV", code="45233100", label="Roads")
    nuts = TaxonomyCode(taxonomy="NUTS", code="ES30", label="Madrid")
    taxonomies.register_code(cpv)
    taxonomies.register_code(nuts)
    assert taxonomies.get_code("CPV", "45233100") is not None
    evidence["f03_taxonomies"] = ["CPV:45233100", "NUTS:ES30"]

    # 4. F04 values and time.
    value = MonetaryValue(amount=1_500_000.0, currency="EUR")
    deadline = TemporalPoint(role="DEADLINE", value=datetime(2026, 9, 1, 12, 0))
    publication = TemporalPoint(role="PUBLICATION", value=datetime(2026, 8, 1))
    assert deadline.value > publication.value, "F04: deadline after publication"
    evidence["f04_value"] = {"amount": value.amount, "currency": value.currency}

    # 5. F05 translation.
    text = TranslatedText(
        original_text="Plazo de presentación de ofertas",
        translations={"en": "Tender submission deadline"},
        translation_provenance={"en": "src-translator-1"},
        translation_confidence={"en": 0.95},
    )
    assert text.effective_text("en") == "Tender submission deadline"
    assert text.original_text == "Plazo de presentación de ofertas"
    evidence["f05_translation"] = {"en": text.effective_text("en")}

    # 6. F06 rights and provenance.
    rights = SourceRightsRecord(
        source_id="src_ted_search_api_v3",
        owner="Publications Office of the EU",
        access_endpoint="https://api.ted.europa.eu/v3/notices/search",
        commercial_use=True,
        attribution_required=True,
        attribution_text="Source: Publications Office of the EU",
    )
    provenance = EvidenceProvenance(
        evidence_id="ev-foundations-1",
        source_id="src_ted_search_api_v3",
        source_version="v3",
        retrieved_at=datetime.now(UTC),
        retrieval_mode="LIVE_API_TECHNICAL_PROBE",
        content_hash=f"sha256:{'f' * 64}",
        request_hash="req-foundations-1",
        original_url="https://api.ted.europa.eu/v3/notices/search",
    )
    assert rights.commercial_use is True
    assert provenance.content_hash.startswith("sha256:")
    evidence["f06_rights"] = {"owner": rights.owner}

    # 7. F07 document pipeline.
    document = DocumentRecord(
        document_id="doc-foundations-1",
        source_id="src_ted_search_api_v3",
        format="PDF",
        content_hash=f"sha256:{'1' * 64}",
        acquired_at=datetime.now(UTC),
    )
    pipeline = run_acquisition_pipeline(document, ocr_needed=False)
    assert pipeline.pipeline_complete, "F07: pipeline must complete"
    assert "OCR" not in pipeline.completed_stages
    evidence["f07_pipeline"] = {"stages": len(pipeline.completed_stages)}

    # 8. Cross-foundation resolution.
    context = ResolutionContext()
    resolution = CrossFoundationResolution(
        resolution_id="res-foundations-1",
        jurisdiction=jurisdiction,
        entity=resolved_entity,
        taxonomy_codes=[cpv, nuts],
        monetary_value=value,
        temporal_points=[publication, deadline],
        translated_text=text,
        provenance=provenance,
        documents=[pipeline.document],
    )
    resolved = context.resolve(resolution)
    assert resolved.resolution_fingerprint is not None
    evidence["f08_resolution"] = {
        "id": resolved.resolution_id,
        "fingerprint": resolved.resolution_fingerprint[:16],
    }

    # 9. Regression still green.
    regression = run_foundational_regression()
    assert all(regression.values())
    evidence["f09_regression_checks"] = len(regression)

    evidence["status"] = "PASS"
    return evidence
