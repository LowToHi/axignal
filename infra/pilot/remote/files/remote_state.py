#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path


def atomic_write(path: Path, content: str, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f'.{path.name}.', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(name, mode)
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def get_value(args: argparse.Namespace) -> int:
    if not args.path.exists():
        print('')
        return 0
    payload = json.loads(args.path.read_text(encoding='utf-8'))
    value = payload.get(args.key)
    print('' if value is None else value)
    return 0


def set_build_sha(args: argparse.Namespace) -> int:
    lines = args.path.read_text(encoding='utf-8').splitlines()
    replacement = f"AXIGNAL_BUILD_SHA='{args.sha}'"
    found = False
    updated = []
    for line in lines:
        if line.startswith('AXIGNAL_BUILD_SHA='):
            updated.append(replacement)
            found = True
        else:
            updated.append(line)
    if not found:
        updated.append(replacement)
    atomic_write(args.path, '\n'.join(updated) + '\n')
    return 0


def write_deployment(args: argparse.Namespace) -> int:
    payload = {
        'status': 'REMOTE_PILOT_ACCEPTED',
        'current_sha': args.current_sha,
        'previous_sha': args.previous_sha or None,
        'release_path': str(args.release_path),
        'backup_path': args.backup_path or None,
        'deployed_at': datetime.now(UTC).isoformat().replace('+00:00', 'Z'),
    }
    atomic_write(args.path, json.dumps(payload, indent=2, sort_keys=True) + '\n')
    print(json.dumps(payload, sort_keys=True))
    return 0


def write_watchdog(args: argparse.Namespace) -> int:
    payload = {
        'status': args.status,
        'build_sha': args.sha,
        'checked_at': datetime.now(UTC).isoformat().replace('+00:00', 'Z'),
    }
    atomic_write(args.path, json.dumps(payload, indent=2, sort_keys=True) + '\n')
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    subs = result.add_subparsers(dest='command', required=True)

    get = subs.add_parser('get')
    get.add_argument('--path', type=Path, required=True)
    get.add_argument('--key', required=True)
    get.set_defaults(handler=get_value)

    update = subs.add_parser('set-build-sha')
    update.add_argument('--path', type=Path, required=True)
    update.add_argument('--sha', required=True)
    update.set_defaults(handler=set_build_sha)

    write = subs.add_parser('write-deployment')
    write.add_argument('--path', type=Path, required=True)
    write.add_argument('--current-sha', required=True)
    write.add_argument('--previous-sha', default='')
    write.add_argument('--release-path', type=Path, required=True)
    write.add_argument('--backup-path', default='')
    write.set_defaults(handler=write_deployment)

    watchdog = subs.add_parser('write-watchdog')
    watchdog.add_argument('--path', type=Path, required=True)
    watchdog.add_argument('--status', choices=['PASS', 'FAIL'], required=True)
    watchdog.add_argument('--sha', required=True)
    watchdog.set_defaults(handler=write_watchdog)
    return result


def main() -> int:
    args = parser().parse_args()
    return args.handler(args)


if __name__ == '__main__':
    raise SystemExit(main())
