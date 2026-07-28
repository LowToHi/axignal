from __future__ import annotations

import argparse
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


def test_prepare_environment_is_root_only_and_contains_no_plaintext_password(tmp_path: Path) -> None:
    module = load('prepare_env', 'prepare_env.py')
    output = tmp_path / 'pilot.env'
    args = argparse.Namespace(
        output=output,
        sha='a' * 40,
        site_address='https://pilot.example.com',
        acme_email='ops@example.com',
        auth_email='operator@example.com',
        auth_subject='usr_operator',
        tenant_id='11111111-1111-4111-8111-111111111111',
        operator_password='correct-horse-battery-staple',
        http_port=80,
        https_port=443,
        allow_http=False,
    )
    values = module.build_environment(args)
    module.write_environment(output, values)
    content = output.read_text(encoding='utf-8')
    assert oct(output.stat().st_mode & 0o777) == '0o600'
    assert 'correct-horse-battery-staple' not in content
    assert "AXIGNAL_AUTH_PASSWORD_SCRYPT='scrypt$" in content
    assert values['AXIGNAL_BUILD_SHA'] == 'a' * 40
    assert values['AXIGNAL_LIVE_SOURCES_ENABLED'] == 'false'
    assert values['AXIGNAL_BILLING_ENABLED'] == 'false'


def test_prepare_environment_rejects_short_sha() -> None:
    module = load('prepare_env_invalid', 'prepare_env.py')
    args = argparse.Namespace(
        sha='abc',
        site_address='https://pilot.example.com',
        acme_email='ops@example.com',
        auth_email='operator@example.com',
        auth_subject='usr_operator',
        tenant_id='11111111-1111-4111-8111-111111111111',
        operator_password='correct-horse-battery-staple',
        http_port=80,
        https_port=443,
        allow_http=False,
    )
    try:
        module.build_environment(args)
    except ValueError as exc:
        assert '40-character' in str(exc)
    else:
        raise AssertionError('short SHA was accepted')


def test_remote_state_updates_only_build_sha_and_writes_deployment(tmp_path: Path) -> None:
    module = load('remote_state', 'files/remote_state.py')
    env_file = tmp_path / 'pilot.env'
    env_file.write_text("AXIGNAL_BUILD_SHA='" + ('a' * 40) + "'\nSECRET='keep'\n", encoding='utf-8')
    os.chmod(env_file, 0o600)
    module.set_build_sha(argparse.Namespace(path=env_file, sha='b' * 40))
    assert "SECRET='keep'" in env_file.read_text(encoding='utf-8')
    assert "AXIGNAL_BUILD_SHA='" + ('b' * 40) + "'" in env_file.read_text(encoding='utf-8')

    state_file = tmp_path / 'current.json'
    module.write_deployment(
        argparse.Namespace(
            path=state_file,
            current_sha='b' * 40,
            previous_sha='a' * 40,
            release_path=Path('/opt/axignal/releases') / ('b' * 40),
            backup_path='/var/backups/axignal/example',
        )
    )
    payload = json.loads(state_file.read_text(encoding='utf-8'))
    assert payload['status'] == 'REMOTE_PILOT_ACCEPTED'
    assert payload['current_sha'] == 'b' * 40
    assert oct(state_file.stat().st_mode & 0o777) == '0o600'
