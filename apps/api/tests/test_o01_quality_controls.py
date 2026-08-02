from __future__ import annotations

from pathlib import Path

import pytest

from axignal_api.gate7_o01_controls import (
    CampaignKillSwitch,
    KillSwitchActive,
    canonical_boundary_state,
    finalize_operational_controls,
    guarded_dispatch,
    rehearse_kill_switch,
)


def test_kill_switch_prevents_dispatch_after_activation(tmp_path: Path) -> None:
    calls: list[dict[str, str]] = []
    signal = tmp_path / "kill.signal"
    switch = CampaignKillSwitch(signal_path=signal)
    switch.activate("operator stop")

    with pytest.raises(KillSwitchActive):
        guarded_dispatch(switch, calls.append, {"query": "blocked"})

    assert calls == []
    assert signal.is_file()


def test_kill_switch_rehearsal_removes_signal_before_campaign(
    tmp_path: Path,
) -> None:
    report = rehearse_kill_switch(tmp_path / "kill.signal")

    assert report["pass"] is True
    assert report["requests_after_activation"] == 0
    assert report["signal_removed_before_campaign"] is True


def test_finalizer_proves_exact_candidate_boundary() -> None:
    baseline = canonical_boundary_state()
    report = finalize_operational_controls(
        checkpoint=baseline,
        kill_switch={
            "pass": True,
            "requests_after_activation": 0,
            "signal_removed_before_campaign": True,
        },
        preliminary={
            "source_state": "CANDIDATE",
            "public_claim_contribution": False,
        },
        notification_entries=[{"external_delivery_authorised": False}],
        raw_retention={"plaintext_uploaded": False},
    )

    assert report["status"] == "PASS"
    assert report["rollback"]["restored_state"] == baseline
    assert report["authority_boundary_unchanged"] is True
    assert report["external_network_requests"] == 0
