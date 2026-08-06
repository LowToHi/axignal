#!/usr/bin/env python3
"""Deterministic economic-identity fixture for trial runtime E2E circuits."""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta
from uuid import NAMESPACE_URL, UUID, uuid5

import psycopg


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def ensure_active_trial_grant(
    dsn: str,
    *,
    tenant_id: UUID,
    now: datetime,
) -> None:
    """Create the minimum canonical P25 identity and active trial grant."""

    user_id = uuid5(NAMESPACE_URL, f"axignal-e2e-user:{tenant_id}")
    grant_id = uuid5(NAMESPACE_URL, f"axignal-e2e-trial-grant:{tenant_id}")
    email = f"{tenant_id.hex}@e2e.axignal.invalid"
    subject = f"usr_e2e_{tenant_id.hex}"
    email_hmac = _digest(f"email:{tenant_id}")
    email_identity_hmac = _digest(f"email-identity:{tenant_id}")
    domain_hmac = _digest(f"domain:{tenant_id}")
    user_handle = hashlib.sha256(f"handle:{tenant_id}".encode()).digest()
    expires_at = now + timedelta(days=7)

    with psycopg.connect(dsn) as connection, connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO identity_private.users (
              user_id, subject, email_normalized, email_hmac,
              email_identity_hmac, webauthn_user_handle, status,
              email_verified_at, created_at, updated_at
            ) VALUES (
              %s, %s, %s, %s, %s, %s, 'ACTIVE', %s, %s, %s
            )
            ON CONFLICT (user_id) DO UPDATE SET
              status = 'ACTIVE',
              email_verified_at = EXCLUDED.email_verified_at,
              updated_at = EXCLUDED.updated_at
            """,
            (
                user_id,
                subject,
                email,
                email_hmac,
                email_identity_hmac,
                user_handle,
                now,
                now,
                now,
            ),
        )
        cursor.execute(
            """
            INSERT INTO identity_private.organisations (
              tenant_id, status, created_by_user_id, primary_domain_hmac,
              created_at, updated_at
            ) VALUES (%s, 'ACTIVE', %s, %s, %s, %s)
            ON CONFLICT (tenant_id) DO UPDATE SET
              status = 'ACTIVE',
              created_by_user_id = EXCLUDED.created_by_user_id,
              primary_domain_hmac = EXCLUDED.primary_domain_hmac,
              updated_at = EXCLUDED.updated_at
            """,
            (tenant_id, user_id, domain_hmac, now, now),
        )
        cursor.execute(
            """
            INSERT INTO identity_private.user_organisations (
              user_id, tenant_id, state, relationship, created_at, revoked_at
            ) VALUES (%s, %s, 'ACTIVE', 'OWNER', %s, NULL)
            ON CONFLICT (user_id, tenant_id) DO UPDATE SET
              state = 'ACTIVE',
              relationship = 'OWNER',
              revoked_at = NULL
            """,
            (user_id, tenant_id, now),
        )
        cursor.execute(
            """
            INSERT INTO identity_private.trial_grants (
              trial_grant_id, tenant_id, requested_by_user_id, state,
              decision, risk_score, risk_policy_version, reason_codes,
              seat_capacity, token_budget_ceiling, cost_budget_microunits,
              cost_microunits_per_token, max_concurrent_runs,
              max_documents_per_run, bulk_export_allowed,
              private_connectors_allowed, prepared_at, started_at,
              expires_at, converted_at, suspended_at, updated_at
            ) VALUES (
              %s, %s, %s, 'ACTIVE', 'ALLOW', 0,
              'trial-abuse-policy@e2e', '[]'::jsonb, 2, 1000000,
              5000000, 5, 1, 25, false, false, %s, %s, %s, NULL, NULL, %s
            )
            ON CONFLICT (tenant_id) DO UPDATE SET
              requested_by_user_id = EXCLUDED.requested_by_user_id,
              state = 'ACTIVE',
              decision = 'ALLOW',
              risk_score = 0,
              risk_policy_version = EXCLUDED.risk_policy_version,
              reason_codes = '[]'::jsonb,
              seat_capacity = 2,
              token_budget_ceiling = 1000000,
              cost_budget_microunits = 5000000,
              cost_microunits_per_token = 5,
              max_concurrent_runs = 1,
              max_documents_per_run = 25,
              bulk_export_allowed = false,
              private_connectors_allowed = false,
              prepared_at = EXCLUDED.prepared_at,
              started_at = EXCLUDED.started_at,
              expires_at = EXCLUDED.expires_at,
              converted_at = NULL,
              suspended_at = NULL,
              updated_at = EXCLUDED.updated_at
            RETURNING trial_grant_id
            """,
            (grant_id, tenant_id, user_id, now, now, expires_at, now),
        )
        persisted_grant_id = cursor.fetchone()[0]
        cursor.execute(
            """
            INSERT INTO identity_private.trial_usage_accounts (
              trial_grant_id, tenant_id, token_budget_total,
              token_budget_reserved, token_budget_consumed,
              cost_budget_microunits, cost_reserved_microunits,
              cost_consumed_microunits, active_runs,
              max_concurrent_runs, updated_at
            ) VALUES (
              %s, %s, 1000000, 0, 0, 5000000, 0, 0, 0, 1, %s
            )
            ON CONFLICT (tenant_id) DO UPDATE SET
              trial_grant_id = EXCLUDED.trial_grant_id,
              token_budget_total = 1000000,
              token_budget_reserved = 0,
              token_budget_consumed = 0,
              cost_budget_microunits = 5000000,
              cost_reserved_microunits = 0,
              cost_consumed_microunits = 0,
              active_runs = 0,
              max_concurrent_runs = 1,
              updated_at = EXCLUDED.updated_at
            """,
            (persisted_grant_id, tenant_id, now),
        )
        connection.commit()
