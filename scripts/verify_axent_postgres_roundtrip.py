from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from uuid import UUID

import psycopg

from axignal_api.axent_notification_repository import AxentNotificationRepository
from axignal_api.axent_repository import AxentRepository

TENANT_A = UUID("a0000000-0000-4000-8000-000000000001")
TENANT_B = UUID("b0000000-0000-4000-8000-000000000002")
SUBJECT = "usr_axent_e2e_customer"
HUMAN = "usr_axent_e2e_reviewer"


def create_roundtrip(database_url: str, state_path: Path) -> None:
    repository = AxentRepository(database_url)
    conversation = repository.create_conversation(
        tenant_id=TENANT_A,
        opened_by_subject=SUBJECT,
        language="es",
    )
    conversation_id = conversation["conversation_id"]
    repository.append_message(
        tenant_id=TENANT_A,
        conversation_id=conversation_id,
        author_type="USER",
        author_subject=SUBJECT,
        content="Necesito ayuda con una exportación fallida.",
    )
    repository.append_message(
        tenant_id=TENANT_A,
        conversation_id=conversation_id,
        author_type="AXENT",
        author_subject=None,
        content="He abierto un caso para intervención humana.",
        model_id="deterministic-support-router/v1",
        prompt_policy_version="axent-read-only/v1",
    )
    support_case = repository.create_case(
        tenant_id=TENANT_A,
        conversation_id=conversation_id,
        case_type="EXPORT",
        severity="S2",
        service_area="subscriber_export",
        customer_impact="The customer cannot retrieve the requested export.",
    )
    case_id = support_case["case_id"]
    repository.transition_case(
        tenant_id=TENANT_A,
        case_id=case_id,
        actor_subject=HUMAN,
        transition="ACKNOWLEDGE",
    )
    repository.transition_case(
        tenant_id=TENANT_A,
        case_id=case_id,
        actor_subject=HUMAN,
        transition="ASSIGN",
    )
    resolved = repository.transition_case(
        tenant_id=TENANT_A,
        case_id=case_id,
        actor_subject=HUMAN,
        transition="RESOLVE",
        resolution="The export was regenerated and verified against its checksum.",
    )
    assert resolved["status"] == "RESOLVED"

    notifications = AxentNotificationRepository(database_url).list_notifications(
        tenant_id=TENANT_A,
        recipient_subject=SUBJECT,
    )
    assert len(notifications) == 1
    notification = notifications[0]
    assert notification["notification_type"] == "CASE_RESOLVED"
    delivered = AxentNotificationRepository(database_url).acknowledge_notification(
        tenant_id=TENANT_A,
        recipient_subject=SUBJECT,
        notification_id=notification["notification_id"],
    )
    assert delivered["delivery_state"] == "DELIVERED"

    assert repository.get_conversation(
        tenant_id=TENANT_B,
        conversation_id=conversation_id,
    ) is None

    state_path.write_text(
        json.dumps(
            {
                "tenant_id": str(TENANT_A),
                "conversation_id": str(conversation_id),
                "case_id": str(case_id),
                "notification_id": str(notification["notification_id"]),
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    print("AXENT_POSTGRES_SUPPORT_ROUND_TRIP_PASS")


def verify_after_restart(database_url: str, state_path: Path) -> None:
    state = json.loads(state_path.read_text(encoding="utf-8"))
    tenant_id = UUID(state["tenant_id"])
    conversation_id = UUID(state["conversation_id"])
    case_id = UUID(state["case_id"])
    notification_id = UUID(state["notification_id"])

    conversation = AxentRepository(database_url).get_conversation(
        tenant_id=tenant_id,
        conversation_id=conversation_id,
    )
    assert conversation is not None
    assert conversation["status"] == "RESOLVED"
    assert len(conversation["messages"]) == 2

    notifications = AxentNotificationRepository(database_url).list_notifications(
        tenant_id=tenant_id,
        recipient_subject=SUBJECT,
    )
    persisted = next(
        item for item in notifications if item["notification_id"] == notification_id
    )
    assert persisted["delivery_state"] == "DELIVERED"

    with psycopg.connect(database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SET ROLE axignal_app")
            cursor.execute("SELECT set_config('app.tenant_id', %s, true)", (str(tenant_id),))
            cursor.execute(
                """
                SELECT status, resolution
                FROM tenant_private.support_cases
                WHERE tenant_id = %s AND case_id = %s
                """,
                (tenant_id, case_id),
            )
            row = cursor.fetchone()
            assert row == (
                "RESOLVED",
                "The export was regenerated and verified against its checksum.",
            )
            cursor.execute(
                """
                SELECT event_type
                FROM tenant_private.support_case_events
                WHERE tenant_id = %s AND case_id = %s
                ORDER BY created_at, event_id
                """,
                (tenant_id, case_id),
            )
            assert [item[0] for item in cursor.fetchall()] == [
                "OPENED",
                "ACKNOWLEDGED",
                "ASSIGNED",
                "RESOLVED",
            ]

    print("AXENT_RESTART_PERSISTENCE_PASS")
    print("AXENT_FRESH_PROCESS_VERIFICATION_PASS")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("create", "verify"))
    parser.add_argument("--state", default="axent-postgres-state.json")
    args = parser.parse_args()
    database_url = os.environ.get(
        "AXIGNAL_DATABASE_URL",
        "postgresql://axignal:axignal@127.0.0.1:5432/axignal",
    )
    state_path = Path(args.state)
    if args.mode == "create":
        create_roundtrip(database_url, state_path)
    else:
        verify_after_restart(database_url, state_path)


if __name__ == "__main__":
    main()
