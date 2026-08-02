from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from axignal_api.o01_source_admission_authority import (
    REQUIRED_AUTHORITIES,
    AdmissionDecisionValue,
    SourceAdmissionDecision,
    VerifiedDecision,
    build_github_identity_signature,
    evaluate_source_admission_authority,
    result_payload,
    verify_human_signature,
)

HEAD = "a" * 40
MANIFEST = "sha256:" + "b" * 64
UNSIGNED_SIGNATURE = "pending-signature-" + "0" * 64
EVIDENCE_EXPIRY = datetime(2026, 8, 29, 10, 2, 52, tzinfo=UTC)
DECISION_MAX = datetime(2026, 8, 28, 10, 0, tzinfo=UTC)
NOW = datetime(2026, 8, 2, 19, 31, tzinfo=UTC)
ISSUES = {
    "PRODUCT": 148,
    "SECURITY": 149,
    "PRIVACY_DATA_RIGHTS": 150,
    "LEGAL": 151,
    "SOURCE_QUALITY": 152,
    "UX_ACCESSIBILITY": 153,
    "HUMAN_COVERAGE_AUTHORITY": 154,
}
SCOPES = {
    authority: f"Approve bounded AX-LIB-O01 TED source admission as {authority}"
    for authority in REQUIRED_AUTHORITIES
}


def _decision(authority: str, *, value: str = "APPROVE") -> SourceAdmissionDecision:
    unsigned = SourceAdmissionDecision(
        authority=authority,
        decision=value,
        scope=SCOPES[authority],
        manifest_reference=MANIFEST,
        head_sha=HEAD,
        reviewed_at="2026-08-02T19:30:00Z",
        expires_at="2026-08-28T10:00:00Z",
        signature=UNSIGNED_SIGNATURE,
        conditions=("Preserve the frozen permanent boundary.",),
    )
    return unsigned.model_copy(
        update={
            "signature": build_github_identity_signature(
                unsigned,
                github_login="LowToHi",
            )
        }
    )


def _verified(authority: str, **overrides: object) -> VerifiedDecision:
    values = {
        "decision": _decision(authority),
        "issue_number": ISSUES[authority],
        "comment_id": 1000 + ISSUES[authority],
        "comment_url": (
            f"https://github.com/LowToHi/axignal/issues/"
            f"{ISSUES[authority]}#issuecomment-1"
        ),
        "comment_author": "LowToHi",
        "comment_user_type": "User",
        "comment_created_at": "2026-08-02T19:30:01Z",
        "comment_updated_at": "2026-08-02T19:30:01Z",
    }
    values.update(overrides)
    return VerifiedDecision(**values)


def _evaluate(decisions: dict[str, VerifiedDecision]):
    return evaluate_source_admission_authority(
        decisions,
        expected_head_sha=HEAD,
        expected_manifest_reference=MANIFEST,
        expected_issues=ISSUES,
        expected_scopes=SCOPES,
        evidence_expires_at=EVIDENCE_EXPIRY,
        decision_max_expires_at=DECISION_MAX,
        evidence_ready=True,
        now=NOW,
    )


def test_all_seven_current_human_approvals_admit() -> None:
    decisions = {authority: _verified(authority) for authority in REQUIRED_AUTHORITIES}
    evaluation = _evaluate(decisions)

    assert evaluation.admitted is True
    assert evaluation.status == "APPROVED_CURRENT"
    assert evaluation.signatures_human is True
    assert set(evaluation.authority_status.values()) == {"APPROVED_CURRENT"}

    payload = result_payload(
        evaluation,
        manifest_reference=MANIFEST,
        target_head_sha=HEAD,
        evidence_expires_at=EVIDENCE_EXPIRY,
        decision_sources=decisions,
    )
    assert payload["output"] == "O01_TED_SOURCE_ADMISSION_PASS"
    assert payload["next_state"] == "PRODUCT_ADMITTED"
    assert payload["bounded_product_use_authorised"] is True
    assert payload["bounded_claim_contribution"] is False
    assert payload["global_coverage_claim_authorised"] is False
    assert payload["public_launch"] == "NO_GO"


