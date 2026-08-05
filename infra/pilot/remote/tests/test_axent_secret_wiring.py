from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = Path(__file__).resolve().parents[4]


def load_prepare_env():
    path = ROOT / "prepare_env.py"
    spec = importlib.util.spec_from_file_location("prepare_env_axent_secret", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def arguments() -> argparse.Namespace:
    return argparse.Namespace(
        sha="a" * 40,
        site_address="https://pilot.example.test",
        acme_email="ops@example.test",
        auth_email="operator@example.test",
        auth_subject="usr_operator",
        edge_mode="shared-traefik",
        bind_address="0.0.0.0",
        http_port=18080,
        https_port=443,
        allow_http=False,
    )


def test_remote_environment_generates_separate_stable_axent_secret_class() -> None:
    module = load_prepare_env()
    values = module.build_environment(
        arguments(),
        "11111111-1111-4111-8111-111111111111",
        "temporary-password-long-enough",
    )
    key = values["AXIGNAL_AXENT_ENCRYPTION_KEY"]
    assert len(key.encode("utf-8")) >= 32
    assert key != values["AXIGNAL_SESSION_SECRET"]
    assert key != values["AXIGNAL_IDENTITY_ASSERTION_SECRET"]
    assert key != values["AXIGNAL_POSTGRES_PASSWORD"]


def test_pilot_compose_requires_axent_key_and_example_documents_it() -> None:
    compose = yaml.safe_load(
        (REPOSITORY_ROOT / "infra/pilot/compose.yaml").read_text(encoding="utf-8")
    )
    value = compose["services"]["api"]["environment"][
        "AXIGNAL_AXENT_ENCRYPTION_KEY"
    ]
    assert value == "${AXIGNAL_AXENT_ENCRYPTION_KEY:?required}"
    example = (REPOSITORY_ROOT / "infra/pilot/env.example").read_text(encoding="utf-8")
    assert "AXIGNAL_AXENT_ENCRYPTION_KEY=" in example
    topology = yaml.safe_load(
        (REPOSITORY_ROOT / "infra/pilot/topology.yaml").read_text(encoding="utf-8")
    )
    assert "axent-conversation-encryption" in topology["security"][
        "required_secret_classes"
    ]
