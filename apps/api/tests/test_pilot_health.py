from fastapi import HTTPException

from axignal_api import pilot_health


def test_liveness_reports_build_and_pilot_mode(monkeypatch):
    monkeypatch.setenv("AXIGNAL_PILOT_MODE", "true")
    monkeypatch.setenv("AXIGNAL_BUILD_SHA", "abc123")

    response = pilot_health.liveness()

    assert response == {
        "status": "ok",
        "service": "axignal-api",
        "pilot_mode": True,
        "build_sha": "abc123",
    }


def test_readiness_requires_all_dependencies(monkeypatch):
    monkeypatch.setattr(pilot_health, "_database_ready", lambda: True)
    monkeypatch.setattr(pilot_health, "_valkey_ready", lambda: True)
    monkeypatch.setattr(pilot_health, "_object_store_ready", lambda: True)

    assert pilot_health.readiness() == {
        "status": "ready",
        "checks": {"postgres": True, "valkey": True, "object_store": True},
    }


def test_readiness_fails_closed(monkeypatch):
    monkeypatch.setattr(pilot_health, "_database_ready", lambda: True)
    monkeypatch.setattr(pilot_health, "_valkey_ready", lambda: False)
    monkeypatch.setattr(pilot_health, "_object_store_ready", lambda: True)

    try:
        pilot_health.readiness()
    except HTTPException as exc:
        assert exc.status_code == 503
        assert exc.detail == "AXIGNAL_PILOT_NOT_READY"
    else:
        raise AssertionError("readiness must fail closed")
