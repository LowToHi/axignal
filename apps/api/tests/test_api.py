from fastapi.testclient import TestClient

from axignal_api.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_legacy_interpret_command_remains_synthetic_and_bounded() -> None:
    response = client.post(
        "/v1/navigator/commands:interpret",
        json={"message": "Quiero ver oportunidades inmobiliarias en Moscú", "locale": "es"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["plan"]["geography"] == "Moscow, Russia"
    assert body["plan"]["selected_lens"] == "GLOBE"
    assert body["plan"]["synthetic"] is True
    assert all(item["synthetic"] is True for item in body["opportunities"])


def test_get_prototype_investigation_returns_shared_context() -> None:
    response = client.get("/v1/prototype/investigations/ctx_moscow_real_estate_v01?locale=es")
    assert response.status_code == 200
    body = response.json()
    assert body["context"]["context_id"] == "ctx_moscow_real_estate_v01"
    assert body["context"]["version"] == 1
    assert body["context"]["lens"] == "GLOBE"
    assert body["context"]["coverage"]["status"] == "PARTIAL"
    assert body["context"]["synthetic"] is True
    assert len(body["opportunities"]) == 4


def test_prototype_command_preserves_selection_and_focuses_contradiction() -> None:
    initial = client.get(
        "/v1/prototype/investigations/ctx_moscow_real_estate_v01?locale=es"
    ).json()
    select_response = client.post(
        "/v1/prototype/navigator/commands:run",
        json={"message": "Selecciona Zona ZIL", "locale": "es", "payload": initial},
    )
    assert select_response.status_code == 200
    selected = select_response.json()
    assert selected["context"]["selection"]["opportunity_ids"] == ["opp_moscow_zil"]
    assert selected["context"]["version"] == 2

    contradiction_response = client.post(
        "/v1/prototype/navigator/commands:run",
        json={
            "message": "Cambia al grafo y muéstrame las contradicciones",
            "locale": "es",
            "payload": selected,
        },
    )
    assert contradiction_response.status_code == 200
    result = contradiction_response.json()
    assert result["context"]["lens"] == "GRAPH"
    assert result["context"]["selection"]["opportunity_ids"] == ["opp_moscow_zil"]
    assert result["context"]["selection"]["claim_ids"] == ["clm_zil_rates"]
    assert result["focus"]["evidence_id"] == "ev_bank_rates"
    assert result["context"]["version"] == 3
    assert result["context"]["history"][-1]["event_type"] == "CONTRADICTION_FOCUSED"


def test_unknown_prototype_context_is_not_fabricated() -> None:
    response = client.get("/v1/prototype/investigations/ctx_unknown_context")
    assert response.status_code == 404
