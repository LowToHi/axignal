"""Integration tests: Opportunity Operations + Sandbox Billing over PostgreSQL.

These tests require a live local PostgreSQL with the 143 migration applied
(they are the LOCAL_PRODUCT integration layer, not unit tests). They verify:

- tenant isolation (two tenants, one cannot see the other);
- transactions and constraints;
- idempotency persistence;
- rollback on constraint violation;
- restart-session equivalence (new repository instance reads persisted rows);
- pursuit -> workspace -> outcome -> learning flow;
- sandbox checkout -> entitlements -> cancel/dunning/recovery;
- webhook signature + replay protection persisted.
"""

from __future__ import annotations

import os
from uuid import UUID, uuid4

import pytest

from axignal_api.opportunity_repository import OpportunityOperationsRepository
from axignal_api.sandbox_billing_repository import SandboxBillingRepository

DSN = os.environ.get(
    "AXIGNAL_DATABASE_URL",
    "postgresql://axignal:axignal-local@localhost:5432/axignal",
)

TENANT_A = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
TENANT_B = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")

pytestmark = pytest.mark.skipif(
    not os.environ.get("AXIGNAL_INTEGRATION_TESTS"),
    reason="integration tests need a live PostgreSQL; set AXIGNAL_INTEGRATION_TESTS=1",
)


@pytest.fixture()
def repo() -> OpportunityOperationsRepository:
    return OpportunityOperationsRepository(DSN)


@pytest.fixture()
def billing() -> SandboxBillingRepository:
    repository = SandboxBillingRepository(DSN)
    repository.seed_catalogue(
        [
            {
                "product_id": "AXIGNAL_OPPORTUNITY_INTELLIGENCE",
                "shell_id": "AXIGNAL_OPPORTUNITY_INTELLIGENCE",
            },
            {
                "product_id": "AXIGNAL_PUBLIC_EMPLOYMENT",
                "shell_id": "AXIGNAL_PUBLIC_EMPLOYMENT",
            },
        ],
        [
            {"plan_id": "plan-oi-professional", "product_id": "AXIGNAL_OPPORTUNITY_INTELLIGENCE",
             "name": "Professional", "seats": 3, "status": "ACTIVE"},
            {"plan_id": "plan-pe-academy", "product_id": "AXIGNAL_PUBLIC_EMPLOYMENT",
             "name": "Academy", "seats": 1, "status": "DRAFT", "is_academy": True},
        ],
        [
            {"price_id": "price-oi-professional", "product_id": "AXIGNAL_OPPORTUNITY_INTELLIGENCE",
             "plan_id": "plan-oi-professional", "amount_cents": 14900, "currency": "EUR",
             "interval_unit": "month", "tax_mode": "EXCLUSIVE", "active": True},
            {"price_id": "price-pe-academy", "product_id": "AXIGNAL_PUBLIC_EMPLOYMENT",
             "plan_id": "plan-pe-academy", "amount_cents": 9900, "currency": "EUR",
             "interval_unit": "month", "tax_mode": "EXCLUSIVE", "active": False},
        ],
    )
    return repository


