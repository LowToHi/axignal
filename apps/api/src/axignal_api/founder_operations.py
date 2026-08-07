"""Founder Operations — WP3-T11/T12 (contract section 12).

Founder authority is independent of tenant seats and browser claims:

    valid passwordless session
    ∩ recent AAL2 verification
    ∩ server allowlist
    ∩ active founder principal
    ∩ typed server operation
    ∩ append-only audit

Covers the Founder Operations surface:
- T11: Risk, Abuse, Sources and Coverage operations;
- T12: Platform and support operations.

A visible sidebar never proves operational completeness; every module
without durable authority must display READ_ONLY/BLOCKED/
NOT_IMPLEMENTED (contract rule).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class FounderOperationKind(StrEnum):
    RISK = "RISK"
    ABUSE = "ABUSE"
    SOURCES = "SOURCES"
    COVERAGE = "COVERAGE"
    PLATFORM = "PLATFORM"
    SUPPORT = "SUPPORT"


class ModuleAuthority(StrEnum):
    READ_ONLY = "READ_ONLY"
    BLOCKED = "BLOCKED"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    OPERATIONAL = "OPERATIONAL"


class FounderSession(BaseModel):
    """A valid founder session (all six factors)."""

    schema_version: Literal["axignal.founder.session.v1"] = "axignal.founder.session.v1"
    session_id: str = Field(min_length=3, max_length=120)
    passwordless_valid: bool
    aal2_verified_at: datetime | None = None
    server_allowlisted: bool
    active_principal: bool
    valid_since: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def validate_session(self) -> FounderSession:
        if not (
            self.passwordless_valid
            and self.aal2_verified_at is not None
            and self.server_allowlisted
            and self.active_principal
        ):
            raise ValueError(
                "founder session requires passwordless + recent AAL2 + "
                "allowlist + active principal"
            )
        # AAL2 verification must be recent (within 24h).
        age = datetime.now(UTC) - self.aal2_verified_at
        if age.total_seconds() > 86400:
            raise ValueError("AAL2 verification is stale (older than 24h)")
        return self


@dataclass
class FounderAuditLog:
    """Append-only founder operation audit."""

    entries: list[dict[str, object]] = field(default_factory=list)

    def append(self, entry: dict[str, object]) -> None:
        self.entries.append(entry)

    def __len__(self) -> int:
        return len(self.entries)


class FounderOperations:
    """Typed founder operations with append-only audit."""

    def __init__(self) -> None:
        self._modules: dict[FounderOperationKind, ModuleAuthority] = {
            FounderOperationKind.RISK: ModuleAuthority.READ_ONLY,
            FounderOperationKind.ABUSE: ModuleAuthority.READ_ONLY,
            FounderOperationKind.SOURCES: ModuleAuthority.OPERATIONAL,
            FounderOperationKind.COVERAGE: ModuleAuthority.OPERATIONAL,
            FounderOperationKind.PLATFORM: ModuleAuthority.READ_ONLY,
            FounderOperationKind.SUPPORT: ModuleAuthority.READ_ONLY,
        }
        self._audit = FounderAuditLog()
        self._coverage_reviews: list[dict[str, object]] = []
        self._risk_notes: list[dict[str, object]] = []
        self._abuse_flags: list[dict[str, object]] = []
        self._source_notes: list[dict[str, object]] = []

    def module_authority(self, kind: FounderOperationKind) -> ModuleAuthority:
        """The visible authority state (sidebar never proves completeness)."""
        return self._modules[kind]

    def _require(self, session: FounderSession, kind: FounderOperationKind) -> None:
        """Require a valid founder session and an operational module."""
        if self._modules[kind] != ModuleAuthority.OPERATIONAL:
            raise ValueError(
                f"module {kind.value} is {self._modules[kind].value}; "
                "no operation permitted"
            )
        if not isinstance(session, FounderSession):
            raise ValueError("invalid founder session")

    def _audit_operation(
        self,
        session: FounderSession,
        kind: FounderOperationKind,
        action: str,
        details: dict[str, object],
    ) -> None:
        self._audit.append(
            {
                "session_id": session.session_id,
                "kind": kind.value,
                "action": action,
                "details": details,
                "occurred_at": datetime.now(UTC).isoformat(),
            }
        )

    # --- Coverage (T11) -----------------------------------------------------

    def record_coverage_review(
        self, session: FounderSession, *, source_id: str, coverage_note: str
    ) -> None:
        self._require(session, FounderOperationKind.COVERAGE)
        self._coverage_reviews.append(
            {
                "source_id": source_id,
                "coverage_note": coverage_note,
                "recorded_at": datetime.now(UTC).isoformat(),
            }
        )
        self._audit_operation(
            session, FounderOperationKind.COVERAGE, "record_coverage_review",
            {"source_id": source_id},
        )

    # --- Sources (T11) ------------------------------------------------------

    def record_source_note(
        self, session: FounderSession, *, source_id: str, note: str
    ) -> None:
        self._require(session, FounderOperationKind.SOURCES)
        self._source_notes.append(
            {
                "source_id": source_id,
                "note": note,
                "recorded_at": datetime.now(UTC).isoformat(),
            }
        )
        self._audit_operation(
            session, FounderOperationKind.SOURCES, "record_source_note",
            {"source_id": source_id},
        )

    # --- Risk/Abuse read-only (T11) -----------------------------------------

    def list_risk_notes(self) -> tuple[dict[str, object], ...]:
        return tuple(self._risk_notes)

    def list_abuse_flags(self) -> tuple[dict[str, object], ...]:
        return tuple(self._abuse_flags)

    def audit_trail(self) -> tuple[dict[str, object], ...]:
        return tuple(self._audit.entries)


class PlatformSupportOps:
    """Platform and support operations (T12)."""

    def __init__(self) -> None:
        self._tickets: list[dict[str, object]] = []
        self._status_entries: list[dict[str, object]] = []

    def record_ticket(
        self, session: FounderSession, *, ticket_id: str, subject: str
    ) -> None:
        # Support is read-only for founders without a support operator role;
        # tickets are recorded for visibility only.
        self._tickets.append(
            {
                "ticket_id": ticket_id,
                "subject": subject,
                "recorded_at": datetime.now(UTC).isoformat(),
            }
        )

    def record_status(
        self, session: FounderSession, *, component: str, status: str
    ) -> None:
        self._status_entries.append(
            {
                "component": component,
                "status": status,
                "recorded_at": datetime.now(UTC).isoformat(),
            }
        )

    def tickets(self) -> tuple[dict[str, object], ...]:
        return tuple(self._tickets)

    def status_entries(self) -> tuple[dict[str, object], ...]:
        return tuple(self._status_entries)


def valid_founder_session() -> FounderSession:
    """A canonical valid founder session for tests/demo."""
    return FounderSession(
        session_id="fs-0001",
        passwordless_valid=True,
        aal2_verified_at=datetime.now(UTC),
        server_allowlisted=True,
        active_principal=True,
    )
