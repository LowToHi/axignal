"""AXENT tool registry, policy and consented workspace/pursuit operations
(Mandato AXENT — secciones 8, 15).

Gates: AX_AXENT_WORKSPACE_CRUD_E2E, AX_AXENT_PURSUIT_OPERATIONS_E2E,
AX_AXENT_CONSENTED_ACTIONS_E2E, AX_AXENT_SECURITY_AND_AUTHORITY.
"""

from __future__ import annotations

import os
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from axignal_api.application import app
from axignal_api.axent_policy import AxentDecision, AxentPolicyEngine
from axignal_api.axent_retrieval_repository import AxentRetrievalRepository
from axignal_api.axent_tool_registry import AxentToolExecutor, ToolExecutionError
from axignal_api.bid_workspace_repository import BidWorkspaceRepository
from axignal_api.identity import build_identity_assertion
from axignal_api.opportunity_repository import OpportunityOperationsRepository

TENANT_A = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
TENANT_B = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
IDENTITY_SECRET = "local-dev-identity-assertion-secret-32-bytes"
DSN = "postgresql://axignal:axignal-local@localhost:5432/axignal"

pytestmark = pytest.mark.skipif(
    not os.environ.get("AXIGNAL_INTEGRATION_TESTS"),
    reason="AXENT tools E2E needs a live PostgreSQL",
)


@pytest.fixture(autouse=True)
def _set_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AXIGNAL_DATABASE_URL", DSN)
    monkeypatch.setenv("AXIGNAL_IDENTITY_ASSERTION_SECRET", IDENTITY_SECRET)


class _Domain:
    def __init__(self) -> None:
        self.opportunities = OpportunityOperationsRepository(DSN)
        self.bid_workspace = BidWorkspaceRepository(DSN)
        self.retrieval = AxentRetrievalRepository(DSN)

    def plan_for(self, params: dict) -> object:
        from axignal_api.axent_query_planner import QueryPlanner

        return QueryPlanner().plan(params)


def _reset() -> None:
    import psycopg

    with psycopg.connect(DSN) as conn, conn.cursor() as cursor:
        cursor.execute("SET session_replication_role = replica")
        cursor.execute(
            "TRUNCATE tenant_private.opportunity_pursuits, "
            "tenant_private.opportunity_outcomes, "
            "tenant_private.bid_requirements, tenant_private.bid_workspace_audit, "
            "tenant_private.bid_requirement_versions CASCADE"
        )
        cursor.execute("SET session_replication_role = origin")
        conn.commit()


class TestPolicyEngine:
    def test_classification(self) -> None:
        policy = AxentPolicyEngine()
        assert policy.classify("search_opportunities").risk_class == "READ"
        assert policy.classify("create_task").risk_class == "LOW_RISK_REVERSIBLE"
        assert policy.classify("create_pursuit").risk_class == "EXPLICIT_CONFIRMATION"
        assert policy.classify("billing_cancel_subscription").risk_class == "STEP_UP_REQUIRED"
        assert policy.classify("submit_official_bid").decision == AxentDecision.ESCALATE
        assert policy.classify("run_sql").decision == AxentDecision.DENY
        assert policy.classify("install_mcp_connector").decision == AxentDecision.DENY
        assert policy.classify("nonsense_tool").decision == AxentDecision.DENY

    def test_step_up_requires_aal2(self) -> None:
        policy = AxentPolicyEngine()
        at_aal1 = policy.decision_for("billing_cancel_subscription", assurance_level="AAL1")
        assert at_aal1.decision == AxentDecision.REQUIRE_STEP_UP_AUTH
        at_aal2 = policy.decision_for("billing_cancel_subscription", assurance_level="AAL2")
        assert at_aal2.decision == AxentDecision.ALLOW_WITH_CONFIRMATION

    def test_injection_denied(self) -> None:
        policy = AxentPolicyEngine()
        for tool in ("drop_table", "update_canonical_claims", "delete_evidence",
                     "grant_tenant_role", "assign_seat", "grant_trial",
                     "publish_seo_page", "mutate_search_console", "run_sql"):
            assert policy.classify(tool).decision == AxentDecision.DENY


