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
from pathlib import Path

SHA_RE = re.compile(r"^[0-9a-f]{40}$")


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


def build_environment(args: argparse.Namespace) -> dict[str, str]:
    sha = args.sha.strip().lower()
    if not SHA_RE.fullmatch(sha):
        raise ValueError("--sha must be a full 40-character lowercase hexadecimal commit")
    site_address = args.site_address.rstrip("/")
    allowed_schemes = ("http://", "https://") if args.allow_http else ("https://",)
    if not site_address.startswith(allowed_schemes):
        raise ValueError("--site-address must use HTTPS")
    tenant_id = str(uuid.UUID(args.tenant_id))
    if tenant_id != args.tenant_id.lower():
        raise ValueError("--tenant-id must use canonical UUID form")

    random_secret = lambda size=32: secrets.token_hex(size)
    return {
        "AXIGNAL_BUILD_SHA": sha,
        "AXIGNAL_PILOT_SITE_ADDRESS": site_address,
        "AXIGNAL_PILOT_ACME_EMAIL": args.acme_email.lower(),
        "AXIGNAL_PILOT_HTTP_PORT": str(args.http_port),
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
        "AXIGNAL_AUTH_EMAIL": args.auth_email.lower(),
        "AXIGNAL_AUTH_SUBJECT": args.auth_subject,
        "AXIGNAL_AUTH_TENANT_ID": tenant_id,
        "AXIGNAL_AUTH_PASSWORD_SCRYPT": scrypt_record(args.operator_password),
        "AXIGNAL_SESSION_SECRET": random_secret(48),
        "AXIGNAL_IDENTITY_ASSERTION_SECRET": random_secret(48),
        "AXIGNAL_VALIDATION_PARTICIPANT_SALT": random_secret(48),
        "AXIGNAL_OTEL_ENABLED": "false",
        "AXIGNAL_LIVE_SOURCES_ENABLED": "false",
        "AXIGNAL_VALIDATION_UI_ENABLED": "false",
        "AXIGNAL_PUBLIC_LAUNCH": "false",
        "AXIGNAL_BILLING_ENABLED": "false",
    }


def write_environment(path: Path, values: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(f"{key}={quote(value)}" for key, value in values.items()) + "\n"
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Create a root-only AXIGNAL pilot environment file")
    result.add_argument("--output", type=Path, required=True)
    result.add_argument("--sha", required=True)
    result.add_argument("--site-address", required=True)
    result.add_argument("--acme-email", required=True)
    result.add_argument("--auth-email", required=True)
    result.add_argument("--auth-subject", required=True)
    result.add_argument("--tenant-id", required=True)
    result.add_argument("--operator-password", required=True)
    result.add_argument("--http-port", type=int, default=80)
    result.add_argument("--https-port", type=int, default=443)
    result.add_argument("--allow-http", action="store_true")
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        values = build_environment(args)
        write_environment(args.output, values)
    except (OSError, ValueError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True))
        return 1
    print(
        json.dumps(
            {
                "status": "PASS",
                "environment_file": str(args.output),
                "mode": oct(args.output.stat().st_mode & 0o777),
                "build_sha": values["AXIGNAL_BUILD_SHA"],
                "site_address": values["AXIGNAL_PILOT_SITE_ADDRESS"],
                "plaintext_operator_password_stored": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
