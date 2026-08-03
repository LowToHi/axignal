from __future__ import annotations

from datetime import UTC, datetime

import pytest

from axignal_api.f01_rights_authority import (
    LEGAL_REQUIRED_ASSERTIONS,
    PRIVACY_REQUIRED_ASSERTIONS,
    F01RightsAuthorityDecision,
    RightsDecisionValue,
    VerifiedDecision,
    build_github_identity_signature,
    evaluate_f01_rights_authority,
    result_payload,
    verify_human_signature,
)

MANIFEST = "sha256:" + "1" * 64
HEAD = "a" * 40
REVIEWED = datetime(2026, 8, 3, 2, 0, tzinfo=UTC)
EXPIRES = datetime(2026, 8, 20, 2, 0, tzinfo=UTC)
EVIDENCE_EXPIRES = datetime(2026, 8, 31, 23, 59, 59, tzinfo=UTC)
DECISION_MAX = datetime(2026, 8, 30, 23, 59, 59, tzinfo=UTC)


def make_decision(
    authority: str,
    *,
    decision: RightsDecisionValue = RightsDecisionValue.APPROVE_WITH_CONDITIONS,
    assertions: dict[str, bool] | None = None,
    expires_at: datetime = EXPIRES,
) -> F01RightsAuthorityDecision:
    required = (
        LEGAL_REQUIRED_ASSERTIONS
        if authority == "LEGAL"
        else PRIVACY_REQUIRED_ASSERTIONS
    )
    unsigned = F01RightsAuthorityDecision(
        authority=authority,
        decision=decision,
        scope="Private bounded F01 evidence authority for the exact baseline only.",
        manifest_reference=MANIFEST,
        technical_head_sha=HEAD,
        reviewed_at=REVIEWED,
        expires_at=expires_at,
        signature="unsigned-placeholder-that-is-long-enough",
        conditions=("Preserve all fail-closed boundaries.",),
        assertions=dict(required if assertions is None else assertions),
    )
    signature = build_github_identity_signature(
        unsigned,
        github_login="human-reviewer",
    )
    return unsigned.model_copy(update={"signature": signature})


def verified(authority: str, comment_id: int) -> VerifiedDecision:
    return VerifiedDecision(
        decision=make_decision(authority),
        comment_id=comment_id,
        comment_url=f"https://example.invalid/comments/{comment_id}",
        comment_author="human-reviewer",
        comment_created_at="2026-08-03T02:00:00Z",
        comment_updated_at="2026-08-03T02:00:00Z",
    )


def test_signature_is_bound_to_human_github_identity() -> None:
    decision = make_decision("LEGAL")
    assert verify_human_signature(
        decision,
        comment_author="human-reviewer",
        comment_user_type="User",
    )
    assert not verify_human_signature(
        decision,
        comment_author="github-actions[bot]",
        comment_user_type="Bot",
    )


def test_authorising_decision_rejects_assertion_drift() -> None:
    drifted = dict(LEGAL_REQUIRED_ASSERTIONS)
    drifted["public_redistribution_permitted"] = True
    with pytest.raises(ValueError, match="safe contract"):
        make_decision("LEGAL", assertions=drifted)


def test_rejection_can_explain_a_negative_assertion() -> None:
    rejected = dict(LEGAL_REQUIRED_ASSERTIONS)
    rejected["private_access_permitted"] = False
    decision = make_decision(
        "LEGAL",
        decision=RightsDecisionValue.REJECT,
        assertions=rejected,
    )
    assert decision.decision is RightsDecisionValue.REJECT


def test_missing_authorities_remain_blocked() -> None:
    evaluation = evaluate_f01_rights_authority(
        {},
        expected_technical_head_sha=HEAD,
        expected_manifest_reference=MANIFEST,
        evidence_expires_at=EVIDENCE_EXPIRES,
        decision_max_expires_at=DECISION_MAX,
        now=REVIEWED,
    )
    assert evaluation.status == "MISSING"
    assert evaluation.campaign_authorised is False
    assert evaluation.legal == "MISSING"
    assert evaluation.privacy_data_rights == "MISSING"


def test_two_current_human_decisions_authorise_only_private_campaign() -> None:
    decisions = {
        "LEGAL": verified("LEGAL", 10),
        "PRIVACY_DATA_RIGHTS": verified("PRIVACY_DATA_RIGHTS", 11),
    }
    evaluation = evaluate_f01_rights_authority(
        decisions,
        expected_technical_head_sha=HEAD,
        expected_manifest_reference=MANIFEST,
        evidence_expires_at=EVIDENCE_EXPIRES,
        decision_max_expires_at=DECISION_MAX,
        now=REVIEWED,
    )
    assert evaluation.status == "APPROVED_CURRENT"
    assert evaluation.campaign_authorised is True
    result = result_payload(
        evaluation,
        manifest_reference=MANIFEST,
        technical_head_sha=HEAD,
        evidence_expires_at=EVIDENCE_EXPIRES,
        decision_sources=decisions,
    )
    assert result["output"] == "F01_PRIVATE_CAMPAIGN_AUTHORISED"
    assert result["authority_boundary"]["product_admitted"] is False
    assert result["authority_boundary"]["active_source"] is False
    assert result["authority_boundary"]["f01_state"] == "BLOCKED"
    assert result["authority_boundary"]["public_launch"] == "NO_GO"


def test_decision_outliving_evidence_is_blocked() -> None:
    late = datetime(2026, 9, 1, 0, 0, tzinfo=UTC)
    decisions = {
        "LEGAL": VerifiedDecision(
            decision=make_decision("LEGAL", expires_at=late),
            comment_id=10,
            comment_url=None,
            comment_author="human-reviewer",
            comment_created_at=None,
            comment_updated_at=None,
        ),
        "PRIVACY_DATA_RIGHTS": verified("PRIVACY_DATA_RIGHTS", 11),
    }
    evaluation = evaluate_f01_rights_authority(
        decisions,
        expected_technical_head_sha=HEAD,
        expected_manifest_reference=MANIFEST,
        evidence_expires_at=EVIDENCE_EXPIRES,
        decision_max_expires_at=DECISION_MAX,
        now=REVIEWED,
    )
    assert evaluation.campaign_authorised is False
    assert evaluation.expiry_within_evidence is False
