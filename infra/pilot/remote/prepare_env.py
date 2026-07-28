#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import secrets
import tempfile
import uuid
from datetime import UTC, datetime
from pathlib import Path

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
EDGE_MODES = ("standalone", "shared-traefik")
TEMPORARY_PASSWORD_BYTES = 32


def quote(value: str) -> str:
    if "\n" in value or "\r" in value or "'" in value:
        raise ValueError("environment values may not contain newlines or single quotes")
    return f"'{value}'"


def scrypt_record(password: str) -> str:
    if len(password) < 14:
        raise ValueError("operator password must contain at least 14 characters")
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=2**14,
        r=8,
        p=1,
        dklen=64,
    )
    return f"scrypt${salt.hex()}${digest.hex()}"


def random_secret(size: int = 32) -> str:
    return secrets.token_hex(size)


def validate_email(value: str, label: str) -> str:
    normalized = value.strip().lower()
    if not EMAIL_RE.fullmatch(normalized):
        raise ValueError(f"{label} must be a valid email address")
    return normalized


def validate_output_path(path: Path, label: str) -> None:
    if path.exists():
        raise ValueError(f"{label} already exists; refusing to overwrite it")
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)


def validate_private_file(path: Path, label: str) -> None:
    if not path.is_file():
        raise ValueError(f"{label} does not exist")
    if path.stat().st_mode & 0o777 != 0o600:
        raise ValueError(f"{label} must have mode 0600")


def build_environment(
    args: argparse.Namespace,
    tenant_id: str,
    operator_password: str,
) -> dict[str, str]:
    sha = args.sha.strip().lower()
    if not SHA_RE.fullmatch(sha):
        raise ValueError("--sha must be a full 40-character lowercase hexadecimal commit")

    site_address = args.site_address.rstrip("/")
    allowed_schemes = ("http://", "https://") if args.allow_http else ("https://",)
    if not site_address.startswith(allowed_schemes):
        raise ValueError("--site-address must use HTTPS")
    if "/" in site_address.removeprefix("https://").removeprefix("http://"):
        raise ValueError("--site-address must not contain a path")

    canonical_tenant_id = str(uuid.UUID(tenant_id))
    if canonical_tenant_id != tenant_id.lower():
        raise ValueError("tenant ID must use canonical UUID form")

    edge_mode = args.edge_mode
    http_port = args.http_port
    if edge_mode == "shared-traefik":
        if not site_address.startswith("https://"):
            raise ValueError("shared-traefik mode requires a public HTTPS site address")
        if not 1024 <= http_port <= 65535:
            raise ValueError("shared-traefik internal HTTP port must be between 1024 and 65535")
        bind_address = "127.0.0.1"
        caddy_site_address = ":80"
    else:
        if not 1 <= http_port <= 65535 or not 1 <= args.https_port <= 65535:
            raise ValueError("standalone ports must be between 1 and 65535")
        bind_address = args.bind_address
        caddy_site_address = site_address

    return {
        "AXIGNAL_BUILD_SHA": sha,
        "AXIGNAL_PILOT_SITE_ADDRESS": site_address,
        "AXIGNAL_PILOT_CADDY_SITE_ADDRESS": caddy_site_address,
        "AXIGNAL_PILOT_EDGE_MODE": edge_mode,
        "AXIGNAL_PILOT_BIND_ADDRESS": bind_address,
        "AXIGNAL_PILOT_ACME_EMAIL": validate_email(args.acme_email, "--acme-email"),
        "AXIGNAL_PILOT_HTTP_PORT": str(http_port),
        "AXIGNAL_PILOT_HTTPS_PORT": str(args.https_port),
        "AXIGNAL_POSTGRES_DB": "axignal",
        "AXIGNAL_POSTGRES_USER": "axignal",
        "AXIGNAL_POSTGRES_PASSWORD": random_secret(),
        "AXIGNAL_PROPOSAL_DB_PASSWORD": random_secret(),
        "AXIGNAL_ADMISSION_DB_PASSWORD": random_secret(),
        "AXIGNAL_HUMAN_REVIEW_DB_PASSWORD": random_secret(),
        "AXIGNAL_VALIDATION_DB_PASSWORD": random_secret(),
        "AXIGNAL_VALIDATION_ANALYST_DB_PASSWORD": random_secret(),
        "AXIGNAL_SCHEDULER_DB_PASSWORD": random_secret(),
        "AXIGNAL_AUTH_EMAIL": validate_email(args.auth_email, "--auth-email"),
        "AXIGNAL_AUTH_SUBJECT": args.auth_subject,
        "AXIGNAL_AUTH_TENANT_ID": canonical_tenant_id,
        "AXIGNAL_AUTH_PASSWORD_SCRYPT": scrypt_record(operator_password),
        "AXIGNAL_SESSION_SECRET": random_secret(48),
        "AXIGNAL_IDENTITY_ASSERTION_SECRET": random_secret(48),
        "AXIGNAL_VALIDATION_PARTICIPANT_SALT": random_secret(48),
        "AXIGNAL_OTEL_ENABLED": "false",
        "AXIGNAL_LIVE_SOURCES_ENABLED": "false",
        "AXIGNAL_VALIDATION_UI_ENABLED": "false",
        "AXIGNAL_PUBLIC_LAUNCH": "false",
        "AXIGNAL_BILLING_ENABLED": "false",
    }


