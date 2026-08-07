"""WP14 — Cross-library Intelligence tests (T01-T11)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest

from axignal_api.cross_library import (
    CausalHypothesis,
    Contradiction,
    EntitlementRegistry,
    EventLineage,
    GlobeLayer,
    GraphEdge,
    GraphLens,
    GraphNode,
    NavigatorQuery,
    Portfolio,
    PortfolioItem,
    TemporalFact,
    TimelinePoint,
)

TENANT = UUID("11111111-1111-4111-8111-111111111111")
OTHER_TENANT = UUID("22222222-2222-4222-8222-222222222222")


class TestEntityGraph:
    def test_node_requires_canonical_library(self) -> None:
        with pytest.raises(ValueError):
            GraphNode(node_id="n-1", library_id="O10", entity_type="COMPANY", entity_ref="e-1")

    def test_valid_node(self) -> None:
        node = GraphNode(
            node_id="n-1", library_id="O01", entity_type="OPPORTUNITY", entity_ref="opp-1"
        )
        assert node.library_id == "O01"

    def test_edge_no_self_loop(self) -> None:
        with pytest.raises(ValueError, match="itself"):
            GraphEdge(edge_id="e-1", from_node_id="n-1", to_node_id="n-1", relation="RELATES")

    def test_awarded_edge_requires_evidence(self) -> None:
        with pytest.raises(ValueError, match="evidence_ref"):
            GraphEdge(edge_id="e-1", from_node_id="n-1", to_node_id="n-2", relation="AWARDED_TO")

    def test_valid_edge(self) -> None:
        edge = GraphEdge(
            edge_id="e-1",
            from_node_id="n-1",
            to_node_id="n-2",
            relation="RELATES",
        )
        assert edge.relation == "RELATES"


class TestEventLineage:
    def test_event_requires_evidence_chain(self) -> None:
        with pytest.raises(ValueError, match="evidence chain"):
            EventLineage(
                event_id="ev-1",
                library_id="O01",
                event_type="NOTICE",
                occurred_at=datetime(2026, 8, 1, tzinfo=UTC),
            )

    def test_valid_event(self) -> None:
        event = EventLineage(
            event_id="ev-1",
            library_id="O01",
            event_type="NOTICE",
            occurred_at=datetime(2026, 8, 1, tzinfo=UTC),
            evidence_chain=["evidence-1"],
        )
        assert event.evidence_chain == ["evidence-1"]


class TestTemporalAlignment:
    def test_award_requires_source(self) -> None:
        with pytest.raises(ValueError, match="source_id"):
            TemporalFact(
                fact_id="f-1",
                library_id="O01",
                subject_ref="opp-1",
                role="AWARD",
                at=datetime(2026, 9, 1, tzinfo=UTC),
            )

    def test_valid_publication_fact(self) -> None:
        fact = TemporalFact(
            fact_id="f-1",
            library_id="O01",
            subject_ref="opp-1",
            role="PUBLICATION",
            at=datetime(2026, 8, 1, tzinfo=UTC),
        )
        assert fact.role == "PUBLICATION"


class TestContradictions:
    def test_same_fact_rejected(self) -> None:
        with pytest.raises(ValueError, match="two distinct facts"):
            Contradiction(
                contradiction_id="c-1",
                fact_a_ref="f-1",
                fact_b_ref="f-1",
                description="Identical facts cannot contradict.",
            )

    def test_open_contradiction_warning(self) -> None:
        contradiction = Contradiction(
            contradiction_id="c-1",
            fact_a_ref="f-1",
            fact_b_ref="f-2",
            description="Deadline differs between notice versions.",
            severity="WARNING",
        )
        assert contradiction.status == "OPEN"

    def test_resolved_requires_evidence(self) -> None:
        with pytest.raises(ValueError, match="resolution evidence"):
            Contradiction(
                contradiction_id="c-1",
                fact_a_ref="f-1",
                fact_b_ref="f-2",
                description="Deadline differs between notice versions.",
                status="RESOLVED",
            )

    def test_propagates_as_warning_not_silent(self) -> None:
        # A contradiction surfaces explicitly; it is never silently merged.
        contradiction = Contradiction(
            contradiction_id="c-1",
            fact_a_ref="f-1",
            fact_b_ref="f-2",
            description="Deadline differs between notice versions.",
        )
        assert contradiction.severity == "WARNING"
        assert contradiction.status == "OPEN"


class TestCausalHypotheses:
    def test_requires_evidence(self) -> None:
        with pytest.raises(ValueError, match="evidence_refs"):
            CausalHypothesis(
                hypothesis_id="h-1",
                cause_ref="c-1",
                effect_ref="e-1",
                rationale="Policy change may affect tender volumes.",
                confidence=0.4,
            )

    def test_hypothesis_status(self) -> None:
        hypothesis = CausalHypothesis(
            hypothesis_id="h-1",
            cause_ref="c-1",
            effect_ref="e-1",
            rationale="Policy change may affect tender volumes.",
            confidence=0.4,
            evidence_refs=["evidence-1"],
        )
        assert hypothesis.status == "HYPOTHESIS"

    def test_never_canonical_fact(self) -> None:
        hypothesis = CausalHypothesis(
            hypothesis_id="h-1",
            cause_ref="c-1",
            effect_ref="e-1",
            rationale="Policy change may affect tender volumes.",
            confidence=0.4,
            evidence_refs=["evidence-1"],
        )
        with pytest.raises(ValueError, match="never canonical facts"):
            hypothesis.to_canonical_fact()


class TestGlobeGraphTimeline:
    def test_globe_layer(self) -> None:
        layer = GlobeLayer(layer_id="l-1", layer_type="SECTORS", context_ref="ctx-1")
        assert layer.enabled is True

    def test_graph_lens(self) -> None:
        lens = GraphLens(lens_id="l-1", lens_type="ENTITY", context_ref="ctx-1")
        assert lens.lens_type == "ENTITY"

    def test_timeline_requires_events(self) -> None:
        with pytest.raises(ValueError, match="ordered events"):
            TimelinePoint(timeline_id="t-1", subject_ref="opp-1")

    def test_timeline_with_gaps_explicit(self) -> None:
        timeline = TimelinePoint(
            timeline_id="t-1",
            subject_ref="opp-1",
            ordered_events=["ev-1", "ev-2"],
            gaps=["2026-08-15..2026-08-20"],
        )
        assert len(timeline.gaps) == 1


class TestNavigator:
    def test_unknown_library_rejected(self) -> None:
        with pytest.raises(ValueError, match="unknown library"):
            NavigatorQuery(
                query_id="q-1",
                tenant_id=TENANT,
                text="highway",
                libraries=["O99"],
            )

    def test_valid_query(self) -> None:
        query = NavigatorQuery(
            query_id="q-1",
            tenant_id=TENANT,
            text="highway",
            libraries=["O01", "O04"],
            languages=["es", "en"],
        )
        assert len(query.libraries) == 2


class TestPortfolio:
    def test_tenant_scoped(self) -> None:
        portfolio = Portfolio()
        portfolio.add(
            PortfolioItem(
                item_id="p-1", tenant_id=TENANT, opportunity_ref="opp-1", library_id="O01"
            )
        )
        portfolio.add(
            PortfolioItem(
                item_id="p-2", tenant_id=OTHER_TENANT, opportunity_ref="opp-2", library_id="O01"
            )
        )
        assert len(portfolio.for_tenant(TENANT)) == 1
        assert len(portfolio.for_tenant(OTHER_TENANT)) == 1


class TestEntitlements:
    def test_default_deny(self) -> None:
        registry = EntitlementRegistry()
        check = registry.check_recorded(TENANT, "bid-workspace:submit")
        assert check.allowed is False

    def test_grant_and_revoke(self) -> None:
        registry = EntitlementRegistry()
        registry.grant(TENANT, "bid-workspace:submit")
        assert registry.check(TENANT, "bid-workspace:submit") is True
        registry.revoke(TENANT, "bid-workspace:submit")
        assert registry.check(TENANT, "bid-workspace:submit") is False

    def test_tenant_isolated(self) -> None:
        registry = EntitlementRegistry()
        registry.grant(TENANT, "bid-workspace:submit")
        assert registry.check(OTHER_TENANT, "bid-workspace:submit") is False

    def test_recorded_check(self) -> None:
        registry = EntitlementRegistry()
        registry.grant(TENANT, "navigator:query")
        check = registry.check_recorded(TENANT, "navigator:query")
        assert check.allowed is True
        assert check.capability == "navigator:query"
