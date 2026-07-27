from dataclasses import replace
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from axignal_api.admission import (
    build_world_bank_inflation_artifacts,
    evaluate_observed_fact,
)
from axignal_api.application import app
from axignal_api.connectors.world_bank import (
    SourceRetrievalError,
    WorldBankConnector,
)

FIXTURE = Path(__file__).parent / "fixtures" / "world_bank_rus_inflation.json"


def admitted_source() -> dict[str, object]:
    return {
        "source_id": "world-bank-wdi",
        "admission_state": "ADMITTED",
        "kill_switch": False,
        "rights_status": "COMMERCIAL_REUSE_WITH_ATTRIBUTION",
        "commercial_use": True,
        "redistribution": True,
        "license_id": "CC-BY-4.0",
    }


def test_world_bank_fixture_is_parsed_and_hashed() -> None:
    observation = WorldBankConnector(
        live_enabled=False,
        fixture_path=FIXTURE,
    ).fetch_latest_inflation()

    assert observation.country_code == "RUS"
    assert observation.indicator_code == "FP.CPI.TOTL.ZG"
    assert observation.period == "2025"
    assert observation.value == 8.7
    assert observation.content_hash.startswith("sha256:")
    assert observation.retrieval_mode == "FROZEN_FIXTURE"


def test_live_connector_refuses_redirects() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(302, headers={"location": "https://example.com"}, request=request)

    connector = WorldBankConnector(
        live_enabled=True,
        client=httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=False),
    )
    with pytest.raises(SourceRetrievalError, match="redirects"):
        connector.fetch_latest_inflation()


def test_deterministic_observed_fact_is_admitted() -> None:
    observation = WorldBankConnector(
        live_enabled=False,
        fixture_path=FIXTURE,
    ).fetch_latest_inflation()
    evidence, candidate = build_world_bank_inflation_artifacts(
        opportunity_id="opp_moscow_ramenki",
        period=observation.period,
        value=observation.value,
        source_content_hash=observation.content_hash,
    )

    decision = evaluate_observed_fact(
        source=admitted_source(),
        evidence=evidence,
        candidate=candidate,
    )

    assert decision.admitted is True
    assert decision.epistemic_class == "OBSERVED_FACT"
    assert decision.reasons == ("all_deterministic_gates_passed",)


def test_generative_proposal_cannot_auto_admit() -> None:
    observation = WorldBankConnector(
        live_enabled=False,
        fixture_path=FIXTURE,
    ).fetch_latest_inflation()
    evidence, candidate = build_world_bank_inflation_artifacts(
        opportunity_id="opp_moscow_ramenki",
        period=observation.period,
        value=observation.value,
        source_content_hash=observation.content_hash,
    )
    model_candidate = replace(candidate, producer_type="LOCAL_MODEL")

    decision = evaluate_observed_fact(
        source=admitted_source(),
        evidence=evidence,
        candidate=model_candidate,
    )

    assert decision.admitted is False
    assert "generative_producer_cannot_auto_admit" in decision.reasons


def test_persistent_endpoint_fails_closed_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AXIGNAL_PERSISTENT_RESEARCH_ENABLED", raising=False)
    client = TestClient(app)
    response = client.post(
        "/v1/research-runs",
        headers={"X-AXIGNAL-Tenant-ID": "11111111-1111-4111-8111-111111111111"},
        json={
            "context_id": "ctx_moscow_real_estate_v01",
            "opportunity_id": "opp_moscow_ramenki",
            "question": "Actualiza el contexto macroeconómico de la oportunidad.",
        },
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Persistent research is disabled"
