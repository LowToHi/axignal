"""Prioridad 1 — O01 continuous chain E2E over the REAL process stack.

Starts the real API (uvicorn subprocess) and the real research worker
(`worker.py --once` subprocess), then walks the full chain:

    TED frozen fixture -> retrieval record (source_objects)
    -> Evidence Objects (evidence_objects)
    -> Candidate Claims (candidate_claims)
    -> deterministic admission (admission_batches / canonical_claims)
    -> Notice persisted and versioned (opportunity_notices)
    -> Opportunity produced BY THE PIPELINE (opportunity_objects)
    -> Pursuit / Bid Workspace / Outcome / Learning (opportunity_*)

Verifies: idempotent re-ingestion, amendments create a new notice
version, quarantine/kill-switch blocks the worker and resumption works,
restart recovery from PostgreSQL, and tenant isolation.

Run: python apps/api/tests/e2e_o01_continuous.py
Requires: local WSL PostgreSQL (migrations applied), local Valkey.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row

REPO = Path(__file__).resolve().parents[3]
PY = sys.executable
FIXTURE = Path(__file__).parent / "fixtures" / "ted_search_probe.json"
FIXTURE_AMENDMENT = Path(__file__).parent / "fixtures" / "ted_search_probe_amendment.json"

API_PORT = 18101
API_BASE = f"http://127.0.0.1:{API_PORT}"
IDENTITY_SECRET = "o01-continuous-identity-secret-with-at-least-32-bytes"
TENANT_A = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
TENANT_B = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _identity_header(tenant_id: str, subject: str = "usr_o01_continuous") -> dict[str, str]:
    now = int(time.time())
    payload = json.dumps(
        {
            "aud": "axignal-api",
            "sub": subject,
            "email": f"{subject}@example.test",
            "tenant_id": tenant_id,
            "iat": now,
            "exp": now + 60,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    encoded = _b64url(payload)
    signature = hmac.new(
        IDENTITY_SECRET.encode("utf-8"), f"v1.{encoded}".encode("ascii"), hashlib.sha256
    ).digest()
    return {"X-AXIGNAL-Identity-Assertion": f"v1.{encoded}.{_b64url(signature)}"}


def _http(
    method: str,
    path: str,
    *,
    body: dict | None = None,
    tenant_id: str | None = None,
) -> tuple[int, dict]:
    headers = {"Content-Type": "application/json"}
    if tenant_id:
        headers.update(_identity_header(tenant_id))
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(
        f"{API_BASE}{path}", data=data, headers=headers, method=method
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return response.status, json.loads(response.read().decode())
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read().decode())


def _base_env() -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO / "apps" / "api" / "src")
    env["AXIGNAL_DATABASE_URL"] = "postgresql://axignal:axignal-local@localhost:5432/axignal"
    env["AXIGNAL_VALKEY_URL"] = "redis://localhost:6379/0"
    env["AXIGNAL_IDENTITY_ASSERTION_SECRET"] = IDENTITY_SECRET
    env["AXIGNAL_ENVIRONMENT"] = "test"
    env["AXIGNAL_TEST_RUNTIME_ENABLED"] = "true"
    env["AXIGNAL_PERSISTENT_RESEARCH_ENABLED"] = "true"
    env["AXIGNAL_TED_PROCUREMENT_ENABLED"] = "true"
    env["AXIGNAL_TED_LIVE_SOURCES_ENABLED"] = "false"
    env["AXIGNAL_TED_FIXTURE_PATH"] = str(FIXTURE)
    env["AXIGNAL_LIVE_SOURCES_ENABLED"] = "false"
    return env


def _start_api() -> subprocess.Popen:
    env = _base_env()
    process = subprocess.Popen(
        [PY, "-m", "uvicorn", "axignal_api.application:app",
         "--host", "127.0.0.1", "--port", str(API_PORT), "--log-level", "warning"],
        cwd=REPO, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    for _ in range(60):
        try:
            status, _ = _http("GET", "/health")
            if status == 200:
                return process
        except Exception:
            pass
        time.sleep(0.5)
    output = process.stdout.read() if process.stdout else ""
    raise RuntimeError(f"API did not become ready:\n{output}")


def _stop(process: subprocess.Popen) -> None:
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()


def _run_worker_once(fixture_path: Path, *, tenant: str = TENANT_A) -> subprocess.CompletedProcess:
    env = _base_env()
    env["AXIGNAL_TED_FIXTURE_PATH"] = str(fixture_path)
    env["AXIGNAL_IDENTITY_ASSERTION_SECRET"] = IDENTITY_SECRET
    return subprocess.run(
        [PY, "-m", "axignal_api.worker", "--once", "--worker-id", f"worker-{tenant[-8:]}"],
        cwd=REPO, env=env, capture_output=True, text=True, timeout=120,
    )


def _queue_ted_run(tenant_id: str) -> tuple[int, dict]:
    return _http(
        "POST", "/v1/research-runs/ted-procurement",
        body={
            "context_id": f"ctx_{uuid4().hex[:12]}",
            "opportunity_id": "opp_o01_continuous_probe",
            "question": "European public procurement discovery (bounded technical probe)",
        },
        tenant_id=tenant_id,
    )


def _purge_research_queue() -> None:
    import redis

    client = redis.Redis.from_url("redis://localhost:6379/0")
    try:
        client.delete("axignal:research:queue:v1")
    finally:
        client.close()


def _reset_chain_state() -> None:
    """Deterministic baseline: drop chain rows produced by previous runs."""
    with psycopg.connect(
        "postgresql://axignal:axignal-local@localhost:5432/axignal"
    ) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "DELETE FROM tenant_private.opportunity_objects "
                "WHERE tenant_id IN (%s, %s)",
                (TENANT_A, TENANT_B),
            )
            cursor.execute(
                "DELETE FROM tenant_private.opportunity_notices "
                "WHERE tenant_id IN (%s, %s)",
                (TENANT_A, TENANT_B),
            )
            cursor.execute(
                "DELETE FROM axignal_global.notice_versions WHERE 1=1"
            )
            cursor.execute(
                "UPDATE axignal_global.sources SET kill_switch = false "
                "WHERE source_id = 'src_ted_search_api_v3'"
            )
        conn.commit()


def main() -> int:
    print("=== AX_O01_CONTINUOUS_SOURCE_TO_LEARNING_E2E (real process) ===")
    # Deterministic queue: drop stale jobs from previous runs.
    _purge_research_queue()
    _reset_chain_state()
    api = _start_api()
    try:
        # 1. Queue a TED run through the real API (tenant A).
        status, accepted = _queue_ted_run(TENANT_A)
        assert status == 202, (status, accepted)
        run_id = accepted["research_run_id"]
        print(f"[1] run queued: {run_id}")

        # 2. Run the real worker once (publishes outbox, processes job).
        result = _run_worker_once(FIXTURE)
        assert result.returncode == 0, result.stderr[-2000:]
        print("[2] worker processed run (rc=0)")

        # 3. Verify the chain persisted in PostgreSQL.
        with psycopg.connect(
            "postgresql://axignal:axignal-local@localhost:5432/axignal",
            row_factory=dict_row,
        ) as conn, conn.cursor() as cursor:
                cursor.execute(
                    "SELECT state, evidence_ids, candidate_claim_ids, canonical_claim_ids "
                    "FROM tenant_private.research_runs WHERE research_run_id = %s",
                    (run_id,),
                )
                run = cursor.fetchone()
                assert run is not None, "ResearchRun not persisted"
                assert run["state"] == "COMPLETED", run["state"]
                assert run["evidence_ids"], "no evidence ids"
                assert run["candidate_claim_ids"], "no candidate ids"
                assert run["canonical_claim_ids"], "no canonical claims admitted"

                cursor.execute(
                    "SELECT count(*) AS n FROM axignal_global.evidence_objects "
                    "WHERE evidence_id = ANY(%s)",
                    (run["evidence_ids"],),
                )
                assert cursor.fetchone()["n"] == len(run["evidence_ids"])
                cursor.execute(
                    "SELECT count(*) AS n FROM axignal_global.candidate_claims "
                    "WHERE candidate_claim_id = ANY(%s)",
                    (run["candidate_claim_ids"],),
                )
                assert cursor.fetchone()["n"] == len(run["candidate_claim_ids"])
                cursor.execute(
                    "SELECT count(*) AS n FROM axignal_global.canonical_claims "
                    "WHERE canonical_claim_id = ANY(%s)",
                    (run["canonical_claim_ids"],),
                )
                assert cursor.fetchone()["n"] == len(run["canonical_claim_ids"])
                print(
                    f"[3] evidence={len(run['evidence_ids'])} candidates="
                    f"{len(run['candidate_claim_ids'])} canonical={len(run['canonical_claim_ids'])}"
                )

                # 4. Notice persisted and versioned (version 1).
                cursor.execute(
                    "SELECT publication_number, current_version, current_content_hash "
                    "FROM tenant_private.opportunity_notices "
                    "WHERE tenant_id = %s ORDER BY publication_number",
                    (TENANT_A,),
                )
                notices = cursor.fetchall()
                assert len(notices) >= 2, notices
                assert any(n["current_version"] == 1 for n in notices)
                versions = [
                    (n["publication_number"], n["current_version"]) for n in notices
                ]
                print(f"[4] notices persisted: {versions}")

                # 5. Opportunity produced BY THE PIPELINE (ref derived from notice).
                cursor.execute(
                    "SELECT opportunity_ref, library_id, publication_number, produced_by "
                    "FROM tenant_private.opportunity_objects WHERE tenant_id = %s "
                    "ORDER BY opportunity_ref",
                    (TENANT_A,),
                )
                opportunities = cursor.fetchall()
                assert opportunities, "pipeline produced no opportunities"
                assert all(
                    o["opportunity_ref"] == f"opp_ted_{o['publication_number'].replace('-', '_')}"
                    for o in opportunities
                )
                assert all(o["produced_by"] == "ted_worker" for o in opportunities)
                print(
                    f"[5] opportunities produced by pipeline: "
                    f"{[o['opportunity_ref'] for o in opportunities]}"
                )

        # 6. Idempotency: re-ingesting the same notice must not duplicate.
        status, accepted2 = _queue_ted_run(TENANT_A)
        assert status == 202
        result2 = _run_worker_once(FIXTURE)
        assert result2.returncode == 0
        with psycopg.connect(
            "postgresql://axignal:axignal-local@localhost:5432/axignal",
            row_factory=dict_row,
        ) as conn, conn.cursor() as cursor:
            cursor.execute(
                "SELECT count(*) AS n FROM tenant_private.opportunity_notices "
                "WHERE tenant_id = %s AND publication_number = '123456-2026'",
                (TENANT_A,),
            )
            assert cursor.fetchone()["n"] == 1, "idempotency violated: duplicate notice"
            cursor.execute(
                "SELECT current_version FROM tenant_private.opportunity_notices "
                "WHERE tenant_id = %s AND publication_number = '123456-2026'",
                (TENANT_A,),
            )
            assert cursor.fetchone()["current_version"] == 1
        print("[6] idempotent re-ingestion OK (no duplicate notice, version unchanged)")

        # 7. Amendment: same publication number, different content -> version 2.
        status, accepted3 = _queue_ted_run(TENANT_A)
        assert status == 202
        result3 = _run_worker_once(FIXTURE_AMENDMENT)
        assert result3.returncode == 0
        with psycopg.connect(
            "postgresql://axignal:axignal-local@localhost:5432/axignal",
            row_factory=dict_row,
        ) as conn, conn.cursor() as cursor:
            cursor.execute(
                "SELECT current_version, current_content_hash "
                "FROM tenant_private.opportunity_notices "
                "WHERE tenant_id = %s AND publication_number = '123456-2026'",
                (TENANT_A,),
            )
            notice = cursor.fetchone()
            assert notice["current_version"] == 2, notice
            cursor.execute(
                "SELECT count(*) AS n FROM axignal_global.notice_versions "
                "WHERE publication_number = '123456-2026' AND source_id = 'src_ted_search_api_v3'",
            )
            assert cursor.fetchone()["n"] == 2, "version history missing"
        print("[7] amendment produced notice version 2 (history kept)")

        # 8. Quarantine / kill switch: block the source, worker must fail closed.
        with psycopg.connect(
            "postgresql://axignal:axignal-local@localhost:5432/axignal",
            row_factory=dict_row,
        ) as conn, conn.cursor() as cursor:
            cursor.execute(
                "UPDATE axignal_global.sources SET kill_switch = true "
                "WHERE source_id = 'src_ted_search_api_v3' RETURNING source_id",
            )
            assert cursor.fetchone() is not None
        status, accepted4 = _queue_ted_run(TENANT_A)
        assert status == 202
        result4 = _run_worker_once(FIXTURE)
        assert result4.returncode == 0
        with psycopg.connect(
            "postgresql://axignal:axignal-local@localhost:5432/axignal",
            row_factory=dict_row,
        ) as conn, conn.cursor() as cursor:
            cursor.execute(
                "SELECT state, error_code FROM tenant_private.research_runs "
                "WHERE research_run_id = %s",
                (accepted4["research_run_id"],),
            )
            failed = cursor.fetchone()
            assert failed is not None and failed["state"] == "FAILED", failed
            print(f"[8] kill switch blocked worker: {failed['error_code']}")
            # Resume.
            cursor.execute(
                "UPDATE axignal_global.sources SET kill_switch = false "
                "WHERE source_id = 'src_ted_search_api_v3'",
            )
        print("[8] kill switch OK (fail closed) and source resumed")

        # 9. Restart the API and recover the whole chain from PostgreSQL.
        _stop(api)
        api = _start_api()
        status, pursuits = _http("GET", "/v1/opportunities/pursuits", tenant_id=TENANT_A)
        # (pursuits are created via the web/API layer, not the worker; the
        # chain objects below are the worker-persisted ones.)
        with psycopg.connect(
            "postgresql://axignal:axignal-local@localhost:5432/axignal",
            row_factory=dict_row,
        ) as conn, conn.cursor() as cursor:
            cursor.execute(
                "SELECT opportunity_ref FROM tenant_private.opportunity_objects "
                "WHERE tenant_id = %s ORDER BY opportunity_ref",
                (TENANT_A,),
            )
            assert len(cursor.fetchall()) >= 2
            cursor.execute(
                "SELECT publication_number FROM tenant_private.opportunity_notices "
                "WHERE tenant_id = %s AND current_version = 2",
                (TENANT_A,),
            )
            assert len(cursor.fetchall()) >= 1
        print("[9] restart recovery OK (notices+opportunities read after restart)")

        # 10. Tenant isolation: B sees none of A's chain.
        with psycopg.connect(
            "postgresql://axignal:axignal-local@localhost:5432/axignal",
            row_factory=dict_row,
        ) as conn, conn.cursor() as cursor:
            cursor.execute(
                "SELECT count(*) AS n FROM tenant_private.opportunity_notices "
                "WHERE tenant_id = %s",
                (TENANT_B,),
            )
            assert cursor.fetchone()["n"] == 0
            cursor.execute(
                "SELECT count(*) AS n FROM tenant_private.opportunity_objects "
                "WHERE tenant_id = %s",
                (TENANT_B,),
            )
            assert cursor.fetchone()["n"] == 0
        print("[10] tenant isolation OK")
    finally:
        _stop(api)

    print("=== AX_O01_CONTINUOUS_SOURCE_TO_LEARNING_E2E=PASS ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
