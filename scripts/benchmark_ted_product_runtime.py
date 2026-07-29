from __future__ import annotations

import json
import math
import os
import time
from pathlib import Path
from statistics import median
from uuid import UUID

import psycopg
from fastapi.testclient import TestClient

from axignal_api.application import app
from axignal_api.identity import build_identity_assertion
from axignal_api.settings import Settings
from axignal_api.worker import build_runtime

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "ted-product-runtime-metrics.json"
TENANT_ID = UUID("11111111-1111-4111-8111-111111111111")
IDENTITY_SECRET = "ci-identity-assertion-secret-with-at-least-32-bytes"
SOURCE_ID = "src_ted_search_api_v3"
RUN_COUNT = 10
MAX_P95_SECONDS = 5.0
MIN_FIELD_COMPLETENESS = 0.85


def headers() -> dict[str, str]:
    return {
        "X-AXIGNAL-Identity-Assertion": build_identity_assertion(
            secret=IDENTITY_SECRET,
            subject="usr_ted_metrics",
            email="ted-metrics@example.test",
            tenant_id=TENANT_ID,
        )
    }


def percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    index = max(0, math.ceil(probability * len(ordered)) - 1)
    return ordered[index]


def create_and_complete(
    *,
    client: TestClient,
    publisher,
    worker,
    index: int,
) -> tuple[float, dict]:
    started = time.perf_counter()
    response = client.post(
        "/v1/research-runs/ted-procurement",
        headers=headers(),
        json={
            "context_id": "ctx_eu_procurement_metrics",
            "opportunity_id": f"opp_eu_procurement_metrics_{index:02d}",
            "question": "Investiga las oportunidades públicas europeas activas.",
            "include_private_knowledge": False,
        },
    )
    assert response.status_code == 202, response.text
    run_id = response.json()["research_run_id"]
    publisher.publish_pending(limit=100)
    assert worker.run_once(timeout_seconds=2) is True
    publisher.publish_pending(limit=100)
    view_response = client.get(
        f"/v1/research-runs/{run_id}",
        headers=headers(),
    )
    assert view_response.status_code == 200, view_response.text
    view = view_response.json()
    elapsed = time.perf_counter() - started
    assert view["state"] == "COMPLETED", view
    assert view["actual_usage"]["model_calls"] == 0
    assert view["dossier"]["status"] == "TRACEABLE_WITH_ADMITTED_FACTS"
    return elapsed, view


