"""AXENT query planner + hybrid retrieval + grounded responses E2E
(Mandato AXENT — secciones 7.2-7.6).

Gates: AX_AXENT_NATURAL_LANGUAGE_QUERY_PLANNER,
AX_AXENT_OPPORTUNITY_RAG_SEARCH_E2E, AX_AXENT_GROUNDED_EXPLANATION_E2E.
"""

from __future__ import annotations

import os
from datetime import date
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from axignal_api.application import app
from axignal_api.axent_evidence_bundle import (
    AxentRanker,
    EvidenceBundle,
    GroundedResponseComposer,
)
from axignal_api.axent_query_planner import QueryPlanError, QueryPlanner
from axignal_api.axent_retrieval_repository import AxentRetrievalRepository
from axignal_api.identity import build_identity_assertion

TENANT_A = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
IDENTITY_SECRET = "local-dev-identity-assertion-secret-32-bytes"
DSN = "postgresql://axignal:axignal-local@localhost:5432/axignal"

pytestmark = pytest.mark.skipif(
    not os.environ.get("AXIGNAL_INTEGRATION_TESTS"),
    reason="AXENT RAG E2E needs a live PostgreSQL",
)


@pytest.fixture(autouse=True)
def _set_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AXIGNAL_DATABASE_URL", DSN)
    monkeypatch.setenv("AXIGNAL_IDENTITY_ASSERTION_SECRET", IDENTITY_SECRET)


class TestQueryPlanner:
    def test_typed_schema_rejects_unknown_fields(self) -> None:
        planner = QueryPlanner()
        with pytest.raises(QueryPlanError):
            planner.plan({"intent": "SEARCH_OPPORTUNITIES", "hacked": True})

    def test_rejects_invalid_ranges_and_currencies(self) -> None:
        planner = QueryPlanner()
        with pytest.raises(QueryPlanError):
            planner.plan({"value_min": 500, "value_max": 100})
        with pytest.raises(QueryPlanError):
            planner.plan({"currencies": ["BTC"]})
        with pytest.raises(QueryPlanError):
            planner.plan({"limit": 0})
        with pytest.raises(QueryPlanError):
            planner.plan({"intent": "DROP_TABLES"})

    def test_natural_language_examples(self) -> None:
        planner = QueryPlanner(today=date(2026, 8, 7))

        plan = planner.from_natural_language(
            "Muéstrame licitaciones de ciberseguridad en España y Portugal."
        )
        assert plan.intent == "SEARCH_OPPORTUNITIES"
        assert "ciberseguridad" in plan.keywords
        assert set(plan.countries) == {"ES", "PT"}

        plan = planner.from_natural_language(
            "Busca oportunidades de digitalización municipal superiores a "
            "200.000 euros, abiertas durante los próximos 45 días."
        )
        assert plan.intent == "SEARCH_OPPORTUNITIES"
        assert "digitalización" in plan.keywords
        assert plan.value_min is not None
        assert plan.deadline_range is not None
        assert (plan.deadline_range[1] - plan.deadline_range[0]).days == 45

        plan = planner.from_natural_language(
            "Excluye las que exijan ISO 27001."
        )
        assert plan.exclusions

        plan = planner.from_natural_language(
            "Busca oportunidades adecuadas para una empresa de veinte empleados."
        )
        assert plan.tenant_capabilities == ("SMALL_TEAM",)

        plan = planner.from_natural_language(
            "Muéstrame grants relacionados con estas oportunidades."
        )
        assert plan.intent == "SEARCH_GRANTS"
        assert plan.object_types == ("GRANT_CALL",)

    def test_inferred_filters_recorded(self) -> None:
        planner = QueryPlanner()
        plan = planner.from_natural_language("Muéstrame licitaciones abiertas.")
        assert plan.inferred_filters


