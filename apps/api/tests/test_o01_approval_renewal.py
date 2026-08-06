from datetime import UTC, datetime, timedelta

from axignal_api.o01_approval_renewal import (
    AuthorityDecisionValue,
    AuthorityEnvelope,
    AuthorityStatus,
    ChangeClass,
    RenewalPhase,
    TypedAuthorityDecision,
    classify_delta,
    evaluate_authority,
)

NOW = datetime(2026, 8, 1, 12, 0, tzinfo=UTC)
HEAD = "a" * 40
OTHER_HEAD = "b" * 40
MANIFEST = f"sha256:{'c' * 64}"


def decision(
    authority: str,
    *,
    value: AuthorityDecisionValue = AuthorityDecisionValue.APPROVE,
    head_sha: str = HEAD,
    expiry: datetime | None = None,
) -> TypedAuthorityDecision:
    return TypedAuthorityDecision(
        authority=authority,
        decision=value,
        scope="Bounded private O01 evidence campaign",
        manifest_digest=MANIFEST,
        head_sha=head_sha,
        timestamp=NOW - timedelta(hours=1),
        expiry=expiry or NOW + timedelta(days=30),
        conditions=("No public claims",),
        signature=f"signed-by-{authority.casefold()}",
    )


def envelope(
    *,
    head_sha: str = HEAD,
    expiry: datetime | None = None,
    privacy_value: AuthorityDecisionValue = AuthorityDecisionValue.APPROVE,
) -> AuthorityEnvelope:
    return AuthorityEnvelope(
        head_sha=head_sha,
        manifest_digest=MANIFEST,
        decisions=(
            decision("LEGAL", head_sha=head_sha, expiry=expiry),
            decision(
                "PRIVACY_DATA_RIGHTS",
                value=privacy_value,
                head_sha=head_sha,
                expiry=expiry,
            ),
        ),
    )


def evaluate(value: AuthorityEnvelope | None, *, now: datetime = NOW):
    return evaluate_authority(
        value,
        expected_head_sha=HEAD,
        expected_manifest_digest=MANIFEST,
        now=now,
        renewal_window_days=14,
        urgent_window_days=3,
    )


def test_missing_approval_never_authorises_execution() -> None:
    result = evaluate(None)
    assert result.status is AuthorityStatus.MISSING
    assert result.phase is RenewalPhase.NO_CURRENT_APPROVAL
    assert result.execution_authorised is False


def test_current_approval_is_active_before_renewal_window() -> None:
    result = evaluate(envelope(expiry=NOW + timedelta(days=30)))
    assert result.status is AuthorityStatus.ACTIVE
    assert result.phase is RenewalPhase.NOT_DUE
    assert result.execution_authorised is True


def test_renewal_window_and_urgent_window_are_distinct() -> None:
    expiring = evaluate(envelope(expiry=NOW + timedelta(days=10)))
    urgent = evaluate(envelope(expiry=NOW + timedelta(days=2)))
    assert expiring.status is AuthorityStatus.EXPIRING
    assert expiring.phase is RenewalPhase.RENEWAL_WINDOW_OPEN
    assert urgent.status is AuthorityStatus.URGENT
    assert urgent.phase is RenewalPhase.URGENT_RENEWAL
    assert expiring.execution_authorised is True
    assert urgent.execution_authorised is True


def test_expiry_has_zero_grace_period_and_fails_closed() -> None:
    expiry = NOW
    result = evaluate(envelope(expiry=expiry), now=expiry)
    assert result.status is AuthorityStatus.EXPIRED
    assert result.phase is RenewalPhase.EXPIRED
    assert result.execution_authorised is False


def test_head_or_manifest_binding_cannot_be_reused() -> None:
    result = evaluate(envelope(head_sha=OTHER_HEAD))
    assert result.status is AuthorityStatus.INVALID_BINDING
    assert result.execution_authorised is False


def test_any_rejection_blocks_execution() -> None:
    result = evaluate(
        envelope(privacy_value=AuthorityDecisionValue.REJECT)
    )
    assert result.status is AuthorityStatus.REJECTED
    assert result.execution_authorised is False


def terms(content_hash: str, *, status: str = "PASS") -> dict[str, dict[str, str]]:
    return {
        "ted-legal": {
            "status": status,
            "content_sha256": f"sha256:{content_hash * 64}",
        }
    }


def test_first_renewal_run_requires_baseline() -> None:
    result = classify_delta(
        current_relevant_files={"policy.json": "sha256:1"},
        previous_relevant_files=None,
        current_terms=terms("a"),
        previous_terms=None,
    )
    assert result.change_class is ChangeClass.BASELINE_REQUIRED


def test_terms_change_is_material_and_blocks_abbreviated_review() -> None:
    result = classify_delta(
        current_relevant_files={"policy.json": "sha256:1"},
        previous_relevant_files={"policy.json": "sha256:1"},
        current_terms=terms("b"),
        previous_terms=terms("a"),
    )
    assert result.change_class is ChangeClass.MATERIAL_TERMS_CHANGE


def test_authority_surface_change_is_detected() -> None:
    result = classify_delta(
        current_relevant_files={"policy.json": "sha256:2"},
        previous_relevant_files={"policy.json": "sha256:1"},
        current_terms=terms("a"),
        previous_terms=terms("a"),
    )
    assert result.change_class is ChangeClass.AUTHORITY_SURFACE_CHANGE
    assert result.changed_relevant_paths == ("policy.json",)


def test_unavailable_official_evidence_fails_closed() -> None:
    result = classify_delta(
        current_relevant_files={"policy.json": "sha256:1"},
        previous_relevant_files={"policy.json": "sha256:1"},
        current_terms=terms("a", status="UNAVAILABLE"),
        previous_terms=terms("a"),
    )
    assert result.change_class is ChangeClass.EVIDENCE_UNAVAILABLE


def test_unchanged_terms_and_authority_surface_allow_abbreviated_review() -> None:
    result = classify_delta(
        current_relevant_files={"policy.json": "sha256:1"},
        previous_relevant_files={"policy.json": "sha256:1"},
        current_terms=terms("a"),
        previous_terms=terms("a"),
    )
    assert result.change_class is ChangeClass.NO_MATERIAL_CHANGE
