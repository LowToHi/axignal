from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from axignal_api.repository import ResearchRepository


class SeatRepository(ResearchRepository):
    def bootstrap_owner(
        self,
        *,
        tenant_id: UUID,
        principal_id: str,
        email: str,
        actor_subject: str,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        current = now or datetime.now(UTC)
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT * FROM tenant_private.bootstrap_organisation_owner(
                  %s, %s, %s, %s
                )
                """,
                (principal_id, email, actor_subject, current),
            )
            row = cursor.fetchone()
            if row is None:
                raise RuntimeError("Owner bootstrap returned no membership")
            return row

    def invitation_by_operation(
        self,
        *,
        tenant_id: UUID,
        operation_id: str,
    ) -> dict[str, Any] | None:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT *
                FROM tenant_private.organisation_invitations
                WHERE tenant_id = %s AND operation_id = %s
                """,
                (tenant_id, operation_id),
            )
            return cursor.fetchone()

    def reserve_invitation(
        self,
        *,
        tenant_id: UUID,
        operation_id: str,
        email: str,
        role_id: str,
        token_digest: str,
        delivery_provider: str,
        invited_by: str,
        expires_at: datetime,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        current = now or datetime.now(UTC)
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT * FROM tenant_private.reserve_seat_invitation(
                  %s, %s, %s, %s, %s, %s, %s, %s
                )
                """,
                (
                    operation_id,
                    email,
                    role_id,
                    token_digest,
                    delivery_provider,
                    invited_by,
                    expires_at,
                    current,
                ),
            )
            row = cursor.fetchone()
            if row is None:
                raise RuntimeError("Seat invitation returned no row")
            return row

    def accept_invitation(
        self,
        *,
        tenant_id: UUID,
        token_digest: str,
        principal_id: str,
        email: str,
        actor_subject: str,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        current = now or datetime.now(UTC)
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT * FROM tenant_private.accept_seat_invitation(
                  %s, %s, %s, %s, %s
                )
                """,
                (token_digest, principal_id, email, actor_subject, current),
            )
            row = cursor.fetchone()
            if row is None:
                raise RuntimeError("Invitation acceptance returned no membership")
            return row

    def revoke_invitation(
        self,
        *,
        tenant_id: UUID,
        invitation_id: UUID,
        actor_subject: str,
        reason: str,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        current = now or datetime.now(UTC)
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT * FROM tenant_private.revoke_seat_invitation(
                  %s, %s, %s, %s
                )
                """,
                (invitation_id, actor_subject, reason, current),
            )
            row = cursor.fetchone()
            if row is None:
                raise RuntimeError("Invitation revocation returned no row")
            return row

    def revoke_membership(
        self,
        *,
        tenant_id: UUID,
        membership_id: UUID,
        actor_subject: str,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        current = now or datetime.now(UTC)
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT * FROM tenant_private.revoke_organisation_membership(
                  %s, %s, %s
                )
                """,
                (membership_id, actor_subject, current),
            )
            row = cursor.fetchone()
            if row is None:
                raise RuntimeError("Membership revocation returned no row")
            return row

    def change_role(
        self,
        *,
        tenant_id: UUID,
        membership_id: UUID,
        role_id: str,
        actor_subject: str,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        current = now or datetime.now(UTC)
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT * FROM tenant_private.change_organisation_membership_role(
                  %s, %s, %s, %s
                )
                """,
                (membership_id, role_id, actor_subject, current),
            )
            row = cursor.fetchone()
            if row is None:
                raise RuntimeError("Role change returned no membership")
            return row

    def access_decision(
        self,
        *,
        tenant_id: UUID,
        principal_id: str,
        write: bool,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        current = now or datetime.now(UTC)
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT tenant_private.seat_access_decision(
                  %s, %s, %s
                ) AS decision
                """,
                (principal_id, write, current),
            )
            row = cursor.fetchone()
            if row is None or not isinstance(row.get("decision"), dict):
                raise RuntimeError("Seat access decision returned no result")
            return row["decision"]

    def summary(self, *, tenant_id: UUID) -> dict[str, Any]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT *
                FROM tenant_private.organisation_seat_entitlements
                WHERE tenant_id = %s
                """,
                (tenant_id,),
            )
            entitlement = cursor.fetchone()
            if entitlement is None:
                raise RuntimeError("seat_entitlement_required")

            cursor.execute(
                """
                SELECT
                  m.*,
                  COALESCE(
                    jsonb_agg(rb.role_id ORDER BY rb.role_id)
                      FILTER (WHERE rb.state = 'ACTIVE'),
                    '[]'::jsonb
                  ) AS roles
                FROM tenant_private.organisation_memberships m
                LEFT JOIN tenant_private.membership_role_bindings rb
                  ON rb.tenant_id = m.tenant_id
                 AND rb.membership_id = m.membership_id
                WHERE m.tenant_id = %s
                GROUP BY m.membership_id
                ORDER BY m.joined_at, m.membership_id
                """,
                (tenant_id,),
            )
            members = list(cursor.fetchall())

            cursor.execute(
                """
                SELECT *
                FROM tenant_private.organisation_invitations
                WHERE tenant_id = %s
                ORDER BY invited_at DESC, invitation_id
                """,
                (tenant_id,),
            )
            invitations = list(cursor.fetchall())

            cursor.execute(
                """
                SELECT
                  count(*) FILTER (WHERE state = 'ACTIVE') AS active,
                  count(*) FILTER (WHERE state = 'RESERVED') AS reserved
                FROM tenant_private.organisation_seat_allocations
                WHERE tenant_id = %s
                """,
                (tenant_id,),
            )
            counts = cursor.fetchone() or {"active": 0, "reserved": 0}

            cursor.execute(
                """
                SELECT *
                FROM tenant_private.membership_audit_events
                WHERE tenant_id = %s
                ORDER BY occurred_at DESC, audit_event_id DESC
                LIMIT 20
                """,
                (tenant_id,),
            )
            audit = list(cursor.fetchall())

        active = int(counts["active"] or 0)
        reserved = int(counts["reserved"] or 0)
        capacity = int(entitlement["seat_capacity"])
        return {
            "seat_entitlement": entitlement,
            "active_seats": active,
            "reserved_seats": reserved,
            "occupied_seats": active + reserved,
            "available_seats": max(capacity - active - reserved, 0),
            "members": members,
            "invitations": invitations,
            "audit": audit,
        }
