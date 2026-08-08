"""AXENT customer support + incident deduplication + governed knowledge
(Mandato AXENT — secciones 12-13).

Gates: AX_AXENT_CUSTOMER_SUPPORT_E2E, AX_AXENT_HUMAN_ESCALATION_ROUND_TRIP,
AX_AXENT_GOVERNED_KNOWLEDGE_E2E, AX_AXENT_INCIDENT_DEDUPLICATION_E2E.
"""

from __future__ import annotations

import os
from uuid import UUID

import pytest

from axignal_api.axent_core_repository import AxentCoreRepository
from axignal_api.axent_support_repository import AxentSupportRepository, sha256_ref

TENANT_A = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
TENANT_B = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
DSN = "postgresql://axignal:axignal-local@localhost:5432/axignal"

pytestmark = pytest.mark.skipif(
    not os.environ.get("AXIGNAL_INTEGRATION_TESTS"),
    reason="AXENT support E2E needs a live PostgreSQL",
)


def _reset() -> None:
    import psycopg

    with psycopg.connect(DSN) as conn, conn.cursor() as cursor:
        cursor.execute("SET session_replication_role = replica")
        cursor.execute(
            "TRUNCATE tenant_private.support_feedback, "
            "tenant_private.support_notifications, "
            "tenant_private.support_incident_links, "
            "tenant_private.support_incidents, "
            "tenant_private.support_case_events, "
            "tenant_private.support_cases, "
            "tenant_private.axent_conversations CASCADE"
        )
        cursor.execute(
            "TRUNCATE axignal_global.knowledge_chunks, "
            "axignal_global.knowledge_revisions, "
            "axignal_global.knowledge_documents CASCADE"
        )
        cursor.execute("SET session_replication_role = origin")
        conn.commit()


