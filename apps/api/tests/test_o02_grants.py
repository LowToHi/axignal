"""WP6 — O02 Grants tests."""

from __future__ import annotations

from datetime import date
from uuid import UUID

import pytest

from axignal_api.o02_grants import (
    ApplicationState,
    ApplicationWorkspace,
    BeneficiaryAward,
    CallState,
    EligibilityRule,
    GrantCall,
    GrantTopic,
    grants_source_manifest,
)

TENANT = UUID("11111111-1111-4111-8111-111111111111")
WS_ID = UUID("33333333-3333-4333-8333-333333333333")


class TestSourceAdmission:
    def test_manifest_discovered_pending_human(self) -> None:
        manifest = grants_source_manifest()
        assert manifest["library_id"] == "O02"
        assert manifest["state"] == "DISCOVERED"
        assert manifest["commercial_use"] == "PENDING_HUMAN_DECISION"
        assert manifest["product_shell"] == "AXIGNAL_OPPORTUNITY_INTELLIGENCE"


class TestGrantCall:
    def test_draft_initial(self) -> None:
        call = GrantCall(call_id="call-1", title="Horizon Europe call")
        assert call.state == CallState.DRAFT

    def test_open_requires_dates(self) -> None:
        with pytest.raises(ValueError, match="opens_at"):
            GrantCall(call_id="call-1", title="Call X", state="OPEN")

    def test_valid_open_call(self) -> None:
        call = GrantCall(
            call_id="call-1",
            title="Horizon Europe call",
            state="OPEN",
            opens_at=date(2026, 1, 1),
            closes_at=date(2026, 6, 30),
        )
        assert call.state == CallState.OPEN

    def test_date_ordering(self) -> None:
        with pytest.raises(ValueError, match="opens_at"):
            GrantCall(
                call_id="call-1",
                title="Call X",
                opens_at=date(2026, 6, 30),
                closes_at=date(2026, 1, 1),
            )

    def test_illegal_transition(self) -> None:
        call = GrantCall(call_id="call-1", title="Call X")
        with pytest.raises(ValueError, match="illegal call transition"):
            call.transition(CallState.CLOSED)

    def test_lifecycle(self) -> None:
        call = GrantCall(
            call_id="call-1",
            title="Call X",
            state="OPEN",
            opens_at=date(2026, 1, 1),
            closes_at=date(2026, 6, 30),
        )
        closed = call.transition(CallState.CLOSED)
        assert closed.state == CallState.CLOSED
        with pytest.raises(ValueError, match="illegal call transition"):
            closed.transition(CallState.OPEN)


class TestEligibility:
    def test_deadline_rule_requires_source(self) -> None:
        with pytest.raises(ValueError, match="source_ref"):
            EligibilityRule(
                rule_id="rule-1",
                call_id="call-1",
                criterion="Applications must arrive before the deadline.",
                category="DEADLINE",
            )

    def test_entity_rule_ok(self) -> None:
        rule = EligibilityRule(
            rule_id="rule-1",
            call_id="call-1",
            criterion="Legal entities established in an EU member state.",
            category="ENTITY_TYPE",
        )
        assert rule.category == "ENTITY_TYPE"


class TestGrantTopic:
    def test_topic_requires_budget_or_rate(self) -> None:
        with pytest.raises(ValueError, match="funding_rate_pct or indicative_budget"):
            GrantTopic(topic_id="topic-1", call_id="call-1", title="Topic")

    def test_topic_with_rate(self) -> None:
        topic = GrantTopic(
            topic_id="topic-1",
            call_id="call-1",
            title="Topic",
            funding_rate_pct=70.0,
        )
        assert topic.funding_rate_pct == 70.0

    def test_topic_with_budget(self) -> None:
        topic = GrantTopic(
            topic_id="topic-1",
            call_id="call-1",
            title="Topic",
            indicative_budget_eur=2_000_000.0,
        )
        assert topic.indicative_budget_eur == 2_000_000.0

    def test_rate_bounds(self) -> None:
        with pytest.raises(ValueError):
            GrantTopic(
                topic_id="topic-1",
                call_id="call-1",
                title="Topic",
                funding_rate_pct=101.0,
            )


class TestBeneficiaryAward:
    def test_award_requires_evidence(self) -> None:
        with pytest.raises(ValueError, match="evidence_ref"):
            BeneficiaryAward(
                award_id="award-1",
                topic_id="topic-1",
                beneficiary_entity_id="ent_uni",
                awarded_amount_eur=500_000.0,
                awarded_at=date(2026, 9, 1),
            )

    def test_valid_award(self) -> None:
        award = BeneficiaryAward(
            award_id="award-1",
            topic_id="topic-1",
            beneficiary_entity_id="ent_uni",
            awarded_amount_eur=500_000.0,
            awarded_at=date(2026, 9, 1),
            evidence_ref="evidence-1",
        )
        assert award.awarded_amount_eur == 500_000.0


class TestApplicationWorkspace:
    def test_draft_initial(self) -> None:
        workspace = ApplicationWorkspace(
            workspace_id=WS_ID,
            tenant_id=TENANT,
            topic_id="topic-1",
            created_by="user-1",
        )
        assert workspace.state == ApplicationState.DRAFT

    def test_approved_requires_authority(self) -> None:
        with pytest.raises(ValueError, match="approved_by"):
            ApplicationWorkspace(
                workspace_id=WS_ID,
                tenant_id=TENANT,
                topic_id="topic-1",
                state="APPROVED",
                created_by="user-1",
            )

    def test_full_lifecycle(self) -> None:
        workspace = ApplicationWorkspace(
            workspace_id=WS_ID,
            tenant_id=TENANT,
            topic_id="topic-1",
            created_by="user-1",
        )
        checked = workspace.transition(ApplicationState.ELIGIBILITY_CHECKED)
        ready = checked.transition(ApplicationState.READY_FOR_APPROVAL)
        approved = ready.transition(ApplicationState.APPROVED)
        submitted = approved.transition(ApplicationState.SUBMITTED)
        assert submitted.state == ApplicationState.SUBMITTED

    def test_illegal_skip(self) -> None:
        workspace = ApplicationWorkspace(
            workspace_id=WS_ID,
            tenant_id=TENANT,
            topic_id="topic-1",
            created_by="user-1",
        )
        with pytest.raises(ValueError, match="illegal application transition"):
            workspace.transition(ApplicationState.SUBMITTED)
