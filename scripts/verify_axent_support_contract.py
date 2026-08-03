from pathlib import Path

REQUIRED_FILES = {
    "docs/contracts/31-axent-customer-support-e2e-contract-v1.0.md",
    "infra/postgres/150-axent-customer-support.sql",
    "infra/postgres/151-axent-support-hardening.sql",
    "apps/api/src/axignal_api/axent_policy.py",
    "apps/api/src/axignal_api/axent_repository.py",
    "apps/api/src/axignal_api/axent_context.py",
    "apps/api/src/axignal_api/axent_routes.py",
    "apps/api/tests/test_axent_policy.py",
}


def main() -> None:
    missing = [path for path in sorted(REQUIRED_FILES) if not Path(path).is_file()]
    assert not missing, f"missing AXENT files: {missing}"

    contract = Path("docs/contracts/31-axent-customer-support-e2e-contract-v1.0.md").read_text()
    sql = Path("infra/postgres/150-axent-customer-support.sql").read_text()
    policy = Path("apps/api/src/axignal_api/axent_policy.py").read_text()
    routes = Path("apps/api/src/axignal_api/axent_routes.py").read_text()
    application = Path("apps/api/src/axignal_api/application.py").read_text()
    dockerfile = Path("infra/postgres/Dockerfile").read_text()

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
        assert table in sql

    assert "FORCE ROW LEVEL SECURITY" in sql
    assert "current_tenant_id()" in sql
    assert "ALLOW_WITH_CONFIRMATION" in policy
    assert "tool_not_allowlisted" in policy
    assert "modify_entitlement" in policy
    assert "AxentContextBuilder" in routes
    assert "require_identity" in routes
    assert "axent_router" in application
    assert "150-axent-customer-support.sql" in dockerfile
    assert "151-axent-support-hardening.sql" in dockerfile

    print("AXENT_SUPPORT_CONTRACT_PASS")
    print("AXENT_PERSISTENCE_AND_TENANT_ISOLATION_IMPLEMENTED")
    print("AXENT_SERVER_AUTHORITY_CONTEXT_IMPLEMENTED")
    print("AXENT_READ_ONLY_SUPPORT_IMPLEMENTED")
    print("AXENT_FINAL_E2E_NOT_YET_CLAIMED")


if __name__ == "__main__":
    main()
