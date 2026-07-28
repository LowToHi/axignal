from __future__ import annotations

import json
from pathlib import Path

import yaml


REQUIRED_PROCESS_FIELDS = {
    "id",
    "command",
    "credential_env",
    "feature_flag",
    "healthcheck",
    "readiness",
    "restart_policy",
    "concurrency_limit",
}


def main() -> int:
    payload = yaml.safe_load(
        Path("infra/runtime/topology.yaml").read_text(encoding="utf-8")
    )
    processes = payload["processes"]
    assert processes
    identifiers = [item["id"] for item in processes]
    assert len(identifiers) == len(set(identifiers))
    for process in processes:
        assert REQUIRED_PROCESS_FIELDS <= set(process)
        assert process["concurrency_limit"] >= 1
        assert process["credential_env"].startswith("AXIGNAL_")
    credentials = payload["security"]["unique_runtime_credentials"]
    assert len(credentials) == len(set(credentials))
    assert "AXIGNAL_SCHEDULER_DATABASE_URL" in credentials
    assert payload["deployment"]["production_authorised"] is False
    print(
        json.dumps(
            {
                "processes": len(processes),
                "unique_credentials": len(credentials),
                "health_readiness_defined": True,
                "production_deployment": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
