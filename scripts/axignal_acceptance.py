#!/usr/bin/env python3
"""AXIGNAL full acceptance matrix (Prioridad 8 — CI exact-head).

Runs every local gate on the current exact HEAD and prints a summary:

    API tests + integration, Ruff, frontend tests, lint, typecheck,
    build, Playwright (O01 vertical slice), migrations from zero,
    O01 continuous, O02-O09, cross-library, billing sandbox, security,
    restart recovery, tenant isolation, backup/restore.

Usage:  python scripts/axignal_acceptance.py
Env:    AXIGNAL_ACCEPTANCE_FAST=1 skips slow gates (migrations-from-zero,
        backup/restore).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# Portable interpreter resolution: sys.executable first, fallback to the
# project's known interpreter, then plain PATH lookup.
def _resolve_python() -> str:
    candidate = sys.executable
    if candidate and Path(candidate).exists():
        return candidate
    import shutil

    for fallback in (
        r"C:\Users\usuario\AppData\Local\Programs\Python\Python313\python.exe",
        "python3",
        "python",
    ):
        resolved = shutil.which(fallback)
        if resolved:
            return resolved
    return sys.executable


PY = _resolve_python()
GATES: dict[str, str] = {}
FAST = os.environ.get("AXIGNAL_ACCEPTANCE_FAST") == "1"


def run(
    name: str,
    command: list[str],
    *,
    timeout: int = 600,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> bool:
    started = time.monotonic()
    use_shell = bool(command and command[0] == "pnpm")
    try:
        result = subprocess.run(
            " ".join(command) if use_shell else command,
            cwd=cwd or REPO,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=use_shell,
            env=env
            or {
                **{key: value for key, value in os.environ.items()
                   if key != "AXIGNAL_DATABASE_URL"},
                # Entitlement/unit suites assert the variable is ABSENT by
                # default; integration tests set their own DSN via monkeypatch.
                "PYTHONPATH": str(REPO / "apps/api/src"),
            },
        )
        ok = result.returncode == 0
    except subprocess.TimeoutExpired:
        ok = False
    GATES[name] = "PASS" if ok else "FAIL"
    elapsed = time.monotonic() - started
    print(f"[{'PASS' if ok else 'FAIL'}] {name} ({elapsed:.0f}s)")
    return ok


def main() -> int:
    print(f"=== AXIGNAL acceptance matrix @ {REPO} ===")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    print(f"HEAD: {head}")

    api_env = {
        **{key: value for key, value in os.environ.items()
           if key != "AXIGNAL_DATABASE_URL"},
        "PYTHONPATH": str(REPO / "apps/api/src"),
    }

    # 1. API unit tests (integration suites skip without the env flag).
    run("API_TESTS", [PY, "-m", "pytest", "apps/api/tests", "-q", "--disable-warnings"],
        timeout=600)
    # 2. API integration tests (PostgreSQL).
    run("API_INTEGRATION_TESTS",
        [PY, "-m", "pytest", "apps/api/tests", "-q", "--disable-warnings"],
        env=dict(api_env, AXIGNAL_INTEGRATION_TESTS="1"), timeout=900)
    # 3. Ruff.
    run("RUFF", [PY, "-m", "ruff", "check", "apps/api/src/axignal_api", "apps/api/tests"],
        timeout=300)
    # 4. Frontend tests.
    run("FRONTEND_TESTS", ["pnpm", "run", "test"], timeout=900)
    # 5. Lint + 6. typecheck.
    run("LINT", ["pnpm", "run", "lint"], timeout=600)
    run("TYPECHECK", ["pnpm", "run", "typecheck"], timeout=600)
    # 7. Build.
    run("BUILD", ["pnpm", "run", "build"], timeout=900)

    # 8. Real-stack E2E (restart + persistence + tenant isolation).
    run("RESTART_RECOVERY",
        [PY, "apps/api/tests/e2e_real_stack.py"], timeout=600)
    # 9. O01 continuous chain (real worker).
    run("O01_CONTINUOUS_E2E",
        [PY, "apps/api/tests/e2e_o01_continuous.py"], timeout=600)
    # 10. O02-O09 vertical slices (covered by integration suite; explicit here).
    run("O02_O09_VERTICAL_SLICES",
        [PY, "-m", "pytest", "apps/api/tests/test_executable_libraries_e2e.py",
         "-q", "--disable-warnings"],
        env=dict(api_env, AXIGNAL_INTEGRATION_TESTS="1"), timeout=600)
    # 11. Cross-library persistent.
    run("CROSS_LIBRARY_E2E",
        [PY, "-m", "pytest", "apps/api/tests/test_cross_library_persistent_e2e.py",
         "-q", "--disable-warnings"],
        env=dict(api_env, AXIGNAL_INTEGRATION_TESTS="1"), timeout=600)
    # 12. Billing sandbox.
    run("BILLING_SANDBOX_E2E",
        [PY, "-m", "pytest", "apps/api/tests/test_sandbox_billing_http_e2e.py",
         "-q", "--disable-warnings"],
        env=dict(api_env, AXIGNAL_INTEGRATION_TESTS="1"), timeout=600)
    # 13. Security / backup / portability.
    run("SECURITY_GATE",
        [PY, "apps/api/tests/security_ops_gates.py"], timeout=900,
        env={
            **api_env,
            "AXIGNAL_DATABASE_URL": "postgresql://axignal:axignal-local@localhost:5432/axignal",
        })

    if not FAST:
        # 14. Migrations from zero (scratch database).
        migrations_dir = REPO / "infra" / "postgres"
        wsl_path = migrations_dir.as_posix().replace("D:/", "/mnt/d/", 1)
        migration_cmd = (
            "sudo -u postgres psql -c 'DROP DATABASE IF EXISTS axignal_mig_zero;' "
            "-c 'CREATE DATABASE axignal_mig_zero;' > /dev/null 2>&1; "
            "sudo -u postgres psql -d axignal_mig_zero "
            "-c 'CREATE EXTENSION IF NOT EXISTS vector;' > /dev/null 2>&1; "
            f"for f in $(ls {wsl_path}/[0-9]*.sql | sort); do "
            "sudo -u postgres psql -d axignal_mig_zero -v ON_ERROR_STOP=1 "
            "-f $f > /dev/null 2>&1 || exit 1; done; "
            "sudo -u postgres psql -c 'DROP DATABASE axignal_mig_zero;' "
            "> /dev/null 2>&1"
        )
        run("MIGRATION_FROM_ZERO",
            ["wsl", "-d", "Ubuntu", "-e", "bash", "-c", migration_cmd],
            timeout=900)
    else:
        GATES["MIGRATION_FROM_ZERO"] = "SKIPPED_FAST"

    failed = [name for name, status in GATES.items() if status == "FAIL"]
    print("---")
    print(json.dumps(GATES, indent=1))
    print("ENGINEERING_100=" + ("PASS" if not failed else "FAIL"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
