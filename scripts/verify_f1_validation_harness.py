from __future__ import annotations

import hashlib
import json
import os
from uuid import UUID

import psycopg
from psycopg.rows import dict_row

TENANT_A = UUID("11111111-1111-4111-8111-111111111111")
TENANT_B = UUID("22222222-2222-4222-8222-222222222222")
TASK_ID = "F1-AUTHORITY-001"


def pseudonym(index: int) -> str:
    return "sha256:" + hashlib.sha256(f"participant-{index}".encode()).hexdigest()


def set_tenant(cursor: psycopg.Cursor, tenant_id: UUID) -> None:
    cursor.execute("SELECT set_config('app.tenant_id', %s, false)", (str(tenant_id),))


def start_session(
    connection: psycopg.Connection,
    tenant_id: UUID,
    participant_id_hash: str,
    profile: str = "DOMAIN_EXPERT",
) -> dict:
    with connection.cursor() as cursor:
        set_tenant(cursor, tenant_id)
        cursor.execute(
            "SELECT evaluation.start_validation_session(%s,%s,%s,%s) AS item",
            (tenant_id, participant_id_hash, profile, TASK_ID),
        )
        row = cursor.fetchone()
        assert row is not None
        return row["item"]


def main() -> int:
    admin_dsn = os.environ["AXIGNAL_DATABASE_URL"]
    validation_dsn = os.environ["AXIGNAL_VALIDATION_DATABASE_URL"]

    with psycopg.connect(admin_dsn, row_factory=dict_row) as admin:
        with admin.cursor() as cursor:
            cursor.execute("SELECT count(*) AS count FROM evaluation.validation_tasks")
            assert cursor.fetchone()["count"] == 6
            cursor.execute(
                """
                SELECT
                  has_table_privilege(
                    'axignal_validation_runtime_login',
                    'axignal_global.canonical_claims',
                    'INSERT'
                  ) AS canonical_insert,
                  has_table_privilege(
                    'axignal_validation_runtime_login',
                    'axignal_global.evidence_objects',
                    'UPDATE'
                  ) AS evidence_update,
                  has_table_privilege(
                    'axignal_validation_runtime_login',
                    'evaluation.validation_sessions',
                    'SELECT'
                  ) AS direct_session_read,
                  has_function_privilege(
                    'axignal_validation_runtime_login',
                    'evaluation.start_validation_session(uuid,text,text,text)',
                    'EXECUTE'
                  ) AS start_execute
                """
            )
            assert cursor.fetchone() == {
                "canonical_insert": False,
                "evidence_update": False,
                "direct_session_read": False,
                "start_execute": True,
            }
            cursor.execute(
                """
                SELECT count(*) AS count
                FROM information_schema.columns
                WHERE table_schema = 'evaluation'
                  AND column_name IN ('email','name','full_name','phone')
                """
            )
            assert cursor.fetchone()["count"] == 0

    with psycopg.connect(validation_dsn, row_factory=dict_row) as validation:
        conditions: dict[str, tuple[str, dict]] = {}
        for index in range(1, 100):
            participant = pseudonym(index)
            bundle = start_session(validation, TENANT_A, participant)
            condition = bundle["session"]["condition"]
            conditions.setdefault(condition, (participant, bundle))
            if set(conditions) == {"AXIGNAL", "CONTROL"}:
                break
        assert set(conditions) == {"AXIGNAL", "CONTROL"}

        axignal_participant, axignal_bundle = conditions["AXIGNAL"]
        control_participant, control_bundle = conditions["CONTROL"]
        assert axignal_bundle["task"]["content_hash"] == control_bundle["task"]["content_hash"]
        assert axignal_bundle["task"]["payload"] == control_bundle["task"]["payload"]

        replay = start_session(validation, TENANT_A, axignal_participant)
        assert replay["session"]["validation_session_id"] == axignal_bundle["session"][
            "validation_session_id"
        ]
        assert replay["session"]["condition"] == "AXIGNAL"

        session_id = UUID(axignal_bundle["session"]["validation_session_id"])
        task = axignal_bundle["task"]["payload"]
        with validation.cursor() as cursor:
            set_tenant(cursor, TENANT_A)
            for event_id, event_type in (
                ("task-opened", "TASK_OPENED"),
                ("evidence-opened", "EVIDENCE_INSPECTED"),
            ):
                cursor.execute(
                    """
                    SELECT evaluation.append_validation_event(
                      %s,%s,%s,%s,%s::jsonb
                    ) AS item
                    """,
                    (TENANT_A, session_id, event_type, event_id, json.dumps({})),
                )
            cursor.execute(
                """
                SELECT evaluation.append_validation_event(
                  %s,%s,%s,%s,%s::jsonb
                ) AS item
                """,
                (TENANT_A, session_id, "EVIDENCE_INSPECTED", "evidence-opened", "{}"),
            )
            cursor.execute(
                "SELECT count(*) AS count FROM evaluation.validation_metrics(%s)",
                (TENANT_A,),
            )
            assert cursor.fetchone()["count"] >= 1

            cursor.execute(
                """
                SELECT evaluation.complete_validation_session(
                  %s,%s,%s,%s,%s,%s,%s
                ) AS item
                """,
                (
                    TENANT_A,
                    session_id,
                    task["authority_layer"],
                    task["required_evidence_ids"],
                    task["required_unknowns"],
                    82,
                    task["reference_answer"],
                ),
            )
            completed = cursor.fetchone()["item"]
            assert completed["session"]["state"] == "COMPLETED"
            assert completed["session"]["outcome"] == {
                "confidence": 82,
                "critical_error": False,
                "task_completed": True,
                "unknowns_identified": True,
                "evidence_traceability": True,
                "authority_layer_correct": True,
            }

            cursor.execute(
                """
                SELECT evaluation.complete_validation_session(
                  %s,%s,%s,%s,%s,%s,%s
                ) AS item
                """,
                (
                    TENANT_A,
                    session_id,
                    task["authority_layer"],
                    task["required_evidence_ids"],
                    task["required_unknowns"],
                    82,
                    task["reference_answer"],
                ),
            )
            assert cursor.fetchone()["item"]["session"]["state"] == "COMPLETED"

            set_tenant(cursor, TENANT_B)
            cursor.execute(
                "SELECT evaluation.validation_session_bundle(%s) AS item",
                (session_id,),
            )
            assert cursor.fetchone()["item"] is None

        control_session_id = UUID(control_bundle["session"]["validation_session_id"])
        control_task = control_bundle["task"]["payload"]
        with validation.cursor() as cursor:
            set_tenant(cursor, TENANT_A)
            cursor.execute(
                """
                SELECT evaluation.complete_validation_session(
                  %s,%s,%s,%s,%s,%s,%s
                ) AS item
                """,
                (
                    TENANT_A,
                    control_session_id,
                    control_task["authority_layer"],
                    control_task["required_evidence_ids"],
                    control_task["required_unknowns"],
                    75,
                    control_task["reference_answer"],
                ),
            )
            assert cursor.fetchone()["item"]["session"]["outcome"]["task_completed"]
            cursor.execute(
                "SELECT item FROM evaluation.validation_metrics(%s) AS item",
                (TENANT_A,),
            )
            metrics = [row["item"] for row in cursor.fetchall()]
            assert {item["condition"] for item in metrics} == {"AXIGNAL", "CONTROL"}
            assert all(float(item["task_completion_rate"]) == 1.0 for item in metrics)

    with psycopg.connect(admin_dsn) as admin:
        with admin.cursor() as cursor:
            try:
                cursor.execute(
                    "UPDATE evaluation.validation_events SET payload='{}'::jsonb"
                )
            except psycopg.Error as exc:
                assert "AXIGNAL_VALIDATION_HISTORY_APPEND_ONLY" in str(exc)
                admin.rollback()
            else:
                raise AssertionError("Append-only validation history was mutable")

    print(
        json.dumps(
            {
                "frozen_tasks_validated": True,
                "deterministic_condition_assignment": True,
                "condition_assignment_immutable": True,
                "control_content_equivalence": True,
                "append_only_events": True,
                "participant_pii_stored": 0,
                "cross_tenant_access": "DENIED",
                "session_replay_idempotent": True,
                "metrics_reproducible": True,
                "validation_canonical_insert": False,
                "validation_evidence_update": False,
                "production_deployment": False,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
