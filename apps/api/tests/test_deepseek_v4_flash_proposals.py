from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from axignal_api.deepseek_proposals import (
    DEEPSEEK_METHOD_VERSION,
    DEEPSEEK_MODEL,
    DEEPSEEK_PRODUCER_ID,
    DEEPSEEK_PROMPT_VERSION,
    DeepSeekV4FlashProposalAdapter,
)
from axignal_api.document_proposals import (
    InstitutionalDocument,
    LocalDocumentProposalPipeline,
    ModelProposalError,
    ProposalBatch,
)
from axignal_api.settings import Settings

FIXTURES = Path(__file__).parent / "fixtures"
DOCUMENT_FIXTURE = FIXTURES / "world_bank_rer41_document.json"
PROPOSAL_FIXTURE = FIXTURES / "world_bank_rer41_proposal.json"


def load_document() -> InstitutionalDocument:
    return InstitutionalDocument.model_validate_json(
        DOCUMENT_FIXTURE.read_text(encoding="utf-8")
    )


def load_proposal_payload() -> dict[str, object]:
    proposal = ProposalBatch.model_validate_json(
        PROPOSAL_FIXTURE.read_text(encoding="utf-8")
    )
    return proposal.model_dump(mode="json")


def test_deepseek_adapter_uses_direct_bounded_json_contract() -> None:
    returned = load_proposal_payload()
    returned.update(
        {
            "producer_id": "untrusted-provider-value",
            "model_version": "untrusted-model-value",
            "method_version": "untrusted-method-value",
            "prompt_version": "untrusted-prompt-value",
        }
    )

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/chat/completions"
        assert request.headers["authorization"] == "Bearer test-secret"
        body = json.loads(request.content)
        assert body["model"] == DEEPSEEK_MODEL
        assert body["temperature"] == 0
        assert body["max_tokens"] == 600
        assert body["thinking"] == {"type": "disabled"}
        assert body["response_format"] == {"type": "json_object"}
        assert "proposal authority only" in body["messages"][0]["content"]
        assert "required_schema" in json.loads(body["messages"][1]["content"])
        return httpx.Response(
            200,
            json={
                "choices": [
                    {"message": {"content": json.dumps(returned)}}
                ]
            },
        )

    adapter = DeepSeekV4FlashProposalAdapter(
        api_key="test-secret",
        max_output_tokens=600,
        transport=httpx.MockTransport(handler),
    )
    result = LocalDocumentProposalPipeline(model_gateway=adapter).execute(
        document=load_document(),
        opportunity_id="opportunity_moscow_real_estate",
        research_question="Extract supporting and adverse evidence",
    )

    assert result.actual_usage["local_model"] == DEEPSEEK_MODEL
    assert result.gates.MODEL_AUTHORITY_BLOCKED is True
    assert result.canonical_claims == []
    assert all(item.producer_id == DEEPSEEK_PRODUCER_ID for item in result.candidate_claims)
    assert all(item.model_version == DEEPSEEK_MODEL for item in result.candidate_claims)
    assert all(item.method_version == DEEPSEEK_METHOD_VERSION for item in result.candidate_claims)
    assert all(item.prompt_version == DEEPSEEK_PROMPT_VERSION for item in result.candidate_claims)
    assert all(item.state == "ADMISSION_QUEUED" for item in result.candidate_claims)


def test_deepseek_adapter_rejects_non_official_host_and_wrong_model() -> None:
    with pytest.raises(ValueError, match="official HTTPS API host"):
        DeepSeekV4FlashProposalAdapter(
            api_key="test-secret",
            base_url="https://proxy.example.test",
        )
    with pytest.raises(ValueError, match="deepseek-v4-flash"):
        DeepSeekV4FlashProposalAdapter(
            api_key="test-secret",
            model="deepseek-v4-pro",
        )


def test_deepseek_adapter_fails_closed_on_invalid_json() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        del request
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "not-json"}}]},
        )

    adapter = DeepSeekV4FlashProposalAdapter(
        api_key="test-secret",
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(ModelProposalError, match="failed closed"):
        LocalDocumentProposalPipeline(model_gateway=adapter).execute(
            document=load_document(),
            opportunity_id="opportunity_moscow_real_estate",
            research_question="Extract claims",
        )


def test_deepseek_settings_require_secret_and_reject_ambiguous_routing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AXIGNAL_PERSISTENT_RESEARCH_ENABLED", "true")
    monkeypatch.setenv("AXIGNAL_PROPOSAL_DATABASE_URL", "postgresql://proposal")
    monkeypatch.setenv("AXIGNAL_VALKEY_URL", "redis://valkey")
    monkeypatch.setenv(
        "AXIGNAL_DOCUMENT_FIXTURE_PATH",
        str(DOCUMENT_FIXTURE),
    )
    monkeypatch.setenv("AXIGNAL_DEEPSEEK_PROPOSAL_ENABLED", "true")
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="DEEPSEEK_API_KEY"):
        Settings.from_env().require_document_proposal_worker()

    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-secret")
    Settings.from_env().require_document_proposal_worker()

    monkeypatch.setenv("AXIGNAL_LOCAL_MODEL_BASE_URL", "http://local-model.test")
    with pytest.raises(RuntimeError, match="cannot be enabled together"):
        Settings.from_env().require_document_proposal_worker()
