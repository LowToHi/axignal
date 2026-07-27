from fastapi.testclient import TestClient

from axignal_api.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_interpret_moscow_command_is_synthetic_and_bounded() -> None:
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
