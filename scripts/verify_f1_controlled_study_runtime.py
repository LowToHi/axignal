from __future__ import annotations

import hashlib
import json
import os
from uuid import UUID

import psycopg
from psycopg.rows import dict_row

TENANT_A = UUID("11111111-1111-4111-8111-111111111111")
TENANT_B = UUID("22222222-2222-4222-8222-222222222222")
PARTICIPANT = "sha256:" + hashlib.sha256(
    b"controlled-study-runtime-check"
).hexdigest()


def main() -> int:
    admin_dsn = os.environ["AXIGNAL_DATABASE_URL"]
    runtime_dsn = os.environ["AXIGNAL_VALIDATION_DATABASE_URL"]
    analyst_dsn = os.environ["AXIGNAL_VALIDATION_ANALYST_DATABASE_URL"]

    with (
        psycopg.connect(admin_dsn, row_factory=dict_row) as admin,
        admin.cursor() as cursor,
    ):
        cursor.execute(
            """
            SELECT
              has_table_privilege(
                'axignal_validation_analyst_login',
                'evaluation.validation_sessions',
                'SELECT'
              ) AS direct_read,
              has_table_privilege(
                'axignal_validation_analyst_login',
                'axignal_global.canonical_claims',
                'INSERT'
              ) AS canonical_insert,
              has_table_privilege(
                'axignal_validation_analyst_login',
                'axignal_global.evidence_objects',
                'UPDATE'
              ) AS evidence_update,
              has_function_privilege(
                'axignal_validation_analyst_login',
                'evaluation.export_validation_study(uuid,text)',
                'EXECUTE'
              ) AS export_execute
            """
        )
        assert cursor.fetchone() == {
            "direct_read": False,
            "canonical_insert": False,
            "evidence_update": False,
            "export_execute": True,
        }

    with (
        psycopg.connect(runtime_dsn, row_factory=dict_row) as runtime,
        runtime.cursor() as cursor,
    ):
        cursor.execute(
            "SELECT evaluation.start_validation_session(%s,%s,%s,%s) AS item",
            (TENANT_A, PARTICIPANT, "ANALYST", "F1-AUTHORITY-001"),
        )
        assert cursor.fetchone()["item"]["session"]["state"] == "STARTED"

    with (
        psycopg.connect(analyst_dsn, row_factory=dict_row) as analyst,
        analyst.cursor() as cursor,
    ):
        cursor.execute(
            "SELECT item FROM evaluation.export_validation_study(%s,%s) AS item",
            (TENANT_A, "f1-qualified-user@0.1.0"),
        )
        rows = [row["item"] for row in cursor.fetchall()]
        assert len(rows) == 1
        row = rows[0]
        assert row["participant_id_hash"] == PARTICIPANT
        assert row["state"] == "STARTED"
        forbidden = {
            "email",
            "name",
            "answer",
            "reference_answer",
            "required_evidence_ids",
            "required_unknowns",
            "task_payload",
        }
        assert forbidden.isdisjoint(row)

        cursor.execute(
            "SELECT item FROM evaluation.export_validation_study(%s,%s) AS item",
            (TENANT_B, "f1-qualified-user@0.1.0"),
        )
        assert cursor.fetchall() == []

        try:
            cursor.execute("SELECT count(*) FROM evaluation.validation_sessions")
        except psycopg.Error:
            analyst.rollback()
        else:
            raise AssertionError("analyst gained direct table read")

    print(
        json.dumps(
            {
                "analyst_direct_table_read": False,
                "analyst_canonical_insert": False,
                "analyst_evidence_update": False,
                "pseudonymised_export_rows": 1,
                "answer_keys_exported": 0,
                "direct_pii_exported": 0,
                "cross_tenant_export": "DENIED_BY_FILTER",
                "controlled_study_runtime_ready": True,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
