from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from axignal_api.application import app
from axignal_api.identity import build_identity_assertion
from axignal_api.proposal_queue import (
    DocumentProposalBudget,
    DocumentProposalJob,
)

TENANT_ID = UUID("11111111-1111-4111-8111-111111111111")
IDENTITY_SECRET = "test-identity-assertion-secret-with-32-bytes"


def identity_headers() -> dict[str, str]:
    return {
        "X-AXIGNAL-Identity-Assertion": build_identity_assertion(
            secret=IDENTITY_SECRET,
            subject="usr_test_operator",
            email="operator@example.test",
            tenant_id=TENANT_ID,
        )
    }


def test_document_proposal_job_round_trip_is_typed() -> None:
    job = DocumentProposalJob(
        tenant_id=TENANT_ID,
        research_run_id=UUID("22222222-2222-4222-8222-222222222222"),
        source_id="world-bank-rer41",
        document_id="doc_world_bank_rer41",
        pipeline_version="local-document-proposal-pipeline@0.1.0",
        budget=DocumentProposalBudget(),
    )

    decoded = DocumentProposalJob.from_payload(job.as_payload())

    assert decoded == job
    assert decoded.as_payload()["job_kind"] == "DOCUMENT_PROPOSAL"
    assert decoded.budget.max_model_calls == 1


def test_document_proposal_job_rejects_wrong_authority_route() -> None:
    payload = {
        "schema_version": 2,
        "job_kind": "ADMISSION_REVIEW",
        "tenant_id": str(TENANT_ID),
        "research_run_id": "22222222-2222-4222-8222-222222222222",
        "source_id": "world-bank-rer41",
        "document_id": "doc_world_bank_rer41",
        "pipeline_version": "local-document-proposal-pipeline@0.1.0",
        "budget": {},
    }

    with pytest.raises(ValueError, match="job kind"):
        DocumentProposalJob.from_payload(payload)


def test_document_proposal_budget_rejects_multiple_model_calls() -> None:
    with pytest.raises(ValueError, match="exactly one"):
        DocumentProposalBudget.from_payload({"max_documents": 1, "max_model_calls": 2})


def test_document_proposal_endpoint_requires_authenticated_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AXIGNAL_IDENTITY_ASSERTION_SECRET", IDENTITY_SECRET)
    client = TestClient(app)

    response = client.post(
        "/v1/research-runs/document-proposals",
        json={
            "context_id": "ctx_moscow_real_estate_v01",
            "opportunity_id": "opp_moscow_ramenki",
            "question": "Extrae evidencia del informe institucional.",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Authenticated identity is required"


def test_document_proposal_endpoint_fails_closed_when_persistence_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AXIGNAL_IDENTITY_ASSERTION_SECRET", IDENTITY_SECRET)
    monkeypatch.delenv("AXIGNAL_PERSISTENT_RESEARCH_ENABLED", raising=False)
    client = TestClient(app)

    response = client.post(
        "/v1/research-runs/document-proposals",
        headers=identity_headers(),
        json={
            "context_id": "ctx_moscow_real_estate_v01",
            "opportunity_id": "opp_moscow_ramenki",
            "question": "Extrae evidencia del informe institucional.",
        },
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Persistent research is disabled"


def test_document_proposal_endpoint_rejects_private_knowledge_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AXIGNAL_IDENTITY_ASSERTION_SECRET", IDENTITY_SECRET)
    monkeypatch.delenv("AXIGNAL_PERSISTENT_RESEARCH_ENABLED", raising=False)
    client = TestClient(app)

    response = client.post(
        "/v1/research-runs/document-proposals",
        headers=identity_headers(),
        json={
            "context_id": "ctx_moscow_real_estate_v01",
            "opportunity_id": "opp_moscow_ramenki",
            "question": "Extrae evidencia del informe institucional.",
            "include_private_knowledge": True,
        },
    )

    assert response.status_code == 422
