"""AXENT typed tool registry and executor (Mandato AXENT — sección 8).

Every tool is typed (strict parameter schema), classified by the policy
engine, and executes ONLY through the existing domain authorities
(opportunity repository, bid workspace repository, cross-library
repository). The assistant never touches tables directly.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from axignal_api.axent_policy import AxentPolicyEngine, PolicyResult

# --- Typed parameter schemas -------------------------------------------------

class SearchOpportunitiesParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    keywords: list[str] = Field(default_factory=list)
    countries: list[str] = Field(default_factory=list)
    sectors: list[str] = Field(default_factory=list)
    value_min: float | None = None
    value_max: float | None = None
    status: list[str] = Field(default_factory=list)
    limit: int = Field(default=10, ge=1, le=100)


class GetOpportunityParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    opportunity_ref: str = Field(min_length=3, max_length=200)


class CompareOpportunitiesParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    opportunity_refs: list[str] = Field(min_length=2, max_length=10)


class CreatePursuitParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    opportunity_ref: str = Field(min_length=3, max_length=200)
    decision: str = Field(default="BID", pattern=r"^(BID|NO_BID)$")


class UpdatePursuitStateParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pursuit_ref: str = Field(min_length=3, max_length=200)
    state: str = Field(
        pattern=r"^(QUALIFIED|DECISION_REVIEW|ACTIVE|WON|LOST|WITHDRAWN)$"
    )


class LinkOpportunityParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workspace_id: str = Field(min_length=8, max_length=64)
    opportunity_ref: str = Field(min_length=3, max_length=200)


class AddToWorkspaceParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workspace_title: str = Field(min_length=2, max_length=200)
    opportunity_refs: list[str] = Field(min_length=1, max_length=10)


class CreateTaskParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workspace_id: str = Field(min_length=8, max_length=64)
    title: str = Field(min_length=2, max_length=300)
    assignee: str | None = None
    due_at: str | None = None


class UpdatePriorityParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pursuit_ref: str = Field(min_length=3, max_length=200)
    priority: str = Field(pattern=r"^(HIGH|MEDIUM|LOW)$")


class SaveSearchParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=2, max_length=200)
    query_json: dict = Field(default_factory=dict)


class RecordOutcomeParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pursuit_ref: str = Field(min_length=3, max_length=200)
    outcome: str = Field(pattern=r"^(WON|LOST|WITHDRAWN)$")
    notes: str | None = None


class RecordBidNoBidParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pursuit_ref: str = Field(min_length=3, max_length=200)
    decision: str = Field(pattern=r"^(BID|NO_BID)$")


class DismissOpportunityParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    opportunity_ref: str = Field(min_length=3, max_length=200)


SCHEMAS: dict[str, type[BaseModel]] = {
    "search_opportunities": SearchOpportunitiesParams,
    "get_opportunity": GetOpportunityParams,
    "compare_opportunities": CompareOpportunitiesParams,
    "create_pursuit": CreatePursuitParams,
    "update_pursuit_state": UpdatePursuitStateParams,
    "link_opportunity_to_workspace": LinkOpportunityParams,
    "add_to_workspace": AddToWorkspaceParams,
    "create_task": CreateTaskParams,
    "update_internal_priority": UpdatePriorityParams,
    "save_search": SaveSearchParams,
    "record_outcome": RecordOutcomeParams,
    "record_bid_no_bid": RecordBidNoBidParams,
    "dismiss_opportunity": DismissOpportunityParams,
}


@dataclass(frozen=True)
class ToolSpec:
    name: str
    risk_class: str
    schema: type[BaseModel]
    handler: Callable[..., dict[str, Any]]


class ToolExecutionError(RuntimeError):
    pass


class AxentToolExecutor:
    """Executes typed tools through domain authorities.

    `domain` exposes the existing repositories (opportunity, bid
    workspace, cross-library). No SQL, no table access, no model-driven
    schemas.
    """

    def __init__(
        self,
        *,
        domain: Any,
        policy: AxentPolicyEngine | None = None,
    ) -> None:
        self.domain = domain
        self.policy = policy or AxentPolicyEngine()
        self._tools: dict[str, ToolSpec] = {}
        self._register()

    def _register(self) -> None:
        handlers: dict[str, Callable[..., dict[str, Any]]] = {
            "search_opportunities": self._search_opportunities,
            "get_opportunity": self._get_opportunity,
            "compare_opportunities": self._compare_opportunities,
            "create_pursuit": self._create_pursuit,
            "update_pursuit_state": self._update_pursuit_state,
            "link_opportunity_to_workspace": self._link_opportunity,
            "add_to_workspace": self._add_to_workspace,
            "create_task": self._create_task,
            "update_internal_priority": self._update_priority,
            "save_search": self._save_search,
            "record_outcome": self._record_outcome,
            "record_bid_no_bid": self._record_bid_no_bid,
            "dismiss_opportunity": self._dismiss_opportunity,
        }
        for name, handler in handlers.items():
            self._tools[name] = ToolSpec(
                name=name,
                risk_class=self.policy.classify(name).risk_class,
                schema=SCHEMAS[name],
                handler=handler,
            )

    def list_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "name": spec.name,
                "risk_class": spec.risk_class,
                "parameter_fields": list(spec.schema.model_fields),
            }
            for spec in sorted(self._tools.values(), key=lambda s: s.name)
        ]

    def policy_for(self, tool_name: str, *, assurance_level: str = "AAL1") -> PolicyResult:
        if tool_name not in self._tools:
            raise ToolExecutionError(f"unknown tool {tool_name!r}")
        return self.policy.decision_for(tool_name, assurance_level=assurance_level)

    def execute(
        self,
        *,
        tool_name: str,
        parameters: dict[str, Any],
        tenant_id: UUID,
        actor_subject: str,
    ) -> dict[str, Any]:
        """Validate the typed schema, then execute through the domain."""
        if tool_name not in self._tools:
            raise ToolExecutionError(f"unknown tool {tool_name!r}")
        spec = self._tools[tool_name]
        try:
            validated = spec.schema.model_validate(parameters)
        except Exception as exc:  # noqa: BLE001
            raise ToolExecutionError(
                f"invalid parameters for {tool_name}: {exc}"
            ) from exc
        return spec.handler(
            tenant_id=tenant_id,
            actor_subject=actor_subject,
            **validated.model_dump(),
        )

    # --- Handlers -------------------------------------------------------------

    def _search_opportunities(
        self, *, tenant_id: UUID, actor_subject: str, **params: Any
    ) -> dict[str, Any]:
        objects = self.domain.retrieval.search_opportunities(
            tenant_id=tenant_id, plan=self.domain.plan_for(params)
        )
        return {
            "tool": "search_opportunities",
            "count": len(objects),
            "results": [
                {
                    "opportunity_ref": obj["opportunity_ref"],
                    "library_id": obj["library_id"],
                    "state": obj["state"],
                    "title": (obj.get("payload") or {}).get("title"),
                }
                for obj in objects[: params.get("limit", 10)]
            ],
        }

    def _get_opportunity(
        self, *, tenant_id: UUID, actor_subject: str, opportunity_ref: str
    ) -> dict[str, Any]:
        opportunity = self.domain.opportunities.get_opportunity(
            tenant_id=tenant_id, opportunity_ref=opportunity_ref
        )
        if opportunity is None:
            raise ToolExecutionError(f"opportunity {opportunity_ref!r} not found")
        return {"tool": "get_opportunity", "opportunity": opportunity}

    def _compare_opportunities(
        self, *, tenant_id: UUID, actor_subject: str, opportunity_refs: list[str]
    ) -> dict[str, Any]:
        from datetime import datetime

        rows = []
        for ref in opportunity_refs:
            opportunity = self.domain.opportunities.get_opportunity(
                tenant_id=tenant_id, opportunity_ref=ref
            )
            if opportunity is not None:
                row = dict(opportunity)
                for key, value in list(row.items()):
                    if isinstance(value, UUID):
                        row[key] = str(value)
                    elif isinstance(value, datetime):
                        row[key] = value.isoformat()
                rows.append(row)
        return {"tool": "compare_opportunities", "compared": len(rows), "rows": rows}

    def _create_pursuit(
        self, *, tenant_id: UUID, actor_subject: str,
        opportunity_ref: str, decision: str = "BID",
    ) -> dict[str, Any]:
        pursuit_ref = f"prs_{opportunity_ref}"
        # Canonical pursuit states: BID -> QUALIFIED, NO_BID -> WITHDRAWN.
        state = "QUALIFIED" if decision == "BID" else "WITHDRAWN"
        existing = self.domain.opportunities.get_pursuit(
            tenant_id=tenant_id, pursuit_ref=pursuit_ref
        )
        if existing is not None:
            return {
                "tool": "create_pursuit",
                "receipt": {"pursuit_ref": pursuit_ref,
                            "pursuit_id": str(existing["pursuit_id"]),
                            "state": existing["state"], "already_exists": True},
            }
        pursuit_id = self.domain.opportunities.create_pursuit(
            tenant_id=tenant_id, pursuit_ref=pursuit_ref,
            opportunity_ref=opportunity_ref, state=state,
            created_by=actor_subject,
        )
        return {
            "tool": "create_pursuit",
            "receipt": {"pursuit_ref": pursuit_ref, "pursuit_id": str(pursuit_id),
                        "state": state},
        }

    def _update_pursuit_state(
        self, *, tenant_id: UUID, actor_subject: str,
        pursuit_ref: str, state: str,
    ) -> dict[str, Any]:
        updated = self.domain.opportunities.transition_pursuit(
            tenant_id=tenant_id, pursuit_ref=pursuit_ref,
            new_state=state, decided_by=actor_subject,
        )
        return {"tool": "update_pursuit_state", "receipt": updated}

    def _link_opportunity(
        self, *, tenant_id: UUID, actor_subject: str,
        workspace_id: str, opportunity_ref: str,
    ) -> dict[str, Any]:
        """Link an opportunity to an existing workspace (by workspace_id).

        The workspace link is represented by a pursuit created inside the
        workspace (workspace_ref set). The pursuit starts QUALIFIED when
        the opportunity is being worked, DECISION_REVIEW otherwise.
        """
        workspace = self.domain.opportunities.get_workspace(
            tenant_id=tenant_id, workspace_id=UUID(workspace_id)
        )
        if workspace is None:
            raise ToolExecutionError(f"workspace {workspace_id!r} not found")
        pursuit_ref = f"prs_{opportunity_ref}"
        pursuit_id = self.domain.opportunities.create_pursuit(
            tenant_id=tenant_id, pursuit_ref=pursuit_ref,
            opportunity_ref=opportunity_ref, state="QUALIFIED",
            created_by=actor_subject, workspace_ref=UUID(workspace_id),
        )
        return {
            "tool": "link_opportunity_to_workspace",
            "receipt": {
                "pursuit_ref": pursuit_ref, "pursuit_id": str(pursuit_id),
                "workspace_id": workspace_id,
                "workspace_title": workspace.get("title"),
                "state": "QUALIFIED",
            },
        }

    def _add_to_workspace(
        self, *, tenant_id: UUID, actor_subject: str,
        workspace_title: str, opportunity_refs: list[str],
    ) -> dict[str, Any]:
        """Add one or more opportunities to a workspace resolved by title.

        If the workspace does not exist it is created (title-scoped);
        each opportunity becomes a pursuit linked to the workspace.
        """
        workspace = self.domain.opportunities.get_workspace_by_title(
            tenant_id=tenant_id, title=workspace_title
        )
        workspace_id = workspace["workspace_id"] if workspace else None
        if workspace_id is None:
            workspace_id = uuid4()
            self.domain.opportunities.create_workspace(
                tenant_id=tenant_id, workspace_id=workspace_id,
                pursuit_ref=f"prs_{opportunity_refs[0]}",
                opportunity_ref=opportunity_refs[0],
                opportunity_version_digest="sha256:" + "0" * 64,
                subscriber_profile_version="v1",
                assessment_version="v1",
                created_by=actor_subject, title=workspace_title,
            )
        receipts = []
        for ref in opportunity_refs:
            opportunity = self.domain.opportunities.get_opportunity(
                tenant_id=tenant_id, opportunity_ref=ref
            )
            if opportunity is None:
                raise ToolExecutionError(f"opportunity {ref!r} not found")
            pursuit_ref = f"prs_{ref}"
            existing = self.domain.opportunities.get_pursuit(
                tenant_id=tenant_id, pursuit_ref=pursuit_ref
            )
            if existing is not None:
                # Idempotent: the pursuit is already linked to a workspace.
                receipts.append({
                    "opportunity_ref": ref,
                    "pursuit_ref": pursuit_ref,
                    "pursuit_id": str(existing["pursuit_id"]),
                    "already_linked": True,
                    "workspace_ref": str(existing["workspace_ref"])
                    if existing.get("workspace_ref") else str(workspace_id),
                })
                continue
            pursuit_id = self.domain.opportunities.create_pursuit(
                tenant_id=tenant_id, pursuit_ref=pursuit_ref,
                opportunity_ref=ref, state="QUALIFIED",
                created_by=actor_subject, workspace_ref=workspace_id,
            )
            receipts.append({
                "opportunity_ref": ref,
                "pursuit_ref": pursuit_ref,
                "pursuit_id": str(pursuit_id),
            })
        return {
            "tool": "add_to_workspace",
            "receipt": {
                "workspace_id": str(workspace_id),
                "workspace_title": workspace_title,
                "added": receipts,
            },
        }

    def _create_task(
        self, *, tenant_id: UUID, actor_subject: str, workspace_id: str,
        title: str, assignee: str | None = None, due_at: str | None = None,
    ) -> dict[str, Any]:
        task_ref = "task_" + uuid4().hex[:10]
        self.domain.bid_workspace.add_task(
            tenant_id=tenant_id, workspace_id=UUID(workspace_id),
            task_ref=task_ref, title=title, owner=assignee or actor_subject,
            due_at=due_at, created_by=actor_subject,
        )
        return {"tool": "create_task",
                "receipt": {"task_ref": task_ref, "title": title,
                            "owner": assignee or actor_subject}}

    def _update_priority(
        self, *, tenant_id: UUID, actor_subject: str,
        pursuit_ref: str, priority: str,
    ) -> dict[str, Any]:
        # Priority is a first-class pursuit field (HIGH/MEDIUM/LOW).
        updated = self.domain.opportunities.set_pursuit_priority(
            tenant_id=tenant_id, pursuit_ref=pursuit_ref, priority=priority,
        )
        return {"tool": "update_internal_priority", "receipt": updated}

    def _save_search(
        self, *, tenant_id: UUID, actor_subject: str, name: str, query_json: dict
    ) -> dict[str, Any]:
        self.domain.opportunities.add_portfolio_item(
            tenant_id=tenant_id, item_ref=name, opportunity_ref=str(query_json),
            library_id="O01",
        )
        return {"tool": "save_search", "receipt": {"search_name": name, "stored": True}}

    def _record_outcome(
        self, *, tenant_id: UUID, actor_subject: str, pursuit_ref: str,
        outcome: str, notes: str | None = None,
    ) -> dict[str, Any]:
        from datetime import UTC, datetime

        outcome_ref = "out_" + uuid4().hex[:10]
        self.domain.opportunities.create_outcome(
            tenant_id=tenant_id, outcome_ref=outcome_ref,
            pursuit_ref=pursuit_ref, result=outcome,
            decided_at=datetime.now(UTC), evidence_refs=[],
            notes=notes,
        )
        return {"tool": "record_outcome",
                "receipt": {"outcome_ref": outcome_ref, "result": outcome}}

    def _record_bid_no_bid(
        self, *, tenant_id: UUID, actor_subject: str,
        pursuit_ref: str, decision: str,
    ) -> dict[str, Any]:
        self.domain.opportunities.transition_pursuit(
            tenant_id=tenant_id, pursuit_ref=pursuit_ref,
            new_state="ACTIVE" if decision == "BID" else "WITHDRAWN",
            decided_by=actor_subject,
        )
        return {"tool": "record_bid_no_bid",
                "receipt": {"pursuit_ref": pursuit_ref, "decision": decision}}

    def _dismiss_opportunity(
        self, *, tenant_id: UUID, actor_subject: str,
        opportunity_ref: str,
    ) -> dict[str, Any]:
        """Dismiss an opportunity (no-bid): canonical qualification NO_BID."""
        self.domain.opportunities.record_qualification(
            tenant_id=tenant_id, opportunity_ref=opportunity_ref,
            decision="NO_BID", decided_by=actor_subject,
        )
        return {
            "tool": "dismiss_opportunity",
            "receipt": {"opportunity_ref": opportunity_ref, "state": "CLOSED"},
        }
