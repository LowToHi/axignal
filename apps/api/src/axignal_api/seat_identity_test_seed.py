from __future__ import annotations

import json
from datetime import UTC, datetime
from os import environ

import psycopg

from axignal_api.identity_risk import risk_subjects


def _enabled(name: str) -> bool:
    return environ.get(name, "").strip().casefold() in {"1", "true", "yes", "on"}


def main() -> None:
    if environ.get("AXIGNAL_ENVIRONMENT", "").strip().casefold() != "test":
        raise RuntimeError(
            "Passwordless seat-owner seed requires AXIGNAL_ENVIRONMENT=test"
        )
    if not _enabled("AXIGNAL_TEST_RUNTIME_ENABLED"):
        raise RuntimeError("Passwordless seat-owner seed requires the test runtime")
    if not _enabled("AXIGNAL_IDENTITY_RUNTIME_ENABLED"):
        raise RuntimeError("Passwordless seat-owner seed requires the identity runtime")

    database_url = environ.get("AXIGNAL_IDENTITY_DATABASE_URL", "").strip()
    pepper = environ.get("AXIGNAL_IDENTITY_HMAC_PEPPER", "").strip()
    subject = environ.get("AXIGNAL_AUTH_SUBJECT", "").strip()
    email = environ.get("AXIGNAL_AUTH_EMAIL", "").strip().casefold()
    if not database_url or not pepper or not subject or not email:
        raise RuntimeError("Passwordless seat-owner seed configuration is incomplete")

    subjects = risk_subjects(
        email=email,
        installation_id="seat-governance-passwordless-seed-v1",
        network="127.0.0.1",
        pepper=pepper,
    )
    now = datetime.now(UTC)
    with psycopg.connect(database_url) as connection, connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO identity_private.users (
              subject,
              email_normalized,
              email_hmac,
              email_identity_hmac,
              status,
              email_verified_at,
              created_at,
              updated_at
            ) VALUES (%s, %s, %s, %s, 'ACTIVE', %s, %s, %s)
            ON CONFLICT (email_normalized) DO UPDATE SET
              subject = EXCLUDED.subject,
              email_hmac = EXCLUDED.email_hmac,
              email_identity_hmac = EXCLUDED.email_identity_hmac,
              status = 'ACTIVE',
              updated_at = EXCLUDED.updated_at
            RETURNING subject, email_normalized
            """,
            (
                subject,
                subjects["email_normalized"],
                subjects["email_hmac"],
                subjects["email_identity_hmac"],
                now,
                now,
                now,
            ),
        )
        row = cursor.fetchone()
    if row != (subject, subjects["email_normalized"]):
        raise RuntimeError("Passwordless seat-owner seed did not materialise")

    print(
        json.dumps(
            {
                "status": "PASS",
                "fixture": "passwordless-seat-owner",
                "subject": subject,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
