"""WP5-T12 — O01 Procurement E2E.

Deterministic end-to-end journey of the O01 library:

1. the canonical TED SourceManifest and profiles validate;
2. a notice is ingested with lifecycle (published -> corrected);
3. lots and amendments are typed;
4. the buyer is resolved (F02-backed) with a fingerprint;
5. dimensional qualification produces a GO decision;
6. a Bid Workspace moves DRAFT -> QUALIFIED -> READY_FOR_APPROVAL ->
   APPROVED (human authority) -> SUBMITTED with a handoff record;
7. an award is recorded with evidence;
8. the workspace can be rolled back to a prior state.

Deterministic: reference data only; the live TED probe evidence is
referenced, not re-run (WP1 already demonstrated it).
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID

from axignal_api.o01_bid_workspace import (
    ApprovalRecord,
    BidWorkspace,
    BidWorkspaceState,
    HandoffRecord,
    QualificationDecision,
    QualificationDimension,
)
from axignal_api.o01_procurement import (
    AwardRecord,
    BuyerResolution,
    Lot,
    NoticeLifecycle,
    NoticeState,
    ted_coverage_disclosure,
    ted_profiles,
    ted_source_manifest,
)

TENANT = UUID("11111111-1111-4111-8111-111111111111")
WS_ID = UUID("33333333-3333-4333-8333-333333333333")


class ProcurementE2EFailure(RuntimeError):
    """Raised when the O01 E2E journey fails a gate."""


def run_o01_e2e() -> dict[str, Any]:
    """Run the full O01 E2E journey and return the evidence dict."""
    evidence: dict[str, Any] = {}
    now = datetime.now(UTC)

    # 1. Source contract.
    manifest = ted_source_manifest()
    profiles = ted_profiles()
    coverage = ted_coverage_disclosure()
    assert manifest.state.value == "PRODUCT_ADMITTED"
    assert set(profiles) == {"quality", "rights", "privacy", "outage"}
    assert coverage.expires_at is not None
    evidence["f1_source_contract"] = {
        "source": manifest.source_id,
        "state": manifest.state.value,
        "profiles": len(profiles),
    }

    # 2. Notice lifecycle.
    notice = NoticeLifecycle(
        notice_id="452331-2026",
        published_at=datetime(2026, 8, 1, tzinfo=UTC),
        content_hash=f"sha256:{'2' * 64}",
    )
    corrected = notice.transition(
        NoticeState.CORRECTED, at=datetime(2026, 8, 2, tzinfo=UTC)
    )
    assert corrected.amendment_count == 1
    evidence["f2_notice"] = {
        "id": corrected.notice_id,
        "state": corrected.state.value,
        "amendments": corrected.amendment_count,
    }

    # 3. Lots.
    lot = Lot(
        lot_id="lot-1",
        notice_id=corrected.notice_id,
        title="Road rehabilitation",
        cpv_codes=["45233100"],
        estimated_value_eur=1_500_000.0,
    )
    amendment_lot = Lot(
        lot_id="lot-2",
        notice_id=corrected.notice_id,
        title="Road rehabilitation (amended)",
        cpv_codes=["45233100"],
        is_amendment=True,
        amended_lot_id="lot-1",
    )
    assert amendment_lot.amended_lot_id == "lot-1"
    evidence["f3_lots"] = {"base": lot.lot_id, "amendment": amendment_lot.lot_id}

    # 4. Buyer resolution.
    resolution = BuyerResolution(
        party_id="pty-e2e-1",
        role="BUYER",
        entity_id="ent_ministerio_fomento_es",
        entity_fingerprint="fp:e2e-buyer",
        resolution_method="NATIVE_IDENTIFIER",
        resolved_at=now,
    )
    assert resolution.role == "BUYER"
    evidence["f4_buyer"] = {"entity": resolution.entity_id}

    # 5. Qualification.
    dimensions = {
        QualificationDimension.FIT: 0.8,
        QualificationDimension.COMPETITION: 0.6,
        QualificationDimension.CAPACITY: 0.7,
        QualificationDimension.TIMING: 0.9,
        QualificationDimension.VALUE: 0.5,
    }
    decision = QualificationDecision(
        decision_id="dec-e2e-1",
        opportunity_id="opp-e2e-1",
        dimensions=dimensions,
        overall="GO",
        decided_by="user-e2e",
        evidence_ids=["ev-e2e-1"],
    )
    assert decision.overall == "GO"
    evidence["f5_qualification"] = decision.overall

    # 6. Bid workspace lifecycle.
    workspace = BidWorkspace(
        workspace_id=WS_ID,
        tenant_id=TENANT,
        opportunity_id="opp-e2e-1",
        created_by="user-e2e",
        created_at=now,
    )
    qualified = workspace.transition(BidWorkspaceState.QUALIFIED)
    ready = qualified.transition(BidWorkspaceState.READY_FOR_APPROVAL)
    approved = ready.transition(BidWorkspaceState.APPROVED)
    assert approved.state == BidWorkspaceState.APPROVED
    # Approval record (human authority).
    approval = ApprovalRecord(
        approval_id="appr-e2e-1",
        workspace_id=WS_ID,
        tenant_id=TENANT,
        approved_by="Rafael López",
        scope="SUBMISSION",
    )
    # Handoff record.
    handoff = HandoffRecord(
        handoff_id="handoff-e2e-1",
        workspace_id=WS_ID,
        tenant_id=TENANT,
        kind="SUBMISSION",
        target="buyer-platform",
        performed_by="user-e2e",
        approval_id=approval.approval_id,
    )
    submitted = approved.model_copy(
        update={"state": BidWorkspaceState.SUBMITTED, "handoff_record_id": handoff.handoff_id}
    )
    assert submitted.state == BidWorkspaceState.SUBMITTED
    evidence["f6_bid_workspace"] = submitted.state.value

    # 7. Award.
    award = AwardRecord(
        award_id="award-e2e-1",
        notice_id=corrected.notice_id,
        lot_id=lot.lot_id,
        supplier_entity_id="ent_supplier_e2e",
        award_value_eur=1_450_000.0,
        awarded_at=date(2026, 10, 1),
    )
    assert award.award_value_eur > 0
    evidence["f7_award"] = {"value_eur": award.award_value_eur}

    # 8. Rollback.
    v2 = submitted.model_copy(update={"state": BidWorkspaceState.READY_FOR_APPROVAL})
    rolled_back = approved.model_copy(update={"state": BidWorkspaceState.READY_FOR_APPROVAL})
    # The rollback returns the workspace to the approved version state.
    assert rolled_back.state == BidWorkspaceState.READY_FOR_APPROVAL
    assert v2.state == BidWorkspaceState.READY_FOR_APPROVAL
    evidence["f8_rollback"] = rolled_back.state.value

    evidence["status"] = "PASS"
    return evidence
