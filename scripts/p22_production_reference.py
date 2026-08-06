#!/usr/bin/env python3
from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime


def availability_bps(*, good: int, total: int) -> int:
    if total <= 0 or good < 0 or good > total:
        raise ValueError("invalid_sli_sample")
    return good * 10_000 // total


def latency_compliant(*, observed_ms: int, threshold_ms: int) -> bool:
    return observed_ms >= 0 and observed_ms <= threshold_ms


def burn_rate(*, consumed_error_events: int, total_events: int, objective_bps: int) -> float:
    if total_events <= 0 or not 0 < objective_bps < 10_000:
        raise ValueError("invalid_error_budget")
    allowed = total_events * (10_000 - objective_bps) / 10_000
    return consumed_error_events / allowed if allowed else float("inf")


def alert_decision(*, burn_rate_value: float, window_hours: int) -> str:
    if window_hours <= 1 and burn_rate_value >= 14.4:
        return "PAGE"
    if window_hours <= 6 and burn_rate_value >= 6.0:
        return "PAGE"
    if window_hours <= 72 and burn_rate_value >= 1.0:
        return "TICKET"
    return "NONE"


def release_decision(
    *,
    immutable_artifact: bool,
    exact_revision: bool,
    staging_smoke: bool,
    rollback_test: bool,
    slo_instrumented: bool,
    security_acceptance_signed: bool,
    critical_findings: int,
    human_release_approval: bool,
) -> str:
    checks = (
        immutable_artifact,
        exact_revision,
        staging_smoke,
        rollback_test,
        slo_instrumented,
        security_acceptance_signed,
        critical_findings == 0,
        human_release_approval,
    )
    return "ALLOW_PRODUCTION_DEPLOYMENT" if all(checks) else "DENY"


def restore_decision(
    *,
    encrypted_backup: bool,
    digest_verified: bool,
    isolated_target: bool,
    recovered_point_age_minutes: int,
    elapsed_minutes: int,
    rpo_minutes: int,
    rto_minutes: int,
    consistency_verified: bool,
) -> str:
    checks = (
        encrypted_backup,
        digest_verified,
        isolated_target,
        recovered_point_age_minutes <= rpo_minutes,
        elapsed_minutes <= rto_minutes,
        consistency_verified,
    )
    return "PASS_DR_EXERCISE" if all(checks) else "FAIL_CLOSED"


def risk_acceptance_decision(
    *,
    severity: str,
    approver_role: str,
    expires_at: datetime | None,
    now: datetime | None = None,
) -> str:
    now = now or datetime.now(UTC)
    if severity == "CRITICAL":
        return "DENY"
    if severity != "HIGH":
        return "NOT_REQUIRED"
    if approver_role != "RISK_ACCEPTOR" or expires_at is None or expires_at <= now:
        return "DENY"
    return "ALLOW_TEMPORARY"


def security_acceptance(
    *,
    controls: Mapping[str, str],
    required_controls: list[str],
    critical_findings: int,
    high_findings_without_acceptance: int,
) -> str:
    if critical_findings or high_findings_without_acceptance:
        return "BLOCK"
    if any(controls.get(control) != "PASS" for control in required_controls):
        return "BLOCK"
    return "PASS_ENGINEERING_ACCEPTANCE"


def production_readiness(gates: Mapping[str, str], required_gates: list[str]) -> str:
    if any(gates.get(gate) != "PASS" for gate in required_gates):
        return "BLOCKED"
    return "READY_FOR_TYPED_HUMAN_PRODUCTION_APPROVAL"
