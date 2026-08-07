"""WP5 — O01 Bid Workspace tests (T08-T11)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest

from axignal_api.o01_bid_workspace import (
    ApprovalRecord,
    BidWorkspace,
    BidWorkspaceState,
    HandoffRecord,
    QualificationDecision,
    QualificationDimension,
    RelevanceEvidence,
)

TENANT = UUID("11111111-1111-4111-8111-111111111111")
WS_ID = UUID("33333333-3333-4333-8333-333333333333")


def full_dimensions() -> dict[QualificationDimension, float]:
    return {
        QualificationDimension.FIT: 0.8,
        QualificationDimension.COMPETITION: 0.6,
        QualificationDimension.CAPACITY: 0.7,
        QualificationDimension.TIMING: 0.9,
        QualificationDimension.VALUE: 0.5,
    }


class TestRelevanceAndQualification:
    def test_evidence_requires_refs(self) -> None:
        with pytest.raises(ValueError, match="evidence_refs"):
            RelevanceEvidence(
                evidence_id="ev-1",
                opportunity_id="opp-1",
                dimension=QualificationDimension.FIT,
                score=0.8,
                basis="Strong fit with capability profile.",
            )

    def test_evidence_with_refs_ok(self) -> None:
        evidence = RelevanceEvidence(
            evidence_id="ev-1",
            opportunity_id="opp-1",
            dimension=QualificationDimension.FIT,
            score=0.8,
            basis="Strong fit with capability profile.",
            evidence_refs=["evidence-1"],
        )
        assert evidence.score == 0.8

    def test_score_bounds(self) -> None:
        with pytest.raises(ValueError):
            RelevanceEvidence(
                evidence_id="ev-1",
                opportunity_id="opp-1",
                dimension=QualificationDimension.FIT,
                score=1.5,
                basis="x" * 20,
                evidence_refs=["evidence-1"],
            )

    def test_qualification_requires_all_five_dimensions(self) -> None:
        with pytest.raises(ValueError, match="five dimensions"):
            QualificationDecision(
                decision_id="dec-1",
                opportunity_id="opp-1",
                dimensions={QualificationDimension.FIT: 0.8},
                overall="REVIEW",
                decided_by="user-1",
            )

    def test_go_requires_evidence(self) -> None:
        with pytest.raises(ValueError, match="evidence_ids"):
            QualificationDecision(
                decision_id="dec-1",
                opportunity_id="opp-1",
                dimensions=full_dimensions(),
                overall="GO",
                decided_by="user-1",
            )

    def test_valid_go_decision(self) -> None:
        decision = QualificationDecision(
            decision_id="dec-1",
            opportunity_id="opp-1",
            dimensions=full_dimensions(),
            overall="GO",
            decided_by="user-1",
            evidence_ids=["ev-1"],
        )
        assert decision.overall == "GO"
        assert len(decision.dimensions) == 5

    def test_no_opaque_single_score(self) -> None:
        # The contract prohibits one opaque opportunity score; the model
        # requires five dimensional scores plus evidence.
        decision = QualificationDecision(
            decision_id="dec-1",
            opportunity_id="opp-1",
            dimensions=full_dimensions(),
            overall="REVIEW",
            decided_by="user-1",
        )
        assert len(decision.dimensions) == 5
        assert decision.overall == "REVIEW"


class TestBidWorkspace:
    def test_draft_initial(self) -> None:
        workspace = BidWorkspace(
            workspace_id=WS_ID,
            tenant_id=TENANT,
            opportunity_id="opp-1",
            created_by="user-1",
        )
        assert workspace.state == BidWorkspaceState.DRAFT

    def test_qualified_requires_decision(self) -> None:
        with pytest.raises(ValueError, match="qualification_decision_id"):
            BidWorkspace(
                workspace_id=WS_ID,
                tenant_id=TENANT,
                opportunity_id="opp-1",
                state=BidWorkspaceState.QUALIFIED,
                created_by="user-1",
            )

    def test_approved_requires_authority(self) -> None:
        with pytest.raises(ValueError, match="approved_by"):
            BidWorkspace(
                workspace_id=WS_ID,
                tenant_id=TENANT,
                opportunity_id="opp-1",
                state=BidWorkspaceState.APPROVED,
                qualification_decision_id="dec-1",
                created_by="user-1",
            )

    def test_submitted_requires_handoff(self) -> None:
        with pytest.raises(ValueError, match="handoff_record_id"):
            BidWorkspace(
                workspace_id=WS_ID,
                tenant_id=TENANT,
                opportunity_id="opp-1",
                state=BidWorkspaceState.SUBMITTED,
                qualification_decision_id="dec-1",
                approved_by="user-1",
                approved_at=datetime.now(UTC),
                created_by="user-1",
            )

    def test_full_lifecycle(self) -> None:
        workspace = BidWorkspace(
            workspace_id=WS_ID,
            tenant_id=TENANT,
            opportunity_id="opp-1",
            created_by="user-1",
        )
        qualified = workspace.transition(BidWorkspaceState.QUALIFIED)
        ready = qualified.transition(BidWorkspaceState.READY_FOR_APPROVAL)
        approved = ready.transition(BidWorkspaceState.APPROVED)
        assert approved.state == BidWorkspaceState.APPROVED

    def test_illegal_skip(self) -> None:
        workspace = BidWorkspace(
            workspace_id=WS_ID,
            tenant_id=TENANT,
            opportunity_id="opp-1",
            created_by="user-1",
        )
        with pytest.raises(ValueError, match="illegal bid workspace transition"):
            workspace.transition(BidWorkspaceState.SUBMITTED)

    def test_submitted_is_terminal(self) -> None:
        workspace = BidWorkspace(
            workspace_id=WS_ID,
            tenant_id=TENANT,
            opportunity_id="opp-1",
            state=BidWorkspaceState.SUBMITTED,
            qualification_decision_id="dec-1",
            approved_by="user-1",
            approved_at=datetime.now(UTC),
            handoff_record_id="handoff-1",
            created_by="user-1",
        )
        with pytest.raises(ValueError, match="illegal bid workspace transition"):
            workspace.transition(BidWorkspaceState.WITHDRAWN)


class TestApproval:
    def test_external_presentation_requires_evidence(self) -> None:
        with pytest.raises(ValueError, match="evidence_refs"):
            ApprovalRecord(
                approval_id="appr-1",
                workspace_id=WS_ID,
                tenant_id=TENANT,
                approved_by="user-1",
                scope="EXTERNAL_PRESENTATION",
            )

    def test_submission_approval_ok(self) -> None:
        approval = ApprovalRecord(
            approval_id="appr-1",
            workspace_id=WS_ID,
            tenant_id=TENANT,
            approved_by="user-1",
        )
        assert approval.scope == "SUBMISSION"


class TestHandoff:
    def test_handoff_requires_target(self) -> None:
        with pytest.raises(ValueError, match="target"):
            HandoffRecord(
                handoff_id="handoff-1",
                workspace_id=WS_ID,
                tenant_id=TENANT,
                kind="SUBMISSION",
                target="",
                performed_by="user-1",
                approval_id="appr-1",
            )

    def test_valid_handoff(self) -> None:
        record = HandoffRecord(
            handoff_id="handoff-1",
            workspace_id=WS_ID,
            tenant_id=TENANT,
            kind="ACTIVATION",
            target="buyer-platform",
            performed_by="user-1",
            approval_id="appr-1",
            outcome_ref="out-1",
        )
        assert record.kind == "ACTIVATION"
        assert record.outcome_ref == "out-1"
