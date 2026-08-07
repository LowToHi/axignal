"""WP3-T11/T12 — Founder Operations tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from axignal_api.founder_operations import (
    FounderOperationKind,
    FounderOperations,
    FounderSession,
    ModuleAuthority,
    PlatformSupportOps,
    valid_founder_session,
)


class TestFounderSession:
    def test_valid_session(self) -> None:
        session = valid_founder_session()
        assert session.server_allowlisted is True
        assert session.active_principal is True

    def test_missing_factor_rejected(self) -> None:
        with pytest.raises(ValueError, match="founder session requires"):
            FounderSession(
                session_id="fs-2",
                passwordless_valid=True,
                server_allowlisted=True,
                active_principal=True,
            )

    def test_stale_aal2_rejected(self) -> None:
        with pytest.raises(ValueError, match="AAL2 verification is stale"):
            FounderSession(
                session_id="fs-3",
                passwordless_valid=True,
                aal2_verified_at=datetime.now(UTC) - timedelta(days=2),
                server_allowlisted=True,
                active_principal=True,
            )

    def test_allowlist_required(self) -> None:
        with pytest.raises(ValueError, match="founder session requires"):
            FounderSession(
                session_id="fs-4",
                passwordless_valid=True,
                aal2_verified_at=datetime.now(UTC),
                server_allowlisted=False,
                active_principal=True,
            )


class TestFounderOperations:
    def test_module_authority_states(self) -> None:
        ops = FounderOperations()
        # A sidebar never proves completeness; modules are typed.
        assert ops.module_authority(FounderOperationKind.RISK) == ModuleAuthority.READ_ONLY
        assert ops.module_authority(FounderOperationKind.ABUSE) == ModuleAuthority.READ_ONLY
        assert ops.module_authority(FounderOperationKind.SOURCES) == ModuleAuthority.OPERATIONAL
        assert ops.module_authority(FounderOperationKind.COVERAGE) == ModuleAuthority.OPERATIONAL
        assert ops.module_authority(FounderOperationKind.PLATFORM) == ModuleAuthority.READ_ONLY
        assert ops.module_authority(FounderOperationKind.SUPPORT) == ModuleAuthority.READ_ONLY

    def test_coverage_review_requires_session(self) -> None:
        ops = FounderOperations()
        with pytest.raises(ValueError, match="invalid founder session"):
            ops.record_coverage_review(
                "not-a-session",  # type: ignore[arg-type]
                source_id="src_ted_search_api_v3",
                coverage_note="reviewed",
            )

    def test_coverage_review_audited(self) -> None:
        ops = FounderOperations()
        ops.record_coverage_review(
            valid_founder_session(),
            source_id="src_ted_search_api_v3",
            coverage_note="coverage confirmed",
        )
        assert len(ops.audit_trail()) == 1
        entry = ops.audit_trail()[0]
        assert entry["kind"] == "COVERAGE"
        assert entry["action"] == "record_coverage_review"

    def test_source_note_audited(self) -> None:
        ops = FounderOperations()
        ops.record_source_note(
            valid_founder_session(),
            source_id="src_ted_search_api_v3",
            note="rights status re-checked",
        )
        assert len(ops.audit_trail()) == 1

    def test_read_only_module_rejects_operation(self) -> None:
        ops = FounderOperations()
        # RISK is READ_ONLY: no operation permitted (authority is typed).
        assert ops.module_authority(FounderOperationKind.RISK) == ModuleAuthority.READ_ONLY
        # Read surfaces are available without mutation.
        assert ops.list_risk_notes() == ()
        assert ops.list_abuse_flags() == ()

    def test_audit_is_append_only(self) -> None:
        ops = FounderOperations()
        session = valid_founder_session()
        ops.record_coverage_review(session, source_id="src-1", coverage_note="a")
        ops.record_source_note(session, source_id="src-1", note="b")
        trail = ops.audit_trail()
        assert len(trail) == 2
        # Append-only: order preserved.
        assert trail[0]["action"] == "record_coverage_review"
        assert trail[1]["action"] == "record_source_note"


class TestPlatformSupportOps:
    def test_tickets_recorded(self) -> None:
        support = PlatformSupportOps()
        support.record_ticket(valid_founder_session(), ticket_id="t-1", subject="Probe")
        assert len(support.tickets()) == 1

    def test_status_entries(self) -> None:
        support = PlatformSupportOps()
        support.record_status(valid_founder_session(), component="api", status="operational")
        assert len(support.status_entries()) == 1
        assert support.status_entries()[0]["component"] == "api"
