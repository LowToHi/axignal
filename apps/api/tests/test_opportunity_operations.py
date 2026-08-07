"""WP4 — Opportunity Operations tests (T01-T11)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest

from axignal_api.opportunity_operations import (
    Learning,
    Outcome,
    Pursuit,
    PursuitState,
    WorkspaceFactory,
)
from axignal_api.procurement_domain import (
    Opportunity,
    OpportunityVersion,
    ProcurementFact,
    SourceProvenance,
    WorkspaceState,
)

TENANT = UUID("11111111-1111-4111-8111-111111111111")
OTHER_TENANT = UUID("22222222-2222-4222-8222-222222222222")


def make_opportunity() -> Opportunity:
    version = OpportunityVersion(
        opportunity_id="opp-1",
        source_notice_id="notice-1",
        source_version="v3",
        observed_at=datetime.now(UTC),
        content_digest=f"sha256:{'a' * 64}",
    )
    fact = ProcurementFact(
        fact_id="fact-1",
        predicate="buyer_name",
        value="Ministerio de Fomento",
        origin="SOURCE_FACT",
        provenance=SourceProvenance(
            source_id="src_ted_search_api_v3",
            source_notice_id="notice-1",
            source_url="https://api.ted.europa.eu/v3/notices/search",
            retrieved_at=datetime.now(UTC),
            source_version="v3",
        ),
    )
    return Opportunity(
        opportunity_id="opp-1",
        current_version=version,
        title="Road construction",
        buyer_organisation="Ministerio de Fomento",
        facts=(fact,),
    )


def make_pursuit(state: PursuitState = PursuitState.QUALIFIED, **overrides: object) -> Pursuit:
    base: dict[str, object] = {
        "pursuit_id": "prs_test_000001",
        "tenant_id": TENANT,
        "opportunity_id": "opp-1",
        "state": state,
        "created_by": "user-1",
    }
    base.update(overrides)
    return Pursuit(**base)


class TestPursuit:
    def test_qualified_initial(self) -> None:
        pursuit = make_pursuit()
        assert pursuit.state == PursuitState.QUALIFIED

    def test_active_requires_workspace(self) -> None:
        with pytest.raises(ValueError, match="workspace_id"):
            make_pursuit(state=PursuitState.ACTIVE)

    def test_terminal_requires_decision(self) -> None:
        with pytest.raises(ValueError, match="decided_by"):
            make_pursuit(
                state=PursuitState.LOST,
                workspace_id=UUID("33333333-3333-4333-8333-333333333333"),
            )

    def test_won_requires_outcome(self) -> None:
        with pytest.raises(ValueError, match="outcome_id"):
            make_pursuit(
                state=PursuitState.WON,
                workspace_id=UUID("33333333-3333-4333-8333-333333333333"),
                decided_by="user-1",
                decided_at=datetime.now(UTC),
            )

    def test_valid_won_pursuit(self) -> None:
        pursuit = make_pursuit(
            state=PursuitState.WON,
            workspace_id=UUID("33333333-3333-4333-8333-333333333333"),
            decided_by="user-1",
            decided_at=datetime.now(UTC),
            outcome_id="out_test_000001",
        )
        assert pursuit.state == PursuitState.WON

    def test_transition_forward(self) -> None:
        pursuit = make_pursuit()
        reviewed = pursuit.transition(PursuitState.DECISION_REVIEW, decided_by="user-1")
        assert reviewed.state == PursuitState.DECISION_REVIEW

    def test_illegal_transition(self) -> None:
        pursuit = make_pursuit()
        with pytest.raises(ValueError, match="illegal pursuit transition"):
            pursuit.transition(PursuitState.WON, decided_by="user-1")

    def test_terminal_states_are_final(self) -> None:
        pursuit = make_pursuit(
            state=PursuitState.LOST,
            workspace_id=UUID("33333333-3333-4333-8333-333333333333"),
            decided_by="user-1",
            decided_at=datetime.now(UTC),
        )
        with pytest.raises(ValueError, match="illegal pursuit transition"):
            pursuit.transition(PursuitState.ACTIVE, decided_by="user-1")

    def test_tenant_scoped(self) -> None:
        pursuit = make_pursuit()
        assert pursuit.tenant_id == TENANT


class TestOutcome:
    def test_won_requires_evidence(self) -> None:
        with pytest.raises(ValueError, match="evidence_refs"):
            Outcome(
                outcome_id="out_test_000001",
                pursuit_id="prs_test_000001",
                tenant_id=TENANT,
                result="WON",
                decided_at=datetime.now(UTC),
            )

    def test_withdrawn_without_evidence_ok(self) -> None:
        outcome = Outcome(
            outcome_id="out_test_000001",
            pursuit_id="prs_test_000001",
            tenant_id=TENANT,
            result="WITHDRAWN",
            decided_at=datetime.now(UTC),
        )
        assert outcome.result == "WITHDRAWN"


class TestLearning:
    def test_requires_evidence(self) -> None:
        with pytest.raises(ValueError, match="evidence_refs"):
            Learning(
                learning_id="lrn_test_000001",
                tenant_id=TENANT,
                outcome_id="out_test_000001",
                insight="A lesson with no evidence",
            )

    def test_valid_learning(self) -> None:
        learning = Learning(
            learning_id="lrn_test_000001",
            tenant_id=TENANT,
            outcome_id="out_test_000001",
            insight="Deadline tracking reduced late submissions.",
            evidence_refs=["evidence-1"],
        )
        assert learning.tenant_id == TENANT


class TestWorkspaceFactory:
    def test_create_workspace(self) -> None:
        factory = WorkspaceFactory()
        workspace_id = UUID("33333333-3333-4333-8333-333333333333")
        workspace = factory.create(
            workspace_id=workspace_id,
            tenant_id=TENANT,
            pursuit=make_pursuit(),
            opportunity=make_opportunity(),
            subscriber_profile_version="v1",
            assessment_version="v1",
            created_by="user-1",
        )
        assert workspace.tenant_id == TENANT
        assert workspace.state == WorkspaceState.CREATED
        assert len(factory) == 1

    def test_tenant_isolation(self) -> None:
        factory = WorkspaceFactory()
        workspace_id = UUID("33333333-3333-4333-8333-333333333333")
        factory.create(
            workspace_id=workspace_id,
            tenant_id=TENANT,
            pursuit=make_pursuit(),
            opportunity=make_opportunity(),
            subscriber_profile_version="v1",
            assessment_version="v1",
            created_by="user-1",
        )
        assert factory.get_for_tenant(workspace_id, TENANT) is not None
        assert factory.get_for_tenant(workspace_id, OTHER_TENANT) is None

    def test_pursuit_tenant_mismatch_rejected(self) -> None:
        factory = WorkspaceFactory()
        with pytest.raises(ValueError, match="tenant"):
            factory.create(
                workspace_id=UUID("33333333-3333-4333-8333-333333333333"),
                tenant_id=OTHER_TENANT,
                pursuit=make_pursuit(),
                opportunity=make_opportunity(),
                subscriber_profile_version="v1",
                assessment_version="v1",
                created_by="user-1",
            )

    def test_pursuit_opportunity_mismatch_rejected(self) -> None:
        factory = WorkspaceFactory()
        with pytest.raises(ValueError, match="opportunity"):
            factory.create(
                workspace_id=UUID("33333333-3333-4333-8333-333333333333"),
                tenant_id=TENANT,
                pursuit=make_pursuit(opportunity_id="opp-other"),
                opportunity=make_opportunity(),
                subscriber_profile_version="v1",
                assessment_version="v1",
                created_by="user-1",
            )

    def test_rollback(self) -> None:
        factory = WorkspaceFactory()
        workspace_id = UUID("33333333-3333-4333-8333-333333333333")
        original = factory.create(
            workspace_id=workspace_id,
            tenant_id=TENANT,
            pursuit=make_pursuit(),
            opportunity=make_opportunity(),
            subscriber_profile_version="v1",
            assessment_version="v1",
            created_by="user-1",
        )
        # Simulate a later version being applied via the factory contract.
        modified = original.model_copy(update={"assessment_version": "v2"})
        factory._workspaces[workspace_id] = modified
        rolled_back = factory.rollback(
            workspace_id, tenant_id=TENANT, prior=original
        )
        assert rolled_back.assessment_version == "v1"

    def test_rollback_foreign_tenant_rejected(self) -> None:
        factory = WorkspaceFactory()
        workspace_id = UUID("33333333-3333-4333-8333-333333333333")
        original = factory.create(
            workspace_id=workspace_id,
            tenant_id=TENANT,
            pursuit=make_pursuit(),
            opportunity=make_opportunity(),
            subscriber_profile_version="v1",
            assessment_version="v1",
            created_by="user-1",
        )
        with pytest.raises(ValueError, match="workspace not found"):
            factory.rollback(workspace_id, tenant_id=OTHER_TENANT, prior=original)