def test_missing_single_authority_blocks() -> None:
    decisions = {authority: _verified(authority) for authority in REQUIRED_AUTHORITIES}
    decisions.pop("SECURITY")

    evaluation = _evaluate(decisions)

    assert evaluation.admitted is False
    assert evaluation.status == "INCOMPLETE"
    assert evaluation.authority_status["SECURITY"] == "MISSING"


def test_rejection_blocks_without_marking_evidence_invalid() -> None:
    decisions = {authority: _verified(authority) for authority in REQUIRED_AUTHORITIES}
    rejected = _decision("LEGAL", value="REJECT")
    decisions["LEGAL"] = _verified("LEGAL", decision=rejected)

    evaluation = _evaluate(decisions)

    assert evaluation.admitted is False
    assert evaluation.evidence_ready is True
    assert evaluation.authority_status["LEGAL"] == "REJECTED_CURRENT"
    assert any("rejected by: LEGAL" in reason for reason in evaluation.reasons)


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("issue_number", 999, "assigned authority issue"),
        ("comment_user_type", "Bot", "human GitHub identity"),
        ("comment_author", "someone-else", "human GitHub identity"),
    ],
)
def test_identity_and_issue_binding_fail_closed(
    field: str,
    value: object,
    reason: str,
) -> None:
    decisions = {authority: _verified(authority) for authority in REQUIRED_AUTHORITIES}
    decisions["PRODUCT"] = _verified("PRODUCT", **{field: value})

    evaluation = _evaluate(decisions)

    assert evaluation.admitted is False
    assert any(reason in item for item in evaluation.reasons)


def test_scope_head_manifest_and_evidence_are_independent_gates() -> None:
    decisions = {authority: _verified(authority) for authority in REQUIRED_AUTHORITIES}
    bad = _decision("PRODUCT").model_copy(
        update={
            "scope": "A different but sufficiently long product authority scope",
            "head_sha": "c" * 40,
            "manifest_reference": "sha256:" + "d" * 64,
        }
    )
    bad = bad.model_copy(
        update={
            "signature": build_github_identity_signature(
                bad,
                github_login="LowToHi",
            )
        }
    )
    decisions["PRODUCT"] = _verified("PRODUCT", decision=bad)

    evaluation = _evaluate(decisions)

    assert evaluation.admitted is False
    assert evaluation.scope_match is False
    assert evaluation.head_match is False
    assert evaluation.manifest_match is False

    no_evidence = evaluate_source_admission_authority(
        {authority: _verified(authority) for authority in REQUIRED_AUTHORITIES},
        expected_head_sha=HEAD,
        expected_manifest_reference=MANIFEST,
        expected_issues=ISSUES,
        expected_scopes=SCOPES,
        evidence_expires_at=EVIDENCE_EXPIRY,
        decision_max_expires_at=DECISION_MAX,
        evidence_ready=False,
        evidence_reasons=("Campaign closure digest mismatch",),
        now=NOW,
    )
    assert no_evidence.admitted is False
    assert "Campaign closure digest mismatch" in no_evidence.reasons


def test_signature_digest_changes_with_conditions() -> None:
    decision = _decision("SOURCE_QUALITY")
    assert verify_human_signature(
        decision,
        comment_author="LowToHi",
        comment_user_type="User",
    )

    changed = decision.model_copy(update={"conditions": ("A different condition.",)})
    assert not verify_human_signature(
        changed,
        comment_author="LowToHi",
        comment_user_type="User",
    )


def test_model_rejects_extra_fields_and_naive_time() -> None:
    payload = _decision("PRODUCT").model_dump(mode="json")
    payload["unexpected"] = True
    with pytest.raises(ValidationError):
        SourceAdmissionDecision.model_validate(payload)

    payload.pop("unexpected")
    payload["reviewed_at"] = "2026-08-02T19:30:00"
    with pytest.raises(ValidationError):
        SourceAdmissionDecision.model_validate(payload)


def test_decision_enum_accepts_approve_with_conditions() -> None:
    decision = _decision("SECURITY", value="APPROVE_WITH_CONDITIONS")
    assert decision.decision is AdmissionDecisionValue.APPROVE_WITH_CONDITIONS
