"""WP2-T03 — manifest state machines and versioning tests."""

from __future__ import annotations

import pytest

from axignal_api.library_manifest import LibraryStatus
from axignal_api.manifest_state_machine import (
    SemanticVersion,
    VersioningError,
    assert_transition_allowed,
    bump_version,
    compare_versions,
    library_can_transition,
    source_can_transition,
    source_is_terminal,
    validate_schema_version,
    version_bump_kind,
)
from axignal_api.source_manifest import SourceState


class TestSemanticVersioning:
    def test_parse_valid(self) -> None:
        assert SemanticVersion.parse("1.0.0") == SemanticVersion(1, 0, 0)
        assert SemanticVersion.parse("0.1.9") == SemanticVersion(0, 1, 9)
        assert SemanticVersion.parse("2.13.4") == SemanticVersion(2, 13, 4)

    def test_parse_invalid(self) -> None:
        for bad in ("1.0", "1.0.0.0", "v1.0.0", "1.0.0-beta", "a.b.c", "01.0.0"):
            with pytest.raises(VersioningError):
                SemanticVersion.parse(bad)

    def test_bump(self) -> None:
        assert str(SemanticVersion.parse("1.2.3").bump("major")) == "2.0.0"
        assert str(SemanticVersion.parse("1.2.3").bump("minor")) == "1.3.0"
        assert str(SemanticVersion.parse("1.2.3").bump("patch")) == "1.2.4"
        assert bump_version("0.9.9", "minor") == "0.10.0"

    def test_compare(self) -> None:
        assert compare_versions("1.0.0", "1.0.0") == 0
        assert compare_versions("1.0.0", "1.0.1") == -1
        assert compare_versions("1.1.0", "1.0.9") == 1
        assert compare_versions("2.0.0", "1.99.99") == 1

    def test_bump_kind_inference(self) -> None:
        assert version_bump_kind("1.0.0", "2.0.0") == "major"
        assert version_bump_kind("1.0.0", "1.1.0") == "minor"
        assert version_bump_kind("1.0.0", "1.0.1") == "patch"
        assert version_bump_kind("1.0.0", "1.0.0") is None

    def test_schema_version_pattern(self) -> None:
        assert validate_schema_version("1.0.0")
        assert not validate_schema_version("nope")
        assert not validate_schema_version("1.0")


class TestLibraryStateMachine:
    def test_forward_flow(self) -> None:
        assert library_can_transition(
            LibraryStatus.NOT_STARTED, LibraryStatus.ENGINEERING_IN_PROGRESS
        )
        assert library_can_transition(
            LibraryStatus.ENGINEERING_IN_PROGRESS, LibraryStatus.ENGINEERING_EVIDENCE_READY
        )
        assert library_can_transition(
            LibraryStatus.ENGINEERING_EVIDENCE_READY, LibraryStatus.ENGINEERING_E2E_PASS
        )
        assert not library_can_transition(
            LibraryStatus.NOT_STARTED, LibraryStatus.ENGINEERING_E2E_PASS
        )

    def test_rejected_and_superseded(self) -> None:
        assert library_can_transition(
            LibraryStatus.ENGINEERING_IN_PROGRESS, LibraryStatus.ENGINEERING_REJECTED
        )
        assert library_can_transition(
            LibraryStatus.ENGINEERING_E2E_PASS, LibraryStatus.SUPERSEDED
        )
        assert not library_can_transition(
            LibraryStatus.ENGINEERING_REJECTED, LibraryStatus.ENGINEERING_E2E_PASS
        )
        assert not library_can_transition(
            LibraryStatus.SUPERSEDED, LibraryStatus.NOT_STARTED
        )

    def test_reopen_allowed(self) -> None:
        assert library_can_transition(
            LibraryStatus.ENGINEERING_REJECTED, LibraryStatus.ENGINEERING_IN_PROGRESS
        )
        assert library_can_transition(
            LibraryStatus.SUPERSEDED, LibraryStatus.ENGINEERING_IN_PROGRESS
        )

    def test_assert_transition_library(self) -> None:
        assert_transition_allowed("library", "NOT_STARTED", "ENGINEERING_IN_PROGRESS")
        with pytest.raises(VersioningError, match="illegal library state transition"):
            assert_transition_allowed("library", "NOT_STARTED", "ENGINEERING_E2E_PASS")


class TestSourceStateMachine:
    def test_forward_flow(self) -> None:
        assert source_can_transition(SourceState.DISCOVERED, SourceState.LEGAL_REVIEW)
        assert source_can_transition(SourceState.LEGAL_REVIEW, SourceState.PRIVACY_REVIEW)
        assert source_can_transition(SourceState.PRIVACY_REVIEW, SourceState.TECHNICAL_PROBE)
        assert source_can_transition(SourceState.TECHNICAL_PROBE, SourceState.EVIDENCE_READY)
        assert source_can_transition(SourceState.EVIDENCE_READY, SourceState.PRODUCT_ADMITTED)
        assert source_can_transition(SourceState.PRODUCT_ADMITTED, SourceState.COMMERCIAL)

    def test_suspend_resume(self) -> None:
        assert source_can_transition(SourceState.COMMERCIAL, SourceState.SUSPENDED)
        assert source_can_transition(SourceState.SUSPENDED, SourceState.COMMERCIAL)
        assert source_can_transition(SourceState.SUSPENDED, SourceState.PRODUCT_ADMITTED)

    def test_terminal_states(self) -> None:
        assert source_is_terminal(SourceState.REJECTED)
        assert source_is_terminal(SourceState.REVOKED)
        assert not source_is_terminal(SourceState.SUSPENDED)
        assert not source_can_transition(SourceState.REJECTED, SourceState.DISCOVERED)
        assert not source_can_transition(SourceState.REVOKED, SourceState.COMMERCIAL)

    def test_illegal_skips(self) -> None:
        assert not source_can_transition(SourceState.DISCOVERED, SourceState.COMMERCIAL)
        assert not source_can_transition(SourceState.DISCOVERED, SourceState.PRODUCT_ADMITTED)

    def test_ted_blocker_keeps_legal_review_state(self) -> None:
        # The TED legal blocker keeps the source in a review state; the
        # transition to PRODUCT_ADMITTED remains gated by human decision.
        assert source_can_transition(SourceState.LEGAL_REVIEW, SourceState.PRIVACY_REVIEW)
        assert source_can_transition(SourceState.PRIVACY_REVIEW, SourceState.TECHNICAL_PROBE)
        assert not source_is_terminal(SourceState.LEGAL_REVIEW)

    def test_assert_transition_source(self) -> None:
        assert_transition_allowed("source", "TECHNICAL_PROBE", "EVIDENCE_READY")
        with pytest.raises(VersioningError, match="illegal source state transition"):
            assert_transition_allowed("source", "DISCOVERED", "COMMERCIAL")
        with pytest.raises(VersioningError, match="unknown manifest kind"):
            assert_transition_allowed("workspace", "A", "B")