class TestCustomerSupport:
    def test_full_support_flow(self) -> None:
        _reset()
        repo = AxentSupportRepository(DSN)
        core = AxentCoreRepository(DSN)
        subject = "usr_support_customer"

        conversation = core.create_conversation(
            tenant_id=TENANT_A, identity_subject=subject,
            title="No veo las búsquedas guardadas",
        )

        # 1. Customer query -> self-service fails -> case.
        case = repo.create_case(
            tenant_id=TENANT_A,
            conversation_id=conversation["conversation_id"],
            subject="No veo las búsquedas guardadas",
            description="Guardé una búsqueda y no aparece en el panel.",
            severity="S3", opened_by=subject,
        )
        assert case["severity"] == "S3"

        # 2. Investigate + await customer (human console actions).
        repo.transition_case(
            tenant_id=TENANT_A, case_ref=case["case_ref"],
            new_status="INVESTIGATING", actor_subject="human_support",
        )
        repo.transition_case(
            tenant_id=TENANT_A, case_ref=case["case_ref"],
            new_status="AWAITING_CUSTOMER", actor_subject="human_support",
        )

        # 3. Resolve with a resolution code.
        resolved = repo.transition_case(
            tenant_id=TENANT_A, case_ref=case["case_ref"],
            new_status="RESOLVED", actor_subject="human_support",
            resolution_code="SEARCH_WAS_FILTERED",
        )
        assert resolved["status"] == "RESOLVED"

        # 4. Event trail is persisted.
        events = repo.case_events(tenant_id=TENANT_A, case_ref=case["case_ref"])
        assert len(events) >= 4
        assert {e["event_type"] for e in events} >= {"OPENED", "STATUS_CHANGED"}

        # 5. Notification + feedback.
        repo.notify_case_update(
            tenant_id=TENANT_A, case_ref=case["case_ref"],
            recipient_subject=subject, notification_type="CASE_RESOLVED",
            body="Tu caso se resolvió: SEARCH_WAS_FILTERED.",
        )
        repo.record_case_feedback(
            tenant_id=TENANT_A, case_ref=case["case_ref"],
            rating=5, comment="resuelto rápido",
        )

        # 6. Human console sees the case (tenant-scoped).
        cases = repo.list_cases(tenant_id=TENANT_A)
        assert len(cases) == 1
        assert cases[0]["status"] == "RESOLVED"
        assert repo.list_cases(tenant_id=TENANT_B) == []

        # 7. Restart equivalence.
        fresh = AxentSupportRepository(DSN)
        assert len(fresh.list_cases(tenant_id=TENANT_A)) == 1

    def test_incident_deduplication(self) -> None:
        _reset()
        repo = AxentSupportRepository(DSN)
        core = AxentCoreRepository(DSN)

        # Two customers hit the same problem -> same fingerprint -> one incident.
        fingerprints = []
        for index, (tenant_id, subject) in enumerate(
            [(TENANT_A, "usr_cust_one"), (TENANT_A, "usr_cust_two")]
        ):
            conversation = core.create_conversation(
                tenant_id=tenant_id, identity_subject=subject,
                title=f"Fallo al exportar {index}",
            )
            case = repo.create_case(
                tenant_id=tenant_id,
                conversation_id=conversation["conversation_id"],
                subject="Fallo al exportar PDF",
                description="La exportación a PDF falla con error 500.",
                severity="S2", opened_by=subject,
            )
            fingerprint = sha256_ref(
                {"error": "export_pdf_500", "component": "export"}
            )
            fingerprints.append(fingerprint)
            incident = repo.upsert_incident(
                tenant_id=tenant_id, fingerprint=fingerprint,
                severity="S2", summary="Export PDF 500",
            )
            repo.link_case_to_incident(
                tenant_id=tenant_id, case_ref=case["case_ref"],
                incident_id=incident["incident_id"],
            )

        # Both cases linked to the SAME incident (deduplicated).
        incidents = repo.list_incidents(tenant_id=TENANT_A)
        assert len(incidents) == 1
        assert incidents[0]["fingerprint"] == fingerprints[0]

        # A different problem -> a second incident.
        other_case_conversation = core.create_conversation(
            tenant_id=TENANT_A, identity_subject="usr_cust_one",
            title="Problema distinto",
        )
        other_case = repo.create_case(
            tenant_id=TENANT_A,
            conversation_id=other_case_conversation["conversation_id"],
            subject="Login lento",
            description="El login tarda mucho.",
            severity="S3", opened_by="usr_cust_one",
        )
        other_incident = repo.upsert_incident(
            tenant_id=TENANT_A,
            fingerprint=sha256_ref({"error": "login_slow"}),
            severity="S3", summary="Login slow",
        )
        repo.link_case_to_incident(
            tenant_id=TENANT_A, case_ref=other_case["case_ref"],
            incident_id=other_incident["incident_id"],
        )
        assert len(repo.list_incidents(tenant_id=TENANT_A)) == 2

    def test_governed_knowledge(self) -> None:
        _reset()
        repo = AxentSupportRepository(DSN)

        # A resolved case generates a CANDIDATE, never active automatically.
        candidate = repo.create_knowledge_candidate(
            title="Fallo export PDF: limpiar caché",
            content="Cuando la exportación a PDF falla con 500, limpiar la "
                    "caché del tenant y reintentar. Si persiste, revisar "
                    "el bucket de documentos.",
            source_authority="HUMAN_SUPPORT_001",
            owner_subject="human_support",
        )
        assert candidate["status"] == "CANDIDATE"

        # Candidates are NOT retrieval-eligible (same term that WILL match
        # after approval — proving governance, not token luck).
        assert repo.search_knowledge(query="caché") == []

        # Human approval makes it effective.
        approved = repo.approve_knowledge_revision(
            revision_id=candidate["revision_id"], reviewed_by="human_reviewer"
        )
        assert approved["status"] == "APPROVED"
        assert approved["effective_at"] is not None

        # Now it is retrieval-eligible.
        hits = repo.search_knowledge(query="caché", limit=5)
        assert len(hits) >= 1
        assert "caché" in hits[0]["content"]

        # Revisions are append-only: UPDATE rejected by trigger.
        import psycopg

        with pytest.raises(psycopg.errors.RaiseException), psycopg.connect(
            DSN
        ) as conn, conn.cursor() as cursor:
            cursor.execute(
                "UPDATE axignal_global.knowledge_revisions "
                "SET content = 'hacked' WHERE revision_id = %s",
                (candidate["revision_id"],),
            )

        # Tenant isolation: B has no cases.
        assert AxentSupportRepository(DSN).list_cases(tenant_id=TENANT_B) == []

    def test_human_escalation_round_trip(self) -> None:
        _reset()
        repo = AxentSupportRepository(DSN)
        core = AxentCoreRepository(DSN)

        conversation = core.create_conversation(
            tenant_id=TENANT_A, identity_subject="usr_esc",
            title="Escalado",
        )
        case = repo.create_case(
            tenant_id=TENANT_A,
            conversation_id=conversation["conversation_id"],
            subject="Billing discrepancy",
            description="Se cobró dos veces.",
            severity="S1", opened_by="usr_esc",
        )
        escalated = repo.transition_case(
            tenant_id=TENANT_A, case_ref=case["case_ref"],
            new_status="ESCALATED", actor_subject="human_agent",
        )
        assert escalated["status"] == "ESCALATED"

        # Reopened after customer says it still fails.
        reopened = repo.transition_case(
            tenant_id=TENANT_A, case_ref=case["case_ref"],
            new_status="REOPENED", actor_subject="human_agent",
        )
        assert reopened["status"] == "REOPENED"

        events = repo.case_events(tenant_id=TENANT_A, case_ref=case["case_ref"])
        statuses = [e["payload"].get("new_status") for e in events
                    if e["event_type"] == "STATUS_CHANGED"]
        assert "ESCALATED" in statuses
        assert "REOPENED" in statuses
