from __future__ import annotations

import json
import os
from pathlib import Path
from uuid import UUID

from fastapi.testclient import TestClient

from axignal_api.application import app
from axignal_api.identity import build_identity_assertion
from axignal_api.settings import Settings
from axignal_api.worker import build_runtime

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "ted-product-runtime-evidence.json"
TENANT_ID = UUID("11111111-1111-4111-8111-111111111111")
OTHER_TENANT_ID = UUID("22222222-2222-4222-8222-222222222222")
IDENTITY_SECRET = "ci-identity-assertion-secret-with-at-least-32-bytes"


def headers(*, tenant_id: UUID, subject: str) -> dict[str, str]:
    return {
        "X-AXIGNAL-Identity-Assertion": build_identity_assertion(
            secret=IDENTITY_SECRET,
            subject=subject,
            email=f"{subject}@example.test",
            tenant_id=tenant_id,
        )
    }


def require_environment() -> None:
    required = (
        "AXIGNAL_DATABASE_URL",
        "AXIGNAL_VALKEY_URL",
        "AXIGNAL_TED_FIXTURE_PATH",
    )
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise SystemExit(f"Missing E2E environment: {', '.join(missing)}")
    os.environ["AXIGNAL_PERSISTENT_RESEARCH_ENABLED"] = "true"
    os.environ["AXIGNAL_TED_PROCUREMENT_ENABLED"] = "true"
    os.environ["AXIGNAL_LIVE_SOURCES_ENABLED"] = "false"
    os.environ["AXIGNAL_IDENTITY_ASSERTION_SECRET"] = IDENTITY_SECRET


def main() -> None:
    require_environment()
    client = TestClient(app)
    publisher, worker = build_runtime(Settings.from_env())
    worker.queue.purge_for_test()

    create_response = client.post(
        "/v1/research-runs/ted-procurement",
        headers=headers(tenant_id=TENANT_ID, subject="usr_ted_e2e"),
        json={
            "context_id": "ctx_eu_procurement_v01",
            "opportunity_id": "opp_eu_procurement_e2e",
            "question": "Investiga las oportunidades públicas europeas activas.",
            "include_private_knowledge": False,
        },
    )
    assert create_response.status_code == 202, create_response.text
    accepted = create_response.json()
    assert accepted["state"] == "QUEUED"
    assert accepted["job_kind"] == "TED_PROCUREMENT"
    assert accepted["source_ids"] == ["src_ted_search_api_v3"]
    run_id = accepted["research_run_id"]

    publisher.publish_pending(limit=100)
    assert worker.run_once(timeout_seconds=2) is True
    publisher.publish_pending(limit=100)

    get_response = client.get(
        f"/v1/research-runs/{run_id}",
        headers=headers(tenant_id=TENANT_ID, subject="usr_ted_e2e"),
    )
    assert get_response.status_code == 200, get_response.text
    view = get_response.json()
    assert view["state"] == "COMPLETED"
    assert view["synthetic"] is False
    assert view["private_knowledge_authorised"] is False
    assert view["actual_usage"]["model_calls"] == 0
    assert view["actual_usage"]["notices"] == 2
    assert len(view["evidence"]) == 7
    assert len(view["candidate_claims"]) == 7
    assert len(view["canonical_claims"]) == 7
    assert all(item["state"] == "ADMITTED" for item in view["candidate_claims"])
    assert all(item["admitted_by"] == "DETERMINISTIC_RUNTIME" for item in view["canonical_claims"])
    assert view["dossier"]["status"] == "TRACEABLE_WITH_ADMITTED_FACTS"
    attribution = view["dossier"]["attribution"]
    assert attribution["source_id"] == "src_ted_search_api_v3"
    assert attribution["api_redistribution"] is False
    assert "Tenders Electronic Daily" in attribution["attribution_text"]

    cross_tenant = client.get(
        f"/v1/research-runs/{run_id}",
        headers=headers(tenant_id=OTHER_TENANT_ID, subject="usr_other_tenant"),
    )
    assert cross_tenant.status_code == 404

    evidence = {
        "status": "PASS",
        "task": "AX-F8-T14",
        "research_run_id": run_id,
        "state": view["state"],
        "source_id": "src_ted_search_api_v3",
        "tenant_resolution": "SIGNED_IDENTITY_ASSERTION_SERVER_SIDE",
        "cross_tenant_read": "BLOCKED_BY_RLS",
        "notice_count": view["actual_usage"]["notices"],
        "evidence_count": len(view["evidence"]),
        "candidate_claim_count": len(view["candidate_claims"]),
        "canonical_claim_count": len(view["canonical_claims"]),
        "dossier_status": view["dossier"]["status"],
        "model_calls": view["actual_usage"]["model_calls"],
        "synthetic": view["synthetic"],
        "api_redistribution": attribution["api_redistribution"],
    }
    OUTPUT.write_text(json.dumps(evidence, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(evidence, sort_keys=True))


if __name__ == "__main__":
    main()
