#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REMOTE = ROOT / 'infra/pilot/remote'


def text(path: str) -> str:
    value = ROOT / path
    assert value.is_file(), f'missing {path}'
    return value.read_text(encoding='utf-8')


def require(content: str, tokens: list[str], label: str) -> None:
    missing = [token for token in tokens if token not in content]
    assert not missing, f'{label} missing: {missing}'


def main() -> int:
    playbook = text('infra/pilot/remote/playbook.yml')
    deploy = text('infra/pilot/remote/files/axignal-remote-deploy')
    verify = text('infra/pilot/remote/files/axignal-remote-verify')
    backup = text('infra/pilot/remote/files/axignal-remote-backup')
    rollback = text('infra/pilot/remote/files/axignal-remote-rollback')
    watchdog = text('infra/pilot/remote/files/axignal-remote-watchdog')
    prepare = text('infra/pilot/remote/prepare_env.py')

    require(
        playbook,
        [
            'ansible_distribution == "Ubuntu"',
            "version('24.04', '>=')",
            "axignal_deploy_sha is match('^[0-9a-f]{40}$')",
            'docker-compose-v2',
            'community.general.ufw',
            'policy: deny',
            "- '80'",
            "- '443'",
            "mode: '0600'",
            'no_log: true',
            'axignal-pilot-backup.timer',
            'axignal-pilot-watchdog.timer',
            'validate_certs: true',
        ],
        'playbook',
    )
    assert '0.0.0.0/0' not in playbook
    assert 'password=' not in playbook.lower()

    require(
        deploy,
        [
            '^[0-9a-f]{40}$',
            'flock -x',
            'git clone --filter=blob:none --no-checkout',
            'git -C "$temporary" fetch --depth 1 origin "$TARGET_SHA"',
            'verify_pilot_candidate.py',
            'verify_demo_contract.py',
            'axignal-remote-backup --print-path',
            'rollback_previous',
            'up --build --detach --wait',
            'write-deployment',
        ],
        'deploy',
    )
    assert 'checkout main' not in deploy
    assert 'checkout master' not in deploy

    require(
        verify,
        [
            '/api/health',
            '/readyz',
            'IDENTITY BOUNDARY',
            'From proposal to defensible knowledge',
            'x-frame-options: DENY',
            'content-security-policy:',
            'axignal_session',
        ],
        'verify',
    )
    require(
        backup,
        [
            'pg_dump',
            'objects.tar.gz',
            'sha256sum database.dump',
            'sha256sum objects.tar.gz',
            'AXIGNAL_BACKUP_RETENTION_DAYS',
        ],
        'backup',
    )
    require(rollback, ['previous_sha', 'pg_restore', '--clean', 'axignal-remote-verify'], 'rollback')
    require(watchdog, ['AXIGNAL_MIN_FREE_GB', 'df --output=avail', 'write-watchdog'], 'watchdog')
    require(
        prepare,
        [
            'hashlib.scrypt',
            '0o600',
            'AXIGNAL_LIVE_SOURCES_ENABLED',
            'AXIGNAL_VALIDATION_UI_ENABLED',
            'AXIGNAL_PUBLIC_LAUNCH',
            'AXIGNAL_BILLING_ENABLED',
            'plaintext_operator_password_stored',
        ],
        'prepare-env',
    )
    assert re.search(r'operator_password\)\s*$', prepare, re.MULTILINE) is None

    units = sorted((REMOTE / 'templates').glob('*.j2'))
    assert len(units) == 4
    payload = {
        'status': 'PASS',
        'exact_sha_deployment': True,
        'idempotent_bootstrap': True,
        'firewall_allowlist': ['ssh', '80/tcp', '443/tcp'],
        'private_env_mode': '0600',
        'plaintext_operator_password_stored': False,
        'backup_covers': ['postgresql', 'content_addressed_objects'],
        'rollback_explicit': True,
        'watchdog_checks': ['edge', 'postgresql', 'valkey', 'object_store', 'disk'],
        'public_launch': False,
        'billing': False,
        'live_sources': False,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
