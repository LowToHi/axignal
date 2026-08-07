"""WP2-T10 — kill switch and quarantine tests."""

from __future__ import annotations

import pytest

from axignal_api.kill_switch import (
    InMemorySourceControlStore,
    KillSwitchError,
    SourceKillSwitch,
)
from axignal_api.manifest_state_machine import VersioningError
from axignal_api.source_manifest import (
    SourceAccessMode,
    SourceManifest,
    SourceState,
)


def ted_row(state: str = "ADMITTED") -> dict[str, object]:
    return {
        "source_id": "src_ted_search_api_v3",
        "name": "TED Search API v3",
        "source_type": "INSTITUTIONAL_API",
        "admission_state": state,
        "commercial_use": True,
    }


def ted_manifest(state: SourceState = SourceState.PRODUCT_ADMITTED) -> SourceManifest:
    return SourceManifest(
        source_id="src_ted_search_api_v3",
        name="TED Search API v3",
        library_id="O01",
        source_type="INSTITUTIONAL_API",
        access_mode=SourceAccessMode.INSTITUTIONAL_API,
        state=state,
        manifest_version="1.0.0",
        product_shell_ids=["AXIGNAL_OPPORTUNITY_INTELLIGENCE"],
    )


class TestSourceKillSwitch:
    def test_quarantine_suspends_source(self) -> None:
        store = InMemorySourceControlStore({"src_ted_search_api_v3": ted_row()})
        control = SourceKillSwitch(store)
        event = control.quarantine("src_ted_search_api_v3", reason="outage detected")
        assert event.from_state == "PRODUCT_ADMITTED"
        assert event.to_state == "SUSPENDED"
        assert store.rows["src_ted_search_api_v3"]["admission_state"] == "QUARANTINED"
        assert len(store.events) == 1

    def test_resume_restores_product_admitted(self) -> None:
        store = InMemorySourceControlStore(
            {"src_ted_search_api_v3": ted_row(state="QUARANTINED")}
        )
        control = SourceKillSwitch(store)
        event = control.resume("src_ted_search_api_v3", reason="outage resolved")
        assert event.to_state == "PRODUCT_ADMITTED"
        assert store.rows["src_ted_search_api_v3"]["admission_state"] == "ADMITTED"

    def test_resume_non_suspended_rejected(self) -> None:
        store = InMemorySourceControlStore({"src_ted_search_api_v3": ted_row()})
        control = SourceKillSwitch(store)
        with pytest.raises(KillSwitchError, match="only SUSPENDED can resume"):
            control.resume("src_ted_search_api_v3", reason="nope")

    def test_reject_is_terminal(self) -> None:
        store = InMemorySourceControlStore({"src_ted_search_api_v3": ted_row()})
        control = SourceKillSwitch(store)
        event = control.reject("src_ted_search_api_v3", reason="legal blocker")
        assert event.to_state == "REJECTED"
        # REJECTED is terminal: resume is refused (state check first).
        with pytest.raises(KillSwitchError, match="only SUSPENDED can resume"):
            control.resume("src_ted_search_api_v3", reason="not allowed")

    def test_quarantine_unknown_source(self) -> None:
        control = SourceKillSwitch(InMemorySourceControlStore())
        with pytest.raises(KillSwitchError, match="not found"):
            control.quarantine("src-ghost", reason="x")

    def test_runtime_usable_rules(self) -> None:
        store = InMemorySourceControlStore({"src_ted_search_api_v3": ted_row()})
        control = SourceKillSwitch(store)
        assert control.is_runtime_usable(ted_manifest(SourceState.PRODUCT_ADMITTED))
        assert control.is_runtime_usable(ted_manifest(SourceState.COMMERCIAL))
        assert not control.is_runtime_usable(ted_manifest(SourceState.SUSPENDED))
        assert not control.is_runtime_usable(ted_manifest(SourceState.REJECTED))
        assert not control.is_runtime_usable(ted_manifest(SourceState.REVOKED))
        quarantined = ted_manifest(SourceState.PRODUCT_ADMITTED).model_copy(
            update={"kill_switch": True}
        )
        assert not control.is_runtime_usable(quarantined)

    def test_kill_switch_not_an_admission_mechanism(self) -> None:
        # Quarantine only suspends; it never grants rights or admits.
        store = InMemorySourceControlStore(
            {"src-x": {"source_id": "src-x", "admission_state": "DISCOVERED"}}
        )
        control = SourceKillSwitch(store)
        with pytest.raises(VersioningError):
            control.quarantine("src-x", reason="cannot jump to SUSPENDED from DISCOVERED")
