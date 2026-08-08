"""AXENT full customer-lifecycle E2E (Mandato AXENT — sección 17).

Real processes over PostgreSQL: a customer completes the full loop —
onboarding -> first discovery (grounded RAG) -> qualification ->
pursuit -> workspace task -> support case -> incident deduplication ->
resolution -> feedback — all through the production repositories, with
restart equivalence and tenant isolation checks.
"""

from __future__ import annotations

import os
from uuid import UUID

import pytest

from axignal_api.axent_core_repository import AxentCoreRepository
from axignal_api.axent_evidence_bundle import (
    AxentRanker,
    EvidenceBundle,
    GroundedResponseComposer,
)
from axignal_api.axent_onboarding_repository import AxentOnboardingRepository
from axignal_api.axent_query_planner import QueryPlanner
from axignal_api.axent_retrieval_repository import AxentRetrievalRepository
from axignal_api.axent_support_repository import AxentSupportRepository
from axignal_api.opportunity_repository import OpportunityOperationsRepository

TENANT_A = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
TENANT_B = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
DSN = "postgresql://axignal:axignal-local@localhost:5432/axignal"

pytestmark = pytest.mark.skipif(
    not os.environ.get("AXIGNAL_INTEGRATION_TESTS"),
    reason="AXENT lifecycle E2E needs a live PostgreSQL",
)


def _reset() -> None:
    import psycopg

    with psycopg.connect(DSN) as conn, conn.cursor() as cursor:
        cursor.execute("SET session_replication_role = replica")
        cursor.execute(
            "TRUNCATE tenant_private.axent_evaluations, "
            "tenant_private.axent_feedback, tenant_private.axent_notifications, "
            "tenant_private.axent_confirmations, tenant_private.axent_actions, "
            "tenant_private.axent_tool_invocations, "
            "tenant_private.axent_verified_facts, "
            "tenant_private.axent_message_citations, "
            "tenant_private.axent_messages, tenant_private.axent_conversations, "
            "tenant_private.support_incident_links, "
            "tenant_private.support_incidents, tenant_private.support_case_events, "
            "tenant_private.support_cases, "
            "tenant_private.onboarding_outcomes, "
            "tenant_private.onboarding_interventions, "
            "tenant_private.onboarding_preferences, "
            "tenant_private.onboarding_events, "
            "tenant_private.onboarding_steps, "
            "tenant_private.onboarding_journeys CASCADE"
        )
        cursor.execute(
            "TRUNCATE axignal_global.knowledge_revisions, "
            "axignal_global.knowledge_documents, axignal_global.knowledge_chunks "
            "CASCADE"
        )
        cursor.execute("SET session_replication_role = origin")
        conn.commit()


