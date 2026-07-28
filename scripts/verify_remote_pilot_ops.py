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
    rotate = text('infra/pilot/remote/files/axignal-remote-rotate-operator')
    prepare = text('infra/pilot/remote/prepare_env.py')
    state = text('infra/pilot/remote/files/remote_state.py')
    compose = text('infra/pilot/compose.yaml')
    shared_edge = text('infra/pilot/remote/compose.shared-traefik.yaml')
    standalone_edge = text('infra/pilot/remote/compose.standalone.yaml')
    traefik = text('infra/pilot/remote/templates/axignal-pilot-traefik.yml.j2')

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
            "item.stat.mode == '0600'",
            'no_log: true',
            'axignal-pilot-backup.timer',
            'axignal-pilot-watchdog.timer',
            'validate_certs: true',
            "axignal_edge_mode == 'shared-traefik'",
            'axignal_internal_http_port',
            'axignal-pilot.yml',
            '/usr/local/lib/axignal/prepare_env.py',
            'DEPLOYED_AWAITING_ACCEPTANCE',
            'axignal_preexisting_containers.stdout_lines',
            'axignal_traefik_after.stdout == axignal_traefik_runtime.stdout',
            "'.acme.email=' ~ axignal_acme_email",
            'axignal_internal_port_listener.stdout | length == 0',
        ],
        'playbook',
    )
    assert '0.0.0.0/0' not in playbook
    assert 'password=' not in playbook.lower()
    assert 'axignal_env_source' not in playbook

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
    require(
        rollback,
        ['previous_sha', 'pg_restore', '--clean', 'axignal-remote-verify'],
        'rollback',
    )
    require(
        watchdog,
        ['AXIGNAL_MIN_FREE_GB', 'df --output=avail', 'write-watchdog'],
        'watchdog',
    )
    require(
        rotate,
        [
            'umask 077',
            'prepare_env.py',
            'rotate',
            'operator-password.rotated',
            'axignal-remote-verify',
        ],
        'credential-rotation',
    )
    require(
        prepare,
        [
            'hashlib.scrypt',
            '0o600',
            'os.umask(0o077)',
            'uuid.uuid4()',
            'secrets.token_urlsafe',
            'TEMPORARY_CREDENTIAL_PENDING_ROTATION',
            'ROTATED_CREDENTIAL_PENDING_HANDOFF',
            'PLAINTEXT_CREDENTIAL_RETIRED',
            'AXIGNAL_LIVE_SOURCES_ENABLED',
            'AXIGNAL_VALIDATION_UI_ENABLED',
            'AXIGNAL_PUBLIC_LAUNCH',
            'AXIGNAL_BILLING_ENABLED',
            'acceptance_evidence',
        ],
        'prepare-env',
    )
    assert '--operator-password' not in prepare
    assert re.search(r'print\([^)]*operator_password', prepare) is None

    assert 'ports:' not in compose
    require(
        shared_edge,
        ['127.0.0.1:${AXIGNAL_PILOT_HTTP_PORT:-18080}:80'],
        'shared Traefik Compose edge',
    )
    assert ':443' not in shared_edge
    require(
        standalone_edge,
        ['AXIGNAL_PILOT_BIND_ADDRESS', 'AXIGNAL_PILOT_HTTP_PORT', 'AXIGNAL_PILOT_HTTPS_PORT'],
        'standalone Compose edge',
    )
    require(
        traefik,
        [
            'Host(`{{ axignal_site_address',
            'axignal_traefik_entrypoint',
            'http://127.0.0.1:{{ axignal_internal_http_port }}',
        ],
        'Traefik route',
    )
    assert 'DEPLOYED_AWAITING_ACCEPTANCE' in state
    assert "'status': 'REMOTE_PILOT_ACCEPTED'" not in state

    units = sorted((REMOTE / 'templates').glob('axignal-pilot-*.service.j2'))
    units += sorted((REMOTE / 'templates').glob('axignal-pilot-*.timer.j2'))
    assert len(units) == 4
    payload = {
        'status': 'PASS',
        'exact_sha_deployment': True,
        'idempotent_bootstrap': True,
        'firewall_allowlist': ['ssh', '80/tcp', '443/tcp'],
        'private_env_mode': '0600',
        'plaintext_operator_password_in_environment': False,
        'temporary_plaintext_password_file': True,
        'temporary_password_file_mode': '0600',
        'host_only_credential_generation': True,
        'credential_rotation_required': True,
        'edge_mode': 'shared-traefik',
        'edge_bind_address': '127.0.0.1',
        'traefik_owns_public_ports': True,
        'deployment_state': 'DEPLOYED_AWAITING_ACCEPTANCE',
        'acceptance_status': 'BLOCKED',
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
