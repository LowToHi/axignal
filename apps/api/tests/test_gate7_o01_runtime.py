from __future__ import annotations

from pathlib import Path

import pytest

from axignal_api import o01_quality_execute
from axignal_api.gate7_o01_controls import CampaignKillSwitch, KillSwitchActive
from axignal_api.gate7_o01_runtime import guarded_network_runtime


def test_actual_campaign_network_binding_obeys_kill_switch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, object]] = []

    def fake_post_json(**kwargs: object) -> dict[str, object]:
        calls.append(kwargs)
        return {"status": "UNEXPECTED"}

    monkeypatch.setattr(o01_quality_execute, "post_json", fake_post_json)
    switch = CampaignKillSwitch(signal_path=tmp_path / "kill.signal")
    switch.activate("operator stop")

    with guarded_network_runtime(switch), pytest.raises(KillSwitchActive):
        o01_quality_execute.post_json(endpoint="https://example.invalid")

    assert calls == []
    assert o01_quality_execute.post_json is fake_post_json
