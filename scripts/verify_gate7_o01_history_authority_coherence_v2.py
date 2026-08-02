from __future__ import annotations

import json
from pathlib import Path

from axignal_api.o01_history_frequency_lag_v6 import (
    DIAGNOSTIC_DIGEST as RUNTIME_DIAGNOSTIC_DIGEST,
)
from axignal_api.o01_history_frequency_lag_v6 import PLAN_SCHEMA as RUNTIME_PLAN_SCHEMA
from axignal_api.o01_history_frequency_lag_v7 import POLICY_SCHEMA
from verify_gate7_o01_history_frequency_lag_v6 import (
    DIAGNOSTIC_DIGEST as VERIFIER_DIAGNOSTIC_DIGEST,
)
from verify_gate7_o01_history_frequency_lag_v6 import PLAN_SCHEMA as VERIFIER_PLAN_SCHEMA

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / (
    "data/acceptance/campaigns/"
    "AX-LIB-O01-history-frequency-lag-plan.v0.5.json"
)
POLICY_PATH = ROOT / (
    "data/acceptance/campaigns/"
    "AX-LIB-O01-official-source-retry-policy.v0.1.json"
)
ACTIVE_PATHS = (
    PLAN_PATH,
    POLICY_PATH,
    ROOT / "apps/api/src/axignal_api/o01_official_source_retry.py",
    ROOT / "apps/api/src/axignal_api/o01_history_frequency_lag_v7.py",
    ROOT / "apps/api/tests/test_o01_official_source_retry.py",
    ROOT / "scripts/run_gate7_o01_history_frequency_lag_v7.py",
    ROOT / "scripts/verify_gate7_o01_history_frequency_lag_v7.py",
    ROOT / ".github/workflows/o01-history-frequency-lag-v0.7.yml",
)
EMPTY_BODY_SHA256 = (
    "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
)


def main() -> int:
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))

    assert plan["schema_version"] == RUNTIME_PLAN_SCHEMA == VERIFIER_PLAN_SCHEMA
    assert (
        plan["history_contract_diagnostic"]["artifact_digest"]
        == RUNTIME_DIAGNOSTIC_DIGEST
        == VERIFIER_DIAGNOSTIC_DIGEST
    )
    assert policy["schema_version"] == POLICY_SCHEMA
    assert policy["task_id"] == plan["task_id"]
    assert policy["library_id"] == plan["library_id"]
    assert policy["source_id"] == plan["source"]["source_id"]
    assert policy["maximum_attempts_per_source"] == 2
    assert policy["final_status_required"] == 200
    assert policy["trigger_evidence"]["artifact_id"] == 8840624551
    assert policy["trigger_evidence"]["response_sha256"] == EMPTY_BODY_SHA256
    assert policy["trigger_evidence"]["state_transition_applied"] is False
    assert policy["accepted_semantics"]["http_202_is_evidence"] is False
    assert policy["accepted_semantics"]["second_http_202_is_failure"] is True
    assert policy["non_authorisations"]["threshold_change"] is False
    assert policy["non_authorisations"]["source_scope_change"] is False
    assert policy["non_authorisations"]["new_host"] is False
    assert policy["non_authorisations"]["raw_body_retention"] is False
    assert policy["non_authorisations"]["public_claim_contribution"] is False
    assert policy["non_authorisations"]["gate7_closed"] is False
    assert policy["non_authorisations"]["public_launch"] == "NO_GO"
    assert plan["network"]["maximum_requests"] == 60
    assert plan["non_authorisations"]["public_claim_contribution"] is False
    assert plan["non_authorisations"]["gate7_closed"] is False
    assert plan["non_authorisations"]["public_launch"] == "NO_GO"

    for path in ACTIVE_PATHS:
        assert path.is_file(), f"Missing active remediation surface: {path}"

    runtime_text = (
        ROOT / "apps/api/src/axignal_api/o01_official_source_retry.py"
    ).read_text(encoding="utf-8")
    assert "status == 200" in runtime_text
    assert "response_body_persisted" in runtime_text
    assert "DEFAULT_RETRYABLE_STATUSES" in runtime_text

    result = {
        "status": "PASS",
        "output": "O01_HISTORY_RETRY_AUTHORITY_COHERENCE_PASS",
        "plan_schema": plan["schema_version"],
        "policy_schema": policy["schema_version"],
        "trigger_artifact_id": policy["trigger_evidence"]["artifact_id"],
        "trigger_artifact_digest": policy["trigger_evidence"]["artifact_digest"],
        "http_202_is_evidence": False,
        "maximum_attempts_per_source": 2,
        "final_status_required": 200,
        "active_surfaces": [str(path.relative_to(ROOT)) for path in ACTIVE_PATHS],
        "claim_contribution": False,
        "gate7_closed": False,
        "public_launch": "NO_GO",
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
