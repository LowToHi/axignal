"""Kill switch and quarantine control — WP2-T10.

Operational control over source availability, backed by the real
`axignal_global.sources` registry.

Rules (contract 11.1, 11.2, 11.3 and section 8):
- kill_switch=true quarantines a source: runtime must not consult it for
  commercial Evidence Objects and it must not contribute to coverage;
- quarantine is reversible (SUSPENDED -> PRODUCT_ADMITTED/COMMERCIAL);
- REJECTED/REVOKED are terminal: the source keeps its decision record but
  is never consulted in runtime;
- every state change is recorded (audit trail);
- kill switch is not an admission mechanism: it never grants rights.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol

from axignal_api.manifest_state_machine import (
    SourceState,
    assert_transition_allowed,
    source_is_terminal,
)
from axignal_api.source_manifest import SourceManifest, state_from_db

LOGGER = logging.getLogger(__name__)


class KillSwitchError(RuntimeError):
    """Raised when a kill-switch operation violates the source contract."""


@dataclass(frozen=True)
class KillSwitchEvent:
    source_id: str
    from_state: str
    to_state: str
    reason: str
    occurred_at: datetime
    exact_head: str | None = None


# Database storage vocabulary (axignal_global.sources check constraint):
# ADMITTED / QUARANTINED / REJECTED.
DB_WRITE_STATE = {
    SourceState.SUSPENDED: "QUARANTINED",
    SourceState.PRODUCT_ADMITTED: "ADMITTED",
    SourceState.COMMERCIAL: "ADMITTED",
    SourceState.REJECTED: "REJECTED",
    SourceState.REVOKED: "REJECTED",
}


class SourceControlStore(Protocol):
    """Minimal persistence protocol for kill-switch operations."""

    def get_source(self, source_id: str) -> dict[str, Any] | None: ...

    def set_source_state(self, source_id: str, state: str, reason: str) -> None: ...

    def record_kill_switch_event(
        self,
        *,
        source_id: str,
        from_state: str,
        to_state: str,
        reason: str,
        occurred_at: datetime,
        exact_head: str | None = None,
    ) -> None: ...


def _db_state(state: SourceState) -> str:
    if state not in DB_WRITE_STATE:
        raise KillSwitchError(
            f"state {state.value!r} is not storable in the source registry"
        )
    return DB_WRITE_STATE[state]


class SourceKillSwitch:
    """Enforces source availability rules against the source registry."""

    def __init__(self, store: SourceControlStore) -> None:
        self.store = store

    def quarantine(self, source_id: str, *, reason: str) -> KillSwitchEvent:
        """Suspend a source immediately (kill switch engaged)."""
        row = self.store.get_source(source_id)
        if row is None:
            raise KillSwitchError(f"source {source_id!r} not found")
        current = state_from_db(row.get("admission_state"))
        target = SourceState.SUSPENDED
        assert_transition_allowed("source", current.value, target.value)
        self.store.set_source_state(source_id, _db_state(target), reason)
        event = KillSwitchEvent(
            source_id=source_id,
            from_state=current.value,
            to_state=target.value,
            reason=reason,
            occurred_at=datetime.now(UTC),
        )
        self.store.record_kill_switch_event(
            source_id=source_id,
            from_state=current.value,
            to_state=target.value,
            reason=reason,
            occurred_at=event.occurred_at,
        )
        LOGGER.warning("source %s quarantined (%s)", source_id, reason)
        return event

    def resume(self, source_id: str, *, reason: str) -> KillSwitchEvent:
        """Resume a suspended source back to PRODUCT_ADMITTED."""
        row = self.store.get_source(source_id)
        if row is None:
            raise KillSwitchError(f"source {source_id!r} not found")
        current = state_from_db(row.get("admission_state"))
        if current != SourceState.SUSPENDED:
            raise KillSwitchError(
                f"source {source_id!r} is {current.value}; only SUSPENDED can resume"
            )
        target = SourceState.PRODUCT_ADMITTED
        assert_transition_allowed("source", current.value, target.value)
        self.store.set_source_state(source_id, _db_state(target), reason)
        event = KillSwitchEvent(
            source_id=source_id,
            from_state=current.value,
            to_state=target.value,
            reason=reason,
            occurred_at=datetime.now(UTC),
        )
        self.store.record_kill_switch_event(
            source_id=source_id,
            from_state=current.value,
            to_state=target.value,
            reason=reason,
            occurred_at=event.occurred_at,
        )
        return event

    def reject(self, source_id: str, *, reason: str) -> KillSwitchEvent:
        """Terminally reject a source (keeps decision record, no runtime use)."""
        row = self.store.get_source(source_id)
        if row is None:
            raise KillSwitchError(f"source {source_id!r} not found")
        current = state_from_db(row.get("admission_state"))
        target = SourceState.REJECTED
        assert_transition_allowed("source", current.value, target.value)
        self.store.set_source_state(source_id, _db_state(target), reason)
        event = KillSwitchEvent(
            source_id=source_id,
            from_state=current.value,
            to_state=target.value,
            reason=reason,
            occurred_at=datetime.now(UTC),
        )
        self.store.record_kill_switch_event(
            source_id=source_id,
            from_state=current.value,
            to_state=target.value,
            reason=reason,
            occurred_at=event.occurred_at,
        )
        return event

    def is_runtime_usable(self, manifest: SourceManifest) -> bool:
        """A source is runtime-usable only when not terminal and not suspended."""
        if source_is_terminal(manifest.state):
            return False
        if manifest.state == SourceState.SUSPENDED:
            return False
        return not manifest.kill_switch


class InMemorySourceControlStore:
    """In-memory store for tests and small deployments."""

    def __init__(self, rows: dict[str, dict[str, Any]] | None = None) -> None:
        self.rows: dict[str, dict[str, Any]] = dict(rows or {})
        self.events: list[KillSwitchEvent] = []

    def get_source(self, source_id: str) -> dict[str, Any] | None:
        row = self.rows.get(source_id)
        return dict(row) if row is not None else None

    def set_source_state(self, source_id: str, state: str, reason: str) -> None:
        if source_id not in self.rows:
            raise KillSwitchError(f"source {source_id!r} not found")
        self.rows[source_id]["admission_state"] = state
        self.rows[source_id]["updated_at"] = datetime.now(UTC).isoformat()

    def record_kill_switch_event(
        self,
        *,
        source_id: str,
        from_state: str,
        to_state: str,
        reason: str,
        occurred_at: datetime,
        exact_head: str | None = None,
    ) -> None:
        self.events.append(
            KillSwitchEvent(
                source_id=source_id,
                from_state=from_state,
                to_state=to_state,
                reason=reason,
                occurred_at=occurred_at,
                exact_head=exact_head,
            )
        )