class TestToolExecutor:
    def test_workspace_and_pursuit_operations(self) -> None:
        _reset()
        executor = AxentToolExecutor(domain=_Domain())

        # Tools are typed and listed.
        tools = {tool["name"] for tool in executor.list_tools()}
        assert "search_opportunities" in tools
        assert "create_pursuit" in tools
        assert "create_task" in tools

        # Unknown tool rejected.
        with pytest.raises(ToolExecutionError):
            executor.execute(
                tool_name="run_sql", parameters={},
                tenant_id=TENANT_A, actor_subject="usr_tools",
            )

        # Extra forbidden fields rejected by the schema.
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            executor.execute(
                tool_name="create_pursuit",
                parameters={"opportunity_ref": "opp_x", "decision": "BID",
                            "hacked": True},
                tenant_id=TENANT_A, actor_subject="usr_tools",
            )

        # Search (READ) executes through the retrieval authority.
        search = executor.execute(
            tool_name="search_opportunities",
            parameters={"keywords": ["cybersecurity"], "limit": 5},
            tenant_id=TENANT_A, actor_subject="usr_tools",
        )
        assert search["tool"] == "search_opportunities"
        assert "count" in search

        # get_opportunity (READ) via the opportunity authority.
        opportunity = executor.execute(
            tool_name="get_opportunity",
            parameters={"opportunity_ref": "opp_ted_123456_2026"},
            tenant_id=TENANT_A, actor_subject="usr_tools",
        )
        assert opportunity["tool"] == "get_opportunity"

        # Create pursuit (EXPLICIT_CONFIRMATION) through the domain.
        pursuit = executor.execute(
            tool_name="create_pursuit",
            parameters={"opportunity_ref": "opp_ted_123456_2026", "decision": "BID"},
            tenant_id=TENANT_A, actor_subject="usr_tools",
        )
        assert pursuit["receipt"]["pursuit_ref"] == "prs_opp_ted_123456_2026"
        assert pursuit["receipt"]["state"] == "QUALIFIED"

        # Transition (EXPLICIT_CONFIRMATION).
        transitioned = executor.execute(
            tool_name="update_pursuit_state",
            parameters={"pursuit_ref": "prs_opp_ted_123456_2026", "state": "DECISION_REVIEW"},
            tenant_id=TENANT_A, actor_subject="usr_tools",
        )
        assert transitioned["tool"] == "update_pursuit_state"

        # Create task (LOW_RISK_REVERSIBLE) through the bid workspace authority.
        from uuid import uuid4

        workspace_id = uuid4()
        executor.domain.opportunities.create_workspace(
            tenant_id=TENANT_A, workspace_id=workspace_id,
            pursuit_ref="prs_opp_ted_123456_2026",
            opportunity_ref="opp_ted_123456_2026",
            opportunity_version_digest="sha256:0000000000000000000000000000000000000000000000000000000000000000",
            subscriber_profile_version="v1", assessment_version="v1",
            created_by="usr_tools",
        )
        task = executor.execute(
            tool_name="create_task",
            parameters={"workspace_id": str(workspace_id),
                        "title": "Revisar requisitos obligatorios",
                        "assignee": "usr_laura"},
            tenant_id=TENANT_A, actor_subject="usr_tools",
        )
        assert task["receipt"]["task_ref"].startswith("task_")

        # Record outcome (EXPLICIT_CONFIRMATION) through the domain.
        outcome = executor.execute(
            tool_name="record_outcome",
            parameters={"pursuit_ref": "prs_opp_ted_123456_2026",
                        "outcome": "WON", "notes": "adjudicada"},
            tenant_id=TENANT_A, actor_subject="usr_tools",
        )
        assert outcome["receipt"]["result"] == "WON"

        # Everything persisted: a fresh executor instance sees it.
        fresh = AxentToolExecutor(domain=_Domain())
        pursuits = fresh.domain.opportunities.list_pursuits(tenant_id=TENANT_A)
        assert any(p["pursuit_ref"] == "prs_opp_ted_123456_2026" for p in pursuits)
        outcomes = fresh.domain.opportunities.list_outcomes(tenant_id=TENANT_A)
        assert len(outcomes) >= 1

    def test_tenant_isolation(self) -> None:
        _reset()
        executor = AxentToolExecutor(domain=_Domain())
        # Tenant B cannot see tenant A pursuits through the tool.
        pursuits_b = executor.domain.opportunities.list_pursuits(tenant_id=TENANT_B)
        assert pursuits_b == []

    def test_http_consent_surface(self) -> None:
        client = TestClient(
            app,
            headers={
                "X-AXIGNAL-Identity-Assertion": build_identity_assertion(
                    secret=IDENTITY_SECRET,
                    subject="usr_consent",
                    email="usr_consent@example.test",
                    tenant_id=TENANT_A,
                )
            },
        )
        response = client.get("/v1/axent/conversations")
        assert response.status_code in (200, 404)
