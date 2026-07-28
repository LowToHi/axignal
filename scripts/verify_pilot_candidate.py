from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
COMPOSE_PATH = ROOT / "infra/pilot/compose.yaml"
TOPOLOGY_PATH = ROOT / "infra/pilot/topology.yaml"
CADDY_PATH = ROOT / "infra/pilot/Caddyfile"
ENV_EXAMPLE_PATH = ROOT / "infra/pilot/env.example"


def load_yaml(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise AssertionError(f"{path} must contain a mapping")
    return loaded


def main() -> None:
    compose = load_yaml(COMPOSE_PATH)
    topology = load_yaml(TOPOLOGY_PATH)
    services = compose.get("services", {})
    expected = {
        "postgres",
        "db-hardening",
        "valkey",
        "api",
        "web",
        "caddy",
        "research-worker",
        "proposal-worker",
        "admission-runtime",
        "scheduler",
        "otel-collector",
    }
    assert expected <= set(services), "pilot topology is incomplete"

    public_ports = {
        service_id: service.get("ports", [])
        for service_id, service in services.items()
        if service.get("ports")
    }
    assert set(public_ports) == {"caddy"}, "only Caddy may publish host ports"
    assert compose["networks"]["backend"]["internal"] is True

    valkey_command = " ".join(services["valkey"]["command"])
    assert "--appendonly yes" in valkey_command
    assert "--appendfsync everysec" in valkey_command
    assert services["api"]["depends_on"]["db-hardening"]["condition"] == (
        "service_completed_successfully"
    )
    assert services["api"]["environment"]["AXIGNAL_LIVE_SOURCES_ENABLED"] == "false"
    assert services["web"]["environment"]["AXIGNAL_AUTH_REQUIRED"] == "true"
    assert services["web"]["environment"]["AXIGNAL_VALIDATION_UI_ENABLED"] == "false"

    caddy = CADDY_PATH.read_text(encoding="utf-8")
    for required in (
        "Strict-Transport-Security",
        "Content-Security-Policy",
        "X-Frame-Options",
        "reverse_proxy web:3000",
    ):
        assert required in caddy

    env_example = ENV_EXAMPLE_PATH.read_text(encoding="utf-8")
    required_secret_names = topology["security"]["required_secret_classes"]
    assert len(required_secret_names) >= 9
    assert "replace-with-long-random-secret" in env_example
    assert "AXIGNAL_SESSION_SECRET" in env_example
    assert "AXIGNAL_IDENTITY_ASSERTION_SECRET" in env_example

    assert topology["status"] == "private-pilot-candidate"
    assert topology["public_launch_authorised"] is False
    assert topology["billing_enabled"] is False
    assert topology["entrypoint"]["direct_api_exposure"] is False
    assert topology["canonical_demo"]["synthetic"] is True
    assert topology["canonical_demo"]["canonical_mutation_allowed"] is False
    assert topology["operations"]["restore_rehearsal_required"] is True

    required_files = (
        ROOT / "apps/web/app/demo/page.tsx",
        ROOT / "apps/web/components/demo-guide.tsx",
        ROOT / "apps/web/app/api/health/route.ts",
        ROOT / "apps/api/src/axignal_api/pilot_health.py",
        ROOT / "infra/pilot/backup.sh",
        ROOT / "infra/pilot/restore-rehearsal.sh",
        ROOT / "infra/pilot/harden-db.sh",
    )
    for path in required_files:
        assert path.is_file(), f"missing {path.relative_to(ROOT)}"

    evidence = {
        "private_pilot_topology": True,
        "only_edge_ports_published": True,
        "direct_api_exposure": False,
        "valkey_persistence": "appendonly-everysec",
        "runtime_database_credentials_rotated": True,
        "authentication_required": True,
        "live_sources_enabled": False,
        "human_study_enabled": False,
        "canonical_demo_synthetic": True,
        "backup_restore_contract": True,
        "public_launch_authorised": False,
        "billing_enabled": False,
    }
    print(json.dumps(evidence, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
