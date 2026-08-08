"""AXENT onboarding first-value + contextual accompaniment
(Mandato AXENT — secciones 10-11).

Gates: AX_AXENT_ONBOARDING_FIRST_VALUE_E2E, AX_AXENT_CONTEXTUAL_ACCOMPANIMENT_E2E.
"""

from __future__ import annotations

import os
from uuid import UUID

import pytest

from axignal_api.axent_onboarding_repository import AxentOnboardingRepository

TENANT_A = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
TENANT_B = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
DSN = "postgresql://axignal:axignal-local@localhost:5432/axignal"

pytestmark = pytest.mark.skipif(
    not os.environ.get("AXIGNAL_INTEGRATION_TESTS"),
    reason="AXENT onboarding E2E needs a live PostgreSQL",
)


def _reset() -> None:
    import psycopg

    with psycopg.connect(DSN) as conn, conn.cursor() as cursor:
        cursor.execute("SET session_replication_role = replica")
        cursor.execute(
            "TRUNCATE tenant_private.onboarding_outcomes, "
            "tenant_private.onboarding_interventions, "
            "tenant_private.onboarding_preferences, "
            "tenant_private.onboarding_events, "
            "tenant_private.onboarding_steps, "
            "tenant_private.onboarding_journeys CASCADE"
        )
        cursor.execute("SET session_replication_role = origin")
        conn.commit()


class TestOnboardingFirstValue:
    def test_journey_to_activation(self) -> None:
        _reset()
        repo = AxentOnboardingRepository(DSN)

        journey = repo.get_or_create_journey(tenant_id=TENANT_A)
        assert journey["state"] == "CREATED"

        # Explicit preference persistence (only confirmed values).
        repo.set_preference(
            tenant_id=TENANT_A, preference_key="sectors",
            value={"sectors": ["CYBERSECURITY", "INFRASTRUCTURE"]},
            confirmed_by_subject="usr_onboard",
        )
        repo.set_preference(
            tenant_id=TENANT_A, preference_key="geographies",
            value={"countries": ["ES", "PT"]},
            confirmed_by_subject="usr_onboard",
        )
        preferences = repo.preferences(tenant_id=TENANT_A)
        assert len(preferences) == 2

        # Progress the journey deterministically.
        for state in (
            "ORGANISATION_READY", "PROFILE_READY", "INTERESTS_READY",
            "CAPABILITIES_READY", "SOURCES_EXPLAINED", "FIRST_DISCOVERY",
            "FIRST_EXPLANATION", "FIRST_QUALIFICATION", "FIRST_WORKSPACE_LINK",
            "FIRST_PURSUIT",
        ):
            repo.advance_state(tenant_id=TENANT_A, journey_type="COMPANY",
                               new_state=state)

        journey = repo.get_or_create_journey(tenant_id=TENANT_A)
        assert journey["state"] == "FIRST_PURSUIT"

        # FIRST_VALUE: user finds + understands + reviews + acts.
        advanced = repo.record_first_value(
            tenant_id=TENANT_A, action="PURSUIT_CREATED"
        )
        assert advanced["state"] == "FIRST_VALUE"

        # ACTIVATED.
        activated = repo.advance_state(
            tenant_id=TENANT_A, journey_type="COMPANY", new_state="ACTIVATED"
        )
        assert activated["state"] == "ACTIVATED"
        assert activated["activated_at"] is not None

        # Events + outcome metric persisted.
        outcomes = repo.outcomes(tenant_id=TENANT_A)
        assert any(o["metric_key"] == "time_to_first_value_days" for o in outcomes)

        # Restart equivalence + tenant isolation.
        fresh = AxentOnboardingRepository(DSN)
        assert fresh.get_or_create_journey(tenant_id=TENANT_A)["state"] == "ACTIVATED"
        assert fresh.get_or_create_journey(tenant_id=TENANT_B)["state"] == "CREATED"
        assert fresh.preferences(tenant_id=TENANT_B) == []

    def test_states_are_monotonic(self) -> None:
        _reset()
        repo = AxentOnboardingRepository(DSN)
        # Advancing backwards is a no-op.
        repo.advance_state(tenant_id=TENANT_A, journey_type="COMPANY",
                           new_state="PROFILE_READY")
        repo.advance_state(tenant_id=TENANT_A, journey_type="COMPANY",
                           new_state="CREATED")
        journey = repo.get_or_create_journey(tenant_id=TENANT_A)
        assert journey["state"] == "PROFILE_READY"


