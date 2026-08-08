"""AXENT server-authoritative context builder (Mandato AXENT — sección 6.2)
and model-outage degradation (sección 16).

Context is built ONLY from server authorities; the browser can never
send tenant/role/entitlement claims. Every material context item carries
authority, authority_version, retrieved_at, freshness, sensitivity and
tenant_scope. Degradation is explicit, never a silent fallback.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from axignal_api.identity import AuthenticatedIdentity
from axignal_api.opportunity_repository import OpportunityOperationsRepository


class ModelOutageError(RuntimeError):
    """Raised when the AI provider is unavailable."""


class ModelDegradationMode:
    FULL_AI = "FULL_AI"
    DEGRADED_DETERMINISTIC = "DEGRADED_DETERMINISTIC"
    READ_ONLY = "READ_ONLY"
    SUPPORT_ONLY = "SUPPORT_ONLY"
    UNAVAILABLE = "UNAVAILABLE"

    @classmethod
    def resolve(cls, *, model_available: bool, provider_error: str | None = None) -> str:
        if not model_available:
            return cls.DEGRADED_DETERMINISTIC
        return cls.FULL_AI


@dataclass(frozen=True)
class AuthorityEnvelope:
    authority: str
    version: str
    retrieved_at: str
    freshness: str
    sensitivity: str
    tenant_scope: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


class AxentContextBuilder:
    """Builds the operational context exclusively from server authorities."""

    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        self.opportunities = OpportunityOperationsRepository(database_url)

    def _envelope(self, authority: str, version: str, sensitivity: str) -> AuthorityEnvelope:
        return AuthorityEnvelope(
            authority=authority,
            version=version,
            retrieved_at=datetime.now(UTC).isoformat(),
            freshness="live",
            sensitivity=sensitivity,
            tenant_scope="tenant",
        )

    def build(
        self,
        *,
        identity: AuthenticatedIdentity,
        current_route: str | None = None,
        opportunity_ref: str | None = None,
        pursuit_ref: str | None = None,
        workspace_id: UUID | None = None,
    ) -> dict[str, Any]:
        context: dict[str, Any] = {
            "identity": {
                **self._envelope("identity", "v1", "private").as_dict(),
                "subject": identity.subject,
                "email": identity.email,
                "tenant_id": str(identity.tenant_id),
                "assurance_level": getattr(identity, "assurance_level", "AAL1"),
            },
            "tenant_scope": str(identity.tenant_id),
            "current_route": current_route,
        }

        # Pursuit (if requested) — server-resolved, never client-sent.
        if pursuit_ref:
            pursuit = self.opportunities.get_pursuit(
                tenant_id=identity.tenant_id, pursuit_ref=pursuit_ref
            )
            context["pursuit"] = {
                **self._envelope("opportunity_repository", "v1", "private").as_dict(),
                "pursuit_ref": pursuit_ref,
                "state": pursuit.get("state") if pursuit else None,
                "found": pursuit is not None,
            }
            if pursuit is None:
                context["pursuit"]["error"] = "not_found_or_not_tenant_scoped"

        # Opportunity (if requested).
        if opportunity_ref:
            opportunity = self.opportunities.get_opportunity(
                tenant_id=identity.tenant_id, opportunity_ref=opportunity_ref
            )
            context["opportunity"] = {
                **self._envelope("opportunity_repository", "v1", "private").as_dict(),
                "opportunity_ref": opportunity_ref,
                "state": opportunity.get("state") if opportunity else None,
                "found": opportunity is not None,
            }

        # Workspace list (always available for AXENT global).
        context["workspaces"] = {
            **self._envelope("opportunity_repository", "v1", "private").as_dict(),
            "items": [
                {
                    "workspace_id": str(w.get("workspace_id") or w.get("id")),
                    "title": w.get("title"),
                    "state": w.get("state"),
                }
                for w in self.opportunities.list_workspaces(tenant_id=identity.tenant_id)
            ],
        }

        context["permitted_actions"] = {
            "search_opportunities": True,
            "create_pursuit": True,
            "create_task": True,
            "submit_official_bid": False,
            "admit_source": False,
        }
        return context


class AxentDegradation:
    """Explicit capability disclosure when the model provider is down.

    Without the model, these keep working: navigation, saved searches,
    structured filters, opportunity/workspace/pursuit/task reads,
    billing reads, deterministic knowledge, case creation,
    notifications, human console, receipts, system status.
    """

    DETERMINISTIC_CAPABILITIES = (
        "navigation", "saved_searches", "structured_filters",
        "opportunity_reads", "workspace_reads", "pursuit_reads",
        "task_reads", "billing_reads", "deterministic_knowledge",
        "case_creation", "notifications", "human_console", "receipts",
        "system_status",
    )

    AI_ONLY_CAPABILITIES = (
        "natural_language_planning", "semantic_retrieval",
        "grounded_composition", "conversational_memory",
    )

    def status(self, *, model_available: bool) -> dict[str, Any]:
        mode = ModelDegradationMode.resolve(model_available=model_available)
        return {
            "mode": mode,
            "available": {
                capability: True
                for capability in self.DETERMINISTIC_CAPABILITIES
            },
            "unavailable": (
                list(self.AI_ONLY_CAPABILITIES) if not model_available else []
            ),
            "message": (
                "Capacidad efectiva: DEGRADED_DETERMINISTIC — las consultas en "
                "lenguaje natural y la composición fundamentada están "
                "suspendidas; la navegación, filtros, lecturas, casos y "
                "notificaciones continúan disponibles."
                if not model_available
                else "Capacidad efectiva: FULL_AI."
            ),
            "checked_at": datetime.now(UTC).isoformat(),
        }
