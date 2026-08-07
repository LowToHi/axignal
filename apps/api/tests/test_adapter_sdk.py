"""WP2-T04 — internal source adapter SDK tests."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from axignal_api.adapter_sdk import (
    DEFAULT_ADAPTER_REGISTRY,
    AdapterConformanceError,
    AdapterProbeResult,
    AdapterRegistry,
    SourceAdapter,
    check_adapter_conformance,
)
from axignal_api.source_manifest import (
    SourceAccessMode,
    SourceManifest,
    SourceState,
)


def ted_manifest(state: SourceState = SourceState.PRODUCT_ADMITTED) -> SourceManifest:
    return SourceManifest(
        source_id="src_ted_search_api_v3",
        name="TED Search API v3",
        library_id="O01",
        source_type="INSTITUTIONAL_API",
        access_mode=SourceAccessMode.INSTITUTIONAL_API,
        base_url="https://api.ted.europa.eu/v3",
        state=state,
        rights_status="COMMERCIAL_REUSE_WITH_ATTRIBUTION",
        commercial_use=(state not in (SourceState.REJECTED, SourceState.REVOKED)),
        manifest_version="1.0.0",
        product_shell_ids=["AXIGNAL_OPPORTUNITY_INTELLIGENCE"],
    )


def wdi_manifest() -> SourceManifest:
    return SourceManifest(
        source_id="world-bank-wdi",
        name="World Bank WDI",
        library_id="O01",
        source_type="INSTITUTIONAL_API",
        access_mode=SourceAccessMode.INSTITUTIONAL_API,
        state=SourceState.PRODUCT_ADMITTED,
        rights_status="COMMERCIAL_REUSE_WITH_ATTRIBUTION",
        commercial_use=True,
        manifest_version="1.0.0",
        product_shell_ids=["AXIGNAL_OPPORTUNITY_INTELLIGENCE"],
    )


class TestAdapterRegistry:
    def test_default_registry_has_ted_and_wdi(self) -> None:
        assert DEFAULT_ADAPTER_REGISTRY.source_ids() == (
            "src_ted_search_api_v3",
            "world-bank-wdi",
        )
        assert DEFAULT_ADAPTER_REGISTRY.has("src_ted_search_api_v3")
        assert DEFAULT_ADAPTER_REGISTRY.has("world-bank-wdi")

    def test_register_requires_source_id(self) -> None:
        registry = AdapterRegistry()

        class NoSourceId(SourceAdapter):
            def probe(self, *, limit: int | None = None) -> AdapterProbeResult:
                raise NotImplementedError

            def manifest(self) -> SourceManifest:
                raise NotImplementedError

        with pytest.raises(AdapterConformanceError, match="source_id"):
            registry.register(NoSourceId)

    def test_register_duplicate_rejected(self) -> None:
        registry = AdapterRegistry()

        class AdapterA(SourceAdapter):
            source_id = "src-x"

            def probe(self, *, limit: int | None = None) -> AdapterProbeResult:
                raise NotImplementedError

            def manifest(self) -> SourceManifest:
                raise NotImplementedError

        class AdapterB(AdapterA):
            pass

        registry.register(AdapterA)
        with pytest.raises(AdapterConformanceError, match="duplicate"):
            registry.register(AdapterB)

    def test_build_unknown_source(self) -> None:
        with pytest.raises(AdapterConformanceError, match="no adapter registered"):
            DEFAULT_ADAPTER_REGISTRY.build(
                "src-does-not-exist", ted_manifest()
            )

    def test_build_mismatched_manifest(self) -> None:
        manifest = ted_manifest()
        manifest = manifest.model_copy(update={"source_id": "world-bank-wdi"})
        with pytest.raises(AdapterConformanceError, match="does not match manifest"):
            DEFAULT_ADAPTER_REGISTRY.build("src_ted_search_api_v3", manifest)

    def test_build_rejected_source_forbidden(self) -> None:
        manifest = ted_manifest(state=SourceState.REJECTED)
        with pytest.raises(AdapterConformanceError, match="no runtime adapter"):
            DEFAULT_ADAPTER_REGISTRY.build("src_ted_search_api_v3", manifest)

    def test_build_ted_with_fixture(self) -> None:
        from pathlib import Path

        fixture = Path("apps/api/tests/fixtures/ted_search_probe.json")
        adapter = DEFAULT_ADAPTER_REGISTRY.build(
            "src_ted_search_api_v3",
            ted_manifest(),
            live_enabled=False,
            fixture_path=fixture,
        )
        result = adapter.probe(limit=3)
        assert isinstance(result, AdapterProbeResult)
        assert result.source_id == "src_ted_search_api_v3"
        assert result.retrieval_mode == "FROZEN_FIXTURE"
        assert result.content_hash.startswith("sha256:")
        assert result.request_hash
        assert adapter.manifest().source_id == "src_ted_search_api_v3"


class TestAdapterConformance:
    def test_conformance_requires_probe_and_manifest(self) -> None:
        class BadAdapter(SourceAdapter):
            source_id = "src_ted_search_api_v3"

            def manifest(self) -> SourceManifest:
                return ted_manifest()

        with pytest.raises(AdapterConformanceError, match="abstract|probe"):
            check_adapter_conformance(BadAdapter, ted_manifest())

    def test_conformance_mismatched_source(self) -> None:
        from axignal_api.adapter_sdk import _BoundedTEDAdapter

        with pytest.raises(AdapterConformanceError, match="does not match"):
            check_adapter_conformance(_BoundedTEDAdapter, wdi_manifest())

    def test_conformance_rejected_source(self) -> None:
        from axignal_api.adapter_sdk import _BoundedTEDAdapter

        with pytest.raises(AdapterConformanceError, match="no runtime adapter"):
            check_adapter_conformance(
                _BoundedTEDAdapter, ted_manifest(state=SourceState.REJECTED)
            )

    def test_probe_result_fields_complete(self) -> None:
        result = AdapterProbeResult(
            source_id="src-test",
            retrieval_mode="TECHNICAL_PROBE",
            retrieved_at=datetime.now(UTC),
            content_hash="sha256:abc",
            request_hash="req-1",
            record_count=2,
            records=({"a": 1}, {"b": 2}),
        )
        assert result.source_id == "src-test"
        assert result.record_count == 2
        assert len(result.records) == 2