class TestContextualAccompaniment:
    def test_intervention_engine_anti_spam(self) -> None:
        _reset()
        repo = AxentOnboardingRepository(DSN)

        # First proposal -> SHOWN.
        first = repo.propose_intervention(
            tenant_id=TENANT_A, recipient_subject="usr_accompany",
            reason="pursuit_stalled", trigger_event="pursuit_no_update_7d",
            priority="HIGH",
            context={"pursuit_ref": "prs_001"},
            proposed_action="review_pursuit",
            cooldown_hours=1,
        )
        assert first["proposed"] is True
        assert first["state"] == "SHOWN"

        # Immediate re-proposal within cooldown -> NOT proposed (anti-spam).
        second = repo.propose_intervention(
            tenant_id=TENANT_A, recipient_subject="usr_accompany",
            reason="pursuit_stalled", trigger_event="pursuit_no_update_7d",
        )
        assert second["proposed"] is False

        # Snooze then act: ACCEPT.
        interventions = repo.list_interventions(
            tenant_id=TENANT_A, recipient_subject="usr_accompany"
        )
        assert len(interventions) == 1
        accepted = repo.act_on_intervention(
            tenant_id=TENANT_A,
            intervention_id=interventions[0]["intervention_id"],
            action="ACCEPT", actor_subject="usr_accompany",
        )
        assert accepted["state"] == "ACCEPTED"

    def test_mute_category_never_reproposes(self) -> None:
        _reset()
        repo = AxentOnboardingRepository(DSN)
        proposed = repo.propose_intervention(
            tenant_id=TENANT_A, recipient_subject="usr_mute",
            reason="search_no_results", trigger_event="search_empty",
            priority="LOW",
        )
        muted = repo.act_on_intervention(
            tenant_id=TENANT_A, intervention_id=proposed["intervention_id"],
            action="MUTE", actor_subject="usr_mute",
        )
        assert muted["state"] == "MUTED"

        again = repo.propose_intervention(
            tenant_id=TENANT_A, recipient_subject="usr_mute",
            reason="search_no_results", trigger_event="search_empty",
        )
        assert again["proposed"] is False
        assert again["state"] == "MUTED"

    def test_frequency_cap(self) -> None:
        _reset()
        repo = AxentOnboardingRepository(DSN)
        first = repo.propose_intervention(
            tenant_id=TENANT_A, recipient_subject="usr_cap",
            reason="deadline_approaching", trigger_event="deadline_7d",
            cooldown_hours=0,
        )
        repo.act_on_intervention(
            tenant_id=TENANT_A, intervention_id=first["intervention_id"],
            action="DISMISS", actor_subject="usr_cap",
        )
        # Cooldown 0 -> second proposal allowed.
        second = repo.propose_intervention(
            tenant_id=TENANT_A, recipient_subject="usr_cap",
            reason="deadline_approaching", trigger_event="deadline_7d",
            cooldown_hours=0,
        )
        assert second["proposed"] is True
        repo.act_on_intervention(
            tenant_id=TENANT_A, intervention_id=second["intervention_id"],
            action="DISMISS", actor_subject="usr_cap",
        )
        third = repo.propose_intervention(
            tenant_id=TENANT_A, recipient_subject="usr_cap",
            reason="deadline_approaching", trigger_event="deadline_7d",
            cooldown_hours=0,
        )
        assert third["proposed"] is True
        repo.act_on_intervention(
            tenant_id=TENANT_A, intervention_id=third["intervention_id"],
            action="DISMISS", actor_subject="usr_cap",
        )
        # Cap = 3 reached -> no more proposals.
        fourth = repo.propose_intervention(
            tenant_id=TENANT_A, recipient_subject="usr_cap",
            reason="deadline_approaching", trigger_event="deadline_7d",
            cooldown_hours=0,
        )
        assert fourth["proposed"] is False
        assert fourth.get("reason") == "frequency_cap_reached"
