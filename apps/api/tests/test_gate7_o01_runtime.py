from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from axignal_api import o01_quality_execute
from axignal_api.gate7_o01_controls import CampaignKillSwitch, KillSwitchActive
from axignal_api.gate7_o01_runtime import guarded_network_runtime
from axignal_api.o01_quality_http import (
    MAXIMUM_RATE_LIMIT_WAIT_SECONDS,
    effective_request_delay,
    rate_limit_wait_seconds,
    retry_after_seconds,
)


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


def test_operational_pacing_preserves_contract_minimum() -> None:
    assert effective_request_delay(0.25) == 2.0
    assert effective_request_delay(3.0) == 3.0
    with pytest.raises(ValueError):
        effective_request_delay(-0.1)


def test_rate_limit_wait_honours_seconds_and_fallback() -> None:
    assert rate_limit_wait_seconds("7", minimum_delay_seconds=0.25) == 7.0
    assert rate_limit_wait_seconds(None, minimum_delay_seconds=0.25) == 10.0
    assert rate_limit_wait_seconds("invalid", minimum_delay_seconds=15.0) == 15.0


def test_retry_after_http_date_is_bounded() -> None:
    now = datetime(2026, 8, 2, 16, 0, tzinfo=UTC)
    retry_at = now + timedelta(seconds=30)
    value = retry_at.strftime("%a, %d %b %Y %H:%M:%S GMT")
    assert retry_after_seconds(value, now=now) == 30.0

    far_future = now + timedelta(hours=1)
    far_value = far_future.strftime("%a, %d %b %Y %H:%M:%S GMT")
    assert retry_after_seconds(far_value, now=now) == MAXIMUM_RATE_LIMIT_WAIT_SECONDS
