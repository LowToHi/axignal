"""WP16 — Public Employment architectural proof tests."""

from __future__ import annotations

from datetime import date
from uuid import UUID

import pytest

from axignal_api.public_employment import (
    ApplicationWorkspace,
    CandidateRecord,
    CandidateState,
    EligibilityPolicy,
    ExamCall,
    ShellManifest,
    roles_capabilities,
    routes,
    vocabulary,
)

TENANT = UUID("11111111-1111-4111-8111-111111111111")
WS_ID = UUID("33333333-3333-4333-8333-333333333333")


class TestShellManifest:
    def test_draft_gate_default(self) -> None:
        manifest = ShellManifest()
        assert manifest.indexable is False
        assert manifest.checkout_enabled is False
        assert manifest.public_copy is False
        assert manifest.public_launch_authorized is False
        assert manifest.live_billing is False
        assert manifest.manifest_version == "0.1.0-draft"

    def test_indexable_rejected(self) -> None:
        with pytest.raises(ValueError, match="hidden/non-indexable"):
            ShellManifest(indexable=True)

    def test_checkout_rejected(self) -> None:
        with pytest.raises(ValueError, match="hidden/non-indexable"):
            ShellManifest(checkout_enabled=True)

    def test_launch_authorization_rejected(self) -> None:
        with pytest.raises(ValueError, match="no launch"):
            ShellManifest(public_launch_authorized=True)

    def test_live_billing_rejected(self) -> None:
        with pytest.raises(ValueError, match="no launch"):
            ShellManifest(live_billing=True)


class TestDomainModel:
    def test_candidate_eligibility_requires_ruleset(self) -> None:
        with pytest.raises(ValueError, match="eligibility_ruleset"):
            CandidateRecord(
                candidate_id="cand-1",
                tenant_id=TENANT,
                state="ELIGIBLE",
            )

    def test_valid_candidate(self) -> None:
        candidate = CandidateRecord(
            candidate_id="cand-1",
            tenant_id=TENANT,
            state="ELIGIBLE",
            eligibility_ruleset="rules-2026",
        )
        assert candidate.state == CandidateState.ELIGIBLE

    def test_call_cannot_be_published(self) -> None:
        with pytest.raises(ValueError, match="cannot be published"):
            ExamCall(
                call_id="call-1",
                title="Convocatoria 2026",
                jurisdiction_id="ES",
                published=True,
            )

    def test_valid_draft_call(self) -> None:
        call = ExamCall(
            call_id="call-1",
            title="Convocatoria 2026",
            jurisdiction_id="ES",
            opens_at=date(2026, 9, 1),
            closes_at=date(2026, 9, 30),
        )
        assert call.published is False

    def test_date_ordering(self) -> None:
        with pytest.raises(ValueError, match="opens_at"):
            ExamCall(
                call_id="call-1",
                title="Convocatoria",
                jurisdiction_id="ES",
                opens_at=date(2026, 9, 30),
                closes_at=date(2026, 9, 1),
            )

    def test_application_workspace(self) -> None:
        workspace = ApplicationWorkspace(
            workspace_id=WS_ID,
            tenant_id=TENANT,
            candidate_id="cand-1",
            call_id="call-1",
            created_by="user-1",
        )
        assert workspace.state == "DRAFT"


class TestEligibilityPolicy:
    def test_approved_requires_source(self) -> None:
        with pytest.raises(ValueError, match="source_ref"):
            EligibilityPolicy(policy_id="pol-1", ruleset="Rule set for 2026.", state="APPROVED")

    def test_draft_policy_ok(self) -> None:
        policy = EligibilityPolicy(policy_id="pol-1", ruleset="Rule set for 2026.")
        assert policy.state == "DRAFT"


class TestShellSurface:
    def test_routes_hidden(self) -> None:
        for route in routes():
            assert route["state"] == "DRAFT_HIDDEN"
            assert route["indexable"] == "false"

    def test_roles_capabilities(self) -> None:
        capabilities = roles_capabilities()
        assert set(capabilities) == {"candidate", "examiner", "admin"}

    def test_vocabulary(self) -> None:
        terms = vocabulary()
        assert terms["convocatoria"] == "call"
        assert terms["oposición"] == "competitive examination"
