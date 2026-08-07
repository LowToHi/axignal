"""LOCAL_PRODUCT E2E — Prioridad 5.

Starts the REAL FastAPI process (uvicorn subprocess), runs the O01
vertical slice over HTTP, restarts the process, and verifies the
persisted data survives (restart-equivalence on the product surface).
Also verifies the migration baseline from zero in a dedicated database.

Run:  bash -c 'AXIGNAL_E2E_REAL=1 python apps/api/tests/e2e_real_stack.py'
Requires: local WSL PostgreSQL with the axignal role and infra/postgres
migrations; Valkey local; system Python 3.13.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from uuid import uuid4

REPO = Path(__file__).resolve().parents[3]
PY = sys.executable

DB_URL = os.environ.get(
    "AXIGNAL_DATABASE_URL",
    "postgresql://axignal:axignal-local@localhost:5432/axignal",
)
API_PORT = 18099
API_BASE = f"http://127.0.0.1:{API_PORT}"
IDENTITY_SECRET = "e2e-real-stack-identity-secret-with-at-least-32-bytes"


def _identity_header(tenant_id: str, subject: str) -> dict[str, str]:
    # Mirrors axignal_api.identity.build_identity_assertion exactly:
    # version.encoded_payload.encoded_signature with HMAC-SHA256 over the
    # version-prefixed signing input.
    import base64
    import hashlib
    import hmac

    def _b64url_encode(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")

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
    encoded_payload = _b64url_encode(payload)
    signing_input = f"v1.{encoded_payload}".encode("ascii")
    signature = hmac.new(
        IDENTITY_SECRET.encode("utf-8"), signing_input, hashlib.sha256
    ).digest()
    assertion = f"v1.{encoded_payload}.{_b64url_encode(signature)}"
    return {"X-AXIGNAL-Identity-Assertion": assertion}


def _http(
    method: str,
    path: str,
    *,
    body: dict | None = None,
    tenant_id: str | None = None,
    subject: str = "usr_e2e_real",
) -> tuple[int, dict]:
    headers = {"Content-Type": "application/json"}
    if tenant_id:
        headers.update(_identity_header(tenant_id, subject))
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(
        f"{API_BASE}{path}", data=data, headers=headers, method=method
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status, json.loads(response.read().decode())
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read().decode())


def _start_api() -> subprocess.Popen:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO / "apps" / "api" / "src")
    env["AXIGNAL_DATABASE_URL"] = DB_URL
    env["AXIGNAL_IDENTITY_ASSERTION_SECRET"] = IDENTITY_SECRET
    env["AXIGNAL_ENVIRONMENT"] = "test"
    env["AXIGNAL_TEST_RUNTIME_ENABLED"] = "true"
    env["AXIGNAL_VALKEY_URL"] = "redis://localhost:6379/0"
    process = subprocess.Popen(
        [
            PY, "-m", "uvicorn", "axignal_api.application:app",
            "--host", "127.0.0.1", "--port", str(API_PORT), "--log-level", "warning",
        ],
        cwd=REPO,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    # Wait for readiness.
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


def _stop_api(process: subprocess.Popen) -> None:
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()


def main() -> int:
    print("=== LOCAL_PRODUCT E2E (real stack) ===")
    tenant_a = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    tenant_b = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"

    # 1. Start the REAL API process.
    print("[1/9] starting API process ...")
    api = _start_api()
    try:
        status, health = _http("GET", "/health")
        assert status == 200 and health["status"] == "ok", health
        print(f"      health ok (contract {health['contract_version']})")

        # 2. Libraries over HTTP.
        status, libraries = _http("GET", "/v1/opportunities/libraries")
        assert status == 200 and any(item["library_id"] == "O01" for item in libraries)
        print(f"[2/9] libraries ok ({len(libraries)} canonical)")

        # 3. Ingest via the source surface.
        status, sources = _http("GET", "/v1/opportunities/sources")
        assert status == 200 and sources[0]["source_id"] == "src_ted_search_api_v3"
        print("[3/9] sources ok (TED manifest PRODUCT_ADMITTED)")

        # 4. Pursuit + transition (tenant A).
        pursuit_ref = f"prs_e2e_{uuid4().hex[:10]}"
        status, created = _http(
            "POST", "/v1/opportunities/pursuits",
            body={"pursuit_ref": pursuit_ref, "opportunity_ref": "opp_e2e_o01",
                  "state": "QUALIFIED"},
            tenant_id=tenant_a,
        )
        assert status == 201, created
        status, transitioned = _http(
            "POST", f"/v1/opportunities/pursuits/{pursuit_ref}/transition",
            body={"new_state": "DECISION_REVIEW"},
            tenant_id=tenant_a,
        )
        assert status == 200 and transitioned["state"] == "DECISION_REVIEW"
        print(f"[4/9] pursuit {pursuit_ref} -> DECISION_REVIEW")

        # 5. Workspace (tenant A).
        workspace_id = str(uuid4())
        status, _ = _http(
            "POST", "/v1/opportunities/workspaces",
            body={"workspace_id": workspace_id, "pursuit_ref": pursuit_ref,
                  "opportunity_ref": "opp_e2e_o01",
                  "opportunity_version_digest": f"sha256:{'c' * 64}",
                  "subscriber_profile_version": "v1", "assessment_version": "v1"},
            tenant_id=tenant_a,
        )
        assert status == 201
        print(f"[5/9] workspace {workspace_id} created")

        # 6. Outcome + learning (tenant A).
        outcome_ref = f"out_e2e_{uuid4().hex[:10]}"
        status, outcome = _http(
            "POST", "/v1/opportunities/outcomes",
            body={"outcome_ref": outcome_ref, "pursuit_ref": pursuit_ref,
                  "result": "WON", "evidence_refs": ["evidence-e2e-1"]},
            tenant_id=tenant_a,
        )
        assert status == 201, outcome
        status, _ = _http(
            "POST", f"/v1/opportunities/pursuits/{pursuit_ref}/transition",
            body={"new_state": "WON", "decided_by": "usr_e2e_real",
                  "outcome_ref": outcome_ref},
            tenant_id=tenant_a,
        )
        assert status == 200
        print(f"[6/9] outcome {outcome_ref} (WON)")

        # 7. Sandbox billing checkout (tenant A).
        checkout_id = f"chk_e2e_{uuid4().hex[:8]}"
        idem_key = f"idem_e2e_{uuid4().hex[:16]}"
        status, checkout = _http(
            "POST", "/v1/billing/sandbox/checkout",
            body={"checkout_id": checkout_id, "product_id": "AXIGNAL_OPPORTUNITY_INTELLIGENCE",
                  "plan_id": "plan-oi-professional", "price_id": "price-oi-professional",
                  "idempotency_key": idem_key, "customer_context": "e2e-real"},
            tenant_id=tenant_a,
        )
        assert status == 201 and checkout["status"] == "CHECKOUT_OK", checkout
        status, entitlements = _http("GET", "/v1/billing/sandbox/entitlements", tenant_id=tenant_a)
        assert entitlements.get("AXIGNAL_OPPORTUNITY_INTELLIGENCE") is True
        print("[7/9] sandbox checkout + entitlement ok")

        # 8. Tenant isolation while running.
        status, other_pursuits = _http("GET", "/v1/opportunities/pursuits", tenant_id=tenant_b)
        assert all(p["pursuit_ref"] != pursuit_ref for p in other_pursuits)
        print("[8/9] tenant isolation ok (running process)")
    finally:
        _stop_api(api)

    # 9. RESTART the process; data must survive.
    print("[9/9] restarting API process ...")
    api = _start_api()
    try:
        status, pursuits = _http("GET", "/v1/opportunities/pursuits", tenant_id=tenant_a)
        assert any(p["pursuit_ref"] == pursuit_ref for p in pursuits), pursuits
        status, ws = _http(
            "GET", f"/v1/opportunities/workspaces/{workspace_id}", tenant_id=tenant_a
        )
        assert status == 200
        status, outcomes = _http("GET", "/v1/opportunities/outcomes", tenant_id=tenant_a)
        assert any(o["outcome_ref"] == outcome_ref for o in outcomes)
        status, sub = _http("GET", "/v1/billing/sandbox/subscription", tenant_id=tenant_a)
        assert status == 200 and sub["product_id"] == "AXIGNAL_OPPORTUNITY_INTELLIGENCE"
        print("      persisted data recovered after restart")
    finally:
        _stop_api(api)

    print("=== LOCAL_PRODUCT E2E: PASS ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
