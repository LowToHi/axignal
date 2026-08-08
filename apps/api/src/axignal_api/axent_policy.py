"""AXENT policy engine (Mandato AXENT — secciones 8.7, 15).

Classifies every tool as READ / LOW_RISK_REVERSIBLE /
EXPLICIT_CONFIRMATION / STEP_UP_REQUIRED / HUMAN_ONLY / DENY.
The model cannot expand tools or authority; the policy is deterministic.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class AxentDecision(StrEnum):
    ALLOW_READ = "ALLOW_READ"
    ALLOW = "ALLOW"
    ALLOW_WITH_CONFIRMATION = "ALLOW_WITH_CONFIRMATION"
    REQUIRE_STEP_UP_AUTH = "REQUIRE_STEP_UP_AUTH"
    ESCALATE = "ESCALATE"
    DENY = "DENY"


@dataclass(frozen=True)
class PolicyResult:
    decision: AxentDecision
    risk_class: str
    reasons: tuple[str, ...]


# Read tools: authorised + tenant-scoped, no extra confirmation.
READ_TOOLS = frozenset(
    {
        "search_opportunities", "get_opportunity", "get_opportunity_evidence",
        "get_opportunity_claims", "get_opportunity_changes",
        "compare_opportunities", "explain_opportunity_match",
        "get_source_status", "get_coverage", "list_workspaces",
        "get_workspace", "list_workspace_opportunities", "get_pursuit",
        "list_pursuits", "get_requirements", "get_missing_evidence",
        "get_tasks", "get_deadlines", "get_outcomes", "get_similar_outcomes",
        "get_recent_changes", "get_my_identity", "get_my_plan",
        "get_my_entitlements", "get_seat_summary", "get_subscription_status",
        "get_invoice_status", "get_research_run_status", "get_workspace_status",
        "list_my_documents", "list_my_exports", "get_active_incidents",
    }
)

# Low-risk reversible: explicit user order, no preview required.
LOW_RISK_TOOLS = frozenset(
    {
        "save_search", "update_saved_search", "archive_saved_search",
        "update_tags", "update_internal_priority", "add_user_note",
        "create_note", "archive_note", "create_task", "update_task",
        "create_alert", "update_alert_preferences", "create_evidence_request",
        "link_opportunity_to_workspace", "rename_support_conversation",
        "attach_context_to_case",
    }
)

# Explicit confirmation: preview required (before-state hash + parameters hash).
CONFIRMATION_TOOLS = frozenset(
    {
        "create_workspace", "create_pursuit", "update_pursuit_state",
        "record_bid_no_bid", "assign_pursuit_owner", "unlink_opportunity_from_workspace",
        "close_pursuit", "reopen_pursuit", "archive_workspace",
        "restore_workspace", "dismiss_opportunity", "record_outcome",
        "assign_task", "create_support_case", "add_to_workspace",
    }
)

# Step-up: AAL2/passkey required.
STEP_UP_TOOLS = frozenset(
    {
        "update_workspace_metadata", "archive_workspace_force",
        "manage_team_members", "manage_integrations",
        "billing_change_plan", "billing_cancel_subscription",
        "recover_tenant_access", "revoke_session",
    }
)

# Human-only: never executable by the assistant.
HUMAN_ONLY_TOOLS = frozenset(
    {
        "submit_official_bid", "approve_legal_compliance",
        "declare_contractual_eligibility", "alter_canonical_evidence",
        "admit_source", "approve_privacy_decision",
        "issue_discretionary_refund", "declare_security_breach",
        "close_critical_incident",
    }
)

# Hard-denied tool names (attempted injection).
DENIED_TOOLS = frozenset(
    {
        "run_sql", "exec_shell", "drop_table", "update_canonical_claims",
        "delete_evidence", "grant_tenant_role", "assign_seat",
        "grant_trial", "publish_seo_page", "mutate_search_console",
        "install_mcp_connector", "authorize_public_launch",
    }
)


class AxentPolicyEngine:
    def classify(self, tool_name: str) -> PolicyResult:
        if tool_name in DENIED_TOOLS:
            return PolicyResult(AxentDecision.DENY, "DENY", ("hard-denied tool",))
        if tool_name in HUMAN_ONLY_TOOLS:
            return PolicyResult(AxentDecision.ESCALATE, "HUMAN_ONLY", ("human authority required",))
        if tool_name in STEP_UP_TOOLS:
            return PolicyResult(
                AxentDecision.REQUIRE_STEP_UP_AUTH, "STEP_UP_REQUIRED",
                ("AAL2 or passkey required",),
            )
        if tool_name in CONFIRMATION_TOOLS:
            return PolicyResult(
                AxentDecision.ALLOW_WITH_CONFIRMATION, "EXPLICIT_CONFIRMATION",
                ("preview + explicit confirmation required",),
            )
        if tool_name in LOW_RISK_TOOLS:
            return PolicyResult(AxentDecision.ALLOW, "LOW_RISK_REVERSIBLE", ())
        if tool_name in READ_TOOLS:
            return PolicyResult(AxentDecision.ALLOW_READ, "READ", ())
        return PolicyResult(AxentDecision.DENY, "DENY", ("unknown tool",))

    def decision_for(
        self, tool_name: str, *, assurance_level: str = "AAL1"
    ) -> PolicyResult:
        result = self.classify(tool_name)
        if result.decision == AxentDecision.REQUIRE_STEP_UP_AUTH:
            if assurance_level in ("AAL2", "AAL3"):
                # Step-up satisfied: the underlying risk is confirmation-class.
                return PolicyResult(
                    AxentDecision.ALLOW_WITH_CONFIRMATION, result.risk_class,
                    ("AAL2 verified; preview + confirmation required",),
                )
            return PolicyResult(
                AxentDecision.REQUIRE_STEP_UP_AUTH, result.risk_class,
                ("AAL2 required; current assurance " + assurance_level,),
            )
        return result


POLICY_VERSION = "axent-policy-v1"
