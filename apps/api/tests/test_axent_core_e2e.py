"""AXENT core persistence E2E over PostgreSQL (Mandato AXENT — 6.1).

Conversations, messages + append-only citations, verified facts, typed
tool invocations, action ledger, confirmations (with expiry), feedback.
Tenant isolation, restart-equivalence, append-only guards.
"""

from __future__ import annotations

import os
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from axignal_api.application import app
from axignal_api.axent_core_repository import AxentCoreRepository, sha256_ref
from axignal_api.identity import build_identity_assertion

TENANT_A = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
TENANT_B = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
IDENTITY_SECRET = "local-dev-identity-assertion-secret-32-bytes"
DSN = "postgresql://axignal:axignal-local@localhost:5432/axignal"

pytestmark = pytest.mark.skipif(
    not os.environ.get("AXIGNAL_INTEGRATION_TESTS"),
    reason="AXENT core E2E needs a live PostgreSQL",
)


@pytest.fixture(autouse=True)
def _set_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AXIGNAL_DATABASE_URL", DSN)
    monkeypatch.setenv("AXIGNAL_IDENTITY_ASSERTION_SECRET", IDENTITY_SECRET)


def _client(tenant_id: UUID, subject: str = "usr_axent") -> TestClient:
    return TestClient(
        app,
        headers={
            "X-AXIGNAL-Identity-Assertion": build_identity_assertion(
                secret=IDENTITY_SECRET,
                subject=subject,
                email=f"{subject}@example.test",
                tenant_id=tenant_id,
            )
        },
    )


def _reset() -> None:
    import psycopg

    # TRUNCATE bypasses row-level append-only triggers.
    with psycopg.connect(DSN) as conn, conn.cursor() as cursor:
        cursor.execute("SET session_replication_role = replica")
        cursor.execute(
            "TRUNCATE tenant_private.axent_evaluations, "
            "tenant_private.axent_feedback, tenant_private.axent_notifications, "
            "tenant_private.axent_confirmations, tenant_private.axent_actions, "
            "tenant_private.axent_tool_invocations, "
            "tenant_private.axent_verified_facts, "
            "tenant_private.axent_message_citations, "
            "tenant_private.axent_messages, "
            "tenant_private.axent_conversations CASCADE"
        )
        cursor.execute("SET session_replication_role = origin")
        conn.commit()


