from __future__ import annotations

from typing import Any
from uuid import UUID

import pytest

from axignal_api import admission_repository as admission_module
from axignal_api import organic_repository as organic_module
from axignal_api import proposal_repository as proposal_module
from axignal_api import retention_repository as retention_module

TENANT = UUID("00000000-0000-4000-8000-000000000301")


class FakeCursor:
    def __init__(self) -> None:
        self.executions: list[tuple[object, object | None]] = []

    def __enter__(self) -> FakeCursor:
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def execute(self, statement: object, params: object | None = None) -> None:
        self.executions.append((statement, params))


class FakeConnection:
    def __init__(self, dsn: str) -> None:
        self.dsn = dsn
        self.cursor_instance = FakeCursor()

    def __enter__(self) -> FakeConnection:
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def cursor(self) -> FakeCursor:
        return self.cursor_instance


def connector(calls: list[FakeConnection]):
    def connect(dsn: str, **_: Any) -> FakeConnection:
        connection = FakeConnection(dsn)
        calls.append(connection)
        return connection

    return connect


def test_admission_cursor_selects_role_credential_and_tenant(monkeypatch) -> None:
    calls: list[FakeConnection] = []
    monkeypatch.setattr(admission_module.psycopg, "connect", connector(calls))
    repository = admission_module.AdmissionRepository(
        app_dsn="postgresql://app",
        admission_dsn="postgresql://admission",
    )

    with repository._cursor("axignal_app", TENANT) as cursor:
        assert cursor is calls[-1].cursor_instance
    assert calls[-1].dsn == "postgresql://app"
    assert len(calls[-1].cursor_instance.executions) == 2
    assert calls[-1].cursor_instance.executions[-1][1] == (str(TENANT),)

    with repository._cursor("axignal_admission_runtime"):
        pass
    assert calls[-1].dsn == "postgresql://admission"
    assert calls[-1].cursor_instance.executions == []


def test_proposal_cursor_selects_role_credential_and_tenant(monkeypatch) -> None:
    calls: list[FakeConnection] = []
    monkeypatch.setattr(proposal_module.psycopg, "connect", connector(calls))
    repository = proposal_module.DocumentProposalRepository(
        app_dsn="postgresql://app",
        proposal_dsn="postgresql://proposal",
    )

    with repository._cursor("axignal_app", TENANT):
        pass
    assert calls[-1].dsn == "postgresql://app"
    assert len(calls[-1].cursor_instance.executions) == 2

    with repository._cursor("axignal_proposal_worker", TENANT):
        pass
    assert calls[-1].dsn == "postgresql://proposal"
    executions = calls[-1].cursor_instance.executions
    assert len(executions) == 1
    statement, params = executions[0]
    assert "app.tenant_id" in str(statement)
    assert params == (str(TENANT),)


def test_organic_cursor_switches_between_application_and_public_roles(monkeypatch) -> None:
    calls: list[FakeConnection] = []
    monkeypatch.setattr(organic_module.psycopg, "connect", connector(calls))
    repository = organic_module.OrganicDiscoveryRepository("postgresql://organic")

    with repository._cursor(application_role=True):
        pass
    assert calls[-1].dsn == "postgresql://organic"
    assert len(calls[-1].cursor_instance.executions) == 1

    with repository._cursor(application_role=False):
        pass
    assert calls[-1].cursor_instance.executions == []


def test_retention_cursor_sets_worker_operator_and_tenant_boundaries(monkeypatch) -> None:
    calls: list[FakeConnection] = []
    monkeypatch.setattr(retention_module.psycopg, "connect", connector(calls))
    repository = retention_module.RetentionRepository("postgresql://retention")

    for role, tenant, expected_count in [
        ("axignal_app", TENANT, 2),
        ("axignal_operator", None, 1),
        ("axignal_retention_worker", None, 1),
    ]:
        with repository._cursor(role=role, tenant_id=tenant):
            pass
        assert calls[-1].dsn == "postgresql://retention"
        assert len(calls[-1].cursor_instance.executions) == expected_count


def test_cursor_contexts_propagate_connection_errors(monkeypatch) -> None:
    def fail(*_: object, **__: object) -> None:
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(admission_module.psycopg, "connect", fail)
    repository = admission_module.AdmissionRepository(app_dsn="postgresql://app")
    with (
        pytest.raises(RuntimeError, match="database unavailable"),
        repository._cursor("axignal_app"),
    ):
        pass
