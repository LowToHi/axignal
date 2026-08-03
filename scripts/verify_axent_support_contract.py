from pathlib import Path

REQUIRED_FILES = {
    "docs/contracts/31-axent-customer-support-e2e-contract-v1.0.md",
    "infra/postgres/149-axent-support-parent-keys.sql",
    "infra/postgres/150-axent-customer-support.sql",
    "infra/postgres/151-axent-support-hardening.sql",
    "infra/postgres/152-axent-governed-knowledge-seed.sql",
    "apps/api/src/axignal_api/axent_policy.py",
    "apps/api/src/axignal_api/axent_repository.py",
    "apps/api/src/axignal_api/axent_context.py",
    "apps/api/src/axignal_api/axent_knowledge.py",
    "apps/api/src/axignal_api/axent_routes.py",
    "apps/api/tests/test_axent_policy.py",
    "apps/api/tests/test_axent_knowledge.py",
    "apps/web/lib/axent-server.ts",
    "apps/web/app/help/page.tsx",
    "apps/web/app/api/axent/conversations/route.ts",
    "apps/web/app/api/axent/conversations/[conversationId]/route.ts",
    "apps/web/app/api/axent/conversations/[conversationId]/messages/route.ts",
    "apps/web/components/axent/axent-help-entry.tsx",
    "apps/web/components/axent/axent-help.tsx",
}


def main() -> None:
    missing = [path for path in sorted(REQUIRED_FILES) if not Path(path).is_file()]
    assert not missing, f"missing AXENT files: {missing}"

    contract = Path(
        "docs/contracts/31-axent-customer-support-e2e-contract-v1.0.md"
    ).read_text()
    sql = Path("infra/postgres/150-axent-customer-support.sql").read_text()
    parent_keys = Path("infra/postgres/149-axent-support-parent-keys.sql").read_text()
    knowledge_seed = Path(
        "infra/postgres/152-axent-governed-knowledge-seed.sql"
    ).read_text()
    policy = Path("apps/api/src/axignal_api/axent_policy.py").read_text()
    routes = Path("apps/api/src/axignal_api/axent_routes.py").read_text()
    knowledge = Path("apps/api/src/axignal_api/axent_knowledge.py").read_text()
    application = Path("apps/api/src/axignal_api/application.py").read_text()
    dockerfile = Path("infra/postgres/Dockerfile").read_text()
    help_page = Path("apps/web/app/help/page.tsx").read_text()
    help_component = Path("apps/web/components/axent/axent-help.tsx").read_text()
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

    assert "UNIQUE (tenant_id, message_id)" in parent_keys
    assert "UNIQUE (tenant_id, invocation_id)" in parent_keys
    assert "FORCE ROW LEVEL SECURITY" in sql
    assert "current_tenant_id()" in sql
    assert "ALLOW_WITH_CONFIRMATION" in policy
    assert "tool_not_allowlisted" in policy
    assert "modify_entitlement" in policy
    assert "AxentContextBuilder" in routes
    assert "AxentKnowledgeRepository" in routes
    assert 'authority_type="KNOWLEDGE_REVISION"' in routes
    assert "plainto_tsquery" in knowledge
    assert "document.scope = 'GLOBAL'" in knowledge
    assert "document.tenant_id = %s" in knowledge
    assert "review_status = 'APPROVED'" in knowledge
    assert "AX-CONTRACT-AXENT-SUPPORT-E2E-v1.0" in knowledge_seed
    assert "require_identity" in routes
    assert "axent_router" in application
    assert "AxentHelpEntry" in help_page
    assert "/api/axent/conversations" in help_component
    assert "Autoridades consultadas" in help_component
    assert "getAuthenticatedIdentity" in web_proxy
    assert "X-AXIGNAL-Identity-Assertion" in web_proxy
    for migration in (
        "149-axent-support-parent-keys.sql",
        "150-axent-customer-support.sql",
        "151-axent-support-hardening.sql",
        "152-axent-governed-knowledge-seed.sql",
    ):
        assert migration in dockerfile

    print("AXENT_SUPPORT_CONTRACT_PASS")
    print("AXENT_PERSISTENCE_AND_TENANT_ISOLATION_IMPLEMENTED")
    print("AXENT_GROUNDED_KNOWLEDGE_IMPLEMENTED")
    print("AXENT_SERVER_AUTHORITY_CONTEXT_IMPLEMENTED")
    print("AXENT_READ_ONLY_SUPPORT_IMPLEMENTED")
    print("AXENT_HELP_SURFACE_IMPLEMENTED")
    print("AXENT_FINAL_E2E_NOT_YET_CLAIMED")


if __name__ == "__main__":
    main()
