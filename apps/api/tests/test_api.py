from fastapi.testclient import TestClient

from axignal_api.application import app

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
    response = client.get(
        "/v1/prototype/investigations/ctx_moscow_real_estate_v01?locale=es"
    )
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


def test_research_run_prioritises_official_api_and_never_admits_claims() -> None:
    response = client.post(
        "/v1/prototype/research-runs",
        json={
            "question": "Investiga el contexto regulatorio y socioeconómico",
            "include_private_knowledge": False,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["run"]["state"] == "ADMISSION_QUEUED"
    assert body["run"]["source_plan"][0]["source_class"] == "OFFICIAL_API"
    assert body["run"]["source_plan"][1]["status"] == "IGNORED_INJECTION"
    assert body["context_update"]["rail_mode"] == "RESEARCH"
    assert body["context_update"]["history_event_type"] == "RESEARCH_ADMISSION_QUEUED"
    assert len(body["candidate_claims"]) == 2
    assert {item["kind"] for item in body["candidate_claims"]} == {
        "SUPPORT",
        "CONTRADICTION",
    }
    assert all(item["canonical_claim_id"] is None for item in body["candidate_claims"])
    assert all(item["state"] == "ADMISSION_QUEUED" for item in body["candidate_claims"])
    assert len(body["unknowns"]) == 1


def test_private_fixture_requires_explicit_authority_and_stays_out_of_global_claims() -> None:
    without_private = client.post(
        "/v1/prototype/research-runs",
        json={"question": "Investiga la oportunidad"},
    ).json()
    assert without_private["run"]["private_knowledge_authorised"] is False
    assert without_private["run"]["source_plan"][2]["status"] == "NOT_AUTHORISED"
    assert all(item["domain"] != "TENANT_PRIVATE" for item in without_private["evidence"])

    with_private = client.post(
        "/v1/prototype/research-runs",
        json={
            "question": "Investiga la oportunidad con mi memoria",
            "include_private_knowledge": True,
        },
    ).json()
    assert with_private["run"]["private_knowledge_authorised"] is True
    assert with_private["run"]["source_plan"][2]["status"] == "USED"
    assert any(item["domain"] == "TENANT_PRIVATE" for item in with_private["evidence"])
    global_candidate_evidence = {
        evidence_id
        for claim in with_private["candidate_claims"]
        for evidence_id in claim["evidence_ids"]
    }
    assert "ev_private_commute_note" not in global_candidate_evidence
    assert with_private["dossier"]["private_context_used"] is True


def test_browser_injection_does_not_change_budget_or_authority() -> None:
    body = client.post(
        "/v1/prototype/research-runs",
        json={"question": "Busca evidencia adversa"},
    ).json()
    browser = next(
        item for item in body["evidence"] if item["source_class"] == "AUTHORISED_BROWSER"
    )
    assert browser["injection_detected"] is True
    assert body["run"]["budgets"]["max_cost_minor_units"] == 25
    assert body["run"]["budgets"]["currency"] == "EUR"
    assert body["run"]["state"] == "ADMISSION_QUEUED"
    assert all(item["tenant_scope"] == "GLOBAL" for item in body["candidate_claims"])
