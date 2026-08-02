from __future__ import annotations

import json
from pathlib import Path

from axignal_api.o01_history_frequency_lag_v6 import (
    DIAGNOSTIC_DIGEST as RUNTIME_DIAGNOSTIC_DIGEST,
)
from axignal_api.o01_history_frequency_lag_v6 import PLAN_SCHEMA as RUNTIME_PLAN_SCHEMA
from verify_gate7_o01_history_frequency_lag_v6 import (
    DIAGNOSTIC_DIGEST as VERIFIER_DIAGNOSTIC_DIGEST,
)
from verify_gate7_o01_history_frequency_lag_v6 import PLAN_SCHEMA as VERIFIER_PLAN_SCHEMA

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / (
    "data/acceptance/campaigns/"
    "AX-LIB-O01-history-frequency-lag-plan.v0.5.json"
)
ACTIVE_PATHS = (
    PLAN_PATH,
    ROOT / "apps/api/src/axignal_api/o01_history_frequency_lag_v6.py",
    ROOT / "scripts/run_gate7_o01_history_frequency_lag_v6.py",
    ROOT / "scripts/verify_gate7_o01_history_frequency_lag_v6.py",
    ROOT / "scripts/verify_gate7_o01_history_authority_coherence.py",
    ROOT / ".github/workflows/o01-history-frequency-lag-v0.6.yml",
)
STALE_DIGESTS = (
    "sha256:f6a75224324c5e1e0d1edec277286ee167c8992e72c40dc12bb98373abf8b7e2",
    "sha256:f6a7524549b8e97a9b65fc21e9a1d728943d80c842d6cb75978a8d83f9e91dc6",
)


def main() -> int:
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    plan_schema = plan["schema_version"]
    plan_digest = plan["history_contract_diagnostic"]["artifact_digest"]

    assert plan_schema == RUNTIME_PLAN_SCHEMA == VERIFIER_PLAN_SCHEMA
    assert plan_digest == RUNTIME_DIAGNOSTIC_DIGEST == VERIFIER_DIAGNOSTIC_DIGEST
    assert plan["history_contract_diagnostic"]["artifact_id"] == 8839903336
    assert plan["history_contract_diagnostic"]["raw_bodies_retained"] is False
    assert plan["baseline"]["admission_artifact_id"] == 8838855002
    assert plan["calendar_format_probe"]["artifact_id"] == 8839697337
    assert plan["network"]["maximum_requests"] == 60
    assert plan["non_authorisations"]["public_claim_contribution"] is False
    assert plan["non_authorisations"]["gate7_closed"] is False
    assert plan["non_authorisations"]["public_launch"] == "NO_GO"

    for path in ACTIVE_PATHS:
        assert path.is_file(), f"Missing active authority surface: {path}"
        text = path.read_text(encoding="utf-8")
        for stale in STALE_DIGESTS:
            assert stale not in text, f"Stale diagnostic digest in {path}: {stale}"

    result = {
        "status": "PASS",
        "output": "O01_HISTORY_AUTHORITY_COHERENCE_PASS",
        "plan_schema": plan_schema,
        "diagnostic_artifact_id": 8839903336,
        "diagnostic_artifact_digest": plan_digest,
        "active_surfaces": [str(path.relative_to(ROOT)) for path in ACTIVE_PATHS],
        "stale_digests_rejected": list(STALE_DIGESTS),
        "claim_contribution": False,
        "gate7_closed": False,
        "public_launch": "NO_GO",
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