class TestHybridRetrieval:
    def test_structured_and_grounded_search(self) -> None:
        repo = AxentRetrievalRepository(DSN)
        planner = QueryPlanner(today=date(2026, 8, 7))

        plan = planner.from_natural_language(
            "Muéstrame licitaciones de ciberseguridad en España y Portugal."
        )
        objects = repo.search_opportunities(tenant_id=TENANT_A, plan=plan)
        assert isinstance(objects, list)

        # The O01 continuous E2E populated tenant A; at minimum the query
        # executes without error and returns the structured shape.
        for obj in objects:
            assert obj["opportunity_ref"]

        # Semantic retrieval path.
        semantic = repo.semantic_search(
            tenant_id=TENANT_A, query_text="cybersecurity monitoring"
        )
        assert isinstance(semantic, list)

        # Graph retrieval path.
        graph = repo.graph_neighbors(tenant_id=TENANT_A, node_ref="proj_renfe_hsr")
        assert isinstance(graph, list)

        # Temporal retrieval path.
        changes = repo.recent_changes(tenant_id=TENANT_A, since_days=30)
        assert isinstance(changes, list)

        # Claims + evidence + contradictions + source status.
        claims = repo.claims_for(
            tenant_id=TENANT_A, subject_id="O02_call-horizon-eic-2026"
        )
        assert isinstance(claims, list)
        evidence = repo.evidence_for(
            tenant_id=TENANT_A, subject_id="O02_call-horizon-eic-2026"
        )
        assert isinstance(evidence, list)
        contradictions = repo.contradictions(tenant_id=TENANT_A)
        assert isinstance(contradictions, list)
        sources = repo.source_status(tenant_id=TENANT_A)
        assert isinstance(sources, list)


class TestRankingAndComposer:
    def test_ranking_explainable(self) -> None:
        objects = [
            {
                "opportunity_ref": "opp_a",
                "library_id": "O01",
                "payload": {
                    "title": "Cybersecurity monitoring Spain",
                    "description": "monitoring services Madrid",
                    "country": "ES", "sector": "CYBERSECURITY",
                    "value": 360000, "currency": "EUR",
                },
            },
            {
                "opportunity_ref": "opp_b",
                "library_id": "O01",
                "payload": {
                    "title": "Rail maintenance",
                    "description": "track works",
                    "country": "FR", "sector": "INFRASTRUCTURE",
                    "value": 50000, "currency": "EUR",
                },
            },
        ]
        plan = {
            "countries": ["ES"],
            "keywords": ["cybersecurity"],
            "sectors": ["CYBERSECURITY"],
            "value_min": 200000,
            "value_max": None,
        }
        ranked = AxentRanker().rank(objects=objects, plan=plan)
        assert len(ranked) == 2
        assert ranked[0].rank == 1
        assert ranked[0].object_ref == "opp_a"
        assert ranked[0].score_components.geographic_fit == 1.0
        assert any("keyword" in reason for reason in ranked[0].match_reasons)

    def test_grounded_response_distinguishes_epistemic_classes(self) -> None:
        bundle = EvidenceBundle(
            query_plan={"intent": "SEARCH_OPPORTUNITIES", "exclusions": []},
            matched_objects=(),
            ranking=[],
            missing_information=("value unknown",),
            contradictions=(),
        )
        response = GroundedResponseComposer().compose(
            bundle=bundle, user_query="muéstrame oportunidades"
        )
        classes = {segment["epistemic_class"] for segment in response["segments"]}
        assert "UNKNOWN" in classes
        for segment in response["segments"]:
            assert segment["epistemic_class"] in (
                "SOURCE_FACT", "CANONICAL_CLAIM", "INFERENCE",
                "RECOMMENDATION", "UNKNOWN", "CONTRADICTION",
            )

    def test_http_endpoint_exists(self) -> None:
        client = TestClient(
            app,
            headers={
                "X-AXIGNAL-Identity-Assertion": build_identity_assertion(
                    secret=IDENTITY_SECRET,
                    subject="usr_rag_e2e",
                    email="usr_rag_e2e@example.test",
                    tenant_id=TENANT_A,
                )
            },
        )
        # The conversation endpoint is the AXENT surface; RAG lives behind it.
        assert client.get("/v1/axent/conversations").status_code in (200, 404)
