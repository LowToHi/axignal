"""WP3-T08 — cross-foundation resolution tests."""

from __future__ import annotations

from datetime import UTC, datetime

from axignal_api.foundations.cross_foundation_resolution import (
    CrossFoundationResolution,
    ResolutionContext,
)
from axignal_api.foundations.f01_geography import CANONICAL_JURISDICTION_REGISTRY
from axignal_api.foundations.f02_entities import Entity, EntityName
from axignal_api.foundations.f03_taxonomies import TaxonomyCode
from axignal_api.foundations.f04_time_currency import MonetaryValue
from axignal_api.foundations.f07_documents import DocumentRecord


def full_resolution() -> CrossFoundationResolution:
    return CrossFoundationResolution(
        resolution_id="res-1",
        jurisdiction=CANONICAL_JURISDICTION_REGISTRY.get("ES"),
        entity=Entity(
            entity_id="ent_ministerio_fomento_es",
            entity_type="PUBLIC_BODY",
            names=[EntityName(name="Ministerio de Fomento")],
        ),
        taxonomy_codes=[
            TaxonomyCode(taxonomy="CPV", code="45233100", label="Roads"),
            TaxonomyCode(taxonomy="NUTS", code="ES30", label="Madrid"),
        ],
        monetary_value=MonetaryValue(amount=1_500_000.0, currency="EUR"),
        documents=[
            DocumentRecord(
                document_id="doc-1",
                source_id="src_ted_search_api_v3",
                format="PDF",
                content_hash=f"sha256:{'b' * 64}",
                acquired_at=datetime.now(UTC),
            )
        ],
    )


class TestCrossFoundationResolution:
    def test_composes_all_foundations(self) -> None:
        resolution = full_resolution()
        assert resolution.jurisdiction.jurisdiction_id == "ES"
        assert resolution.entity.entity_id == "ent_ministerio_fomento_es"
        assert len(resolution.taxonomy_codes) == 2
        assert resolution.monetary_value.amount == 1_500_000.0
        assert len(resolution.documents) == 1

    def test_fingerprint_reproducible(self) -> None:
        a = full_resolution()
        b = full_resolution()
        assert a.compute_fingerprint() == b.compute_fingerprint()

    def test_fingerprint_changes_with_facets(self) -> None:
        a = full_resolution()
        b = full_resolution().model_copy(
            update={"jurisdiction": None}
        )
        assert a.compute_fingerprint() != b.compute_fingerprint()

    def test_resolved_stamps_fingerprint(self) -> None:
        context = ResolutionContext()
        resolved = context.resolve(full_resolution())
        assert resolved.resolution_fingerprint == resolved.compute_fingerprint()

    def test_context_roundtrip(self) -> None:
        context = ResolutionContext()
        context.resolve(full_resolution())
        assert len(context) == 1
        assert context.get("res-1") is not None
        assert context.get("missing") is None

    def test_foundations_do_not_mutate_each_other(self) -> None:
        resolution = full_resolution()
        before = resolution.jurisdiction.jurisdiction_id
        # Resolving stamps only the resolution, never the facets.
        resolved = resolution.resolved()
        assert resolved.jurisdiction.jurisdiction_id == before
        assert resolution.jurisdiction.jurisdiction_id == before

    def test_partial_resolution_allowed(self) -> None:
        resolution = CrossFoundationResolution(
            resolution_id="res-partial",
            jurisdiction=CANONICAL_JURISDICTION_REGISTRY.get("LU"),
        )
        assert resolution.compute_fingerprint().startswith("fp:")

    def test_unknown_facets_not_silently_defaulted(self) -> None:
        resolution = CrossFoundationResolution(resolution_id="res-empty")
        assert resolution.monetary_value is None
        assert resolution.entity is None
        assert resolution.provenance is None
        assert resolution.translated_text is None
