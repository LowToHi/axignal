from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from . import o01_quality_execute
from .gate7_o01_controls import CampaignKillSwitch, guarded_dispatch


@contextmanager
def guarded_network_runtime(
    kill_switch: CampaignKillSwitch,
) -> Iterator[None]:
    original_post_json = o01_quality_execute.post_json

    def guarded_post_json(**kwargs: Any) -> Any:
        return guarded_dispatch(kill_switch, original_post_json, **kwargs)

    o01_quality_execute.post_json = guarded_post_json
    try:
        yield
    finally:
        o01_quality_execute.post_json = original_post_json


def run_campaign_v0_2(
    *,
    plan_path: Path,
    authority_envelope_path: Path,
    raw_dir: Path,
    output_dir: Path,
    kill_switch_path: Path,
) -> dict[str, Any]:
    kill_switch = CampaignKillSwitch(signal_path=kill_switch_path)
    with guarded_network_runtime(kill_switch):
        return o01_quality_execute.run_campaign(
            plan_path=plan_path,
            authority_envelope_path=authority_envelope_path,
            raw_dir=raw_dir,
            output_dir=output_dir,
        )
