from uuid import UUID

from fastapi.testclient import TestClient

from axignal_api.application import app
from axignal_api.identity import build_identity_assertion
from axignal_api.retention_config import RetentionSettings

TENANT_ID = UUID("11111111-1111-4111-8111-111111111111")
OTHER_TENANT_ID = UUID("22222222-2222-4222-8222-222222222222")
IDENTITY_SECRET = "test-retention-identity-secret-with-at-least-32-bytes"


def identity_headers() -> dict[str, str]:
    return {
        "X-AXIGNAL-Identity-Assertion": build_identity_assertion(
            secret=IDENTITY_SECRET,
            subject="usr_retention_test",
            email="retention@example.test",
            tenant_id=TENANT_ID,
        )
    }


def test_retention_runtime_is_disabled_and_unconfigured_by_default(monkeypatch) -> None:
    for name in (
        "AXIGNAL_RETENTION_DATABASE_URL",
        "AXIGNAL_DATABASE_URL",
        "AXIGNAL_DELETION_REQUESTS_ENABLED",
        "AXIGNAL_PURGE_WORKER_ENABLED",
        "AXIGNAL_OPERATOR_SUSPENSION_ENABLED",
        "AXIGNAL_TRIAL_RETENTION_SECONDS",
    ):
        monkeypatch.delenv(name, raising=False)
    settings = RetentionSettings.from_env()
    assert settings.database_url is None
    assert settings.deletion_requests_enabled is False
    assert settings.purge_worker_enabled is False
    assert settings.operator_suspension_enabled is False
    assert settings.retention_seconds == 0


def test_deletion_request_requires_authenticated_identity(monkeypatch) -> None:
    monkeypatch.setenv("AXIGNAL_IDENTITY_ASSERTION_SECRET", IDENTITY_SECRET)
    response = TestClient(app).post(
        "/v1/workspace/deletion-requests",
        json={"confirm_permanent_deletion": True},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Authenticated identity is required"


def test_deletion_request_rejects_client_tenant_injection(monkeypatch) -> None:
    monkeypatch.setenv("AXIGNAL_IDENTITY_ASSERTION_SECRET", IDENTITY_SECRET)
    response = TestClient(app).post(
        "/v1/workspace/deletion-requests",
        headers=identity_headers(),
        json={
            "confirm_permanent_deletion": True,
            "tenant_id": str(OTHER_TENANT_ID),
        },
    )
    assert response.status_code == 422
    locations = [tuple(item["loc"]) for item in response.json()["detail"]]
    assert ("body", "tenant_id") in locations


def test_deletion_request_fails_closed_when_disabled(monkeypatch) -> None:
    monkeypatch.setenv("AXIGNAL_IDENTITY_ASSERTION_SECRET", IDENTITY_SECRET)
    monkeypatch.setenv(
        "AXIGNAL_RETENTION_DATABASE_URL",
        "postgresql://example.invalid/axignal",
    )
    monkeypatch.setenv("AXIGNAL_TRIAL_RETENTION_SECONDS", "3600")
    monkeypatch.delenv("AXIGNAL_DELETION_REQUESTS_ENABLED", raising=False)
    response = TestClient(app).post(
        "/v1/workspace/deletion-requests",
        headers=identity_headers(),
        json={"confirm_permanent_deletion": True},
    )
    assert response.status_code == 503
    assert response.json()["detail"] == "Workspace deletion requests are disabled"


def test_deletion_request_requires_explicit_retention_policy(monkeypatch) -> None:
    monkeypatch.setenv("AXIGNAL_IDENTITY_ASSERTION_SECRET", IDENTITY_SECRET)
    monkeypatch.setenv(
        "AXIGNAL_RETENTION_DATABASE_URL",
        "postgresql://example.invalid/axignal",
    )
    monkeypatch.setenv("AXIGNAL_DELETION_REQUESTS_ENABLED", "true")
    monkeypatch.delenv("AXIGNAL_TRIAL_RETENTION_SECONDS", raising=False)
    response = TestClient(app).post(
        "/v1/workspace/deletion-requests",
        headers=identity_headers(),
        json={"confirm_permanent_deletion": True},
    )
    assert response.status_code == 503
    assert response.json()["detail"] == (
        "AXIGNAL_TRIAL_RETENTION_SECONDS must be configured"
    )


def test_purge_worker_requires_independent_flag(monkeypatch) -> None:
    monkeypatch.setenv(
        "AXIGNAL_RETENTION_DATABASE_URL",
        "postgresql://example.invalid/axignal",
    )
    monkeypatch.delenv("AXIGNAL_PURGE_WORKER_ENABLED", raising=False)
    settings = RetentionSettings.from_env()
    try:
        settings.require_purge_worker()
    except RuntimeError as exc:
        assert str(exc) == "Workspace purge worker is disabled"
    else:
        raise AssertionError("Purge worker unexpectedly enabled")