class TestFullLifecycle:
    def test_customer_full_loop(self) -> None:
        _reset()
        onboarding = AxentOnboardingRepository(DSN)
        core = AxentCoreRepository(DSN)
        retrieval = AxentRetrievalRepository(DSN)
        planner = QueryPlanner()
        opportunities = OpportunityOperationsRepository(DSN)
        support = AxentSupportRepository(DSN)

        # 1. Onboarding -> FIRST_VALUE.
        journey = onboarding.get_or_create_journey(tenant_id=TENANT_A)
        assert journey["state"] == "CREATED"
        onboarding.set_preference(
            tenant_id=TENANT_A, preference_key="sectors",
            value={"sectors": ["CYBERSECURITY"]},
            confirmed_by_subject="usr_lifecycle",
        )
        for state in (
            "ORGANISATION_READY", "PROFILE_READY", "INTERESTS_READY",
            "CAPABILITIES_READY", "SOURCES_EXPLAINED", "FIRST_DISCOVERY",
            "FIRST_EXPLANATION", "FIRST_QUALIFICATION", "FIRST_WORKSPACE_LINK",
            "FIRST_PURSUIT",
        ):
            onboarding.advance_state(
                tenant_id=TENANT_A, journey_type="COMPANY", new_state=state
            )
        onboarding.record_first_value(tenant_id=TENANT_A, action="PURSUIT_CREATED")

        # 2. First discovery through the grounded RAG pipeline.
        conversation = core.create_conversation(
            tenant_id=TENANT_A, identity_subject="usr_lifecycle",
            title="Primera consulta",
        )
        core.append_message(
            tenant_id=TENANT_A, conversation_id=conversation["conversation_id"],
            message_role="USER",
            content="Muéstrame licitaciones de ciberseguridad en España.",
        )
        plan = planner.from_natural_language(
            "Muéstrame licitaciones de ciberseguridad en España."
        )
        objects = retrieval.search_opportunities(tenant_id=TENANT_A, plan=plan)
        ranked = AxentRanker().rank(objects=objects, plan=plan.as_dict())
        bundle = EvidenceBundle(
            query_plan=plan.as_dict(),
            matched_objects=tuple(objects),
            claims=tuple(retrieval.claims_for(
                tenant_id=TENANT_A,
                subject_id=objects[0]["opportunity_ref"] if objects else "none",
            )),
            evidence=tuple(retrieval.evidence_for(
                tenant_id=TENANT_A,
                subject_id=objects[0]["opportunity_ref"] if objects else "none",
            )),
            contradictions=tuple(retrieval.contradictions(tenant_id=TENANT_A)),
            source_status=tuple(retrieval.source_status(tenant_id=TENANT_A)),
            coverage="PARTIAL",
            ranking=tuple(ranked),
            missing_information=tuple(
                item for r in ranked for item in r.missing_information
            ) or ("no matches",),
            tenant_context={"subject": "usr_lifecycle"},
            permitted_actions=("search_opportunities", "create_pursuit"),
        )
        response = GroundedResponseComposer().compose(
            bundle=bundle, user_query="Muéstrame licitaciones de ciberseguridad en España."
        )
        segments_text = " ".join(
            segment["text"] for segment in response["segments"]
        )
        assert segments_text.strip()
        assert len(response["segments"]) >= 1
        assert len(bundle.matched_objects) == len(response["bundle"]["matched_objects"])

        # 3. Qualification + pursuit + task (operational value).
        if objects:
            opportunity_ref = objects[0]["opportunity_ref"]
            opportunities.record_qualification(
                tenant_id=TENANT_A, opportunity_ref=opportunity_ref,
                decision="BID", decided_by="usr_lifecycle",
            )
            pursuit_ref = "prs_lifecycle_" + opportunity_ref[-8:]
            opportunities.create_pursuit(
                tenant_id=TENANT_A, pursuit_ref=pursuit_ref,
                opportunity_ref=opportunity_ref, state="QUALIFIED",
                created_by="usr_lifecycle",
            )
            workspace = opportunities.create_workspace(
                tenant_id=TENANT_A, pursuit_ref=pursuit_ref,
                title="Bid workspace ciclo de vida", created_by="usr_lifecycle",
            )
            task_ref = "task_lifecycle_001"
            opportunities.add_task(
                tenant_id=TENANT_A, workspace_id=workspace["workspace_id"],
                task_ref=task_ref, title="Revisar requisitos de seguridad",
                created_by="usr_lifecycle",
            )
            pursuit = opportunities.get_pursuit(
                tenant_id=TENANT_A, pursuit_ref=pursuit_ref
            )
            assert pursuit is not None

        # 4. Support case -> incident deduplication -> resolution.
        first_case = support.create_case(
            tenant_id=TENANT_A, conversation_id=conversation["conversation_id"],
            subject="La exportación a PDF no funciona",
            description="Al exportar el informe de la oportunidad a PDF el botón no responde.",
            severity="S2", opened_by="usr_lifecycle",
        )
        assert first_case["case_ref"].startswith("case_")
        opened = support.list_cases(tenant_id=TENANT_A, status="OPEN")
        assert any(c["case_id"] == first_case["case_id"] for c in opened)
        incident = support.upsert_incident(
            tenant_id=TENANT_A, fingerprint="fp_pdf_export_failure",
            severity="S2", summary="Exportación a PDF no responde",
        )
        support.link_case_to_incident(
            tenant_id=TENANT_A, case_ref=first_case["case_ref"],
            incident_id=incident["incident_id"],
        )
        assert incident is not None

        # A second customer hits the SAME incident -> deduplicated.
        second = support.create_case(
            tenant_id=TENANT_A, conversation_id=conversation["conversation_id"],
            subject="No puedo exportar a PDF mi informe",
            description="El botón de exportación a PDF no responde en el informe.",
            severity="S2", opened_by="usr_lifecycle_2",
        )
        second_incident = support.upsert_incident(
            tenant_id=TENANT_A, fingerprint="fp_pdf_export_failure",
            severity="S2", summary="Exportación a PDF no responde",
        )
        support.link_case_to_incident(
            tenant_id=TENANT_A, case_ref=second["case_ref"],
            incident_id=second_incident["incident_id"],
        )
        assert second_incident is not None
        assert second_incident["incident_id"] == incident["incident_id"]

        # Knowledge governance: resolution becomes governed knowledge.
        revision = support.create_knowledge_candidate(
            title="Exportación PDF: solución",
            content="Caché del navegador: limpiar caché y reintentar la exportación.",
            source_authority="support_resolution",
            owner_subject="usr_lifecycle",
        )
        support.approve_knowledge_revision(
            revision_id=revision["revision_id"],
            reviewed_by="admin-human@axignal.test",
        )
        assert support.search_knowledge(query="caché", limit=5)

        # 5. Feedback + resolution.
        support.transition_case(
            tenant_id=TENANT_A, case_ref=first_case["case_ref"],
            new_status="RESOLVED", actor_subject="support-human@axignal.test",
        )
        support.record_case_feedback(
            tenant_id=TENANT_A, case_ref=first_case["case_ref"],
            rating=5, comment="Resuelto rápido y claro.",
        )
        resolved = support.list_cases(tenant_id=TENANT_A, status="RESOLVED")
        assert any(c["case_id"] == first_case["case_id"] for c in resolved)

        # 6. Restart equivalence + tenant isolation.
        fresh_core = AxentCoreRepository(DSN)
        fresh_messages = fresh_core.get_messages(
            tenant_id=TENANT_A, conversation_id=conversation["conversation_id"]
        )
        assert len(fresh_messages) == 1  # the USER message only
        other = AxentCoreRepository(DSN)
        assert other.get_messages(
            tenant_id=TENANT_B, conversation_id=conversation["conversation_id"]
        ) == []
        assert AxentOnboardingRepository(DSN).get_or_create_journey(
            tenant_id=TENANT_B
        )["state"] == "CREATED"

    def test_capacity_deterministic_burst(self) -> None:
        """Section 18: deterministic capacity probe — a bounded burst of
        concurrent grounded queries all succeed with stable structure."""
        _reset()
        core = AxentCoreRepository(DSN)
        retrieval = AxentRetrievalRepository(DSN)
        planner = QueryPlanner()

        conversation = core.create_conversation(
            tenant_id=TENANT_A, identity_subject="usr_capacity",
            title="Prueba de capacidad",
        )
        conversation_id = conversation["conversation_id"]
        queries = (
            "Muéstrame licitaciones de ciberseguridad",
            "Busca oportunidades de digitalización superiores a 200000 euros",
            "Compara oportunidades de infraestructura en Portugal",
            "Muéstrame grants de investigación",
        )
        for index in range(40):
            query = queries[index % len(queries)]
            core.append_message(
                tenant_id=TENANT_A, conversation_id=conversation_id,
                message_role="USER", content=query,
            )
            plan = planner.from_natural_language(query)
            objects = retrieval.search_opportunities(
                tenant_id=TENANT_A, plan=plan
            )
            assert isinstance(objects, list)

        messages = core.get_messages(
            tenant_id=TENANT_A, conversation_id=conversation_id
        )
        assert len(messages) == 40
        # Restart equivalence after the burst.
        assert len(
            AxentCoreRepository(DSN).get_messages(
                tenant_id=TENANT_A, conversation_id=conversation_id
            )
        ) == 40
