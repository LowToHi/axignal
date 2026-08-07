"""WP14 — Cross-library Intelligence (T01-T12).

Cross-library layer over O01-O09:

- T01 entity graph: typed nodes/edges across libraries;
- T02 event lineage: events reference their evidence chain;
- T03 temporal alignment: facts aligned on a common timeline;
- T04 contradiction propagation: contradictions propagate as warnings,
  never silently resolved;
- T05 causal hypotheses: always HYPOTHESIS, never canonical facts;
- T06 Globe layers: navigable layers over the context;
- T07 Graph lenses: typed views of the same shared context;
- T08 Timeline reconstruction: ordered events with gaps explicit;
- T09 cross-library Navigator: multi-facet search over libraries;
- T10 portfolio: tenant-scoped portfolio of opportunities;
- T11 entitlements: capability-based access checks;
- T12 mandatory cross-library E2E (in cross_library_e2e).
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

CANONICAL_LIBRARIES = (
    "O01",
    "O02",
    "O03",
    "O04",
    "O05",
    "O06",
    "O07",
    "O08",
    "O09",
)


class GraphNode(BaseModel):
    """A typed entity-graph node (T01)."""

    schema_version: Literal["axignal.wp14.node.v1"] = "axignal.wp14.node.v1"
    node_id: str = Field(min_length=3, max_length=120)
    library_id: str = Field(pattern=r"^O0[1-9]$")
    entity_type: str = Field(min_length=2, max_length=80)
    entity_ref: str = Field(min_length=3, max_length=120)

    @model_validator(mode="after")
    def validate_node(self) -> GraphNode:
        if self.library_id not in CANONICAL_LIBRARIES:
            raise ValueError(f"unknown library {self.library_id!r}")
        return self


class GraphEdge(BaseModel):
    """A typed edge between graph nodes (T01)."""

    schema_version: Literal["axignal.wp14.edge.v1"] = "axignal.wp14.edge.v1"
    edge_id: str = Field(min_length=3, max_length=120)
    from_node_id: str
    to_node_id: str
    relation: str = Field(min_length=2, max_length=80)
    observed_at: date | None = None
    evidence_ref: str | None = None

    @model_validator(mode="after")
    def validate_edge(self) -> GraphEdge:
        if self.from_node_id == self.to_node_id:
            raise ValueError("a graph edge cannot connect a node to itself")
        if self.relation in ("SUBSIDIARY_OF", "AWARDED_TO", "AMENDS") and not self.evidence_ref:
            raise ValueError(f"{self.relation} edges require evidence_ref")
        return self


class EventLineage(BaseModel):
    """An event with its evidence chain (T02)."""

    schema_version: Literal["axignal.wp14.event.v1"] = "axignal.wp14.event.v1"
    event_id: str = Field(min_length=3, max_length=120)
    library_id: str = Field(pattern=r"^O0[1-9]$")
    event_type: str = Field(min_length=2, max_length=80)
    occurred_at: datetime
    evidence_chain: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_event(self) -> EventLineage:
        if not self.evidence_chain:
            raise ValueError("events require an evidence chain")
        return self


class TemporalFact(BaseModel):
    """A fact aligned on the common timeline (T03)."""

    schema_version: Literal["axignal.wp14.temporal-fact.v1"] = "axignal.wp14.temporal-fact.v1"
    fact_id: str = Field(min_length=3, max_length=120)
    library_id: str = Field(pattern=r"^O0[1-9]$")
    subject_ref: str = Field(min_length=3, max_length=120)
    role: Literal["PUBLICATION", "OBSERVATION", "VALIDITY", "DEADLINE", "AWARD", "EXECUTION"]
    at: datetime
    source_id: str | None = None

    @model_validator(mode="after")
    def validate_fact(self) -> TemporalFact:
        if self.role in ("AWARD", "EXECUTION") and not self.source_id:
            raise ValueError(f"{self.role} facts require source_id")
        return self


class Contradiction(BaseModel):
    """A detected contradiction between facts (T04)."""

    schema_version: Literal["axignal.wp14.contradiction.v1"] = "axignal.wp14.contradiction.v1"
    contradiction_id: str = Field(min_length=3, max_length=120)
    fact_a_ref: str
    fact_b_ref: str
    description: str = Field(min_length=10, max_length=1000)
    severity: Literal["WARNING", "BLOCKING"] = "WARNING"
    status: Literal["OPEN", "RESOLVED"] = "OPEN"
    resolution_evidence_ref: str | None = None

    @model_validator(mode="after")
    def validate_contradiction(self) -> Contradiction:
        if self.fact_a_ref == self.fact_b_ref:
            raise ValueError("a contradiction needs two distinct facts")
        if self.status == "RESOLVED" and not self.resolution_evidence_ref:
            raise ValueError("RESOLVED contradictions require resolution evidence")
        return self


class CausalHypothesis(BaseModel):
    """A causal hypothesis, never a canonical fact (T05)."""

    schema_version: Literal["axignal.wp14.hypothesis.v1"] = "axignal.wp14.hypothesis.v1"
    hypothesis_id: str = Field(min_length=3, max_length=120)
    cause_ref: str
    effect_ref: str
    rationale: str = Field(min_length=10, max_length=2000)
    confidence: float = Field(ge=0.0, le=1.0)
    status: Literal["HYPOTHESIS", "SUPPORTED", "REFUTED"] = "HYPOTHESIS"
    evidence_refs: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_hypothesis(self) -> CausalHypothesis:
        if self.cause_ref == self.effect_ref:
            raise ValueError("cause and effect must differ")
        if not self.evidence_refs:
            raise ValueError("hypotheses require evidence_refs")
        return self

    def to_canonical_fact(self) -> None:
        """A causal hypothesis can never become a canonical fact."""
        raise ValueError(
            "causal hypotheses are never canonical facts; "
            "they remain hypotheses with evidence"
        )


class GlobeLayer(BaseModel):
    """A Globe layer over the shared context (T06)."""

    schema_version: Literal["axignal.wp14.globe-layer.v1"] = "axignal.wp14.globe-layer.v1"
    layer_id: str = Field(min_length=3, max_length=120)
    layer_type: Literal["REGIONS", "SECTORS", "SOURCES", "OPPORTUNITIES", "SIGNALS"]
    context_ref: str
    enabled: bool = True


class GraphLens(BaseModel):
    """A Graph lens over the same shared context (T07)."""

    schema_version: Literal["axignal.wp14.graph-lens.v1"] = "axignal.wp14.graph-lens.v1"
    lens_id: str = Field(min_length=3, max_length=120)
    lens_type: Literal["ENTITY", "EVENT", "CONTRADICTION", "CAUSALITY", "TEMPORAL"]
    context_ref: str
    node_ids: list[str] = Field(default_factory=list)


class TimelinePoint(BaseModel):
    """A timeline entry with explicit gaps (T08)."""

    schema_version: Literal["axignal.wp14.timeline.v1"] = "axignal.wp14.timeline.v1"
    timeline_id: str = Field(min_length=3, max_length=120)
    subject_ref: str
    ordered_events: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_timeline(self) -> TimelinePoint:
        if not self.ordered_events:
            raise ValueError("timeline requires ordered events")
        return self


class NavigatorQuery(BaseModel):
    """A cross-library navigator query (T09)."""

    schema_version: Literal["axignal.wp14.navigator.v1"] = "axignal.wp14.navigator.v1"
    query_id: str = Field(min_length=3, max_length=120)
    tenant_id: UUID
    text: str = Field(min_length=2, max_length=500)
    libraries: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_query(self) -> NavigatorQuery:
        for library in self.libraries:
            if library not in CANONICAL_LIBRARIES:
                raise ValueError(f"unknown library {library!r}")
        return self


class PortfolioItem(BaseModel):
    """A tenant-scoped portfolio item (T10)."""

    schema_version: Literal["axignal.wp14.portfolio.v1"] = "axignal.wp14.portfolio.v1"
    item_id: str = Field(min_length=3, max_length=120)
    tenant_id: UUID
    opportunity_ref: str
    library_id: str = Field(pattern=r"^O0[1-9]$")
    added_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class EntitlementCheck(BaseModel):
    """A capability-based entitlement check (T11)."""

    schema_version: Literal["axignal.wp14.entitlement.v1"] = "axignal.wp14.entitlement.v1"
    check_id: str = Field(min_length=3, max_length=120)
    tenant_id: UUID
    capability: str = Field(min_length=3, max_length=120)
    allowed: bool = False
    checked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Portfolio:
    """Tenant-scoped portfolio of opportunities (T10)."""

    def __init__(self) -> None:
        self._items: dict[str, PortfolioItem] = {}

    def add(self, item: PortfolioItem) -> None:
        self._items[item.item_id] = item

    def for_tenant(self, tenant_id: UUID) -> tuple[PortfolioItem, ...]:
        return tuple(
            item for item in self._items.values() if item.tenant_id == tenant_id
        )

    def __len__(self) -> int:
        return len(self._items)


class EntitlementRegistry:
    """Capability-based entitlement registry (T11)."""

    def __init__(self) -> None:
        self._grants: dict[tuple[UUID, str], bool] = {}

    def grant(self, tenant_id: UUID, capability: str) -> None:
        self._grants[(tenant_id, capability)] = True

    def revoke(self, tenant_id: UUID, capability: str) -> None:
        self._grants.pop((tenant_id, capability), None)

    def check(self, tenant_id: UUID, capability: str) -> bool:
        return self._grants.get((tenant_id, capability), False)

    def check_recorded(self, tenant_id: UUID, capability: str) -> EntitlementCheck:
        return EntitlementCheck(
            check_id=f"chk-{tenant_id}-{capability}",
            tenant_id=tenant_id,
            capability=capability,
            allowed=self.check(tenant_id, capability),
        )