class TestAxentCorePersistence:
    def test_full_core_lifecycle(self) -> None:
        _reset()
        repo = AxentCoreRepository(DSN)
        subject = "usr_axent_core"

        # 1. Conversation persisted.
        conversation = repo.create_conversation(
            tenant_id=TENANT_A, identity_subject=subject,
            title="Cybersecurity tenders ES/PT",
        )
        conversation_id = conversation["conversation_id"]

        # 2. Messages with append-only citations.
        repo.append_message(
            tenant_id=TENANT_A, conversation_id=conversation_id,
            message_role="USER", content="Muéstrame licitaciones de ciberseguridad",
        )
        assistant_message = repo.append_message(
            tenant_id=TENANT_A, conversation_id=conversation_id,
            message_role="ASSISTANT",
            content="Encontré 2 oportunidades con evidencia admitida.",
            citations=[
                {"authority_type": "OPPORTUNITY",
                 "authority_id": "opp_ted_123456_2026",
                 "authority_version": "v2",
                 "excerpt": "Cybersecurity monitoring services"},
                {"authority_type": "CANONICAL_CLAIM",
                 "authority_id": "cc_001",
                 "authority_version": "v1",
                 "excerpt": "published 2026-01-15"},
            ],
        )
        messages = repo.get_messages(
            tenant_id=TENANT_A, conversation_id=conversation_id
        )
        assert len(messages) == 2
        citations = repo.get_citations(
            tenant_id=TENANT_A, message_id=assistant_message["message_id"]
        )
        assert len(citations) == 2
        assert {c["authority_id"] for c in citations} == {
            "opp_ted_123456_2026", "cc_001"
        }

        # 3. Citations are append-only: UPDATE must be rejected by trigger.
        import psycopg

        with pytest.raises(psycopg.errors.RaiseException), psycopg.connect(
            DSN
        ) as conn, conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE tenant_private.axent_message_citations
                SET authority_id = 'hacked'
                WHERE tenant_id = %s AND message_id = %s
                """,
                (TENANT_A, assistant_message["message_id"]),
            )

        # 4. Verified facts.
        repo.record_verified_fact(
            tenant_id=TENANT_A, conversation_id=conversation_id,
            fact_type="SOURCE_FACT", subject_type="OPPORTUNITY",
            subject_id="opp_ted_123456_2026",
            value={"value": "360000", "currency": "EUR"},
        )
        repo.record_verified_fact(
            tenant_id=TENANT_A, conversation_id=conversation_id,
            fact_type="INFERENCE", subject_type="OPPORTUNITY",
            subject_id="opp_ted_123456_2026",
            value={"note": "fits cybersecurity sector"},
        )

        # 5. Typed tool invocation -> action ledger.
        invocation = repo.create_invocation(
            tenant_id=TENANT_A, conversation_id=conversation_id,
            tool_name="create_pursuit", tool_version="v1",
            parameters={"opportunity_ref": "opp_ted_123456_2026",
                        "decision": "BID"},
            risk_class="EXPLICIT_CONFIRMATION",
        )
        assert invocation["risk_class"] == "EXPLICIT_CONFIRMATION"

        # 6. Confirmation with expiry.
        confirmation = repo.create_confirmation(
            tenant_id=TENANT_A, conversation_id=conversation_id,
            invocation_id=invocation["invocation_id"],
            action_type="create_pursuit",
            parameters={"opportunity_ref": "opp_ted_123456_2026"},
            before_state_hash=sha256_ref({"pursuits": 0}),
        )
        resolved = repo.resolve_confirmation(
            tenant_id=TENANT_A, confirmation_id=confirmation["confirmation_id"],
            decision="CONFIRMED", confirmed_by=subject,
        )
        assert resolved["state"] == "CONFIRMED"

        # 7. Execution receipt.
        repo.complete_invocation(
            tenant_id=TENANT_A, invocation_id=invocation["invocation_id"],
            state="EXECUTED",
            before_state_hash=sha256_ref({"pursuits": 0}),
            after_state_hash=sha256_ref({"pursuits": 1}),
        )
        repo.record_action(
            tenant_id=TENANT_A, conversation_id=conversation_id,
            invocation_id=invocation["invocation_id"],
            action_type="create_pursuit", object_type="PURSUIT",
            object_ref="prs_ted_123456_2026",
            parameters={"decision": "BID"},
            receipt={"pursuit_ref": "prs_ted_123456_2026", "state": "QUALIFYING"},
            outcome="SUCCESS", actor_subject=subject,
        )
        actions = repo.list_actions(
            tenant_id=TENANT_A, conversation_id=conversation_id
        )
        assert len(actions) == 1
        assert actions[0]["receipt_json"]["state"] == "QUALIFYING"

        # 8. Action ledger is append-only.
        with pytest.raises(psycopg.errors.RaiseException), psycopg.connect(
            DSN
        ) as conn, conn.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM tenant_private.axent_actions
                WHERE tenant_id = %s
                """,
                (TENANT_A,),
            )

        # 9. Notification + feedback.
        repo.create_notification(
            tenant_id=TENANT_A, recipient_subject=subject,
            notification_type="ACTION_RECEIPT",
            title="Pursuit created",
            body="prs_ted_123456_2026 está en QUALIFYING",
            route_path="/opportunity-intelligence/pursuits",
        )
        notifications = repo.list_notifications(
            tenant_id=TENANT_A, recipient_subject=subject
        )
        assert len(notifications) == 1
        repo.record_feedback(
            tenant_id=TENANT_A, message_id=assistant_message["message_id"],
            rating=5, comment="claro y citado",
        )

        # 10. Restart-equivalence: new repository instance sees everything.
        fresh = AxentCoreRepository(DSN)
        assert len(fresh.list_conversations(tenant_id=TENANT_A, subject=subject)) == 1
        assert len(fresh.get_messages(tenant_id=TENANT_A, conversation_id=conversation_id)) == 2
        assert len(fresh.list_actions(tenant_id=TENANT_A, conversation_id=conversation_id)) == 1

        # 11. Tenant isolation: B sees nothing.
        b_repo = AxentCoreRepository(DSN)
        assert b_repo.list_conversations(tenant_id=TENANT_B) == []
        assert b_repo.get_messages(
            tenant_id=TENANT_B, conversation_id=conversation_id
        ) == []

    def test_confirmation_expiry(self) -> None:
        _reset()
        repo = AxentCoreRepository(DSN)
        conversation = repo.create_conversation(
            tenant_id=TENANT_A, identity_subject="usr_axent_expiry",
            title="expiry test",
        )
        invocation = repo.create_invocation(
            tenant_id=TENANT_A, conversation_id=conversation["conversation_id"],
            tool_name="close_pursuit", tool_version="v1",
            parameters={"pursuit_ref": "prs_x"},
            risk_class="EXPLICIT_CONFIRMATION",
        )
        confirmation = repo.create_confirmation(
            tenant_id=TENANT_A,
            conversation_id=conversation["conversation_id"],
            invocation_id=invocation["invocation_id"],
            action_type="close_pursuit",
            parameters={"pursuit_ref": "prs_x"},
            before_state_hash=sha256_ref({"state": "QUALIFYING"}),
            ttl_seconds=-10,
        )
        import psycopg

        with psycopg.connect(DSN) as conn, conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE tenant_private.axent_confirmations
                SET expires_at = now() - interval '1 minute'
                WHERE confirmation_id = %s
                """,
                (confirmation["confirmation_id"],),
            )
            conn.commit()
        resolved = repo.resolve_confirmation(
            tenant_id=TENANT_A,
            confirmation_id=confirmation["confirmation_id"],
            decision="CONFIRMED", confirmed_by="usr_axent_expiry",
        )
        assert resolved["state"] == "EXPIRED"
