from __future__ import annotations

from datetime import UTC, datetime, timedelta

from axignal_api.o01_campaign_authority import (
    CampaignAuthorityDecision,
    CampaignDecisionValue,
    VerifiedDecision,
    build_github_identity_signature,
    evaluate_campaign_authority,
    verify_human_signature,
)

HEAD = "b754b5641e5f17c5a084434aace4f939a4be0e84"
MANIFEST = "sha256:" + "1" * 64
NOW = datetime(2026, 8, 2, 1, tzinfo=UTC)
EVIDENCE_EXPIRY = datetime(2026, 8, 29, tzinfo=UTC)
DECISION_MAX = datetime(2026, 8, 28, tzinfo=UTC)


def make_decision(
    authority: str,
    *,
    decision: CampaignDecisionValue = CampaignDecisionValue.APPROVE,
    head_sha: str = HEAD,
    manifest_reference: str = MANIFEST,
    reviewed_at: datetime = NOW - timedelta(minutes=1),
    expires_at: datetime = NOW + timedelta(days=5),
    login: str = "human-reviewer",
) -> CampaignAuthorityDecision:
    unsigned = CampaignAuthorityDecision(
        authority=authority,
        decision=decision,
        scope="AX-LIB-O01 private bounded evidence campaign only",
        manifest_reference=manifest_reference,
        head_sha=head_sha,
        reviewed_at=reviewed_at,
        expires_at=expires_at,
        signature="pending-signature-value-that-is-long-enough",
        conditions=("No public claims or source admission",),
    )
    return unsigned.model_copy(
        update={
            "signature": build_github_identity_signature(
                unsigned,
                github_login=login,
            )
        }
    )


def verified(decision: CampaignAuthorityDecision, comment_id: int) -> VerifiedDecision:
    return VerifiedDecision(
        decision=decision,
        comment_id=comment_id,
        comment_url=f"https://example.test/{comment_id}",
        comment_author="human-reviewer",
        comment_created_at="2026-08-02T00:59:00Z",
        comment_updated_at="2026-08-02T00:59:00Z",
    )


def evaluate(decisions: dict[str, VerifiedDecision]):
    return evaluate_campaign_authority(
        decisions,
        expected_head_sha=HEAD,
        expected_manifest_reference=MANIFEST,
        evidence_expires_at=EVIDENCE_EXPIRY,
        decision_max_expires_at=DECISION_MAX,
        now=NOW,
    )


def test_github_identity_signature_round_trip() -> None:
    item = make_decision("LEGAL")
    assert verify_human_signature(
        item,
        comment_author="human-reviewer",
        comment_user_type="User",
    )


def test_bot_or_wrong_author_cannot_satisfy_human_signature() -> None:
    item = make_decision("LEGAL")
    assert not verify_human_signature(
        item,
        comment_author="human-reviewer",
        comment_user_type="Bot",
    )
    assert not verify_human_signature(
        item,
        comment_author="another-human",
        comment_user_type="User",
    )


def test_both_current_approvals_authorise_only_campaign_execution() -> None:
    result = evaluate(
        {
            "LEGAL": verified(make_decision("LEGAL"), 1),
            "PRIVACY_DATA_RIGHTS": verified(
                make_decision("PRIVACY_DATA_RIGHTS"), 2
            ),
        }
    )
    assert result.status == "APPROVED_CURRENT"
    assert result.execution_authorised is True
    assert result.head_match is True
    assert result.manifest_match is True
    assert result.signatures_human is True
    assert result.expiry_within_evidence is True


def test_approve_with_conditions_is_authorising() -> None:
    result = evaluate(
        {
            "LEGAL": verified(
                make_decision(
                    "LEGAL",
                    decision=CampaignDecisionValue.APPROVE_WITH_CONDITIONS,
                ),
                1,
            ),
            "PRIVACY_DATA_RIGHTS": verified(
                make_decision("PRIVACY_DATA_RIGHTS"), 2
            ),
        }
    )
    assert result.execution_authorised is True


def test_rejection_blocks_campaign() -> None:
    result = evaluate(
        {
            "LEGAL": verified(
                make_decision("LEGAL", decision=CampaignDecisionValue.REJECT),
                1,
            ),
            "PRIVACY_DATA_RIGHTS": verified(
                make_decision("PRIVACY_DATA_RIGHTS"), 2
            ),
        }
    )
    assert result.execution_authorised is False
    assert result.legal == "REJECTED_CURRENT"


def test_wrong_head_or_manifest_blocks_campaign() -> None:
    result = evaluate(
        {
            "LEGAL": verified(make_decision("LEGAL", head_sha="a" * 40), 1),
            "PRIVACY_DATA_RIGHTS": verified(
                make_decision("PRIVACY_DATA_RIGHTS"), 2
            ),
        }
    )
    assert result.execution_authorised is False
    assert result.head_match is False


def test_decision_must_expire_strictly_before_evidence() -> None:
    result = evaluate(
        {
            "LEGAL": verified(
                make_decision("LEGAL", expires_at=EVIDENCE_EXPIRY), 1
            ),
            "PRIVACY_DATA_RIGHTS": verified(
                make_decision("PRIVACY_DATA_RIGHTS"), 2
            ),
        }
    )
    assert result.execution_authorised is False
    assert result.expiry_within_evidence is False


def test_missing_authority_is_fail_closed() -> None:
    result = evaluate({"LEGAL": verified(make_decision("LEGAL"), 1)})
    assert result.status == "INCOMPLETE"
    assert result.execution_authorised is False
    assert result.signatures_human is False


def test_future_review_or_expired_decision_blocks() -> None:
    future = evaluate(
        {
            "LEGAL": verified(
                make_decision("LEGAL", reviewed_at=NOW + timedelta(minutes=1)), 1
            ),
            "PRIVACY_DATA_RIGHTS": verified(
                make_decision("PRIVACY_DATA_RIGHTS"), 2
            ),
        }
    )
    assert future.execution_authorised is False
    expired = evaluate(
        {
            "LEGAL": verified(
                make_decision(
                    "LEGAL",
                    reviewed_at=NOW - timedelta(days=2),
                    expires_at=NOW - timedelta(days=1),
                ),
                1,
            ),
            "PRIVACY_DATA_RIGHTS": verified(
                make_decision("PRIVACY_DATA_RIGHTS"), 2
            ),
        }
    )
    assert expired.execution_authorised is False
