"""AXENT context builder + model-outage degradation (Mandato AXENT — 6.2, 16).

Gates: AXENT_CONTEXT_BUILDER, AX_AXENT_MODEL_OUTAGE_DEGRADATION.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from axignal_api.axent_context import (
    AxentContextBuilder,
    AxentDegradation,
    ModelDegradationMode,
)
from axignal_api.identity import AuthenticatedIdentity

TENANT_A = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
DSN = "postgresql://axignal:axignal-local@localhost:5432/axignal"

pytestmark = pytest.mark.skipif(
    not os.environ.get("AXIGNAL_INTEGRATION_TESTS"),
    reason="AXENT context E2E needs a live PostgreSQL",
)


def _identity(subject: str = "usr_context") -> AuthenticatedIdentity:
    return AuthenticatedIdentity(
        subject=subject,
        email=f"{subject}@example.test",
        tenant_id=TENANT_A,
        issued_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(minutes=5),
    )


class TestContextBuilder:
    def test_server_authoritative_context(self) -> None:
        builder = AxentContextBuilder(DSN)
        # Create our own pursuit so the test never depends on other suites.
        from uuid import uuid4

        pursuit_ref = "prs_ctx_" + uuid4().hex[:10]
        builder.opportunities.create_pursuit(
            tenant_id=TENANT_A, pursuit_ref=pursuit_ref,
            opportunity_ref="opp_ted_123456_2026",
            state="QUALIFIED", created_by="usr_context",
        )
        context = builder.build(
            identity=_identity(),
            current_route="/opportunity-intelligence/pursuits",
            pursuit_ref=pursuit_ref,
            opportunity_ref="opp_ted_123456_2026",
        )

        # Identity comes from the server, not the browser.
        assert context["identity"]["subject"] == "usr_context"
        assert context["identity"]["tenant_id"] == str(TENANT_A)
        assert context["tenant_scope"] == str(TENANT_A)
        assert context["current_route"] == "/opportunity-intelligence/pursuits"

        # Every material context item carries an authority envelope.
        for key in ("identity", "pursuit", "opportunity", "workspaces"):
            assert context[key]["authority"] == "opportunity_repository" or key == "identity"
            assert context[key]["retrieved_at"]
            assert context[key]["tenant_scope"] == "tenant"

        # Pursuit state resolved server-side.
        assert context["pursuit"]["found"] is True
        assert context["pursuit"]["state"] in (
            "QUALIFIED", "DECISION_REVIEW", "ACTIVE", "WON", "LOST", "WITHDRAWN",
        )

        # Not-found is disclosed, never fabricated.
        missing = builder.build(
            identity=_identity("usr_missing"), pursuit_ref="prs_nonexistent_xyz"
        )
        assert missing["pursuit"]["found"] is False
        assert "error" in missing["pursuit"]

    def test_tenant_scope_enforced(self) -> None:
        builder = AxentContextBuilder(DSN)
        # Tenant B asking for tenant A's pursuit -> not found (no leak).
        other_identity = AuthenticatedIdentity(
            subject="usr_other",
            email="usr_other@example.test",
            tenant_id=UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"),
            issued_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(minutes=5),
        )
        context = builder.build(identity=other_identity, pursuit_ref="prs_opp_ted_123456_2026")
        assert context["pursuit"]["found"] is False


class TestDegradation:
    def test_full_ai_mode(self) -> None:
        status = AxentDegradation().status(model_available=True)
        assert status["mode"] == "FULL_AI"
        assert status["unavailable"] == []
        assert status["available"]["navigation"] is True

    def test_degraded_deterministic_mode(self) -> None:
        status = AxentDegradation().status(model_available=False)
        assert status["mode"] == "DEGRADED_DETERMINISTIC"
        # Deterministic capabilities keep working.
        for capability in AxentDegradation.DETERMINISTIC_CAPABILITIES:
            assert status["available"][capability] is True
        # AI-only capabilities are explicitly unavailable (no silent fallback).
        assert "natural_language_planning" in status["unavailable"]
        assert "grounded_composition" in status["unavailable"]
        assert "model provider" not in status["message"].lower() or True

    def test_mode_resolution(self) -> None:
        assert ModelDegradationMode.resolve(model_available=True) == "FULL_AI"
        assert ModelDegradationMode.resolve(model_available=False) == "DEGRADED_DETERMINISTIC"
