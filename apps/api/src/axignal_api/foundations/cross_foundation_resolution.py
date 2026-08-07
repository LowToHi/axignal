"""WP3-T08 — cross-foundation resolution.

A resolver that joins the F01-F07 foundational libraries into a single
typed resolution context. It demonstrates that foundations compose
without coupling: a resolved object may carry jurisdiction, entity,
taxonomy, value, language, rights and document facets, each backed by
its own foundational library.

Rules:
- every facet is optional but typed;
- resolution is deterministic and reproducible (fingerprint of facets);
- unknown facets are never silently defaulted;
- no foundation may mutate another foundation's record.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Literal

from pydantic import BaseModel, Field

from axignal_api.foundations.f01_geography import Jurisdiction
from axignal_api.foundations.f02_entities import Entity
from axignal_api.foundations.f03_taxonomies import TaxonomyCode
from axignal_api.foundations.f04_time_currency import MonetaryValue, TemporalPoint
from axignal_api.foundations.f05_languages import TranslatedText
from axignal_api.foundations.f06_rights_provenance import EvidenceProvenance
from axignal_api.foundations.f07_documents import DocumentRecord


class CrossFoundationResolution(BaseModel):
    """A resolved object joining facets from F01-F07."""

    schema_version: Literal["axignal.foundations.resolution.v1"] = (
        "axignal.foundations.resolution.v1"
    )
    resolution_id: str = Field(min_length=3, max_length=120)
    jurisdiction: Jurisdiction | None = None
    entity: Entity | None = None
    taxonomy_codes: list[TaxonomyCode] = Field(default_factory=list)
    monetary_value: MonetaryValue | None = None
    temporal_points: list[TemporalPoint] = Field(default_factory=list)
    translated_text: TranslatedText | None = None
    provenance: EvidenceProvenance | None = None
    documents: list[DocumentRecord] = Field(default_factory=list)
    resolution_fingerprint: str | None = None

    def compute_fingerprint(self) -> str:
        facets: dict[str, Any] = {
            "resolution_id": self.resolution_id,
            "jurisdiction_id": self.jurisdiction.jurisdiction_id if self.jurisdiction else None,
            "entity_id": self.entity.entity_id if self.entity else None,
            "taxonomy_ids": sorted(
                code.qualified_id for code in self.taxonomy_codes
            ),
            "currency": self.monetary_value.currency if self.monetary_value else None,
            "document_hashes": sorted(
                doc.content_hash for doc in self.documents
            ),
        }
        encoded = json.dumps(facets, sort_keys=True).encode("utf-8")
        return f"fp:{hashlib.sha256(encoded).hexdigest()}"

    def resolved(self) -> CrossFoundationResolution:
        return self.model_copy(
            update={"resolution_fingerprint": self.compute_fingerprint()}
        )


@dataclass
class ResolutionContext:
    """Composition root for cross-foundation resolution."""

    resolutions: dict[str, CrossFoundationResolution] = field(default_factory=dict)

    def resolve(self, resolution: CrossFoundationResolution) -> CrossFoundationResolution:
        resolved = resolution.resolved()
        self.resolutions[resolved.resolution_id] = resolved
        return resolved

    def get(self, resolution_id: str) -> CrossFoundationResolution | None:
        return self.resolutions.get(resolution_id)

    def __len__(self) -> int:
        return len(self.resolutions)
