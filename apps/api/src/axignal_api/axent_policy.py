from __future__ import annotations

from collections.abc import Iterable
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
    policy: str
    reasons: tuple[str, ...]


READ_TOOLS = frozenset(
    {
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
    }
)

LOW_RISK_TOOLS = frozenset(
    {
        "rename_support_conversation",
        "reopen_support_case",
        "create_support_case",
        "attach_context_to_case",
    }
)

CONFIRMATION_TOOLS = frozenset(
    {
        "cancel_subscription_at_period_end",
        "remove_team_member",
        "change_billing_contact",
        "disable_alert",
        "archive_workspace",
        "revoke_integration",
    }
)

HUMAN_ONLY_TOOLS = frozenset(
    {
        "issue_refund",
        "modify_entitlement",
        "approve_legal_decision",
        "approve_privacy_decision",
        "admit_source",
        "alter_canonical_evidence",
        "irreversible_delete",
        "resolve_contract_dispute",
        "declare_security_breach",
        "close_critical_incident",
    }
)

WRITE_ROLES = frozenset(
    {"ORG_OWNER", "ORG_ADMIN", "B2G_MANAGER", "RESEARCH_OPERATOR"}
)


def decide_tool(
    *,
    tool_name: str,
    role_ids: Iterable[str],
    entitlement_state: str | None,
    assurance_level: str | None,
    confirmed: bool = False,
) -> PolicyResult:
    roles = frozenset(role_ids)
    active = entitlement_state == "ACTIVE"

    if tool_name in HUMAN_ONLY_TOOLS:
        return PolicyResult(
            AxentDecision.ESCALATE,
            "axent.human-only/v1",
            ("human_authority_required",),
        )
    if tool_name in READ_TOOLS:
        return PolicyResult(
            AxentDecision.ALLOW_READ,
            "axent.read/v1",
            ("tenant_scoped_read",),
        )
    if tool_name in LOW_RISK_TOOLS:
        if not active or not roles.intersection(WRITE_ROLES):
            return PolicyResult(
                AxentDecision.DENY,
                "axent.low-risk-write/v1",
                ("active_entitlement_and_write_role_required",),
            )
        return PolicyResult(
            AxentDecision.ALLOW,
            "axent.low-risk-write/v1",
            ("reversible_low_risk_action",),
        )
    if tool_name in CONFIRMATION_TOOLS:
        if not active or "ORG_OWNER" not in roles:
            return PolicyResult(
                AxentDecision.DENY,
                "axent.material-action/v1",
                ("owner_and_active_entitlement_required",),
            )
        if assurance_level not in {"AAL2", "PHISHING_RESISTANT"}:
            return PolicyResult(
                AxentDecision.REQUIRE_STEP_UP_AUTH,
                "axent.material-action/v1",
                ("step_up_auth_required",),
            )
        if not confirmed:
            return PolicyResult(
                AxentDecision.ALLOW_WITH_CONFIRMATION,
                "axent.material-action/v1",
                ("explicit_confirmation_required",),
            )
        return PolicyResult(
            AxentDecision.ALLOW,
            "axent.material-action/v1",
            ("confirmation_and_authority_current",),
        )
    return PolicyResult(
        AxentDecision.DENY,
        "axent.default-deny/v1",
        ("tool_not_allowlisted",),
    )
