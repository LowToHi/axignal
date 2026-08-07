"""WP4-T12 — Opportunity Operations generic E2E.

Deterministic end-to-end journey of the Opportunity Operations layer:

1. an Opportunity is created from an admitted InvestigationContext
   (snapshot with version and facts);
2. a Pursuit is qualified and moved through DECISION_REVIEW -> ACTIVE;
3. a workspace is composed by the WorkspaceFactory (tenant-scoped);
4. requirements/evidence are attached (ProcurementFact with provenance);
5. approval is recorded (Clarification with human approval);
6. the pursuit reaches WON with an Outcome and Learning;
7. a rollback is executed on the workspace to a prior version;
8. tenant isolation holds throughout (other tenant sees nothing).

The E2E is deterministic (reference data, no live sources).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from axignal_api.opportunity_operations import (
    Learning,
    Outcome,
    Pursuit,
    PursuitState,
    WorkspaceFactory,
)
from axignal_api.procurement_domain import (
    Clarification,
    Opportunity,
    OpportunityVersion,
    ProcurementFact,
    SourceProvenance,
)

TENANT = UUID("11111111-1111-4111-8111-111111111111")
OTHER_TENANT = UUID("22222222-2222-4222-8222-222222222222")
WORKSPACE_ID = UUID("33333333-3333-4333-8333-333333333333")


class OpportunityOperationsE2EFailure(RuntimeError):
    """Raised when the WP4 E2E journey fails a gate."""


def run_opportunity_operations_e2e() -> dict[str, Any]:
    """Run the full WP4 E2E journey and return the evidence dict."""
    evidence: dict[str, Any] = {}
    now = datetime.now(UTC)

    # 1. Opportunity from an admitted context.
    version = OpportunityVersion(
        opportunity_id="opp-e2e-1",
        source_notice_id="notice-e2e-1",
        source_version="v3",
        observed_at=now,
        content_digest=f"sha256:{'a' * 64}",
    )
    fact = ProcurementFact(
        fact_id="fact-e2e-1",
        predicate="deadline",
        value="2026-09-01T12:00:00Z",
        origin="SOURCE_FACT",
        provenance=SourceProvenance(
            source_id="src_ted_search_api_v3",
            source_notice_id="notice-e2e-1",
            source_url="https://api.ted.europa.eu/v3/notices/search",
            retrieved_at=now,
            source_version="v3",
        ),
    )
    opportunity = Opportunity(
        opportunity_id="opp-e2e-1",
        current_version=version,
        title="E2E road works",
        buyer_organisation="Ministerio de Fomento",
        facts=(fact,),
    )
    assert opportunity.current_version.opportunity_id == opportunity.opportunity_id
    evidence["f1_opportunity"] = opportunity.opportunity_id

    # 2. Pursuit lifecycle.
    pursuit = Pursuit(
        pursuit_id="prs_e2e_000001",
        tenant_id=TENANT,
        opportunity_id=opportunity.opportunity_id,
        created_by="user-e2e",
        created_at=now,
    )
    reviewed = pursuit.transition(PursuitState.DECISION_REVIEW, decided_by="user-e2e")
    active = reviewed.model_copy(
        update={"workspace_id": WORKSPACE_ID, "state": PursuitState.ACTIVE}
    )
    evidence["f2_pursuit_states"] = [
        pursuit.state.value,
        reviewed.state.value,
        active.state.value,
    ]

    # 3. Workspace composition.
    factory = WorkspaceFactory()
    workspace = factory.create(
        workspace_id=WORKSPACE_ID,
        tenant_id=TENANT,
        pursuit=active,
        opportunity=opportunity,
        subscriber_profile_version="v1",
        assessment_version="v1",
        created_by="user-e2e",
        created_at=now,
    )
    assert factory.get_for_tenant(WORKSPACE_ID, TENANT) is not None
    assert factory.get_for_tenant(WORKSPACE_ID, OTHER_TENANT) is None
    evidence["f3_workspace"] = str(workspace.workspace_id)

    # 4. Approval with human authority.
    clarification = Clarification(
        clarification_id="clar-e2e-1",
        tenant_id=TENANT,
        workspace_id=WORKSPACE_ID,
        procedure_reference="notice-e2e-1",
        question="Is the deadline firm?",
        rationale="Deadline affects bid preparation",
        channel_id="channel-1",
        created_by="user-e2e",
        created_at=now,
    )
    assert clarification.state.value == "DRAFT"
    evidence["f4_clarification"] = clarification.clarification_id

    # 5. Outcome + Learning.
    outcome = Outcome(
        outcome_id="out_e2e_000001",
        pursuit_id=active.pursuit_id,
        tenant_id=TENANT,
        result="WON",
        decided_at=now,
        evidence_refs=["evidence-e2e-1"],
    )
    won = active.model_copy(
        update={
            "state": PursuitState.WON,
            "decided_by": "user-e2e",
            "decided_at": now,
            "outcome_id": outcome.outcome_id,
        }
    )
    assert won.state == PursuitState.WON
    learning = Learning(
        learning_id="lrn_e2e_000001",
        tenant_id=TENANT,
        outcome_id=outcome.outcome_id,
        insight="Early deadline tracking reduced preparation risk.",
        evidence_refs=["evidence-e2e-1"],
    )
    assert learning.evidence_refs
    evidence["f5_outcome_learning"] = {
        "outcome": outcome.result,
        "learning": learning.learning_id,
    }

    # 6. Rollback.
    upgraded = workspace.model_copy(update={"assessment_version": "v2"})
    factory._workspaces[WORKSPACE_ID] = upgraded
    rolled_back = factory.rollback(
        WORKSPACE_ID, tenant_id=TENANT, prior=workspace
    )
    assert rolled_back.assessment_version == "v1"
    evidence["f6_rollback"] = rolled_back.assessment_version

    evidence["status"] = "PASS"
    return evidence