def atomic_write(path: Path, content: str, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, mode)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def write_environment(path: Path, values: dict[str, str]) -> None:
    content = "\n".join(f"{key}={quote(value)}" for key, value in values.items()) + "\n"
    atomic_write(path, content)


def file_metadata(path: Path) -> dict[str, str | int | bool]:
    stat = path.stat()
    return {
        "path": str(path),
        "exists": True,
        "owner_uid": stat.st_uid,
        "mode": f"{stat.st_mode & 0o777:04o}",
    }


def write_metadata(
    path: Path,
    *,
    status: str,
    environment_path: Path,
    password_path: Path,
    tenant_id: str,
    rotation_required: bool,
    handoff_required: bool,
    sessions_invalidated: bool,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "status": status,
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "environment_file": file_metadata(environment_path),
        "password_file": file_metadata(password_path),
        "tenant_fingerprint": f"sha256:{hashlib.sha256(tenant_id.encode()).hexdigest()}",
        "temporary_password": rotation_required,
        "rotation_required": rotation_required,
        "secure_handoff_required": handoff_required,
        "sessions_invalidated": sessions_invalidated,
        "plaintext_password_in_environment": False,
        "deployment_evidence": False,
        "acceptance_evidence": False,
    }
    atomic_write(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return payload


def replace_environment_values(path: Path, replacements: dict[str, str]) -> None:
    validate_private_file(path, "environment file")
    lines = path.read_text(encoding="utf-8").splitlines()
    found: set[str] = set()
    updated: list[str] = []
    for line in lines:
        key = line.split("=", 1)[0]
        if key in replacements:
            updated.append(f"{key}={quote(replacements[key])}")
            found.add(key)
        else:
            updated.append(line)
    missing = set(replacements) - found
    if missing:
        raise ValueError(f"environment file does not contain {sorted(missing)}")
    atomic_write(path, "\n".join(updated) + "\n")


def create(args: argparse.Namespace) -> dict[str, object]:
    validate_output_path(args.output, "environment output")
    validate_output_path(args.password_output, "password output")
    validate_output_path(args.metadata_output, "metadata output")

    tenant_id = str(uuid.uuid4())
    operator_password = secrets.token_urlsafe(TEMPORARY_PASSWORD_BYTES)
    values = build_environment(args, tenant_id, operator_password)
    write_environment(args.output, values)
    atomic_write(args.password_output, operator_password + "\n")
    return write_metadata(
        args.metadata_output,
        status="TEMPORARY_CREDENTIAL_PENDING_ROTATION",
        environment_path=args.output,
        password_path=args.password_output,
        tenant_id=tenant_id,
        rotation_required=True,
        handoff_required=True,
        sessions_invalidated=False,
    )


def rotate(args: argparse.Namespace) -> dict[str, object]:
    validate_private_file(args.environment, "environment file")
    validate_private_file(args.current_password_file, "current password file")
    validate_output_path(args.password_output, "rotated password output")

    current_values = dict(
        line.split("=", 1)
        for line in args.environment.read_text(encoding="utf-8").splitlines()
        if "=" in line
    )
    tenant_id = current_values["AXIGNAL_AUTH_TENANT_ID"].strip("'")
    new_password = secrets.token_urlsafe(TEMPORARY_PASSWORD_BYTES)
    atomic_write(args.password_output, new_password + "\n")
    replace_environment_values(
        args.environment,
        {
            "AXIGNAL_AUTH_PASSWORD_SCRYPT": scrypt_record(new_password),
            "AXIGNAL_SESSION_SECRET": random_secret(48),
        },
    )
    args.current_password_file.unlink()
    return write_metadata(
        args.metadata_output,
        status="ROTATED_CREDENTIAL_PENDING_HANDOFF",
        environment_path=args.environment,
        password_path=args.password_output,
        tenant_id=tenant_id,
        rotation_required=False,
        handoff_required=True,
        sessions_invalidated=True,
    )


def retire(args: argparse.Namespace) -> dict[str, object]:
    validate_private_file(args.password_file, "password file")
    validate_private_file(args.metadata_output, "credential metadata file")
    payload = json.loads(args.metadata_output.read_text(encoding="utf-8"))
    args.password_file.unlink()
    payload.update(
        {
            "status": "PLAINTEXT_CREDENTIAL_RETIRED",
            "retired_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "password_file": {
                "path": str(args.password_file),
                "exists": False,
            },
            "rotation_required": False,
            "secure_handoff_required": False,
            "deployment_evidence": False,
            "acceptance_evidence": False,
        }
    )
    atomic_write(args.metadata_output, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return payload


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Manage host-only AXIGNAL pilot credentials without printing secret values"
    )
    commands = result.add_subparsers(dest="command", required=True)

    create_parser = commands.add_parser("create")
    create_parser.add_argument("--output", type=Path, required=True)
    create_parser.add_argument("--password-output", type=Path, required=True)
    create_parser.add_argument("--metadata-output", type=Path, required=True)
    create_parser.add_argument("--sha", required=True)
    create_parser.add_argument("--site-address", required=True)
    create_parser.add_argument("--acme-email", required=True)
    create_parser.add_argument("--auth-email", required=True)
    create_parser.add_argument("--auth-subject", required=True)
    create_parser.add_argument("--edge-mode", choices=EDGE_MODES, default="standalone")
    create_parser.add_argument("--bind-address", default="0.0.0.0")
    create_parser.add_argument("--http-port", type=int, default=80)
    create_parser.add_argument("--https-port", type=int, default=443)
    create_parser.add_argument("--allow-http", action="store_true")
    create_parser.set_defaults(handler=create)

    rotate_parser = commands.add_parser("rotate")
    rotate_parser.add_argument("--environment", type=Path, required=True)
    rotate_parser.add_argument("--current-password-file", type=Path, required=True)
    rotate_parser.add_argument("--password-output", type=Path, required=True)
    rotate_parser.add_argument("--metadata-output", type=Path, required=True)
    rotate_parser.set_defaults(handler=rotate)

    retire_parser = commands.add_parser("retire")
    retire_parser.add_argument("--password-file", type=Path, required=True)
    retire_parser.add_argument("--metadata-output", type=Path, required=True)
    retire_parser.set_defaults(handler=retire)
    return result


def main() -> int:
    old_umask = os.umask(0o077)
    try:
        args = parser().parse_args()
        payload = args.handler(args)
    except (KeyError, OSError, ValueError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True))
        return 1
    finally:
        os.umask(old_umask)
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
