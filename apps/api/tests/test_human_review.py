from types import SimpleNamespace
from uuid import UUID

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from axignal_api.human_review import HumanReviewActionRequest, _reviewer_dsn


def _identity(subject: str) -> SimpleNamespace:
    return SimpleNamespace(
        subject=subject,
        email="reviewer@example.test",
        tenant_id=UUID("11111111-1111-4111-8111-111111111111"),
    )


def test_human_review_action_requires_structured_reason_code() -> None:
    with pytest.raises(ValidationError):
        HumanReviewActionRequest(
            action="ACCEPT_AS_CONTEXT",
            reason_code="free form reason",
        )
    command = HumanReviewActionRequest(
        action="ACCEPT_AS_CONTEXT",
        reason_code="LIMITATION_CONFIRMED",
    )
    assert command.reason_code == "LIMITATION_CONFIRMED"


def test_human_reviewer_identity_must_be_allowlisted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "AXIGNAL_HUMAN_REVIEW_DATABASE_URL",
        "postgresql://reviewer@localhost/axignal",
    )
    monkeypatch.setenv("AXIGNAL_HUMAN_REVIEWER_SUBJECTS", "usr_allowed")
    monkeypatch.setenv("AXIGNAL_PERSISTENT_RESEARCH_ENABLED", "true")
    assert _reviewer_dsn(_identity("usr_allowed")) == (
        "postgresql://reviewer@localhost/axignal"
    )
    with pytest.raises(HTTPException) as exc_info:
        _reviewer_dsn(_identity("usr_denied"))
    assert exc_info.value.status_code == 403
