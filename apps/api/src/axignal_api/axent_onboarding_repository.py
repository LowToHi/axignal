"""AXENT onboarding and contextual accompaniment (Mandato AXENT — 10-11).

Journeys with explicit states up to ACTIVATED, FIRST_VALUE defined as:
find a relevant opportunity + understand why it matches + review
evidence + execute a useful operational action. Intervention engine is
deterministic-rule driven with anti-spam controls (cooldown, caps,
dismiss/snooze/mute).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from psycopg.types.json import Jsonb

from axignal_api.repository import ResearchRepository

JOURNEY_STATES = (
    "CREATED", "ORGANISATION_READY", "PROFILE_READY", "INTERESTS_READY",
    "CAPABILITIES_READY", "SOURCES_EXPLAINED", "FIRST_DISCOVERY",
    "FIRST_EXPLANATION", "FIRST_QUALIFICATION", "FIRST_WORKSPACE_LINK",
    "FIRST_PURSUIT", "FIRST_VALUE", "ACTIVATED",
)

FIRST_VALUE_ACTIONS = (
    "SAVED", "LINKED_TO_WORKSPACE", "QUALIFIED", "PURSUIT_CREATED",
    "TASK_CREATED", "DISMISSED_WITH_REASON",
)


class AxentOnboardingRepository(ResearchRepository):
    # --- Journeys ------------------------------------------------------------

    def get_or_create_journey(
        self, *, tenant_id: UUID, journey_type: str = "COMPANY"
    ) -> dict[str, Any]:
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                INSERT INTO tenant_private.onboarding_journeys (
                  journey_id, tenant_id, journey_type, state
                ) VALUES (%s, %s, %s, 'CREATED')
                ON CONFLICT (tenant_id, journey_type) DO NOTHING
                """,
                (uuid4(), tenant_id, journey_type),
            )
            cursor.execute(
                """
                SELECT journey_id, journey_type, state, activated_at,
                       created_at, updated_at
                FROM tenant_private.onboarding_journeys
                WHERE tenant_id = %s AND journey_type = %s
                """,
                (tenant_id, journey_type),
            )
            row = cursor.fetchone()
            return dict(row) if row else {}

    def advance_state(
        self, *, tenant_id: UUID, journey_type: str, new_state: str
    ) -> dict[str, Any]:
        if new_state not in JOURNEY_STATES:
            raise ValueError(f"invalid journey state {new_state!r}")
        current = self.get_or_create_journey(tenant_id=tenant_id, journey_type=journey_type)
        current_index = JOURNEY_STATES.index(current["state"])
        new_index = JOURNEY_STATES.index(new_state)
        if new_index <= current_index:
            return current
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                UPDATE tenant_private.onboarding_journeys
                SET state = %s,
                    activated_at = CASE WHEN %s = 'ACTIVATED' THEN now()
                                        ELSE activated_at END,
                    updated_at = now()
                WHERE tenant_id = %s AND journey_type = %s
                RETURNING journey_id, state, activated_at
                """,
                (new_state, new_state, tenant_id, journey_type),
            )
            row = cursor.fetchone()
            return dict(row) if row else current

    def record_event(
        self,
        *,
        tenant_id: UUID,
        journey_id: UUID,
        event_type: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                INSERT INTO tenant_private.onboarding_events (
                  event_id, tenant_id, journey_id, event_type, payload
                ) VALUES (%s, %s, %s, %s, %s)
                """,
                (uuid4(), tenant_id, journey_id, event_type, Jsonb(payload or {})),
            )

    def set_preference(
        self,
        *,
        tenant_id: UUID,
        preference_key: str,
        value: dict[str, Any],
        confirmed_by_subject: str,
    ) -> None:
        """Only EXPLICIT user-confirmed preferences persist."""
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                INSERT INTO tenant_private.onboarding_preferences (
                  preference_id, tenant_id, preference_key, value_json,
                  confirmed_by_subject, confirmed_at
                ) VALUES (%s, %s, %s, %s, %s, now())
                ON CONFLICT (tenant_id, preference_key) DO UPDATE SET
                  value_json = EXCLUDED.value_json,
                  confirmed_by_subject = EXCLUDED.confirmed_by_subject,
                  confirmed_at = now(), updated_at = now()
                """,
                (uuid4(), tenant_id, preference_key, Jsonb(value), confirmed_by_subject),
            )

    def preferences(
        self, *, tenant_id: UUID
    ) -> list[dict[str, Any]]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT preference_key, value_json, confirmed_by_subject,
                       confirmed_at
                FROM tenant_private.onboarding_preferences
                WHERE tenant_id = %s
                ORDER BY updated_at DESC
                """,
                (tenant_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def record_first_value(
        self, *, tenant_id: UUID, action: str
    ) -> dict[str, Any]:
        """FIRST_VALUE: relevant opportunity + understanding + evidence
        review + a useful operational action."""
        if action not in FIRST_VALUE_ACTIONS:
            raise ValueError(f"invalid first-value action {action!r}")
        journey = self.get_or_create_journey(tenant_id=tenant_id)
        advanced = self.advance_state(
            tenant_id=tenant_id, journey_type="COMPANY", new_state="FIRST_VALUE"
        )
        self.record_event(
            tenant_id=tenant_id, journey_id=journey["journey_id"],
            event_type="FIRST_VALUE", payload={"action": action},
        )
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                INSERT INTO tenant_private.onboarding_outcomes (
                  outcome_id, tenant_id, metric_key, value, measured_at
                ) VALUES (%s, %s, 'time_to_first_value_days', 1, now())
                ON CONFLICT (tenant_id, metric_key, measured_at) DO NOTHING
                """,
                (uuid4(), tenant_id),
            )
        return advanced

    # --- Interventions -------------------------------------------------------

    def propose_intervention(
        self,
        *,
        tenant_id: UUID,
        recipient_subject: str,
        reason: str,
        trigger_event: str,
        priority: str = "NORMAL",
        context: dict[str, Any] | None = None,
        proposed_action: str | None = None,
        cooldown_hours: int = 24,
    ) -> dict[str, Any]:
        """Anti-spam: unique (tenant, subject, reason, trigger); respects
        cooldown and frequency cap; muted categories never re-propose."""
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT intervention_id, state, cooldown_until, shown_count,
                       frequency_cap
                FROM tenant_private.onboarding_interventions
                WHERE tenant_id = %s AND recipient_subject = %s
                  AND reason = %s AND trigger_event = %s
                """,
                (tenant_id, recipient_subject, reason, trigger_event),
            )
            existing = cursor.fetchone()
            now = datetime.now(UTC)
            if existing is not None:
                if existing["state"] == "MUTED":
                    return {"intervention_id": existing["intervention_id"],
                            "state": "MUTED", "proposed": False}
                if (
                    existing["cooldown_until"] is not None
                    and existing["cooldown_until"] > now
                ):
                    return {"intervention_id": existing["intervention_id"],
                            "state": existing["state"], "proposed": False}
                if existing["shown_count"] >= existing["frequency_cap"]:
                    return {"intervention_id": existing["intervention_id"],
                            "state": "PENDING", "proposed": False,
                            "reason": "frequency_cap_reached"}
                cursor.execute(
                    """
                    UPDATE tenant_private.onboarding_interventions
                    SET shown_count = shown_count + 1,
                        cooldown_until = now() + make_interval(hours => %s),
                        state = 'SHOWN', shown_at = now()
                    WHERE intervention_id = %s
                    RETURNING intervention_id, state, shown_count
                    """,
                    (cooldown_hours, existing["intervention_id"]),
                )
                row = cursor.fetchone()
                return dict(row) | {"proposed": True}

            intervention_id = uuid4()
            cursor.execute(
                """
                INSERT INTO tenant_private.onboarding_interventions (
                  intervention_id, tenant_id, recipient_subject, reason,
                  trigger_event, priority, context_json, proposed_action,
                  state, cooldown_until, shown_count
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'SHOWN',
                          now() + make_interval(hours => %s), 1)
                RETURNING intervention_id, state, shown_count
                """,
                (
                    intervention_id, tenant_id, recipient_subject, reason,
                    trigger_event, priority, Jsonb(context or {}),
                    proposed_action, cooldown_hours,
                ),
            )
            row = cursor.fetchone()
            return dict(row) | {"proposed": True}

    def act_on_intervention(
        self,
        *,
        tenant_id: UUID,
        intervention_id: UUID,
        action: str,
        actor_subject: str,
    ) -> dict[str, Any]:
        """action: DISMISS | SNOOZE | ACCEPT | MUTE | EXECUTE."""
        valid = {"DISMISS", "SNOOZE", "ACCEPT", "MUTE", "EXECUTE"}
        if action not in valid:
            raise ValueError(f"invalid intervention action {action!r}")
        state_map = {
            "DISMISS": "DISMISSED", "SNOOZE": "SNOOZED",
            "ACCEPT": "ACCEPTED", "MUTE": "MUTED", "EXECUTE": "EXECUTED",
        }
        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                UPDATE tenant_private.onboarding_interventions
                SET state = %s,
                    dismissed_at = CASE WHEN %s = 'DISMISSED' THEN now()
                                        ELSE dismissed_at END,
                    accepted_at = CASE WHEN %s IN ('ACCEPTED', 'EXECUTED')
                                       THEN now() ELSE accepted_at END,
                    outcome = CASE WHEN %s = 'EXECUTED' THEN 'EXECUTED'
                                   ELSE outcome END
                WHERE tenant_id = %s AND intervention_id = %s
                RETURNING intervention_id, state
                """,
                (state_map[action], state_map[action], state_map[action],
                 state_map[action], tenant_id, intervention_id),
            )
            row = cursor.fetchone()
            if row is None:
                raise LookupError("intervention not found")
            return dict(row)

    def list_interventions(
        self, *, tenant_id: UUID, recipient_subject: str
    ) -> list[dict[str, Any]]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT intervention_id, reason, trigger_event, priority,
                       context_json, proposed_action, state, shown_count,
                       created_at
                FROM tenant_private.onboarding_interventions
                WHERE tenant_id = %s AND recipient_subject = %s
                ORDER BY created_at DESC
                """,
                (tenant_id, recipient_subject),
            )
            return [dict(row) for row in cursor.fetchall()]

    # --- Outcomes ------------------------------------------------------------

    def outcomes(
        self, *, tenant_id: UUID
    ) -> list[dict[str, Any]]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT metric_key, value, measured_at
                FROM tenant_private.onboarding_outcomes
                WHERE tenant_id = %s
                ORDER BY measured_at
                """,
                (tenant_id,),
            )
            return [dict(row) for row in cursor.fetchall()]
