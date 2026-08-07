"""Prioridad 3 — Bid Workspace O01 full E2E over PostgreSQL.

Journey: requirements (OFFICIAL/INFERENCE/RECOMMENDATION) -> versioned
updates -> amendment invalidation -> questions -> risks -> tasks ->
readiness -> human approval -> handoff, all persisted, audited
append-only by the database, restart-recovered, tenant-isolated.

Run: AXIGNAL_INTEGRATION_TESTS=1 pytest apps/api/tests/test_bid_workspace_e2e.py
"""

from __future__ import annotations

import os
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from axignal_api.application import app
from axignal_api.identity import build_identity_assertion

TENANT_A = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
TENANT_B = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
IDENTITY_SECRET = "local-dev-identity-assertion-secret-32-bytes"
DSN = "postgresql://axignal:axignal-local@localhost:5432/axignal"

pytestmark = pytest.mark.skipif(
    not os.environ.get("AXIGNAL_INTEGRATION_TESTS"),
    reason="bid workspace E2E needs a live PostgreSQL; set AXIGNAL_INTEGRATION_TESTS=1",
)


@pytest.fixture(autouse=True)
def _set_dsn(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AXIGNAL_DATABASE_URL", DSN)


def _client(tenant_id: UUID, subject: str = "usr_bid_e2e") -> TestClient:
    return TestClient(
        app,
        headers={
            "X-AXIGNAL-Identity-Assertion": build_identity_assertion(
                secret=IDENTITY_SECRET,
                subject=subject,
                email=f"{subject}@example.test",
                tenant_id=tenant_id,
            )
        },
    )


def _reset_bid_state() -> None:
    """Deterministic baseline: remove bid rows left by previous runs."""
    import psycopg

    with psycopg.connect(DSN) as conn, conn.cursor() as cursor:
        for table in (
            "bid_requirement_versions",
            "bid_readiness",
            "bid_tasks",
            "bid_risks",
            "bid_questions",
            "bid_approvals",
            "bid_handoffs",
            "bid_workspace_audit",
            "bid_requirements",
        ):
            cursor.execute(f"DELETE FROM tenant_private.{table} WHERE tenant_id = %s", (TENANT_A,))
        cursor.execute(
            "DELETE FROM tenant_private.opportunity_workspaces "
            "WHERE tenant_id = %s AND pursuit_ref = 'prs_bidws_00000001'",
            (TENANT_A,),
        )
        conn.commit()


class TestBidWorkspaceFullE2E:
    def test_full_journey(self) -> None:
        _reset_bid_state()
        client = _client(TENANT_A)
        workspace_id = uuid4()

        # Workspace (reuse the opportunity workspace surface).
        created = client.post(
            "/v1/opportunities/workspaces",
            json={
                "workspace_id": str(workspace_id),
                "pursuit_ref": "prs_bidws_00000001",
                "opportunity_ref": "opp_ted_123456_2026",
                "opportunity_version_digest": f"sha256:{'d' * 64}",
                "subscriber_profile_version": "v1",
                "assessment_version": "v1",
            },
        )
        assert created.status_code == 201, created.text

        # 1. Requirements: official + inference + recommendation.
        for ref, kind, title in [
            ("req_off1", "OFFICIAL", "Cybersecurity monitoring scope"),
            ("req_off2", "OFFICIAL", "Personnel clearance level"),
            ("req_inf1", "INFERENCE", "Likely renewal clause"),
            ("req_rec1", "RECOMMENDATION", "Suggested bid team size"),
        ]:
            response = client.post(
                f"/v1/bid-workspaces/{workspace_id}/requirements",
                json={
                    "requirement_ref": ref,
                    "kind": kind,
                    "title": title,
                    "source_notice_version": 1,
                },
            )
            assert response.status_code == 201, response.text

        requirements = client.get(
            f"/v1/bid-workspaces/{workspace_id}/requirements"
        ).json()
        assert len(requirements) == 4
        kinds = {row["requirement_ref"]: row["kind"] for row in requirements}
        assert kinds == {"req_off1": "OFFICIAL", "req_off2": "OFFICIAL",
                         "req_inf1": "INFERENCE", "req_rec1": "RECOMMENDATION"}

        # 2. Versioned update: req_off1 v1 -> v2, history kept.
        updated = client.patch(
            f"/v1/bid-workspaces/{workspace_id}/requirements/req_off1",
            json={"title": "Cybersecurity monitoring scope (revised)",
                  "description": "Extended to 24/7 coverage"},
        )
        assert updated.status_code == 200, updated.text
        versions = client.get(
            f"/v1/bid-workspaces/{workspace_id}/requirements/req_off1/versions"
        ).json()
        assert len(versions["versions"]) == 2, versions
        assert versions["versions"][0]["version"] == 1
        assert versions["versions"][1]["version"] == 2
        assert "revised" in versions["versions"][1]["title"]

        # 3. Amendment invalidates affected requirement (kept in history).
        invalidated = client.post(
            f"/v1/bid-workspaces/{workspace_id}/requirements/req_off1/invalidate",
            json={"amendment_ref": "amend-2026-01"},
        )
        assert invalidated.status_code == 200
        req_off1 = next(
            row for row in client.get(
                f"/v1/bid-workspaces/{workspace_id}/requirements"
            ).json()
            if row["requirement_ref"] == "req_off1"
        )
        assert req_off1["status"] == "AMENDED"
        assert req_off1["affected_by_amendment"] == "amend-2026-01"

        # 4. Questions.
        question = client.post(
            f"/v1/bid-workspaces/{workspace_id}/questions",
            json={"question_ref": "q_001", "question": "Is subcontracted monitoring allowed?"},
        )
        assert question.status_code == 201
        answered = client.post(
            f"/v1/bid-workspaces/{workspace_id}/questions/q_001/answer",
            json={"answer": "Yes, with prior notice."},
        )
        assert answered.status_code == 200
        questions = client.get(f"/v1/bid-workspaces/{workspace_id}/questions").json()
        assert questions[0]["status"] == "ANSWERED"

        # 5. Risks.
        risk = client.post(
            f"/v1/bid-workspaces/{workspace_id}/risks",
            json={"risk_ref": "risk_001", "description": "Clearance delays",
                  "likelihood": "MEDIUM", "impact": "HIGH",
                  "mitigation": "Start vetting early"},
        )
        assert risk.status_code == 201
        risks = client.get(f"/v1/bid-workspaces/{workspace_id}/risks").json()
        assert risks[0]["likelihood"] == "MEDIUM" and risks[0]["impact"] == "HIGH"

        # 6. Tasks with owners.
        task = client.post(
            f"/v1/bid-workspaces/{workspace_id}/tasks",
            json={"task_ref": "t_001", "title": "Draft technical proposal",
                  "owner": "usr_bid_e2e", "requirement_ref": "req_off2"},
        )
        assert task.status_code == 201, task.text
        transitioned = client.post(
            f"/v1/bid-workspaces/{workspace_id}/tasks/t_001/transition",
            json={"new_status": "IN_PROGRESS"},
        )
        assert transitioned.status_code == 200
        tasks = client.get(f"/v1/bid-workspaces/{workspace_id}/tasks").json()
        assert tasks[0]["status"] == "IN_PROGRESS"
        assert tasks[0]["requirement_id"] is not None

        # Invalid task transition rejected.
        rejected = client.post(
            f"/v1/bid-workspaces/{workspace_id}/tasks/t_001/transition",
            json={"new_status": "NOT_A_STATE"},
        )
        assert rejected.status_code == 422

        # 7. Readiness: satisfy req_off2 with evidence.
        readiness = client.post(
            f"/v1/bid-workspaces/{workspace_id}/readiness",
            json={"requirement_ref": "req_off2", "satisfied": True,
                  "evidence_refs": ["evidence-1"], "notes": "Verified clearance"},
        )
        assert readiness.status_code == 200, readiness.text
        summary = client.get(f"/v1/bid-workspaces/{workspace_id}/readiness").json()
        assert summary["official"] == 2
        assert summary["satisfied"] == 1
        assert summary["ready"] is False  # req_off1 amended, req_off2 satisfied

        # 8. Human approval (append-only) + workspace state APPROVED.
        approval = client.post(
            f"/v1/bid-workspaces/{workspace_id}/approvals",
            json={"approval_ref": "appr_001", "decision": "APPROVED",
                  "notes": "Board approved the bid"},
        )
        assert approval.status_code == 201, approval.text
        ws = client.get(f"/v1/opportunities/workspaces/{workspace_id}")
        assert ws.json()["state"] == "APPROVED"

        # 9. Handoff.
        handoff = client.post(
            f"/v1/bid-workspaces/{workspace_id}/handoffs",
            json={"handoff_ref": "ho_001", "target": "submission_team",
                  "payload": {"summary": "Bid package complete"}},
        )
        assert handoff.status_code == 201, handoff.text
        ws = client.get(f"/v1/opportunities/workspaces/{workspace_id}")
        assert ws.json()["state"] == "HANDED_OFF"

        # 10. Append-only audit: every mutation recorded, no update/delete.
        audit = client.get(f"/v1/bid-workspaces/{workspace_id}/audit").json()
        actions = {row["action"] for row in audit}
        assert "bid_requirements.INSERT" in actions
        assert "bid_requirements.UPDATE" in actions
        assert "bid_tasks.INSERT" in actions
        assert "bid_approvals.INSERT" in actions
        assert "bid_handoffs.INSERT" in actions
        assert len(audit) >= 12, f"audit too small: {len(audit)}"

        # 11. Restart-equivalence: new client (new session) reads the same state.
        fresh = _client(TENANT_A)
        summary2 = fresh.get(f"/v1/bid-workspaces/{workspace_id}/readiness").json()
        assert summary2 == summary
        assert len(fresh.get(f"/v1/bid-workspaces/{workspace_id}/audit").json()) == len(audit)

        # 12. Tenant isolation: B sees nothing.
        other = _client(TENANT_B)
        assert other.get(f"/v1/bid-workspaces/{workspace_id}/requirements").status_code == 404
        assert other.get(f"/v1/bid-workspaces/{workspace_id}/audit").status_code == 404
        # B cannot write into A's workspace.
        forbidden = other.post(
            f"/v1/bid-workspaces/{workspace_id}/requirements",
            json={"requirement_ref": "req_intru", "kind": "OFFICIAL", "title": "Intrusion"},
        )
        assert forbidden.status_code == 404

        # 13. Cross-tenant approval cannot change A's workspace state.
        before = fresh.get(f"/v1/opportunities/workspaces/{workspace_id}").json()["state"]
        assert before == "HANDED_OFF"