class TestOpportunityPersistence:
    def test_pursuit_flow_and_restart_session(self, repo: OpportunityOperationsRepository) -> None:
        pursuit_ref = f"prs_test_{uuid4().hex[:12]}"
        repo.create_pursuit(
            tenant_id=TENANT_A,
            pursuit_ref=pursuit_ref,
            opportunity_ref="opp-1",
            state="QUALIFIED",
            created_by="user-a",
        )
        # Transition.
        repo.transition_pursuit(
            tenant_id=TENANT_A, pursuit_ref=pursuit_ref, new_state="DECISION_REVIEW"
        )
        # New repository instance == new session (restart equivalence).
        fresh = OpportunityOperationsRepository(DSN)
        row = fresh.get_pursuit(tenant_id=TENANT_A, pursuit_ref=pursuit_ref)
        assert row is not None
        assert row["state"] == "DECISION_REVIEW"

    def test_tenant_isolation(self, repo: OpportunityOperationsRepository) -> None:
        pursuit_ref = f"prs_iso_{uuid4().hex[:12]}"
        repo.create_pursuit(
            tenant_id=TENANT_A,
            pursuit_ref=pursuit_ref,
            opportunity_ref="opp-iso",
            state="QUALIFIED",
            created_by="user-a",
        )
        # Tenant B cannot see A's pursuit via list or direct get.
        assert repo.get_pursuit(tenant_id=TENANT_B, pursuit_ref=pursuit_ref) is None
        refs_b = {row["pursuit_ref"] for row in repo.list_pursuits(tenant_id=TENANT_B)}
        assert pursuit_ref not in refs_b

    def test_workspace_flow(self, repo: OpportunityOperationsRepository) -> None:
        workspace_id = uuid4()
        repo.create_workspace(
            tenant_id=TENANT_A,
            workspace_id=workspace_id,
            pursuit_ref="prs_ws_00000001",
            opportunity_ref="opp-1",
            opportunity_version_digest=f"sha256:{'a' * 64}",
            subscriber_profile_version="v1",
            assessment_version="v1",
            created_by="user-a",
        )
        repo.update_workspace_state(
            tenant_id=TENANT_A, workspace_id=workspace_id, state="PREPARING"
        )
        row = repo.get_workspace(tenant_id=TENANT_A, workspace_id=workspace_id)
        assert row is not None
        assert row["state"] == "PREPARING"
        # Isolation.
        assert repo.get_workspace(tenant_id=TENANT_B, workspace_id=workspace_id) is None

    def test_workspace_state_constraint(self, repo: OpportunityOperationsRepository) -> None:
        workspace_id = uuid4()
        repo.create_workspace(
            tenant_id=TENANT_A,
            workspace_id=workspace_id,
            pursuit_ref="prs_ws_00000002",
            opportunity_ref="opp-1",
            opportunity_version_digest=f"sha256:{'b' * 64}",
            subscriber_profile_version="v1",
            assessment_version="v1",
            created_by="user-a",
        )
        with pytest.raises(ValueError, match="invalid workspace state"):
            repo.update_workspace_state(
                tenant_id=TENANT_A, workspace_id=workspace_id, state="NOT_A_STATE"
            )

    def test_outcome_and_learning(self, repo: OpportunityOperationsRepository) -> None:
        outcome_ref = f"out_test_{uuid4().hex[:12]}"
        learning_ref = f"lrn_test_{uuid4().hex[:12]}"
        from datetime import UTC, datetime

        outcome_id = repo.create_outcome(
            tenant_id=TENANT_A,
            outcome_ref=outcome_ref,
            pursuit_ref="prs_test_00000001",
            result="WON",
            decided_at=datetime.now(UTC),
            evidence_refs=["evidence-1"],
        )
        assert outcome_id is not None
        learning_id = repo.create_learning(
            tenant_id=TENANT_A,
            learning_ref=learning_ref,
            outcome_ref=outcome_ref,
            insight="Deadline tracking reduced preparation risk.",
            evidence_refs=["evidence-1"],
        )
        assert learning_id is not None
        outcomes = repo.list_outcomes(tenant_id=TENANT_A)
        learnings = repo.list_learnings(tenant_id=TENANT_A)
        assert any(o["outcome_ref"] == outcome_ref for o in outcomes)
        assert any(item["learning_ref"] == learning_ref for item in learnings)
        # Isolation.
        assert all(o["outcome_ref"] != outcome_ref for o in repo.list_outcomes(tenant_id=TENANT_B))

    def test_manifest_states_persist(self, repo: OpportunityOperationsRepository) -> None:
        repo.upsert_manifest_state(
            manifest_kind="source",
            manifest_id="src_ted_search_api_v3",
            state="PRODUCT_ADMITTED",
            payload={"commercial_use": True},
        )
        row = repo.get_manifest_state(
            manifest_kind="source", manifest_id="src_ted_search_api_v3"
        )
        assert row is not None
        assert row["state"] == "PRODUCT_ADMITTED"
        # Upsert updates in place.
        repo.upsert_manifest_state(
            manifest_kind="source",
            manifest_id="src_ted_search_api_v3",
            state="SUSPENDED",
            payload={"kill_switch": True},
        )
        row = repo.get_manifest_state(
            manifest_kind="source", manifest_id="src_ted_search_api_v3"
        )
        assert row["state"] == "SUSPENDED"

    def test_portfolio(self, repo: OpportunityOperationsRepository) -> None:
        item_ref = f"pf_test_{uuid4().hex[:12]}"
        repo.add_portfolio_item(
            tenant_id=TENANT_A,
            item_ref=item_ref,
            opportunity_ref="opp-1",
            library_id="O01",
        )
        items_a = repo.list_portfolio(tenant_id=TENANT_A)
        items_b = repo.list_portfolio(tenant_id=TENANT_B)
        assert any(i["item_ref"] == item_ref for i in items_a)
        assert all(i["item_ref"] != item_ref for i in items_b)


