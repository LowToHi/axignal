from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from axignal_api.identity import AuthenticatedIdentity
from axignal_api.settings import Settings
from axignal_api.validation import (
    CompleteValidationSessionRequest,
    StartValidationSessionRequest,
    ValidationEventRequest,
    participant_hash,
)


def identity(subject: str = "usr-qualified-1") -> AuthenticatedIdentity:
    now = datetime.now(UTC)
    return AuthenticatedIdentity(
        subject=subject,
        email="qualified@example.com",
        tenant_id=UUID("11111111-1111-4111-8111-111111111111"),
        issued_at=now,
        expires_at=now + timedelta(minutes=1),
    )


def test_participant_hash_is_stable_and_excludes_email() -> None:
    salt = "validation-salt-with-more-than-32-bytes"
    first = participant_hash(identity(), salt)
    changed_email = identity()
    object.__setattr__(changed_email, "email", "different@example.com")
    assert participant_hash(changed_email, salt) == first
    assert first.startswith("sha256:")
    assert "qualified" not in first
    assert "example.com" not in first
    assert participant_hash(identity("usr-qualified-2"), salt) != first


def test_validation_commands_are_structured() -> None:
    command = StartValidationSessionRequest(
        task_id="F1-AUTHORITY-001",
        participant_profile="DOMAIN_EXPERT",
    )
    assert command.task_id == "F1-AUTHORITY-001"
    event = ValidationEventRequest(
        event_type="EVIDENCE_INSPECTED",
        idempotency_key="evidence-1",
        payload={"evidence_id": "EV-1"},
    )
    assert event.payload == {"evidence_id": "EV-1"}
    complete = CompleteValidationSessionRequest(
        authority_layer="CANONICAL_CLAIM",
        evidence_ids=["EV-1"],
        unknown_ids=["UNKNOWN-1"],
        confidence=80,
        answer="Structured answer",
    )
    assert complete.confidence == 80


def test_validation_rejects_invalid_confidence() -> None:
    with pytest.raises(ValueError):
        CompleteValidationSessionRequest(
            authority_layer="CANONICAL_CLAIM",
            confidence=101,
        )


def test_require_validation_is_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AXIGNAL_VALIDATION_ENABLED", "true")
    monkeypatch.setenv(
        "AXIGNAL_VALIDATION_DATABASE_URL",
        "postgresql://validation@example/axignal",
    )
    monkeypatch.setenv("AXIGNAL_VALIDATION_PARTICIPANT_SALT", "short")
    with pytest.raises(RuntimeError, match="at least 32 bytes"):
        Settings.from_env().require_validation()
