#!/usr/bin/env python3
"""AXIGNAL portable local stack launcher (Prioridad 8 — AX_FRESH_INSTALL).

One command to bring up the whole local stack:

    PostgreSQL (WSL or local)  + Valkey + migrations + technical seed
    -> API (uvicorn subprocess) -> research worker (optional) -> web (optional)

Usage:
    python scripts/axignal_stack.py up            # DB check + migrations + API
    python scripts/axignal_stack.py up --worker   # + research worker
    python scripts/axignal_stack.py up --web      # + Next.js dev server
    python scripts/axignal_stack.py down          # stop API/worker/web

Portable: interpreter from sys.executable, ports overridable via
AXIGNAL_API_PORT / AXIGNAL_WEB_PORT, DB DSN via AXIGNAL_DATABASE_URL,
Valkey via AXIGNAL_VALKEY_URL. No hardcoded machine paths.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PY = sys.executable

API_PORT = int(os.environ.get("AXIGNAL_API_PORT", "8000"))
WEB_PORT = int(os.environ.get("AXIGNAL_WEB_PORT", "3000"))
DB_URL = os.environ.get(
    "AXIGNAL_DATABASE_URL",
    "postgresql://axignal:axignal-local@localhost:5432/axignal",
)
VALKEY_URL = os.environ.get("AXIGNAL_VALKEY_URL", "redis://localhost:6379/0")


def _env() -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO / "apps" / "api" / "src")
    env["AXIGNAL_DATABASE_URL"] = DB_URL
    env["AXIGNAL_VALKEY_URL"] = VALKEY_URL
    env.setdefault(
        "AXIGNAL_IDENTITY_ASSERTION_SECRET",
        "local-dev-identity-assertion-secret-32-bytes",
    )
    env.setdefault("AXIGNAL_ENVIRONMENT", "test")
    env.setdefault("AXIGNAL_TEST_RUNTIME_ENABLED", "true")
    env.setdefault("AXIGNAL_PERSISTENT_RESEARCH_ENABLED", "true")
    env.setdefault("AXIGNAL_TED_PROCUREMENT_ENABLED", "true")
    env.setdefault("AXIGNAL_TED_LIVE_SOURCES_ENABLED", "false")
    fixture_path = REPO / "apps/api/tests/fixtures/ted_search_probe.json"
    env.setdefault("AXIGNAL_TED_FIXTURE_PATH", str(fixture_path))
    return env


def _http_ready(url: str, attempts: int = 40) -> bool:
    for _ in range(attempts):
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def _wsl_db_ready() -> bool:
    probe = subprocess.run(
        ["wsl", "-d", "Ubuntu", "-e", "bash", "-c",
         "pg_isready -h localhost -p 5432 > /dev/null 2>&1 && echo OK"],
        capture_output=True, text=True, timeout=30,
    )
    return "OK" in probe.stdout


def _run_migrations() -> bool:
    """Apply infra/postgres/*.sql in order (idempotent)."""
    files = sorted((REPO / "infra" / "postgres").glob("[0-9]*.sql"))
    for path in files:
        result = subprocess.run(
            ["wsl", "-d", "Ubuntu", "-e", "bash", "-c",
             f"sudo -u postgres psql -d axignal -v ON_ERROR_STOP=1 "
             f"-f /mnt/d/AXIGNAL/AXIGNAL_E2E/infra/postgres/{path.name} > /dev/null 2>&1"],
            cwd=REPO, timeout=120,
        )
        if result.returncode != 0:
            # Fallback: try through the app DSN when the WSL mount is absent.
            fallback = subprocess.run(
                [PY, "-c",
                 "import psycopg, sys; "
                 f"conn = psycopg.connect({DB_URL!r}); "
                 f"conn.execute(open({str(path)!r}).read()); conn.commit(); print('OK')"],
                env=_env(), capture_output=True, text=True, timeout=120,
            )
            if "OK" not in fallback.stdout:
                print(f"[migrate] FAILED {path.name}")
                return False
    print(f"[migrate] applied {len(files)} migrations")
    return True


def cmd_up(args: argparse.Namespace) -> int:
    if not _wsl_db_ready():
        print("[db] WSL PostgreSQL not ready; start it with: "
              "wsl -d Ubuntu -e bash -c 'sudo service postgresql start'")
        return 1
    if not _run_migrations():
        return 1

    env = _env()
    processes: list[subprocess.Popen] = []

    api = subprocess.Popen(
        [PY, "-m", "uvicorn", "axignal_api.application:app",
         "--host", "127.0.0.1", "--port", str(API_PORT), "--log-level", "warning"],
        cwd=REPO, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    processes.append(api)
    if not _http_ready(f"http://127.0.0.1:{API_PORT}/health"):
        print("[api] FAILED to become ready")
        return 1
    print(f"[api] ready on 127.0.0.1:{API_PORT}")

    if args.worker:
        worker = subprocess.Popen(
            [PY, "-m", "axignal_api.worker", "--poll-seconds", "2.0"],
            cwd=REPO, env=env,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        )
        processes.append(worker)
        print("[worker] started")

    if args.web:
        web = subprocess.Popen(
            ["pnpm", "--dir", str(REPO / "apps" / "web"), "dev"],
            cwd=REPO, env=env,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        )
        processes.append(web)
        if not _http_ready(f"http://127.0.0.1:{WEB_PORT}"):
            print("[web] dev server did not become ready quickly (may still be compiling)")
        else:
            print(f"[web] ready on 127.0.0.1:{WEB_PORT}")

    print("[stack] UP — keep this process running; Ctrl+C stops all.")
    try:
        while True:
            time.sleep(2)
            for process in processes:
                if process.poll() is not None:
                    print(f"[stack] a component exited with {process.returncode}")
                    return process.returncode or 1
    except KeyboardInterrupt:
        for process in processes:
            process.terminate()
        print("\n[stack] DOWN")
    return 0


def cmd_down(_args: argparse.Namespace) -> int:
    import psutil  # type: ignore[import-not-found]

    killed = 0
    for process in psutil.process_iter(["pid", "name", "cmdline"]):
        cmdline = " ".join(process.info["cmdline"] or [])
        if "axignal_api.application:app" in cmdline or "axignal_api.worker" in cmdline:
            try:
                process.terminate()
                killed += 1
            except psutil.Error:
                pass
    print(f"[stack] stopped {killed} AXIGNAL processes")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="AXIGNAL portable stack")
    sub = parser.add_subparsers(dest="command", required=True)
    up = sub.add_parser("up", help="start the local stack")
    up.add_argument("--worker", action="store_true", help="also start the research worker")
    up.add_argument("--web", action="store_true", help="also start the Next.js dev server")
    sub.add_parser("down", help="stop local AXIGNAL processes")
    args = parser.parse_args()
    if args.command == "up":
        return cmd_up(args)
    return cmd_down(args)


if __name__ == "__main__":
    sys.exit(main())
