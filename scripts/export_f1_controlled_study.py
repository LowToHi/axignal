from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import psycopg
from psycopg.rows import dict_row

STUDY_ID = "AXIGNAL-F1-CONTROLLED-001"
PROTOCOL_VERSION = "1.0.0"
EXPERIMENT_VERSION = "f1-qualified-user@0.1.0"
INCIDENT_KEYS = (
    "privacy_incidents_max",
    "cross_tenant_incidents_max",
    "canonical_mutations_max",
    "answer_key_exposures_max",
    "direct_participant_pii_records_max",
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Export a pseudonymised F1 study dataset."
    )
    parser.add_argument("--tenant-id", type=UUID, required=True)
    parser.add_argument("--output", type=Path, required=True)
    for key in INCIDENT_KEYS:
        option = f"--{key.replace('_max', '').replace('_', '-')}"
        parser.add_argument(option, type=int, required=True)
    args = parser.parse_args()

    dsn = os.environ["AXIGNAL_VALIDATION_ANALYST_DATABASE_URL"]
    incident_values = {
        key: getattr(args, key.replace("_max", "")) for key in INCIDENT_KEYS
    }
    if any(value < 0 for value in incident_values.values()):
        raise SystemExit("incident counts must be non-negative")

    with (
        psycopg.connect(dsn, row_factory=dict_row) as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute(
            "SELECT item FROM evaluation.export_validation_study(%s,%s) AS item",
            (args.tenant_id, EXPERIMENT_VERSION),
        )
        sessions = [row["item"] for row in cursor.fetchall()]

    payload = {
        "study_id": STUDY_ID,
        "protocol_version": PROTOCOL_VERSION,
        "experiment_version": EXPERIMENT_VERSION,
        "exported_at": datetime.now(UTC).isoformat(),
        "synthetic": False,
        "incidents": incident_values,
        "sessions": sessions,
    }
    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {"sessions_exported": len(sessions), "output": str(args.output)},
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