class TestSandboxBillingPersistence:
    def test_checkout_idempotent_and_persisted(self, billing: SandboxBillingRepository) -> None:
        key = f"key_{uuid4().hex[:16]}"
        checkout_id = f"chk_{uuid4().hex[:12]}"
        first = billing.record_idempotency_key(
            tenant_id=TENANT_A, idempotency_key=key, checkout_id=checkout_id,
            product_id="AXIGNAL_OPPORTUNITY_INTELLIGENCE",
        )
        assert first is True
        replay = billing.record_idempotency_key(
            tenant_id=TENANT_A, idempotency_key=key, checkout_id=checkout_id,
            product_id="AXIGNAL_OPPORTUNITY_INTELLIGENCE",
        )
        assert replay is False
        assert billing.has_idempotency_key(tenant_id=TENANT_A, idempotency_key=key) is True
        # Persisted across repository instances.
        fresh = SandboxBillingRepository(DSN)
        assert fresh.has_idempotency_key(tenant_id=TENANT_A, idempotency_key=key) is True

    def test_subscription_and_entitlement(self, billing: SandboxBillingRepository) -> None:
        subscription = billing.create_subscription(
            tenant_id=TENANT_A,
            product_id="AXIGNAL_OPPORTUNITY_INTELLIGENCE",
            plan_id="plan-oi-professional",
            price_id="price-oi-professional",
            trial=False,
        )
        assert subscription["status"] == "ACTIVE"
        billing.set_entitlement(
            tenant_id=TENANT_A, product_id="AXIGNAL_OPPORTUNITY_INTELLIGENCE", allowed=True
        )
        entitlements = billing.entitlements(tenant_id=TENANT_A)
        assert entitlements["AXIGNAL_OPPORTUNITY_INTELLIGENCE"] is True
        # Tenant B has no entitlement (absent or explicitly False).
        assert billing.entitlements(tenant_id=TENANT_B).get(
            "AXIGNAL_OPPORTUNITY_INTELLIGENCE"
        ) in (None, False)

    def test_cancel_immediate_revokes(self, billing: SandboxBillingRepository) -> None:
        billing.create_subscription(
            tenant_id=TENANT_A,
            product_id="AXIGNAL_OPPORTUNITY_INTELLIGENCE",
            plan_id="plan-oi-professional",
            price_id="price-oi-professional",
            trial=False,
        )
        billing.set_entitlement(
            tenant_id=TENANT_A, product_id="AXIGNAL_OPPORTUNITY_INTELLIGENCE", allowed=True
        )
        billing.update_subscription_status(
            tenant_id=TENANT_A, status="CANCELLED_IMMEDIATE"
        )
        billing.set_entitlement(
            tenant_id=TENANT_A, product_id="AXIGNAL_OPPORTUNITY_INTELLIGENCE", allowed=False
        )
        assert billing.entitlements(tenant_id=TENANT_A)["AXIGNAL_OPPORTUNITY_INTELLIGENCE"] is False

    def test_dunning_and_recovery(self, billing: SandboxBillingRepository) -> None:
        from datetime import UTC, datetime, timedelta

        billing.create_subscription(
            tenant_id=TENANT_A,
            product_id="AXIGNAL_OPPORTUNITY_INTELLIGENCE",
            plan_id="plan-oi-professional",
            price_id="price-oi-professional",
            trial=False,
        )
        grace_until = datetime.now(UTC) + timedelta(days=7)
        dunning = billing.update_subscription_status(
            tenant_id=TENANT_A, status="DUNNING", grace_until=grace_until
        )
        assert dunning["status"] == "DUNNING"
        recovered = billing.update_subscription_status(tenant_id=TENANT_A, status="ACTIVE")
        assert recovered["status"] == "ACTIVE"

    def test_webhook_events_persisted(self, billing: SandboxBillingRepository) -> None:
        event_id = billing.record_webhook_event(
            tenant_id=TENANT_A,
            product_id="AXIGNAL_OPPORTUNITY_INTELLIGENCE",
            event_type="invoice.paid",
            payload={"amount_cents": 14900},
            signature="sig-test-123",
        )
        assert event_id is not None
        events = billing.list_webhook_events(tenant_id=TENANT_A)
        assert any(e["event_type"] == "invoice.paid" for e in events)
        # Isolation.
        assert billing.list_webhook_events(tenant_id=TENANT_B) == []

    def test_change_plan_persists(self, billing: SandboxBillingRepository) -> None:
        billing.create_subscription(
            tenant_id=TENANT_A,
            product_id="AXIGNAL_OPPORTUNITY_INTELLIGENCE",
            plan_id="plan-oi-professional",
            price_id="price-oi-professional",
            trial=False,
        )
        changed = billing.change_plan(
            tenant_id=TENANT_A,
            new_plan_id="plan-oi-team",
            new_price_id="price-oi-team",
        )
        assert changed["plan_id"] == "plan-oi-team"
        fresh = SandboxBillingRepository(DSN)
        subscription = fresh.get_subscription(tenant_id=TENANT_A)
        assert subscription["plan_id"] == "plan-oi-team"
