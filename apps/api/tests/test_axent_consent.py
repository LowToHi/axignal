from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from axignal_api.axent_consent import (
    ConsentError,
    canonical_hash,
    issue_confirmation_token,
    verify_confirmation_token,
)

TENANT_ID = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
CONVERSATION_ID = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
CONFIRMATION_ID = UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc")
SECRET = "axent-test-secret-that-is-at-least-thirty-two-bytes"
NOW = datetime(2026, 8, 3, 12, 0, tzinfo=UTC)
PARAMETERS_HASH = canonical_hash({"workspace_id": "workspace-1"})
STATE_HASH = canonical_hash({"state": "ACTIVE", "revision": 4})


def _issue():
    return issue_confirmation_token(
        confirmation_id=CONFIRMATION_ID,
        tenant_id=TENANT_ID,
        conversation_id=CONVERSATION_ID,
        subject="usr_owner",
        action_type="archive_workspace",
        parameters_hash=PARAMETERS_HASH,
        before_state_hash=STATE_HASH,
        assurance_level="AAL2",
        secret=SECRET,
        now=NOW,
    )[0]


def test_confirmation_token_is_bound_to_authority_action_and_state() -> None:
    claims = verify_confirmation_token(
        _issue(),
        secret=SECRET,
        expected_tenant_id=TENANT_ID,
        expected_conversation_id=CONVERSATION_ID,
        expected_subject="usr_owner",
        expected_action_type="archive_workspace",
        expected_parameters_hash=PARAMETERS_HASH,
        expected_before_state_hash=STATE_HASH,
        now=NOW + timedelta(minutes=1),
    )
    assert claims.confirmation_id == CONFIRMATION_ID
    assert claims.expires_at == NOW + timedelta(minutes=5)


def test_confirmation_token_rejects_parameter_substitution() -> None:
    with pytest.raises(ConsentError, match="parameters_mismatch"):
        verify_confirmation_token(
            _issue(),
            secret=SECRET,
            expected_tenant_id=TENANT_ID,
            expected_conversation_id=CONVERSATION_ID,
            expected_subject="usr_owner",
            expected_action_type="archive_workspace",
            expected_parameters_hash=canonical_hash({"workspace_id": "workspace-2"}),
            expected_before_state_hash=STATE_HASH,
            now=NOW + timedelta(minutes=1),
        )


def test_confirmation_token_rejects_tampering_and_expiry() -> None:
    token = _issue()
    tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
    with pytest.raises(ConsentError, match="signature_invalid"):
        verify_confirmation_token(
            tampered,
            secret=SECRET,
            expected_tenant_id=TENANT_ID,
            expected_conversation_id=CONVERSATION_ID,
            expected_subject="usr_owner",
            expected_action_type="archive_workspace",
            expected_parameters_hash=PARAMETERS_HASH,
            expected_before_state_hash=STATE_HASH,
            now=NOW + timedelta(minutes=1),
        )
    with pytest.raises(ConsentError, match="expired"):
        verify_confirmation_token(
            token,
            secret=SECRET,
            expected_tenant_id=TENANT_ID,
            expected_conversation_id=CONVERSATION_ID,
            expected_subject="usr_owner",
            expected_action_type="archive_workspace",
            expected_parameters_hash=PARAMETERS_HASH,
            expected_before_state_hash=STATE_HASH,
            now=NOW + timedelta(minutes=6),
        )
