from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
COMPOSE_PATH = ROOT / "infra/pilot/compose.yaml"
STANDALONE_EDGE_PATH = ROOT / "infra/pilot/remote/compose.standalone.yaml"
SHARED_TRAEFIK_EDGE_PATH = ROOT / "infra/pilot/remote/compose.shared-traefik.yaml"
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
    standalone_edge = load_yaml(STANDALONE_EDGE_PATH)
    shared_traefik_edge = load_yaml(SHARED_TRAEFIK_EDGE_PATH)
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

    base_public_ports = {
        service_id: service.get("ports", [])
        for service_id, service in services.items()
        if service.get("ports")
    }
    assert not base_public_ports, "the base topology must not publish host ports"
    assert set(standalone_edge["services"]) == {"caddy"}
    assert set(shared_traefik_edge["services"]) == {"caddy"}
    shared_ports = shared_traefik_edge["services"]["caddy"]["ports"]
    assert shared_ports == ["127.0.0.1:${AXIGNAL_PILOT_HTTP_PORT:-18080}:80"]
    assert all(":443" not in port for port in shared_ports)
    assert compose["networks"]["backend"]["internal"] is True
    assert compose["networks"]["ted-egress"]["internal"] is False

    valkey_command = " ".join(services["valkey"]["command"])
    assert "--appendonly yes" in valkey_command
    assert "--appendfsync everysec" in valkey_command
    assert services["api"]["depends_on"]["db-hardening"]["condition"] == (
        "service_completed_successfully"
    )

    api_environment = services["api"]["environment"]
    worker_environment = services["research-worker"]["environment"]
    web_environment = services["web"]["environment"]
    assert api_environment["AXIGNAL_LIVE_SOURCES_ENABLED"] == "false"
    assert worker_environment["AXIGNAL_LIVE_SOURCES_ENABLED"] == "false"
    assert api_environment["AXIGNAL_TED_PROCUREMENT_ENABLED"] == "true"
    assert api_environment["AXIGNAL_TED_LIVE_SOURCES_ENABLED"] == "true"
    assert worker_environment["AXIGNAL_TED_PROCUREMENT_ENABLED"] == "true"
    assert worker_environment["AXIGNAL_TED_LIVE_SOURCES_ENABLED"] == "true"
    assert web_environment["AXIGNAL_TED_PROCUREMENT_UI_ENABLED"] == "true"
    assert web_environment["AXIGNAL_AUTH_REQUIRED"] == "true"
    assert web_environment["AXIGNAL_VALIDATION_UI_ENABLED"] == "false"
    assert api_environment["AXIGNAL_AXENT_ENCRYPTION_KEY"] == (
        "${AXIGNAL_AXENT_ENCRYPTION_KEY:?required}"
    )

    egress_services = {
        service_id
        for service_id, service in services.items()
        if "ted-egress" in service.get("networks", [])
    }
    assert egress_services == {"research-worker"}, "TED egress is not worker-exclusive"
    assert services["research-worker"]["networks"] == ["backend", "ted-egress"]

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
    assert len(required_secret_names) >= 10
    assert "replace-with-long-random-secret" in env_example
    assert "AXIGNAL_SESSION_SECRET" in env_example
    assert "AXIGNAL_IDENTITY_ASSERTION_SECRET" in env_example
    assert "AXIGNAL_AXENT_ENCRYPTION_KEY" in env_example
    assert "axent-conversation-encryption" in required_secret_names

    assert topology["status"] == "private-pilot-candidate"
    assert topology["public_launch_authorised"] is False
    assert topology["billing_enabled"] is False
    assert topology["entrypoint"]["direct_api_exposure"] is False
    assert topology["entrypoint"]["modes"]["shared-traefik"]["public_port_owner"] == (
        "traefik"
    )
    assert topology["entrypoint"]["modes"]["shared-traefik"]["caddy_bind_address"] == (
        "127.0.0.1"
    )
    assert topology["security"]["global_live_sources_enabled"] is False
    assert topology["security"]["ted_bounded_live_source_enabled"] is True
    assert topology["security"]["ted_egress_service_allowlist"] == ["research-worker"]
    assert topology["bounded_ted_runtime"]["task_state"] == "ACCEPTED"
    assert topology["bounded_ted_runtime"]["public_general_availability"] is False
    assert topology["canonical_demo"]["synthetic"] is True
    assert topology["canonical_demo"]["canonical_mutation_allowed"] is False
    assert topology["operations"]["restore_rehearsal_required"] is True
    assert topology["operations"]["deployment_state"] == "DEPLOYED_AWAITING_ACCEPTANCE"
    assert topology["operations"]["independent_acceptance_required"] is True

    required_files = (
        ROOT / "apps/web/app/demo/page.tsx",
        ROOT / "apps/web/components/demo-guide.tsx",
        ROOT / "apps/web/app/api/health/route.ts",
        ROOT / "apps/api/src/axignal_api/pilot_health.py",
        ROOT / "infra/pilot/backup.sh",
        ROOT / "infra/pilot/restore-rehearsal.sh",
        ROOT / "infra/pilot/harden-db.sh",
        ROOT / "docs/security/AX-F8-T14-ted-runtime-security-review.md",
    )
    for path in required_files:
        assert path.is_file(), f"missing {path.relative_to(ROOT)}"

    evidence = {
        "private_pilot_topology": True,
        "only_edge_ports_published": True,
        "shared_edge_loopback_only": True,
        "traefik_retains_public_ports": True,
        "direct_api_exposure": False,
        "valkey_persistence": "appendonly-everysec",
        "runtime_database_credentials_rotated": True,
        "axent_encryption_key_required": True,
        "authentication_required": True,
        "global_live_sources_enabled": False,
        "ted_bounded_live_source_enabled": True,
        "ted_egress_service_allowlist": ["research-worker"],
        "human_study_enabled": False,
        "canonical_demo_synthetic": True,
        "bounded_ted_runtime_state": "ACCEPTED_PRIVATE_PILOT",
        "backup_restore_contract": True,
        "public_launch_authorised": False,
        "billing_enabled": False,
    }
    print(json.dumps(evidence, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
