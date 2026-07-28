from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fast_scrypt_record(password: str) -> str:
    digest = hashlib.sha256(password.encode()).hexdigest()
    return f"scrypt$test${digest}"


def create_args(tmp_path: Path, *, edge_mode: str = "shared-traefik") -> argparse.Namespace:
    return argparse.Namespace(
        output=tmp_path / "pilot.env",
        password_output=tmp_path / "operator-password.pending",
        metadata_output=tmp_path / "credential-metadata.json",
        sha="a" * 40,
        site_address="https://pilot.example.com",
        acme_email="ops@example.com",
        auth_email="operator@example.com",
        auth_subject="usr_operator",
        edge_mode=edge_mode,
        bind_address="0.0.0.0",
        http_port=18080 if edge_mode == "shared-traefik" else 80,
        https_port=443,
        allow_http=False,
    )


def test_host_only_create_contains_no_plaintext_credentials(tmp_path: Path) -> None:
    module = load("prepare_env_create", "prepare_env.py")
    args = create_args(tmp_path)
    payload = module.create(args)

    environment = args.output.read_text(encoding="utf-8")
    password = args.password_output.read_text(encoding="utf-8").strip()
    tenant_line = next(
        line for line in environment.splitlines() if line.startswith("AXIGNAL_AUTH_TENANT_ID=")
    )
    tenant_id = tenant_line.split("=", 1)[1].strip("'")
    serialized_metadata = json.dumps(payload, sort_keys=True)

    if os.name != "nt":
        assert oct(args.output.stat().st_mode & 0o777) == "0o600"
        assert oct(args.password_output.stat().st_mode & 0o777) == "0o600"
        assert oct(args.metadata_output.stat().st_mode & 0o777) == "0o600"
    assert password not in environment
    assert password not in serialized_metadata
    assert tenant_id not in serialized_metadata
    assert "AXIGNAL_AUTH_PASSWORD_SCRYPT='scrypt$" in environment
    assert "AXIGNAL_PILOT_EDGE_MODE='shared-traefik'" in environment
    assert "AXIGNAL_PILOT_BIND_ADDRESS='127.0.0.1'" in environment
    assert "AXIGNAL_PILOT_CADDY_SITE_ADDRESS=':80'" in environment
    assert payload["rotation_required"] is True
    assert payload["deployment_evidence"] is False
    assert payload["acceptance_evidence"] is False


def test_standalone_environment_preserves_direct_tls_boundary(tmp_path: Path) -> None:
    module = load("prepare_env_standalone", "prepare_env.py")
    module.scrypt_record = fast_scrypt_record
    args = create_args(tmp_path, edge_mode="standalone")
    payload = module.create(args)
    environment = args.output.read_text(encoding="utf-8")
    assert "AXIGNAL_PILOT_EDGE_MODE='standalone'" in environment
    assert "AXIGNAL_PILOT_BIND_ADDRESS='0.0.0.0'" in environment
    assert "AXIGNAL_PILOT_CADDY_SITE_ADDRESS='https://pilot.example.com'" in environment
    assert payload["status"] == "TEMPORARY_CREDENTIAL_PENDING_ROTATION"


def test_create_rejects_short_sha_without_writing_secrets(tmp_path: Path) -> None:
    module = load("prepare_env_invalid", "prepare_env.py")
    args = create_args(tmp_path)
    args.sha = "abc"
    try:
        module.create(args)
    except ValueError as exc:
        assert "40-character" in str(exc)
    else:
        raise AssertionError("short SHA was accepted")
    assert not args.output.exists()
    assert not args.password_output.exists()


def test_rotation_consumes_temporary_password_and_retirement_removes_plaintext(
    tmp_path: Path,
) -> None:
    module = load("prepare_env_rotation", "prepare_env.py")
    module.scrypt_record = fast_scrypt_record
    if os.name == "nt":
        def windows_private_file(path: Path, label: str) -> None:
            if not path.is_file():
                raise ValueError(f"{label} does not exist")

        module.validate_private_file = windows_private_file
    create_namespace = create_args(tmp_path)
    module.create(create_namespace)
    original_hash = next(
        line
        for line in create_namespace.output.read_text(encoding="utf-8").splitlines()
        if line.startswith("AXIGNAL_AUTH_PASSWORD_SCRYPT=")
    )
    original_session_secret = next(
        line
        for line in create_namespace.output.read_text(encoding="utf-8").splitlines()
        if line.startswith("AXIGNAL_SESSION_SECRET=")
    )

    rotated_password = tmp_path / "operator-password.rotated"
    rotation = argparse.Namespace(
        environment=create_namespace.output,
        current_password_file=create_namespace.password_output,
        password_output=rotated_password,
        metadata_output=create_namespace.metadata_output,
    )
    rotation_payload = module.rotate(rotation)
    rotated_hash = next(
        line
        for line in create_namespace.output.read_text(encoding="utf-8").splitlines()
        if line.startswith("AXIGNAL_AUTH_PASSWORD_SCRYPT=")
    )
    rotated_session_secret = next(
        line
        for line in create_namespace.output.read_text(encoding="utf-8").splitlines()
        if line.startswith("AXIGNAL_SESSION_SECRET=")
    )
    assert not create_namespace.password_output.exists()
    assert rotated_password.exists()
    assert original_hash != rotated_hash
    assert original_session_secret != rotated_session_secret
    assert rotation_payload["status"] == "ROTATED_CREDENTIAL_PENDING_HANDOFF"
    assert rotation_payload["rotation_required"] is False
    assert rotation_payload["sessions_invalidated"] is True
    assert rotation_payload["acceptance_evidence"] is False

    retirement = argparse.Namespace(
        password_file=rotated_password,
        metadata_output=create_namespace.metadata_output,
    )
    retired_payload = module.retire(retirement)
    assert not rotated_password.exists()
    assert retired_payload["status"] == "PLAINTEXT_CREDENTIAL_RETIRED"
    assert retired_payload["password_file"]["exists"] is False


def test_remote_state_records_deployment_without_self_acceptance(tmp_path: Path) -> None:
    module = load("remote_state", "files/remote_state.py")
    env_file = tmp_path / "pilot.env"
    env_file.write_text(
        "AXIGNAL_BUILD_SHA='" + ("a" * 40) + "'\nSECRET='keep'\n",
        encoding="utf-8",
    )
    os.chmod(env_file, 0o600)
    module.set_build_sha(argparse.Namespace(path=env_file, sha="b" * 40))
    assert "SECRET='keep'" in env_file.read_text(encoding="utf-8")
    assert "AXIGNAL_BUILD_SHA='" + ("b" * 40) + "'" in env_file.read_text(encoding="utf-8")

    state_file = tmp_path / "current.json"
    module.write_deployment(
        argparse.Namespace(
            path=state_file,
            current_sha="b" * 40,
            previous_sha="a" * 40,
            release_path=Path("/opt/axignal/releases") / ("b" * 40),
            backup_path="/var/backups/axignal/example",
        )
    )
    payload = json.loads(state_file.read_text(encoding="utf-8"))
    assert payload["status"] == "DEPLOYED_AWAITING_ACCEPTANCE"
    assert payload["acceptance_status"] == "BLOCKED"
    assert payload["current_sha"] == "b" * 40
    if os.name != "nt":
        assert oct(state_file.stat().st_mode & 0o777) == "0o600"
