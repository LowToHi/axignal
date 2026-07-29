from dataclasses import replace
from pathlib import Path
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from axignal_api.application import app
from axignal_api.connectors.ted import TEDSearchConnector
from axignal_api.identity import build_identity_assertion
from axignal_api.queue import ResearchJob
from axignal_api.ted_runtime import (
    PROFILE_ID,
    build_ted_search_artifacts,
    evaluate_ted_observed_field,
    sanitised_projection,
)
from axignal_api.worker import ResearchWorker

FIXTURE = Path(__file__).parent / "fixtures" / "ted_search_probe.json"
TENANT_ID = UUID("11111111-1111-4111-8111-111111111111")
IDENTITY_SECRET = "test-identity-assertion-secret-with-32-bytes"


def admitted_source() -> dict[str, object]:
    return {
        "source_id": "src_ted_search_api_v3",
        "admission_state": "ADMITTED",
        "kill_switch": False,
        "rights_status": "COMMERCIAL_REUSE_WITH_ATTRIBUTION",
        "commercial_use": True,
        "redistribution": False,
        "license_id": "TED-LEGAL-NOTICE-REUSE",
        "config": {
            "product_profile": PROFILE_ID,
            "api_redistribution_allowed": False,
        },
    }


def identity_headers() -> dict[str, str]:
    return {
        "X-AXIGNAL-Identity-Assertion": build_identity_assertion(
            secret=IDENTITY_SECRET,
            subject="usr_test_operator",
            email="operator@example.test",
            tenant_id=TENANT_ID,
        )
    }


class KillSwitchRepository:
    def __init__(self) -> None:
        self.failures: list[dict[str, object]] = []

    def get_run_for_worker(self, **_: object) -> dict[str, object]:
        return {
            "state": "QUEUED",
            "opportunity_id": "opp_eu_procurement",
            "job_kind": "TED_PROCUREMENT",
        }

    def get_source(self, _: str) -> dict[str, object]:
        return admitted_source() | {"kill_switch": True}

    def fail_run(self, **values: object) -> None:
        self.failures.append(values)


def test_ted_projection_is_sanitised_and_deterministic() -> None:
    page = TEDSearchConnector(
        live_enabled=False,
        fixture_path=FIXTURE,
    ).fetch_probe_page()

    projection = sanitised_projection(page)
    encoded = str(projection)
    assert "links" not in encoded
    assert "xml" not in encoded
    assert len(projection["notices"]) == 2

    first = build_ted_search_artifacts(
        page=page,
        opportunity_id="opp_eu_procurement",
    )
    second = build_ted_search_artifacts(
        page=page,
        opportunity_id="opp_eu_procurement",
    )
    assert first == second
    evidence, candidates = first
    assert len(evidence) == 7
    assert len(candidates) == 7
    assert all(item.producer_type == "DETERMINISTIC_PARSER" for item in candidates)
    assert all(item.method_version == "ted-search-observed-field@0.1.0" for item in candidates)


def test_exact_ted_observed_fields_are_admitted() -> None:
    page = TEDSearchConnector(
        live_enabled=False,
        fixture_path=FIXTURE,
    ).fetch_probe_page()
    evidence, candidates = build_ted_search_artifacts(
        page=page,
        opportunity_id="opp_eu_procurement",
    )

    decisions = [
        evaluate_ted_observed_field(
            source=admitted_source(),
            evidence=evidence_item,
            candidate=candidate,
        )
        for evidence_item, candidate in zip(evidence, candidates, strict=True)
    ]

    assert all(item.admitted for item in decisions)
    assert all(item.epistemic_class == "OBSERVED_FACT" for item in decisions)
    assert all(item.reasons == ("all_ted_projection_gates_passed",) for item in decisions)


def test_ted_kill_switch_blocks_admission() -> None:
    page = TEDSearchConnector(
        live_enabled=False,
        fixture_path=FIXTURE,
    ).fetch_probe_page()
    evidence, candidates = build_ted_search_artifacts(
        page=page,
        opportunity_id="opp_eu_procurement",
    )
    source = admitted_source() | {"kill_switch": True}

    decision = evaluate_ted_observed_field(
        source=source,
        evidence=evidence[0],
        candidate=candidates[0],
    )

    assert decision.admitted is False
    assert "source_kill_switch_enabled" in decision.reasons


def test_ted_source_kill_switch_blocks_worker_before_retrieval() -> None:
    repository = KillSwitchRepository()
    worker = ResearchWorker(
        repository=repository,  # type: ignore[arg-type]
        queue=object(),  # type: ignore[arg-type]
        world_bank_connector=object(),  # type: ignore[arg-type]
    )
    worker.process(
        ResearchJob(
            tenant_id=TENANT_ID,
            research_run_id=uuid4(),
            source_id="src_ted_search_api_v3",
        )
    )

    assert len(repository.failures) == 1
    failure = repository.failures[0]
    assert failure["error_code"] == "SOURCE_NOT_ADMITTED"
    assert failure["error_detail"] == "Source kill switch is enabled"


def test_generative_ted_candidate_cannot_auto_admit() -> None:
    page = TEDSearchConnector(
        live_enabled=False,
        fixture_path=FIXTURE,
    ).fetch_probe_page()
    evidence, candidates = build_ted_search_artifacts(
        page=page,
        opportunity_id="opp_eu_procurement",
    )
    model_candidate = replace(candidates[0], producer_type="LOCAL_MODEL")

    decision = evaluate_ted_observed_field(
        source=admitted_source(),
        evidence=evidence[0],
        candidate=model_candidate,
    )

    assert decision.admitted is False
    assert "generative_producer_cannot_auto_admit" in decision.reasons


def test_ted_endpoint_fails_closed_without_identity(
    monkeypatch,
) -> None:
    monkeypatch.setenv("AXIGNAL_IDENTITY_ASSERTION_SECRET", IDENTITY_SECRET)
    client = TestClient(app)
    response = client.post(
        "/v1/research-runs/ted-procurement",
        json={
            "context_id": "ctx_eu_procurement_v01",
            "opportunity_id": "opp_eu_procurement",
            "question": "Investiga la contratación pública europea activa.",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Authenticated identity is required"


def test_ted_endpoint_fails_closed_when_runtime_disabled(
    monkeypatch,
) -> None:
    monkeypatch.setenv("AXIGNAL_IDENTITY_ASSERTION_SECRET", IDENTITY_SECRET)
    monkeypatch.setenv("AXIGNAL_PERSISTENT_RESEARCH_ENABLED", "true")
    monkeypatch.delenv("AXIGNAL_TED_PROCUREMENT_ENABLED", raising=False)
    client = TestClient(app)
    response = client.post(
        "/v1/research-runs/ted-procurement",
        headers=identity_headers(),
        json={
            "context_id": "ctx_eu_procurement_v01",
            "opportunity_id": "opp_eu_procurement",
            "question": "Investiga la contratación pública europea activa.",
        },
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "TED procurement runtime is disabled"


def test_ted_endpoint_rejects_private_knowledge(
    monkeypatch,
) -> None:
    monkeypatch.setenv("AXIGNAL_IDENTITY_ASSERTION_SECRET", IDENTITY_SECRET)
    client = TestClient(app)
    response = client.post(
        "/v1/research-runs/ted-procurement",
        headers=identity_headers(),
        json={
            "context_id": "ctx_eu_procurement_v01",
            "opportunity_id": "opp_eu_procurement",
            "question": "Investiga la contratación pública europea activa.",
            "include_private_knowledge": True,
        },
    )

    assert response.status_code == 422
