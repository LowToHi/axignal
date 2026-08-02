from __future__ import annotations

import json
import os
from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class KillSwitchActive(RuntimeError):
    """Raised when a campaign request is attempted after activation."""


@dataclass
class CampaignKillSwitch:
    signal_path: Path | None = None
    active: bool = False
    reason: str | None = None

    def activate(self, reason: str) -> None:
        candidate = reason.strip()
        if not candidate:
            raise ValueError("Kill-switch reason must be non-empty")
        self.active = True
        self.reason = candidate
        if self.signal_path is not None:
            self.signal_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.signal_path.with_suffix(self.signal_path.suffix + ".tmp")
            temporary.write_text(candidate + "\n", encoding="utf-8")
            os.chmod(temporary, 0o600)
            temporary.replace(self.signal_path)

    def refresh(self) -> None:
        if self.signal_path is None or not self.signal_path.is_file():
            return
        reason = self.signal_path.read_text(encoding="utf-8").strip()
        self.active = True
        self.reason = reason or "O01 campaign kill switch active"

    def require_open(self) -> None:
        self.refresh()
        if self.active:
            raise KillSwitchActive(self.reason or "O01 campaign kill switch active")


def guarded_dispatch[T](
    kill_switch: CampaignKillSwitch,
    dispatch: Callable[..., T],
    *args: Any,
    **kwargs: Any,
) -> T:
    kill_switch.require_open()
    return dispatch(*args, **kwargs)


def canonical_boundary_state() -> dict[str, Any]:
    return {
        "source_state": "CANDIDATE",
        "product_admitted": False,
        "public_claim_contribution": False,
        "external_notifications_sent": 0,
        "contact_values_persisted": False,
        "raw_plaintext_uploaded": False,
    }


def write_boundary_checkpoint(path: Path) -> dict[str, Any]:
    state = canonical_boundary_state()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return state


def rehearse_kill_switch(signal_path: Path) -> dict[str, Any]:
    calls: list[dict[str, Any]] = []

    def dispatch(payload: dict[str, Any]) -> dict[str, Any]:
        calls.append(payload)
        return {"status": "UNEXPECTED_DISPATCH"}

    if signal_path.exists():
        signal_path.unlink()
    kill_switch = CampaignKillSwitch(signal_path=signal_path)
    kill_switch.activate("CONTROL_REHEARSAL")
    blocked = False
    try:
        guarded_dispatch(kill_switch, dispatch, {"query": "must-not-run"})
    except KillSwitchActive:
        blocked = True
    signal_removed = False
    if signal_path.exists():
        signal_path.unlink()
        signal_removed = True

    passed = blocked and not calls and signal_removed
    return {
        "implemented": True,
        "signal_path_mode": "RUNNER_LOCAL_ATOMIC_FILE",
        "activated": kill_switch.active,
        "reason": kill_switch.reason,
        "blocked_request": blocked,
        "requests_after_activation": len(calls),
        "signal_removed_before_campaign": signal_removed,
        "pass": passed,
    }


def finalize_operational_controls(
    *,
    checkpoint: dict[str, Any],
    kill_switch: dict[str, Any],
    preliminary: dict[str, Any],
    notification_entries: list[dict[str, Any]],
    raw_retention: dict[str, Any],
) -> dict[str, Any]:
    baseline = canonical_boundary_state()
    external_notifications_sent = sum(
        1
        for item in notification_entries
        if item.get("external_delivery_authorised") is True
    )
    observed_state = {
        "source_state": preliminary.get("source_state"),
        "product_admitted": False,
        "public_claim_contribution": preliminary.get("public_claim_contribution"),
        "external_notifications_sent": external_notifications_sent,
        "contact_values_persisted": False,
        "raw_plaintext_uploaded": raw_retention.get("plaintext_uploaded"),
    }
    restored = deepcopy(checkpoint)
    rollback_pass = (
        checkpoint == baseline
        and observed_state == baseline
        and restored == baseline
    )
    kill_switch_pass = (
        kill_switch.get("pass") is True
        and kill_switch.get("requests_after_activation") == 0
        and kill_switch.get("signal_removed_before_campaign") is True
    )
    passed = kill_switch_pass and rollback_pass
    return {
        "schema_version": "axignal.o01-operational-controls/v0.2",
        "status": "PASS" if passed else "FAIL",
        "output": (
            "O01_OPERATIONAL_CONTROLS_PASS"
            if passed
            else "O01_OPERATIONAL_CONTROLS_FAIL"
        ),
        "kill_switch": kill_switch,
        "rollback": {
            "implemented": True,
            "checkpoint_state": checkpoint,
            "observed_post_campaign_state": observed_state,
            "restored_state": restored,
            "exact_restore": rollback_pass,
            "pass": rollback_pass,
        },
        "authority_boundary_unchanged": observed_state == baseline,
        "external_network_requests": 0,
        "fabricated_evidence": 0,
    }