def verify_kill_switch_residue(
    *,
    client: TestClient,
    publisher,
    worker,
    admin_dsn: str,
) -> dict[str, object]:
    with psycopg.connect(admin_dsn) as connection, connection.cursor() as cursor:
        cursor.execute(
            "UPDATE axignal_global.sources SET kill_switch=true WHERE source_id=%s",
            (SOURCE_ID,),
        )

    try:
        response = client.post(
            "/v1/research-runs/ted-procurement",
            headers=headers(),
            json={
                "context_id": "ctx_eu_procurement_metrics",
                "opportunity_id": "opp_eu_procurement_kill_switch",
                "question": "Comprueba el rollback de la fuente TED.",
                "include_private_knowledge": False,
            },
        )
        assert response.status_code == 202, response.text
        run_id = response.json()["research_run_id"]
        publisher.publish_pending(limit=100)
        assert worker.run_once(timeout_seconds=2) is True
        publisher.publish_pending(limit=100)
        view_response = client.get(
            f"/v1/research-runs/{run_id}",
            headers=headers(),
        )
        assert view_response.status_code == 200, view_response.text
        view = view_response.json()
        assert view["state"] == "FAILED"
        assert view["error_code"] == "SOURCE_NOT_ADMITTED"
        assert view["evidence"] == []
        assert view["candidate_claims"] == []
        assert view["canonical_claims"] == []
        assert view["dossier"] is None

        with psycopg.connect(admin_dsn) as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                  cardinality(evidence_ids),
                  cardinality(candidate_claim_ids),
                  cardinality(canonical_claim_ids),
                  dossier_id
                FROM tenant_private.research_runs
                WHERE research_run_id=%s
                """,
                (run_id,),
            )
            row = cursor.fetchone()
            assert row == (0, 0, 0, None)
        return {
            "failed_state": view["state"],
            "error_code": view["error_code"],
            "rollback_residue_count": 0,
        }
    finally:
        with psycopg.connect(admin_dsn) as connection, connection.cursor() as cursor:
            cursor.execute(
                "UPDATE axignal_global.sources SET kill_switch=false WHERE source_id=%s",
                (SOURCE_ID,),
            )


def main() -> None:
    required = (
        "AXIGNAL_DATABASE_URL",
        "AXIGNAL_VALKEY_URL",
        "AXIGNAL_TED_FIXTURE_PATH",
    )
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise SystemExit(f"Missing metric environment: {', '.join(missing)}")

    os.environ["AXIGNAL_PERSISTENT_RESEARCH_ENABLED"] = "true"
    os.environ["AXIGNAL_TED_PROCUREMENT_ENABLED"] = "true"
    os.environ["AXIGNAL_TED_LIVE_SOURCES_ENABLED"] = "false"
    os.environ["AXIGNAL_IDENTITY_ASSERTION_SECRET"] = IDENTITY_SECRET

    settings = Settings.from_env()
    client = TestClient(app)
    publisher, worker = build_runtime(settings)
    worker.queue.purge_for_test()

    durations: list[float] = []
    completion_ratios: list[float] = []
    failures: list[str] = []
    model_calls = 0
    for index in range(RUN_COUNT):
        try:
            duration, view = create_and_complete(
                client=client,
                publisher=publisher,
                worker=worker,
                index=index,
            )
            durations.append(duration)
            expected_fields = view["actual_usage"]["notices"] * 4
            completion_ratios.append(len(view["evidence"]) / expected_fields)
            model_calls += int(view["actual_usage"]["model_calls"])
        except Exception as exc:
            failures.append(f"{exc.__class__.__name__}: {exc}")

    rollback = verify_kill_switch_residue(
        client=client,
        publisher=publisher,
        worker=worker,
        admin_dsn=os.environ["AXIGNAL_DATABASE_URL"],
    )

    completed = len(durations)
    failure_rate = len(failures) / RUN_COUNT
    p50 = median(durations) if durations else float("inf")
    p95 = percentile(durations, 0.95) if durations else float("inf")
    completeness = min(completion_ratios) if completion_ratios else 0.0

    gates = {
        "all_runs_completed": completed == RUN_COUNT,
        "failure_rate_zero": failure_rate == 0.0,
        "p95_within_budget": p95 <= MAX_P95_SECONDS,
        "field_completeness_within_profile": completeness >= MIN_FIELD_COMPLETENESS,
        "model_calls_zero": model_calls == 0,
        "rollback_residue_zero": rollback["rollback_residue_count"] == 0,
    }
    result = {
        "status": "PASS" if all(gates.values()) else "FAIL",
        "task": "AX-F8-T14",
        "profile": "ted-search-non-personal-projection@0.1.0",
        "run_count": RUN_COUNT,
        "completed_run_count": completed,
        "failure_count": len(failures),
        "failure_rate": failure_rate,
        "latency_seconds": {
            "p50": round(p50, 6),
            "p95": round(p95, 6),
            "maximum_allowed_p95": MAX_P95_SECONDS,
        },
        "source_field_completeness": round(completeness, 6),
        "minimum_source_field_completeness": MIN_FIELD_COMPLETENESS,
        "external_variable_cost_eur_per_run": 0.0,
        "cost_scope": "TED Search API fee and model fee; infrastructure excluded",
        "model_calls": model_calls,
        "rollback": rollback,
        "gates": gates,
        "failures": failures,
    }
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
