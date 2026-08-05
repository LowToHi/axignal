from pathlib import Path

SCRIPT = Path("apps/api/src/axignal_api/c4_axent_e2e.py")


def test_c4_executor_does_not_embed_ci_topology_secrets() -> None:
    source = SCRIPT.read_text(encoding="utf-8")

    assert "ci-admin-password" not in source
    assert "ci-axent-key" not in source
    assert "AXIGNAL_AXENT_ENCRYPTION_KEY" in source
    assert "secrets.token_urlsafe" in source


def test_c4_executor_uses_the_real_pilot_and_database_verifier() -> None:
    source = SCRIPT.read_text(encoding="utf-8")

    assert "infra/pilot/compose.yaml" in source
    assert "infra/pilot/remote/compose.shared-traefik.yaml" in source
    assert "scripts/verify_axent_research_persistence_e2e.py" in source
    assert "docker compose" in source
