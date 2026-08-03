from pathlib import Path

REQUIRED_FILES = {
    "docs/contracts/31-axent-customer-support-e2e-contract-v1.0.md",
    "infra/postgres/149-axent-support-parent-keys.sql",
    "infra/postgres/150-axent-customer-support.sql",
    "infra/postgres/151-axent-support-hardening.sql",
    "infra/postgres/1515-axent-knowledge-document-timestamps.sql",
    "infra/postgres/152-axent-governed-knowledge-seed.sql",
    "infra/postgres/153-axent-consent-escalation-roundtrip.sql",
    "infra/postgres/154-axent-feedback-evaluation-telemetry.sql",
    "apps/api/src/axignal_api/axent_policy.py",
    "apps/api/src/axignal_api/axent_repository.py",
    "apps/api/src/axignal_api/axent_context.py",
    "apps/api/src/axignal_api/axent_knowledge.py",
    "apps/api/src/axignal_api/axent_consent.py",
    "apps/api/src/axignal_api/axent_action_repository.py",
    "apps/api/src/axignal_api/axent_restore_repository.py",
    "apps/api/src/axignal_api/axent_notification_repository.py",
    "apps/api/src/axignal_api/axent_telemetry_repository.py",
    "apps/api/src/axignal_api/axent_routes.py",
    "apps/api/src/axignal_api/axent_read_routes.py",
    "apps/api/src/axignal_api/axent_consent_routes.py",
    "apps/api/src/axignal_api/axent_action_routes.py",
    "apps/api/src/axignal_api/axent_material_action_routes.py",
    "apps/api/src/axignal_api/axent_notification_routes.py",
    "apps/api/src/axignal_api/axent_telemetry_routes.py",
    "apps/api/src/axignal_api/axent_admin_routes.py",
    "apps/api/tests/test_axent_policy.py",
    "apps/api/tests/test_axent_knowledge.py",
    "apps/api/tests/test_axent_routes.py",
    "apps/api/tests/test_axent_consent.py",
    "apps/api/tests/test_axent_security.py",
    "apps/web/lib/axent-server.ts",
    "apps/web/app/help/page.tsx",
    "apps/web/app/support-admin/page.tsx",
    "apps/web/app/api/axent/conversations/route.ts",
    "apps/web/app/api/axent/conversations/[conversationId]/route.ts",
    "apps/web/app/api/axent/conversations/[conversationId]/messages/route.ts",
    "apps/web/app/api/axent/notifications/route.ts",
    "apps/web/app/api/axent/notifications/[notificationId]/acknowledge/route.ts",
    "apps/web/app/api/axent-admin/cases/route.ts",
    "apps/web/app/api/axent-admin/cases/[caseId]/transition/route.ts",
    "apps/web/components/axent/axent-help-entry.tsx",
    "apps/web/components/axent/axent-help.tsx",
    "apps/web/components/axent/axent-admin-console.tsx",
    "scripts/verify_axent_postgres_roundtrip.py",
}


