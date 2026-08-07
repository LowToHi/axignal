"""Internal source adapter SDK — WP2-T04.

A thin, non-speculative SDK that standardises how source connectors are
registered, built from a SourceManifest and checked for contract
conformance. It wraps the existing bounded connectors (TED Search API,
World Bank) without reimplementing them.

Conformance rules (contract sections 11 and 8.2):
- an adapter must declare the source_id it serves;
- an adapter must be buildable from the canonical SourceManifest of that
  source (library placement, access mode, states);
- an adapter must implement a bounded probe with retrieval metadata
  (source_id, retrieved_at, content_hash, request_hash, retrieval_mode);
- an adapter must not admit sources, claims or rights by itself;
- a REJECTED source cannot be wrapped by a runtime adapter.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from axignal_api.source_manifest import SourceManifest, SourceState

LOGGER = logging.getLogger(__name__)


class AdapterConformanceError(RuntimeError):
    """Raised when an adapter violates the source adapter contract."""


@dataclass(frozen=True)
class AdapterProbeResult:
    """Bounded retrieval result produced by a conformant adapter."""

    source_id: str
    retrieval_mode: str
    retrieved_at: datetime
    content_hash: str
    request_hash: str
    record_count: int
    records: tuple[dict[str, Any], ...]


class SourceAdapter(ABC):
    """Interface every internal source adapter must implement."""

    source_id: str

    @abstractmethod
    def probe(self, *, limit: int | None = None) -> AdapterProbeResult:
        """Execute a bounded technical probe against the source."""

    @abstractmethod
    def manifest(self) -> SourceManifest:
        """Return the canonical SourceManifest of this source."""

    def close(self) -> None:
        """Release any held resources; default no-op."""
        return None


class AdapterRegistry:
    """Registry of source adapters keyed by source_id."""

    def __init__(self) -> None:
        self._adapters: dict[str, type[SourceAdapter]] = {}

    def register(self, adapter_type: type[SourceAdapter]) -> None:
        source_id = getattr(adapter_type, "source_id", None)
        if not isinstance(source_id, str) or not source_id:
            raise AdapterConformanceError(
                f"adapter {adapter_type.__name__} must declare source_id"
            )
        if source_id in self._adapters:
            raise AdapterConformanceError(f"duplicate adapter for source {source_id!r}")
        self._adapters[source_id] = adapter_type

    def get(self, source_id: str) -> type[SourceAdapter] | None:
        return self._adapters.get(source_id)

    def has(self, source_id: str) -> bool:
        return source_id in self._adapters

    def source_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._adapters))

    def build(self, source_id: str, manifest: SourceManifest, **kwargs: Any) -> SourceAdapter:
        """Build an adapter for a source from its canonical manifest."""
        adapter_type = self.get(source_id)
        if adapter_type is None:
            raise AdapterConformanceError(f"no adapter registered for source {source_id!r}")
        check_adapter_conformance(adapter_type, manifest)
        return adapter_type(manifest=manifest, **kwargs)


class _BoundedTEDAdapter(SourceAdapter):
    """Adapter wrapper over the existing bounded TED Search connector."""

    source_id = "src_ted_search_api_v3"

    def __init__(self, manifest: SourceManifest, **kwargs: Any) -> None:
        from axignal_api.connectors.ted import TEDSearchConnector

        self._manifest = manifest
        live_enabled = kwargs.pop("live_enabled", False)
        fixture_path = kwargs.pop("fixture_path", None)
        client = kwargs.pop("client", None)
        self._connector = TEDSearchConnector(
            live_enabled=live_enabled,
            fixture_path=fixture_path,
            client=client,
        )

    def probe(self, *, limit: int | None = None) -> AdapterProbeResult:
        page = self._connector.fetch_probe_page()
        return AdapterProbeResult(
            source_id=page.source_id,
            retrieval_mode=page.retrieval_mode,
            retrieved_at=page.retrieved_at,
            content_hash=page.content_hash,
            request_hash=page.request_hash,
            record_count=len(page.notices),
            records=tuple(
                {
                    "publication_number": notice.publication_number,
                    "fields": notice.fields,
                    "missing_requested_fields": notice.missing_requested_fields,
                }
                for notice in page.notices
            ),
        )

    def manifest(self) -> SourceManifest:
        return self._manifest


class _WorldBankWDIAdapter(SourceAdapter):
    """Adapter wrapper over the existing World Bank WDI connector."""

    source_id = "world-bank-wdi"

    def __init__(self, manifest: SourceManifest, **kwargs: Any) -> None:
        from axignal_api.connectors.world_bank import WorldBankConnector

        self._manifest = manifest
        live_enabled = kwargs.pop("live_enabled", False)
        fixture_path = kwargs.pop("fixture_path", None)
        client = kwargs.pop("client", None)
        self._connector = WorldBankConnector(
            live_enabled=live_enabled,
            fixture_path=fixture_path,
            client=client,
        )

    def probe(self, *, limit: int | None = None) -> AdapterProbeResult:
        observation = self._connector.fetch_latest_inflation()
        payload = {
            "indicator": observation.indicator_code,
            "value": observation.value,
            "period": observation.period,
            "country": observation.country_code,
        }
        return AdapterProbeResult(
            source_id=self.source_id,
            retrieval_mode=observation.retrieval_mode,
            retrieved_at=observation.retrieved_at,
            content_hash=observation.content_hash,
            request_hash=observation.retrieval_key,
            record_count=1 if observation.value is not None else 0,
            records=(payload,),
        )

    def manifest(self) -> SourceManifest:
        return self._manifest


def check_adapter_conformance(adapter_type: type[SourceAdapter], manifest: SourceManifest) -> None:
    """Validate that an adapter type satisfies the SourceManifest contract."""
    import inspect

    source_id = getattr(adapter_type, "source_id", None)
    if source_id != manifest.source_id:
        raise AdapterConformanceError(
            f"adapter source_id {source_id!r} does not match manifest {manifest.source_id!r}"
        )
    if manifest.state in (SourceState.REJECTED, SourceState.REVOKED):
        raise AdapterConformanceError(
            f"source {manifest.source_id!r} is {manifest.state.value}; "
            "no runtime adapter may wrap it"
        )
    if inspect.isabstract(adapter_type):
        raise AdapterConformanceError(
            f"adapter {adapter_type.__name__} is abstract; "
            "it must implement probe() and manifest()"
        )
    if not hasattr(adapter_type, "probe") or not hasattr(adapter_type, "manifest"):
        raise AdapterConformanceError(
            f"adapter {adapter_type.__name__} must implement probe() and manifest()"
        )


DEFAULT_ADAPTER_REGISTRY = AdapterRegistry()
DEFAULT_ADAPTER_REGISTRY.register(_BoundedTEDAdapter)
DEFAULT_ADAPTER_REGISTRY.register(_WorldBankWDIAdapter)
