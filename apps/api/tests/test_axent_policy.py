from axignal_api.axent_policy import AxentDecision, decide_tool


def test_read_tool_is_tenant_scoped_read() -> None:
    result = decide_tool(
        tool_name="get_my_plan",
        role_ids=("ORG_MEMBER",),
        entitlement_state="ACTIVE",
        assurance_level="AAL1",
    )
    assert result.decision is AxentDecision.ALLOW_READ


def test_unknown_tool_is_denied() -> None:
    result = decide_tool(
        tool_name="execute_sql",
        role_ids=("ORG_OWNER",),
        entitlement_state="ACTIVE",
        assurance_level="PHISHING_RESISTANT",
    )
    assert result.decision is AxentDecision.DENY
    assert "tool_not_allowlisted" in result.reasons


def test_human_only_tool_escalates() -> None:
    result = decide_tool(
        tool_name="modify_entitlement",
        role_ids=("ORG_OWNER",),
        entitlement_state="ACTIVE",
        assurance_level="PHISHING_RESISTANT",
    )
    assert result.decision is AxentDecision.ESCALATE


def test_material_action_requires_owner_step_up_and_confirmation() -> None:
    denied = decide_tool(
        tool_name="cancel_subscription_at_period_end",
        role_ids=("ORG_ADMIN",),
        entitlement_state="ACTIVE",
        assurance_level="PHISHING_RESISTANT",
    )
    assert denied.decision is AxentDecision.DENY

    step_up = decide_tool(
        tool_name="cancel_subscription_at_period_end",
        role_ids=("ORG_OWNER",),
        entitlement_state="ACTIVE",
        assurance_level="AAL1",
    )
    assert step_up.decision is AxentDecision.REQUIRE_STEP_UP_AUTH

    confirm = decide_tool(
        tool_name="cancel_subscription_at_period_end",
        role_ids=("ORG_OWNER",),
        entitlement_state="ACTIVE",
        assurance_level="PHISHING_RESISTANT",
    )
    assert confirm.decision is AxentDecision.ALLOW_WITH_CONFIRMATION

    allowed = decide_tool(
        tool_name="cancel_subscription_at_period_end",
        role_ids=("ORG_OWNER",),
        entitlement_state="ACTIVE",
        assurance_level="PHISHING_RESISTANT",
        confirmed=True,
    )
    assert allowed.decision is AxentDecision.ALLOW
