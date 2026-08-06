from __future__ import annotations

from pathlib import Path
from typing import Any

from . import o01_history_frequency_lag as legacy
from . import o01_history_frequency_lag_v6 as v6
from .o01_official_source_retry import (
    OfficialSourceFetchError,
    observe_official_source_with_retry,
)
from .o01_quality_common import O01QualityCampaignError, sha256_prefixed

POLICY_SCHEMA = "axignal.o01-official-source-retry-policy/v0.1"
POLICY_PATH = Path(
    "data/acceptance/campaigns/"
    "AX-LIB-O01-official-source-retry-policy.v0.1.json"
)


def _validate_policy(policy: dict[str, Any]) -> None:
    if policy["schema_version"] != POLICY_SCHEMA:
        raise O01QualityCampaignError("Unexpected official-source retry policy schema")
    if policy["task_id"] != "AX-GE2E-G7-O01-E":
        raise O01QualityCampaignError("Official-source retry policy task drift")
    if policy["library_id"] != "AX-LIB-O01":
        raise O01QualityCampaignError("Official-source retry policy library drift")
    if policy["source_id"] != "src_ted_search_api_v3":
        raise O01QualityCampaignError("Official-source retry policy source drift")
    if policy["scope"] != "OFFICIAL_DOCUMENT_GET_ONLY":
        raise O01QualityCampaignError("Official-source retry scope drift")
    if policy["final_status_required"] != 200:
        raise O01QualityCampaignError("Official-source final status weakened")
    if policy["maximum_attempts_per_source"] != 2:
        raise O01QualityCampaignError("Official-source attempt count drift")
    if policy["retryable_http_statuses"] != [202, 429, 500, 502, 503, 504]:
        raise O01QualityCampaignError("Official-source retry statuses drift")
    if policy["minimum_retry_delay_seconds"] < 2.0:
        raise O01QualityCampaignError("Official-source retry delay weakened")
    if policy["attempt_ledger"]["persisted"] is not True:
        raise O01QualityCampaignError("Official-source attempt ledger disabled")
    if policy["attempt_ledger"]["response_body_persisted"] is not False:
        raise O01QualityCampaignError("Official-source body retention enabled")
    semantics = policy["accepted_semantics"]
    if semantics["http_202_is_evidence"] is not False:
        raise O01QualityCampaignError("HTTP 202 was authorised as evidence")
    if semantics["second_http_202_is_failure"] is not True:
        raise O01QualityCampaignError("Repeated HTTP 202 fail-closed rule disabled")
    boundary = policy["non_authorisations"]
    for key in (
        "threshold_change",
        "source_scope_change",
        "new_host",
        "raw_body_retention",
        "public_claim_contribution",
        "gate7_closed",
    ):
        if boundary[key] is not False:
            raise O01QualityCampaignError(
                f"Official-source retry policy enabled forbidden authority: {key}"
            )
    if boundary["public_launch"] != "NO_GO":
        raise O01QualityCampaignError("Official-source retry policy enabled launch")


def run_campaign(
    plan_path: Path,
    policy_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    plan = legacy.load_json(plan_path)
    policy = legacy.load_json(policy_path)
    _validate_policy(policy)
    if plan["schema_version"] != v6.PLAN_SCHEMA:
        raise O01QualityCampaignError("Unexpected O01-E measurement plan schema")
    if plan["network"]["maximum_requests"] != 60:
        raise O01QualityCampaignError("O01-E network budget drift")

    output_dir.mkdir(parents=True, exist_ok=True)
    ledger_path = output_dir / "official-source-attempt-ledger.v0.1.json"
    ledger: dict[str, Any] = {
        "schema_version": "axignal.o01-official-source-attempt-ledger/v0.1",
        "status": "IN_PROGRESS",
        "policy_sha256": sha256_prefixed(policy_path.read_bytes()),
        "maximum_attempts_per_source": policy["maximum_attempts_per_source"],
        "retryable_http_statuses": policy["retryable_http_statuses"],
        "sources": [],
        "response_bodies_persisted": False,
        "claim_contribution": False,
        "gate7_closed": False,
        "public_launch": "NO_GO",
    }
    legacy.write_json(ledger_path, ledger)

    original_source_observation = legacy._source_observation

    def source_observation(
        *,
        url: str,
        anchors: list[str],
        allowed_hosts: frozenset[str],
        timeout_seconds: float,
        max_response_bytes: int,
        budget: Any,
    ) -> dict[str, Any]:
        try:
            observation, attempts = observe_official_source_with_retry(
                url=url,
                anchors=anchors,
                allowed_hosts=allowed_hosts,
                timeout_seconds=timeout_seconds,
                max_response_bytes=max_response_bytes,
                budget=budget,
                maximum_attempts=policy["maximum_attempts_per_source"],
                minimum_delay_seconds=policy["minimum_retry_delay_seconds"],
                retryable_statuses=frozenset(policy["retryable_http_statuses"]),
            )
        except OfficialSourceFetchError as exc:
            ledger["sources"].append(
                {
                    "url": url,
                    "status": "FAIL",
                    "anchors_expected": anchors,
                    "attempts": exc.attempts,
                    "response_body_persisted": False,
                }
            )
            ledger["status"] = "FAIL"
            legacy.write_json(ledger_path, ledger)
            final_status = (
                exc.attempts[-1].get("http_status") if exc.attempts else None
            )
            raise O01QualityCampaignError(
                "Official source observation failed for "
                f"{url}; attempts={len(exc.attempts)}; "
                f"final_http_status={final_status}"
            ) from exc

        ledger["sources"].append(
            {
                "url": url,
                "status": "PASS",
                "anchors_expected": anchors,
                "attempts": attempts,
                "response_body_persisted": False,
            }
        )
        legacy.write_json(ledger_path, ledger)
        return observation

    legacy._source_observation = source_observation
    try:
        result = v6.run_campaign(plan_path, output_dir)
    finally:
        legacy._source_observation = original_source_observation

    ledger["status"] = "PASS"
    ledger["source_count"] = len(ledger["sources"])
    ledger["attempt_count"] = sum(
        len(source["attempts"]) for source in ledger["sources"]
    )
    legacy.write_json(ledger_path, ledger)

    observations_path = output_dir / "official-source-observations.v0.1.json"
    observations = legacy.load_json(observations_path)
    observations["schema_version"] = (
        "axignal.o01-official-source-observations/v0.7"
    )
    observations["retry_policy_sha256"] = ledger["policy_sha256"]
    observations["attempt_ledger"] = ledger_path.name
    observations["response_bodies_persisted"] = False
    legacy.write_json(observations_path, observations)

    result["schema_version"] = "axignal.o01-history-frequency-lag-result/v0.7"
    result["official_source_retry_policy_sha256"] = ledger["policy_sha256"]
    result["official_source_attempt_ledger"] = ledger_path.name
    result["official_source_attempt_count"] = ledger["attempt_count"]
    result["official_source_response_bodies_persisted"] = False
    legacy.write_json(output_dir / "final-result.v0.1.json", result)
    return result
