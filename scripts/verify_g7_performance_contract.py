from __future__ import annotations

import json
from pathlib import Path

CONTRACT_PATH = Path(
    "data/acceptance/performance/AX-G7-performance-capacity-contract.v0.2.json"
)
REQUIRED_PROFILES = {"CI_CHARACTERISATION", "PRODUCTION_REPRESENTATIVE"}
REQUIRED_THRESHOLDS = {
    "liveness_error_rate_max",
    "liveness_p95_ms_max",
    "liveness_p99_ms_max",
    "readiness_error_rate_max",
    "readiness_p95_ms_max",
    "enqueue_error_rate_max",
    "enqueue_p95_ms_max",
    "research_success_rate_min",
    "completion_p95_seconds_max",
    "completion_p99_seconds_max",
    "tenant_fairness_ratio_min",
    "queue_max_depth_max",
    "queue_residual_max",
    "container_restarts_max",
    "memory_limit_utilisation_max",
}


def main() -> int:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    assert contract["contract_id"] == "AX-G7-PERFORMANCE-CAPACITY-v0.2"
    assert contract["supersedes"] == "AX-G7-PERFORMANCE-CAPACITY-v0.1"
    assert contract["gate"] == "G7"
    assert contract["status"] == "IN_PROGRESS"
    assert set(contract["profiles"]) == REQUIRED_PROFILES
    assert contract["baseline"]["authority_sha"] == (
        "55ed7fb6d73bee8ca22ccdcaeaf4c5a550819a22"
    )

    for profile_name, profile in contract["profiles"].items():
        assert profile["closure_authority"] is False
        assert profile["minimum_liveness_requests"] > 0
        assert profile["minimum_readiness_requests"] > 0
        assert profile["minimum_research_runs"] > 0
        assert profile["minimum_soak_seconds"] > 0
        thresholds = profile["thresholds"]
        assert set(thresholds) >= REQUIRED_THRESHOLDS
        assert 0 <= thresholds["liveness_error_rate_max"] < 1
        assert 0 <= thresholds["readiness_error_rate_max"] < 1
        assert 0 <= thresholds["enqueue_error_rate_max"] < 1
        assert 0 < thresholds["research_success_rate_min"] <= 1
        assert 0 < thresholds["tenant_fairness_ratio_min"] <= 1
        assert thresholds["queue_max_depth_max"] >= profile["minimum_research_runs"]
        if profile_name == "PRODUCTION_REPRESENTATIVE":
            assert "memory_growth_mib_per_hour_max" in thresholds

    truth = contract["truth_boundary"]
    assert truth == {
        "ci_pass_closes_g7": False,
        "production_campaign_pass_closes_g7": False,
        "human_capacity_acceptance_required": True,
        "public_launch_authorised": False,
    }
    assert set(contract["required_launch_decisions"]) == {
        "SRE_OPERATIONS",
        "PRODUCT_CAPACITY_AUTHORITY",
    }

    result = {
        "status": "PASS",
        "output": "AX_G7_PERFORMANCE_CAPACITY_CONTRACT_V02_PASS",
        "gate_decision": "IN_PROGRESS",
        "profiles": sorted(REQUIRED_PROFILES),
        "closure_authorised": False,
        "public_launch_authorised": False,
    }
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
