from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from axignal_api.repository import ResearchRepository


class IdentityRepository(ResearchRepository):
    def consume_rate_limit(
        self,
        *,
        key_hmac: str,
        route_key: str,
        limit: int,
        window_seconds: int,
        now: datetime | None = None,
    ) -> bool:
        current = now or datetime.now(UTC)
        with self._cursor(role="axignal_app") as cursor:
            cursor.execute(
                """
                SELECT identity_private.consume_rate_limit(
                  %s, %s, %s, %s, %s
                ) AS allowed
                """,
                (key_hmac, route_key, limit, window_seconds, current),
            )
            row = cursor.fetchone()
            if row is None:
                raise RuntimeError("Identity rate limit returned no result")
            return bool(row["allowed"])

    def begin_email_challenge(
        self,
        *,
        purpose: str,
        token_digest: str,
        subjects: dict[str, str],
        expires_at: datetime,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        current = now or datetime.now(UTC)
        with self._cursor(role="axignal_app") as cursor:
            cursor.execute(
                """
                SELECT * FROM identity_private.begin_email_challenge(
                  %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                """,
                (
                    purpose,
                    token_digest,
                    subjects["email_normalized"],
                    subjects["email_hmac"],
                    subjects["email_identity_hmac"],
                    subjects["domain_hmac"],
                    subjects["installation_hmac"],
                    subjects["network_hmac"],
                    subjects["disposable_domain"] == "true",
                    expires_at,
                    current,
                ),
            )
            row = cursor.fetchone()
            if row is None:
                raise RuntimeError("Email challenge returned no row")
            return row

    def consume_signup_challenge(
        self,
        *,
        token_digest: str,
        registration_ticket_digest: str,
        operation_id: str,
        full_token_budget: int,
        restricted_token_budget: int,
        full_cost_budget_microunits: int,
        restricted_cost_budget_microunits: int,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        current = now or datetime.now(UTC)
        with self._cursor(role="axignal_app") as cursor:
            cursor.execute(
                """
                SELECT identity_private.consume_signup_challenge(
                  %s, %s, %s, %s, %s, %s, %s, %s
                ) AS result
                """,
                (
                    token_digest,
                    registration_ticket_digest,
                    operation_id,
                    full_token_budget,
                    restricted_token_budget,
                    full_cost_budget_microunits,
                    restricted_cost_budget_microunits,
                    current,
                ),
            )
            row = cursor.fetchone()
            if row is None or not isinstance(row.get("result"), dict):
                raise RuntimeError("Signup verification returned no result")
            return row["result"]

    def resolve_bootstrap_ticket(
        self,
        *,
        token_digest: str,
        purpose: str,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        current = now or datetime.now(UTC)
        with self._cursor(role="axignal_app") as cursor:
            cursor.execute(
                """
                SELECT identity_private.resolve_bootstrap_ticket(
                  %s, %s, %s
                ) AS result
                """,
                (token_digest, purpose, current),
            )
            row = cursor.fetchone()
            if row is None or not isinstance(row.get("result"), dict):
                raise RuntimeError("Bootstrap ticket returned no result")
            return row["result"]

    def create_webauthn_challenge(
        self,
        *,
        challenge_value: str,
        challenge_digest: str,
        purpose: str,
        user_id: UUID | None,
        bootstrap_ticket_id: UUID | None,
        rp_id: str,
        expected_origin: str,
        expires_at: datetime,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        current = now or datetime.now(UTC)
        with self._cursor(role="axignal_app") as cursor:
            cursor.execute(
                """
                SELECT * FROM identity_private.create_webauthn_challenge(
                  %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                """,
                (
                    challenge_value,
                    challenge_digest,
                    purpose,
                    user_id,
                    bootstrap_ticket_id,
                    rp_id,
                    expected_origin,
                    expires_at,
                    current,
                ),
            )
            row = cursor.fetchone()
            if row is None:
                raise RuntimeError("WebAuthn challenge returned no row")
            return row

    def pending_webauthn_challenge(
        self,
        *,
        challenge_digest: str,
        purpose: str,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        current = now or datetime.now(UTC)
        with self._cursor(role="axignal_app") as cursor:
            cursor.execute(
                """
                SELECT identity_private.pending_webauthn_challenge(
                  %s, %s, %s
                ) AS result
                """,
                (challenge_digest, purpose, current),
            )
            row = cursor.fetchone()
            if row is None or not isinstance(row.get("result"), dict):
                raise RuntimeError("Pending WebAuthn challenge returned no result")
            return row["result"]

    def credential_for_authentication(self, *, credential_id: str) -> dict[str, Any]:
        with self._cursor(role="axignal_app") as cursor:
            cursor.execute(
                "SELECT identity_private.credential_for_authentication(%s) AS result",
                (credential_id,),
            )
            row = cursor.fetchone()
            if row is None or not isinstance(row.get("result"), dict):
                raise RuntimeError("webauthn_credential_not_found")
            return row["result"]

    def complete_registration(
        self,
        *,
        challenge_digest: str,
        bootstrap_ticket_digest: str,
        credential_id: str,
        credential_public_key: bytes,
        sign_count: int,
        transports: list[str],
        device_type: str,
        backed_up: bool,
        aaguid: str | None,
        session_token_digest: str,
        installation_hmac: str,
        network_hmac: str,
        user_agent_hmac: str,
        recovery_code_digests: list[str],
        idle_seconds: int,
        absolute_seconds: int,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        current = now or datetime.now(UTC)
        with self._cursor(role="axignal_app") as cursor:
            cursor.execute(
                """
                SELECT identity_private.complete_passkey_registration(
                  %s, %s, %s, %s, %s, %s, %s, %s, %s,
                  %s, %s, %s, %s, %s, %s, %s, %s
                ) AS result
                """,
                (
                    challenge_digest,
                    bootstrap_ticket_digest,
                    credential_id,
                    credential_public_key.hex(),
                    sign_count,
                    transports,
                    device_type,
                    backed_up,
                    aaguid,
                    session_token_digest,
                    installation_hmac,
                    network_hmac,
                    user_agent_hmac,
                    recovery_code_digests,
                    idle_seconds,
                    absolute_seconds,
                    current,
                ),
            )
            row = cursor.fetchone()
            if row is None or not isinstance(row.get("result"), dict):
                raise RuntimeError("Passkey registration returned no result")
            return row["result"]

    def complete_authentication(
        self,
        *,
        challenge_digest: str,
        credential_id: str,
        new_sign_count: int,
        session_token_digest: str,
        installation_hmac: str,
        network_hmac: str,
        user_agent_hmac: str,
        idle_seconds: int,
        absolute_seconds: int,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        current = now or datetime.now(UTC)
        with self._cursor(role="axignal_app") as cursor:
            cursor.execute(
                """
                SELECT identity_private.complete_passkey_authentication(
                  %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) AS result
                """,
                (
                    challenge_digest,
                    credential_id,
                    new_sign_count,
                    session_token_digest,
                    installation_hmac,
                    network_hmac,
                    user_agent_hmac,
                    idle_seconds,
                    absolute_seconds,
                    current,
                ),
            )
            row = cursor.fetchone()
            if row is None or not isinstance(row.get("result"), dict):
                raise RuntimeError("Passkey authentication returned no result")
            return row["result"]

    def resolve_session(
        self,
        *,
        token_digest: str,
        touch_interval_seconds: int,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        current = now or datetime.now(UTC)
        with self._cursor(role="axignal_app") as cursor:
            cursor.execute(
                """
                SELECT identity_private.resolve_identity_session(
                  %s, %s, %s
                ) AS result
                """,
                (token_digest, touch_interval_seconds, current),
            )
            row = cursor.fetchone()
            if row is None or not isinstance(row.get("result"), dict):
                raise RuntimeError("Identity session returned no result")
            return row["result"]

    def revoke_session(
        self,
        *,
        token_digest: str,
        reason: str,
        now: datetime | None = None,
    ) -> bool:
        current = now or datetime.now(UTC)
        with self._cursor(role="axignal_app") as cursor:
            cursor.execute(
                """
                SELECT identity_private.revoke_identity_session(
                  %s, %s, %s
                ) AS revoked
                """,
                (token_digest, reason, current),
            )
            row = cursor.fetchone()
            return bool(row and row["revoked"])

    def begin_recovery(
        self,
        *,
        email_identity_hmac: str,
        code_digest: str,
        recovery_ticket_digest: str,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        current = now or datetime.now(UTC)
        with self._cursor(role="axignal_app") as cursor:
            cursor.execute(
                """
                SELECT identity_private.begin_recovery(
                  %s, %s, %s, %s
                ) AS result
                """,
                (email_identity_hmac, code_digest, recovery_ticket_digest, current),
            )
            row = cursor.fetchone()
            if row is None or not isinstance(row.get("result"), dict):
                raise RuntimeError("Recovery returned no result")
            return row["result"]

    def trial_status(self, *, tenant_id: UUID) -> dict[str, Any] | None:
        with self._cursor(role="axignal_app") as cursor:
            cursor.execute(
                "SELECT identity_private.trial_status_for_tenant(%s) AS result",
                (tenant_id,),
            )
            row = cursor.fetchone()
            if row is None:
                return None
            result = row.get("result")
            return result if isinstance(result, dict) else None

    def approve_test_step_up(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        claim_type: str,
        claim_hmac: str,
        actor_subject: str,
        full_token_budget: int,
        full_cost_budget_microunits: int,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        current = now or datetime.now(UTC)
        with self._cursor(role="axignal_app") as cursor:
            cursor.execute(
                """
                SELECT identity_private.approve_trial_step_up(
                  %s, %s, %s, %s, %s, %s, %s, %s
                ) AS result
                """,
                (
                    tenant_id,
                    user_id,
                    claim_type,
                    claim_hmac,
                    actor_subject,
                    full_token_budget,
                    full_cost_budget_microunits,
                    current,
                ),
            )
            row = cursor.fetchone()
            if row is None or not isinstance(row.get("result"), dict):
                raise RuntimeError("Trial step-up returned no result")
            return row["result"]

    def start_prepared_trial(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        subject: str,
        email: str,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        current = now or datetime.now(UTC)
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT * FROM tenant_private.start_prepared_identity_trial(
                  %s, %s, %s, %s
                )
                """,
                (user_id, subject, email, current),
            )
            row = cursor.fetchone()
            if row is None:
                raise RuntimeError("Prepared trial start returned no entitlement")
            return row
