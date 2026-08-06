from __future__ import annotations

import argparse
import json
from pathlib import Path

from verify_gate7_o01_history_frequency_lag import (
    ContractError,
    digest,
    load_json,
    require,
)
from verify_gate7_o01_history_frequency_lag_v4 import (
    verify_result as verify_v4_result,
)
from verify_gate7_o01_history_frequency_lag_v6 import (
    verify_plan as verify_v6_plan,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLAN = ROOT / (
    "data/acceptance/campaigns/"
    "AX-LIB-O01-history-frequency-lag-plan.v0.5.json"
)
DEFAULT_POLICY = ROOT / (
    "data/acceptance/campaigns/"
    "AX-LIB-O01-official-source-retry-policy.v0.1.json"
)


def verify_policy(policy: dict, policy_path: Path) -> dict:
    require(
        policy["schema_version"]
        == "axignal.o01-official-source-retry-policy/v0.1",
        "Unexpected retry policy schema",
    )
    require(policy["task_id"] == "AX-GE2E-G7-O01-E", "Retry task drift")
    require(policy["library_id"] == "AX-LIB-O01", "Retry library drift")
    require(policy["source_id"] == "src_ted_search_api_v3", "Retry source drift")
    require(policy["scope"] == "OFFICIAL_DOCUMENT_GET_ONLY", "Retry scope drift")
    require(policy["final_status_required"] == 200, "Final HTTP status weakened")
    require(policy["maximum_attempts_per_source"] == 2, "Attempt count drift")
    require(
        policy["retryable_http_statuses"] == [202, 429, 500, 502, 503, 504],
        "Retryable status drift",
    )
    require(policy["minimum_retry_delay_seconds"] >= 2.0, "Retry delay weakened")
    require(policy["maximum_retry_after_seconds"] <= 120.0, "Retry wait widened")

    trigger = policy["trigger_evidence"]
    require(trigger["workflow_run_id"] == 30771301480, "Trigger run drift")
    require(trigger["job_id"] == 91558921256, "Trigger job drift")
    require(
        trigger["request_head_sha"]
        == "b28b0438fb8e38f9c213e2621e92e1dc20d42011",
        "Trigger head drift",
    )
    require(trigger["artifact_id"] == 8840624551, "Trigger artifact drift")
    require(
        trigger["artifact_digest"]
        == "sha256:b585a8c11bc5d23075a86696dca7153a376aa49c4e22e2b7677c834d9b9500ce",
        "Trigger artifact digest drift",
    )
    require(trigger["failure"] == "HTTP_202_EMPTY_BODY", "Trigger failure drift")
    require(
        trigger["response_sha256"]
        == "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "Trigger empty-body digest drift",
    )
    require(trigger["preflight_passed"] is True, "Trigger preflight not proven")
    require(
        trigger["state_transition_applied"] is False,
        "Failed trigger applied a state transition",
    )

    ledger = policy["attempt_ledger"]
    require(ledger["persisted"] is True, "Attempt ledger disabled")
    require(ledger["response_body_persisted"] is False, "Body retention enabled")
    required_fields = {
        "attempt",
        "url",
        "final_url",
        "http_status",
        "content_type",
        "retry_after",
        "response_bytes",
        "response_sha256",
        "started_at",
        "completed_at",
        "duration_seconds",
        "resolved_addresses",
        "selected_address",
        "redirects_followed",
        "retry_wait_seconds",
        "accepted",
        "response_body_persisted",
    }
    require(
        required_fields.issubset(set(ledger["fields"])),
        "Attempt ledger fields are incomplete",
    )

    semantics = policy["accepted_semantics"]
    require(semantics["http_202_is_evidence"] is False, "HTTP 202 accepted")
    require(semantics["http_202_may_be_retried"] is True, "HTTP 202 retry disabled")
    require(semantics["second_http_202_is_failure"] is True, "Repeated 202 allowed")
    require(
        semantics["http_200_without_all_frozen_anchors_is_failure"] is True,
        "Anchor failure disabled",
    )
    require(
        semantics["network_budget_consumed_per_request"] is True,
        "Retry requests excluded from budget",
    )

    boundary = policy["non_authorisations"]
    for key in (
        "threshold_change",
        "source_scope_change",
        "new_host",
        "raw_body_retention",
        "public_claim_contribution",
        "gate7_closed",
    ):
        require(boundary[key] is False, f"Retry policy enabled {key}")
    require(boundary["public_launch"] == "NO_GO", "Retry policy enabled launch")

    return {
        "status": "PASS",
        "output": "O01_OFFICIAL_SOURCE_RETRY_POLICY_PASS",
        "policy_sha256": f"sha256:{digest(policy_path)}",
        "trigger_artifact_id": trigger["artifact_id"],
        "trigger_artifact_digest": trigger["artifact_digest"],
        "maximum_attempts_per_source": policy["maximum_attempts_per_source"],
        "claim_contribution": False,
        "gate7_closed": False,
        "public_launch": "NO_GO",
    }


def verify_result(
    result_dir: Path,
    plan: dict,
    plan_path: Path,
    policy: dict,
    policy_path: Path,
) -> dict:
    compatibility_plan = dict(plan)
    compatibility_plan["schema_version"] = (
        "axignal.o01-history-frequency-lag-plan/v0.4"
    )
    common = verify_v4_result(result_dir, compatibility_plan, plan_path)
    policy_result = verify_policy(policy, policy_path)
    ledger = load_json(result_dir / "official-source-attempt-ledger.v0.1.json")
    observations = load_json(
        result_dir / "official-source-observations.v0.1.json"
    )
    final = load_json(result_dir / "final-result.v0.1.json")

    require(ledger["status"] == "PASS", "Official-source ledger failed")
    require(
        ledger["policy_sha256"] == policy_result["policy_sha256"],
        "Ledger policy digest drift",
    )
    require(ledger["response_bodies_persisted"] is False, "Source bodies retained")
    require(ledger["source_count"] == 5, "Unexpected official-source count")
    require(len(ledger["sources"]) == 5, "Incomplete official-source ledger")
    require(5 <= ledger["attempt_count"] <= 10, "Attempt count outside contract")

    observed_urls = {item["url"] for item in plan["official_sources"]}
    ledger_urls = {item["url"] for item in ledger["sources"]}
    require(ledger_urls == observed_urls, "Official-source URL set drift")
    for source in ledger["sources"]:
        require(source["status"] == "PASS", f"Source failed: {source['url']}")
        require(source["response_body_persisted"] is False, "Source body retained")
        attempts = source["attempts"]
        require(1 <= len(attempts) <= 2, "Per-source attempt count drift")
        require(attempts[-1]["http_status"] == 200, "Final source status is not 200")
        require(attempts[-1]["accepted"] is True, "Final source response rejected")
        for attempt in attempts:
            require(
                attempt["response_body_persisted"] is False,
                "Attempt body was persisted",
            )
            if attempt["http_status"] == 202:
                require(attempt["accepted"] is False, "HTTP 202 accepted as evidence")

    require(
        observations["schema_version"]
        == "axignal.o01-official-source-observations/v0.7",
        "Observation schema drift",
    )
    require(
        observations["retry_policy_sha256"] == policy_result["policy_sha256"],
        "Observation policy digest drift",
    )
    require(
        observations["attempt_ledger"]
        == "official-source-attempt-ledger.v0.1.json",
        "Observation ledger reference drift",
    )
    require(
        observations["response_bodies_persisted"] is False,
        "Observation bodies retained",
    )
    require(len(observations["documents"]) == 5, "Observation count drift")
    require(
        all(item["status"] == "PASS" for item in observations["documents"]),
        "An official source observation failed",
    )

    require(
        final["schema_version"]
        == "axignal.o01-history-frequency-lag-result/v0.7",
        "Unexpected final result schema",
    )
    require(final["status"] == "PASS", "Final result failed")
    require(final["output"] == "O01_HISTORY_FREQUENCY_LAG_PASS", "Output drift")
    require(
        final["official_source_retry_policy_sha256"]
        == policy_result["policy_sha256"],
        "Final policy digest drift",
    )
    require(
        final["official_source_attempt_ledger"]
        == "official-source-attempt-ledger.v0.1.json",
        "Final ledger reference drift",
    )
    require(
        final["official_source_attempt_count"] == ledger["attempt_count"],
        "Final attempt count drift",
    )
    require(
        final["official_source_response_bodies_persisted"] is False,
        "Final result retained source bodies",
    )
    return {
        **common,
        **policy_result,
        "implementation": "INSTRUMENTED_OFFICIAL_SOURCE_RETRY_V0_7",
        "official_source_count": ledger["source_count"],
        "official_source_attempt_count": ledger["attempt_count"],
        "all_official_sources_final_http_200": True,
        "official_source_response_bodies_persisted": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--retry-policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--result-dir", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    plan_path = args.plan.resolve()
    policy_path = args.retry_policy.resolve()
    try:
        plan = load_json(plan_path)
        policy = load_json(policy_path)
        plan_result = verify_v6_plan(plan, plan_path)
        policy_result = verify_policy(policy, policy_path)
        result = {**plan_result, **policy_result}
        if args.result_dir is not None:
            result = verify_result(
                args.result_dir,
                plan,
                plan_path,
                policy,
                policy_path,
            )
    except (KeyError, OSError, TypeError, ValueError, ContractError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True))
        return 1

    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
