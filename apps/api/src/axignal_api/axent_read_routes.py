from __future__ import annotations

from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from axignal_api.axent_context import AxentContextBuilder
from axignal_api.axent_knowledge import AxentKnowledgeRepository
from axignal_api.axent_repository import AxentRepository
from axignal_api.billing_repository import BillingRepository
from axignal_api.identity import AuthenticatedIdentity, require_identity
from axignal_api.settings import Settings

router = APIRouter(prefix="/v1/axent", tags=["axent-read-tools"])
Authenticated = Annotated[AuthenticatedIdentity, Depends(require_identity)]

ReadToolName = Literal[
    "get_my_identity",
    "get_my_plan",
    "get_my_entitlements",
    "get_seat_summary",
    "get_subscription_status",
    "get_invoice_status",
    "get_research_run_status",
    "get_workspace_status",
    "list_my_documents",
    "list_my_exports",
    "get_source_status",
    "get_recent_account_audit",
    "search_help_knowledge",
    "get_active_incidents",
]


class ReadToolRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tool_name: ReadToolName
    input: dict[str, Any] = Field(default_factory=dict)


def _settings() -> Settings:
    settings = Settings.from_env()
    if not settings.database_url:
        raise HTTPException(status_code=503, detail="axent_persistence_unavailable")
    return settings


def _active_incidents(
    repository: AxentRepository,
    *,
    tenant_id: UUID,
) -> list[dict[str, Any]]:
    cases = repository.list_open_cases(tenant_id=tenant_id)
    return [case for case in cases if case["case_type"] == "SERVICE_INCIDENT"]


@router.post("/conversations/{conversation_id}/read")
def execute_read_tool(
    conversation_id: UUID,
    command: ReadToolRequest,
    identity: Authenticated,
) -> dict[str, Any]:
    settings = _settings()
    assert settings.database_url is not None
    repository = AxentRepository(settings.database_url)
    conversation = repository.get_conversation(
        tenant_id=identity.tenant_id,
        conversation_id=conversation_id,
    )
    if conversation is None:
        raise HTTPException(status_code=404, detail="support_conversation_not_found")
    context = AxentContextBuilder(settings.database_url).build(
        identity=identity,
        workspace_id=conversation.get("workspace_id"),
        research_run_id=conversation.get("research_run_id"),
    )
    projection = context["account_projection"]
    billing = BillingRepository(settings.database_url)
    values: dict[str, Any] = {
        "get_my_identity": context["identity"],
        "get_my_plan": context["commercial"]["entitlement"],
        "get_my_entitlements": context["commercial"]["entitlement"],
        "get_seat_summary": context["commercial"]["seats"],
        "get_subscription_status": billing.current_selection(
            tenant_id=identity.tenant_id
        ),
        "get_invoice_status": billing.ledger(tenant_id=identity.tenant_id)[:20],
        "get_research_run_status": context["research_run"],
        "get_workspace_status": context["workspace"],
        "list_my_documents": projection["documents"],
        "list_my_exports": projection["exports"],
        "get_recent_account_audit": projection["audit"][:100],
        "get_active_incidents": _active_incidents(
            repository,
            tenant_id=identity.tenant_id,
        ),
    }
    if command.tool_name == "search_help_knowledge":
        query = str(command.input.get("query") or "").strip()
        if not query:
            raise HTTPException(status_code=422, detail="knowledge_query_required")
        value = AxentKnowledgeRepository(settings.database_url).search(
            tenant_id=identity.tenant_id,
            query=query,
            language=str(conversation.get("language") or "es"),
        )
        authority = "governed_knowledge"
    elif command.tool_name == "get_source_status":
        source_id = str(command.input.get("source_id") or "").strip()
        runs = projection["research_runs"]
        related = [
            run
            for run in runs
            if not source_id
            or source_id.casefold() in str(run).casefold()
        ]
        value = {
            "source_id": source_id or None,
            "related_research_runs": related[:20],
            "status_authority_available": bool(related),
            "disclosure": (
                "No independent source-status authority is persisted for this "
                "source; Axent returns only tenant research runtime evidence."
                if not related
                else "Status is derived from persisted tenant research runtime evidence."
            ),
        }
        authority = "persistent_research_runtime"
    else:
        value = values[command.tool_name]
        authority = "server"
    return {
        "schema_version": "axignal.axent-read-tool/v1",
        "tool_name": command.tool_name,
        "value": value,
        "authority": authority,
        "tenant_id": identity.tenant_id,
    }