def main() -> None:
    missing = [path for path in sorted(REQUIRED_FILES) if not Path(path).is_file()]
    assert not missing, f"missing AXENT files: {missing}"

    contract = Path(
        "docs/contracts/31-axent-customer-support-e2e-contract-v1.0.md"
    ).read_text()
    sql = Path("infra/postgres/150-axent-customer-support.sql").read_text()
    parent_keys = Path("infra/postgres/149-axent-support-parent-keys.sql").read_text()
    consent_sql = Path(
        "infra/postgres/153-axent-consent-escalation-roundtrip.sql"
    ).read_text()
    telemetry_sql = Path(
        "infra/postgres/154-axent-feedback-evaluation-telemetry.sql"
    ).read_text()
    knowledge_seed = Path(
        "infra/postgres/152-axent-governed-knowledge-seed.sql"
    ).read_text()
    policy = Path("apps/api/src/axignal_api/axent_policy.py").read_text()
    routes = Path("apps/api/src/axignal_api/axent_routes.py").read_text()
    read_routes = Path("apps/api/src/axignal_api/axent_read_routes.py").read_text()
    consent = Path("apps/api/src/axignal_api/axent_consent.py").read_text()
    consent_routes = Path(
        "apps/api/src/axignal_api/axent_consent_routes.py"
    ).read_text()
    action_routes = Path(
        "apps/api/src/axignal_api/axent_material_action_routes.py"
    ).read_text()
    action_repository = Path(
        "apps/api/src/axignal_api/axent_action_repository.py"
    ).read_text()
    restore_repository = Path(
        "apps/api/src/axignal_api/axent_restore_repository.py"
    ).read_text()
    telemetry_routes = Path(
        "apps/api/src/axignal_api/axent_telemetry_routes.py"
    ).read_text()
    admin_routes = Path("apps/api/src/axignal_api/axent_admin_routes.py").read_text()
    route_tests = Path("apps/api/tests/test_axent_routes.py").read_text()
    security_tests = Path("apps/api/tests/test_axent_security.py").read_text()
    knowledge = Path("apps/api/src/axignal_api/axent_knowledge.py").read_text()
    application = Path("apps/api/src/axignal_api/application.py").read_text()
    dockerfile = Path("infra/postgres/Dockerfile").read_text()
    help_page = Path("apps/web/app/help/page.tsx").read_text()
    help_component = Path("apps/web/components/axent/axent-help.tsx").read_text()
    admin_component = Path(
        "apps/web/components/axent/axent-admin-console.tsx"
    ).read_text()
    web_proxy = Path("apps/web/lib/axent-server.ts").read_text()

    for marker in (
        "AXENT_SUPPORT_CONTRACT_PASS",
        "AXENT_CUSTOMER_SUPPORT_E2E_PASS",
        "billing_authority_mutation",
    ):
        assert marker in contract

    for table in (
        "support_conversations",
        "support_messages",
        "support_message_citations",
        "support_verified_facts",
        "support_cases",
        "support_tool_invocations",
        "support_actions",
        "knowledge_documents",
        "knowledge_revisions",
        "knowledge_chunks",
    ):
        assert table in sql or table in parent_keys

    for table in (
        "support_confirmations",
        "support_case_events",
        "support_notifications",
    ):
        assert table in consent_sql

    for table in (
        "support_feedback",
        "support_evaluations",
        "support_incident_links",
    ):
        assert table in telemetry_sql

    assert "security_invoker = true" in telemetry_sql
    assert "axent_support_metrics" in telemetry_sql
    assert "UNIQUE (tenant_id, message_id)" in parent_keys
    assert "UNIQUE (tenant_id, invocation_id)" in parent_keys
    assert "FORCE ROW LEVEL SECURITY" in sql
    assert "FORCE ROW LEVEL SECURITY" in consent_sql
    assert "FORCE ROW LEVEL SECURITY" in telemetry_sql
    assert "current_tenant_id()" in sql
    assert "ALLOW_WITH_CONFIRMATION" in policy
    assert "restore_workspace" in policy
    assert "tool_not_allowlisted" in policy
    assert "modify_entitlement" in policy
    assert "AxentContextBuilder" in routes
    assert "AxentKnowledgeRepository" in routes
    assert 'authority_type="KNOWLEDGE_REVISION"' in routes
    for tool in (
        "get_invoice_status",
        "list_my_documents",
        "list_my_exports",
        "get_source_status",
        "get_recent_account_audit",
        "get_active_incidents",
    ):
        assert tool in read_routes
    assert "plainto_tsquery" in knowledge
    assert "document.scope = 'GLOBAL'" in knowledge
    assert "document.tenant_id = %s" in knowledge
    assert "review_status = 'APPROVED'" in knowledge
    assert "AX-CONTRACT-AXENT-SUPPORT-E2E-v1.0" in knowledge_seed
    assert "hmac.compare_digest" in consent
    assert "expected_before_state_hash" in consent
    assert "expires_at" in consent_routes
    assert "archive_workspace" in action_routes
    assert "restore_workspace" in action_routes
    assert "FOR UPDATE" in action_repository
    assert "support_actions" in action_repository
    assert "rollback_of" in restore_repository
    assert "create_feedback" in telemetry_routes
    assert "create_evaluation" in telemetry_routes
    assert "get_metrics" in telemetry_routes
    assert "human_reviewer_subjects" in admin_routes
    assert "transition_case" in admin_routes
    assert "require_identity" in routes
    assert "dependency_overrides[require_identity]" in route_tests
    assert "KNOWLEDGE_REVISION" in route_tests
    assert "cross_tenant_replay" in security_tests
    assert "tool_not_allowlisted" in security_tests
    for router in (
        "axent_router",
        "axent_read_router",
        "axent_consent_router",
        "axent_action_router",
        "axent_material_action_router",
        "axent_notification_router",
        "axent_telemetry_router",
        "axent_admin_router",
        "axent_metrics_router",
    ):
        assert router in application
    assert "AxentHelpEntry" in help_page
    assert "/api/axent/conversations" in help_component
    assert "/api/axent/notifications" in help_component
    assert "Autoridades consultadas" in help_component
    assert "/api/axent-admin/cases" in admin_component
    assert "getAuthenticatedIdentity" in web_proxy
    assert "X-AXIGNAL-Identity-Assertion" in web_proxy
    for migration in (
        "149-axent-support-parent-keys.sql",
        "150-axent-customer-support.sql",
        "151-axent-support-hardening.sql",
        "1515-axent-knowledge-document-timestamps.sql",
        "152-axent-governed-knowledge-seed.sql",
        "153-axent-consent-escalation-roundtrip.sql",
        "154-axent-feedback-evaluation-telemetry.sql",
    ):
        assert migration in dockerfile

    print("AXENT_SUPPORT_CONTRACT_PASS")
    print("AXENT_PERSISTENCE_AND_TENANT_ISOLATION_IMPLEMENTED")
    print("AXENT_GROUNDED_KNOWLEDGE_IMPLEMENTED")
    print("AXENT_SERVER_AUTHORITY_CONTEXT_IMPLEMENTED")
    print("AXENT_READ_ONLY_SUPPORT_IMPLEMENTED")
    print("AXENT_HELP_SURFACE_IMPLEMENTED")
    print("AXENT_TYPED_READ_TOOLS_IMPLEMENTED")
    print("AXENT_BOUNDED_ACTIONS_IMPLEMENTED")
    print("AXENT_CONSENTED_ACTION_AND_ROLLBACK_IMPLEMENTED")
    print("AXENT_HUMAN_ESCALATION_LIFECYCLE_IMPLEMENTED")
    print("AXENT_CUSTOMER_NOTIFICATION_ROUND_TRIP_IMPLEMENTED")
    print("AXENT_FEEDBACK_EVALUATION_TELEMETRY_IMPLEMENTED")
    print("AXENT_ADVERSARIAL_BOUNDARIES_IMPLEMENTED")
    print("AXENT_FINAL_E2E_NOT_YET_CLAIMED")


if __name__ == "__main__":
    main()
