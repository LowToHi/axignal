from __future__ import annotations

from collections import deque
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import psycopg
import pytest

from axignal_api.billing_repository import BillingRepository
from axignal_api.entitlement_repository import EntitlementRepository
from axignal_api.identity_repository import IdentityRepository
from axignal_api.organic_repository import OrganicDiscoveryRepository
from axignal_api.retention_repository import RetentionRepository
from axignal_api.seat_repository import SeatRepository

NOW = datetime(2026, 8, 1, tzinfo=UTC)
TENANT = UUID("00000000-0000-4000-8000-000000000101")
USER = UUID("00000000-0000-4000-8000-000000000102")
ENTITY = UUID("00000000-0000-4000-8000-000000000103")


class Cursor:
    def __init__(
        self,
        *,
        one: list[dict[str, Any] | None] | None = None,
        many: list[list[dict[str, Any]]] | None = None,
        rowcount: int = 1,
    ) -> None:
        self.one = deque(one or [])
        self.many = deque(many or [])
        self.rowcount = rowcount
        self.executions: list[tuple[object, object | None]] = []

    def execute(self, statement: object, params: object | None = None) -> None:
        self.executions.append((statement, params))

    def fetchone(self) -> dict[str, Any] | None:
        return self.one.popleft() if self.one else None

    def fetchall(self) -> list[dict[str, Any]]:
        return self.many.popleft() if self.many else []


class Plan:
    def __init__(self, *cursors: Cursor) -> None:
        self.cursors = deque(cursors)
        self.contexts: list[dict[str, object]] = []

    @contextmanager
    def __call__(self, *args: object, **kwargs: object) -> Iterator[Cursor]:
        context = dict(kwargs)
        if args:
            context["args"] = args
        self.contexts.append(context)
        if not self.cursors:
            raise AssertionError("unexpected repository cursor")
        yield self.cursors.popleft()


def attach(repository: object, *cursors: Cursor) -> Plan:
    plan = Plan(*cursors)
    repository._cursor = plan
    return plan


def identity_subjects() -> dict[str, str]:
    return {
        "email_normalized": "buyer@example.test",
        "email_hmac": "email-hmac",
        "email_identity_hmac": "identity-hmac",
        "domain_hmac": "domain-hmac",
        "installation_hmac": "installation-hmac",
        "network_hmac": "network-hmac",
        "disposable_domain": "false",
    }


def test_identity_repository_success_and_role_surface() -> None:
    repository = IdentityRepository("postgresql://identity")
    plan = attach(repository, Cursor(one=[{"allowed": True}]))
    assert (
        repository.consume_rate_limit(
            key_hmac="key", route_key="signup", limit=5, window_seconds=60, now=NOW
        )
        is True
    )
    assert plan.contexts == [{"role": "axignal_app"}]

    direct_rows = [
        (
            lambda: repository.begin_email_challenge(
                purpose="SIGNUP",
                token_digest="digest",
                subjects=identity_subjects(),
                expires_at=NOW + timedelta(minutes=10),
                now=NOW,
            ),
            {"challenge_id": ENTITY},
        ),
        (
            lambda: repository.create_webauthn_challenge(
                challenge_value="challenge",
                challenge_digest="digest",
                purpose="REGISTRATION",
                user_id=USER,
                bootstrap_ticket_id=ENTITY,
                rp_id="axignal.test",
                expected_origin="https://axignal.test",
                expires_at=NOW + timedelta(minutes=5),
                now=NOW,
            ),
            {"challenge_id": ENTITY},
        ),
        (
            lambda: repository.start_prepared_trial(
                tenant_id=TENANT,
                user_id=USER,
                subject="buyer",
                email="buyer@example.test",
                now=NOW,
            ),
            {"entitlement_id": ENTITY},
        ),
    ]
    for invoke, expected in direct_rows:
        attach(repository, Cursor(one=[expected]))
        assert invoke() == expected

    result_calls = [
        lambda: repository.consume_signup_challenge(
            token_digest="digest",
            registration_ticket_digest="ticket",
            operation_id="op",
            full_token_budget=100,
            restricted_token_budget=50,
            full_cost_budget_microunits=1000,
            restricted_cost_budget_microunits=500,
            now=NOW,
        ),
        lambda: repository.resolve_bootstrap_ticket(
            token_digest="ticket", purpose="REGISTRATION", now=NOW
        ),
        lambda: repository.pending_webauthn_challenge(
            challenge_digest="digest", purpose="REGISTRATION", now=NOW
        ),
        lambda: repository.credential_for_authentication(credential_id="credential"),
        lambda: repository.complete_registration(
            challenge_digest="challenge",
            bootstrap_ticket_digest="ticket",
            credential_id="credential",
            credential_public_key=b"public",
            sign_count=1,
            transports=["internal"],
            device_type="singleDevice",
            backed_up=False,
            aaguid=None,
            session_token_digest="session",
            installation_hmac="installation",
            network_hmac="network",
            user_agent_hmac="agent",
            recovery_code_digests=["recovery"],
            idle_seconds=300,
            absolute_seconds=3600,
            now=NOW,
        ),
        lambda: repository.complete_authentication(
            challenge_digest="challenge",
            credential_id="credential",
            new_sign_count=2,
            session_token_digest="session",
            installation_hmac="installation",
            network_hmac="network",
            user_agent_hmac="agent",
            idle_seconds=300,
            absolute_seconds=3600,
            now=NOW,
        ),
        lambda: repository.resolve_session(
            token_digest="session", touch_interval_seconds=60, now=NOW
        ),
        lambda: repository.begin_recovery(
            email_identity_hmac="identity",
            code_digest="code",
            recovery_ticket_digest="ticket",
            now=NOW,
        ),
        lambda: repository.approve_test_step_up(
            tenant_id=TENANT,
            user_id=USER,
            claim_type="ORGANISATION",
            claim_hmac="claim",
            actor_subject="founder",
            full_token_budget=100,
            full_cost_budget_microunits=1000,
            now=NOW,
        ),
    ]
    for invoke in result_calls:
        attach(repository, Cursor(one=[{"result": {"status": "PASS"}}]))
        assert invoke() == {"status": "PASS"}

    attach(repository, Cursor(one=[{"revoked": True}]))
    assert repository.revoke_session(token_digest="session", reason="LOGOUT", now=NOW) is True
    attach(repository, Cursor(one=[None]))
    assert repository.revoke_session(token_digest="session", reason="LOGOUT", now=NOW) is False

    attach(repository, Cursor(one=[{"result": {"state": "PREPARED"}}]))
    assert repository.trial_status(tenant_id=TENANT) == {"state": "PREPARED"}
    attach(repository, Cursor(one=[None]))
    assert repository.trial_status(tenant_id=TENANT) is None


def test_identity_repository_fails_closed_when_required_rows_are_missing() -> None:
    repository = IdentityRepository("postgresql://identity")
    calls = [
        lambda: repository.consume_rate_limit(
            key_hmac="key", route_key="route", limit=1, window_seconds=60, now=NOW
        ),
        lambda: repository.begin_email_challenge(
            purpose="SIGNUP",
            token_digest="token",
            subjects=identity_subjects(),
            expires_at=NOW,
            now=NOW,
        ),
        lambda: repository.resolve_bootstrap_ticket(
            token_digest="token", purpose="SIGNUP", now=NOW
        ),
        lambda: repository.credential_for_authentication(credential_id="missing"),
        lambda: repository.resolve_session(
            token_digest="session", touch_interval_seconds=60, now=NOW
        ),
        lambda: repository.start_prepared_trial(
            tenant_id=TENANT,
            user_id=USER,
            subject="buyer",
            email="buyer@example.test",
            now=NOW,
        ),
    ]
    for invoke in calls:
        attach(repository, Cursor(one=[None]))
        with pytest.raises(RuntimeError):
            invoke()


def billing_event(repository: BillingRepository) -> dict[str, Any]:
    return repository.apply_stripe_event(
        event_id="evt_test",
        event_type="customer.subscription.updated",
        event_created_at=NOW,
        livemode=False,
        payload_digest="sha256:event",
        provider_account_id="acct_test",
        selection_id=ENTITY,
        checkout_session_id="cs_test",
        customer_id="cus_test",
        subscription_id="sub_test",
        subscription_item_id="si_test",
        price_id="price_test",
        plan_code="PROFESSIONAL_MONTHLY",
        subscription_status="active",
        current_period_end=NOW + timedelta(days=30),
        cancel_at_period_end=False,
        amount_minor=14900,
        currency="eur",
        actor_subject="stripe",
        now=NOW,
    )


def test_billing_repository_roles_success_and_missing_rows() -> None:
    repository = BillingRepository("postgresql://billing")
    row = {"selection_id": ENTITY}
    app_calls = [
        lambda: repository.request_selection(
            tenant_id=TENANT,
            operation_id="op",
            plan_code="PROFESSIONAL_MONTHLY",
            provider_account_id="acct_test",
            actor_subject="buyer",
            now=NOW,
        ),
        lambda: repository.mark_checkout_created(
            tenant_id=TENANT,
            selection_id=ENTITY,
            checkout_session_id="cs_test",
            price_id="price_test",
            actor_subject="buyer",
            now=NOW,
        ),
        lambda: repository.request_upgrade(
            tenant_id=TENANT,
            target_plan_code="TEAM_MONTHLY",
            target_price_id="price_team",
            actor_subject="buyer",
            now=NOW,
        ),
        lambda: repository.request_cancellation(
            tenant_id=TENANT,
            cancel_at_period_end=True,
            actor_subject="buyer",
            now=NOW,
        ),
    ]
    for invoke in app_calls:
        plan = attach(repository, Cursor(one=[row]))
        assert invoke() == row
        assert plan.contexts == [{"role": "axignal_app", "tenant_id": TENANT}]

    attach(repository, Cursor(one=[row]))
    assert repository.current_selection(tenant_id=TENANT) == row
    plan = attach(repository, Cursor(one=[{"result": {"state": "ACTIVE"}}]))
    assert billing_event(repository) == {"state": "ACTIVE"}
    assert plan.contexts == [{"role": "axignal_billing_worker"}]
    plan = attach(repository, Cursor(one=[row]))
    assert repository.rollback(selection_id=ENTITY, actor_subject="operator", now=NOW) == row
    assert plan.contexts == [{"role": "axignal_billing_worker"}]
    attach(repository, Cursor(many=[[{"ledger_entry_id": ENTITY}]]))
    assert len(repository.ledger(tenant_id=TENANT)) == 1

    for invoke in [
        *app_calls,
        lambda: billing_event(repository),
        lambda: repository.rollback(selection_id=ENTITY, actor_subject="operator", now=NOW),
    ]:
        attach(repository, Cursor(one=[None]))
        with pytest.raises(RuntimeError):
            invoke()


def test_entitlement_repository_lifecycle_and_expiry_guard(monkeypatch) -> None:
    repository = EntitlementRepository("postgresql://entitlement")
    row = {"entitlement_id": ENTITY}
    attach(repository, Cursor(one=[row]))
    assert repository.activate_trial(tenant_id=TENANT, actor_subject="buyer", now=NOW) == row
    attach(repository, Cursor(one=[{"expired": True}]))
    assert repository.expire_due_trial(tenant_id=TENANT, actor_subject="system", now=NOW) is True

    monkeypatch.setattr(repository, "expire_due_trial", lambda **_: False)
    mutations = [
        lambda: repository.reserve(
            tenant_id=TENANT,
            operation_id="op",
            capability="RESEARCH",
            requested_tokens=10,
            actor_subject="buyer",
            now=NOW,
        ),
        lambda: repository.reconcile(
            tenant_id=TENANT,
            reservation_id=ENTITY,
            actual_tokens=8,
            actor_subject="buyer",
            now=NOW,
        ),
        lambda: repository.release(
            tenant_id=TENANT,
            reservation_id=ENTITY,
            actor_subject="buyer",
            now=NOW,
        ),
        lambda: repository.expire_trial(tenant_id=TENANT, actor_subject="operator", now=NOW),
    ]
    for invoke in mutations:
        attach(repository, Cursor(one=[row]))
        assert invoke() == row

    monkeypatch.setattr(repository, "expire_due_trial", lambda **_: True)
    with pytest.raises(RuntimeError, match="trial_expired"):
        repository.reserve(
            tenant_id=TENANT,
            operation_id="expired",
            capability="RESEARCH",
            requested_tokens=1,
            actor_subject="buyer",
            now=NOW,
        )

    monkeypatch.setattr(repository, "expire_due_trial", lambda **_: False)
    attach(repository, Cursor(one=[row]))
    assert repository.current_entitlement(tenant_id=TENANT) == row
    attach(repository, Cursor(one=[row]))
    assert repository.usage(tenant_id=TENANT) == row


def test_seat_repository_mutations_access_and_summary() -> None:
    repository = SeatRepository("postgresql://seats")
    row = {"membership_id": ENTITY, "state": "ACTIVE"}
    calls = [
        lambda: repository.bootstrap_owner(
            tenant_id=TENANT,
            principal_id="owner",
            email="owner@example.test",
            actor_subject="owner",
            now=NOW,
        ),
        lambda: repository.reserve_invitation(
            tenant_id=TENANT,
            operation_id="invite-op",
            email="member@example.test",
            role_id="MEMBER",
            token_digest="token",
            delivery_provider="test",
            invited_by="owner",
            expires_at=NOW + timedelta(days=1),
            now=NOW,
        ),
        lambda: repository.accept_invitation(
            tenant_id=TENANT,
            token_digest="token",
            principal_id="member",
            email="member@example.test",
            actor_subject="member",
            now=NOW,
        ),
        lambda: repository.revoke_invitation(
            tenant_id=TENANT,
            invitation_id=ENTITY,
            actor_subject="owner",
            reason="REVOKED",
            now=NOW,
        ),
        lambda: repository.revoke_membership(
            tenant_id=TENANT,
            membership_id=ENTITY,
            actor_subject="owner",
            now=NOW,
        ),
        lambda: repository.change_role(
            tenant_id=TENANT,
            membership_id=ENTITY,
            role_id="ADMIN",
            actor_subject="owner",
            now=NOW,
        ),
    ]
    for invoke in calls:
        plan = attach(repository, Cursor(one=[row]))
        assert invoke() == row
        assert plan.contexts == [{"role": "axignal_app", "tenant_id": TENANT}]

    attach(repository, Cursor(one=[row]))
    assert repository.invitation_by_operation(tenant_id=TENANT, operation_id="invite-op") == row
    attach(repository, Cursor(one=[{"decision": {"allowed": True}}]))
    assert repository.access_decision(
        tenant_id=TENANT, principal_id="member", write=True, now=NOW
    ) == {"allowed": True}

    cursor = Cursor(
        one=[{"seat_capacity": 5}, {"active": 2, "reserved": 1}],
        many=[
            [{"membership_id": USER}],
            [{"invitation_id": ENTITY}],
            [{"audit_event_id": ENTITY}],
        ],
    )
    attach(repository, cursor)
    summary = repository.summary(tenant_id=TENANT)
    assert summary["occupied_seats"] == 3
    assert summary["available_seats"] == 2
    assert len(summary["members"]) == 1
    assert len(summary["invitations"]) == 1
    assert len(summary["audit"]) == 1

    attach(repository, Cursor(one=[None]))
    with pytest.raises(RuntimeError, match="seat_entitlement_required"):
        repository.summary(tenant_id=TENANT)


def test_organic_repository_public_admin_alert_and_failure_contracts() -> None:
    repository = OrganicDiscoveryRepository("postgresql://organic")
    result = {"status": "PASS"}
    attach(repository, Cursor())
    assert repository.founder_authorized(subject="founder") is True

    class Denied:
        @contextmanager
        def __call__(self, **_: object) -> Iterator[Cursor]:
            raise psycopg.OperationalError("denied")
            yield Cursor()

    repository._cursor = Denied()
    assert repository.founder_authorized(subject="intruder") is False

    attach(repository, Cursor(one=[{"result": result}]))
    assert repository.overview(actor_subject="founder") == result
    attach(repository, Cursor(one=[None]))
    assert repository.overview(actor_subject="founder") == {}
    for method in (repository.pages, repository.contacts, repository.alerts):
        attach(repository, Cursor(many=[[result]]))
        assert method(actor_subject="founder") == [result]

    calls = [
        lambda: repository.evaluate(page_id=ENTITY, actor_subject="founder"),
        lambda: repository.publish(
            page_id=ENTITY,
            actor_subject="founder",
            content_hash="sha256:page",
            ttl_hours=24,
        ),
        lambda: repository.subscribe_alert(
            email="buyer@example.test",
            email_hmac="email",
            confirmation_token_digest="token",
            country_code="ES",
            sector_slug="agriculture",
            locale="en",
            cadence="DAILY",
            source_path="/spain/agriculture",
        ),
        lambda: repository.confirm_alert(confirmation_token_digest="token"),
        lambda: repository.fail_alert_delivery(subscription_id=ENTITY, reason="DELIVERY_FAILED"),
        lambda: repository.unsubscribe_alert(confirmation_token_digest="token"),
    ]
    for invoke in calls:
        attach(repository, Cursor(one=[{"result": result}]))
        assert invoke() == result

    attach(repository, Cursor(one=[{"result": result}]))
    assert (
        repository.public_page(
            country_slug="spain",
            sector_slug="agriculture",
            page_kind="MARKET",
            locale="en",
        )
        == result
    )
    attach(repository, Cursor(one=[None]))
    assert (
        repository.public_page(
            country_slug="missing",
            sector_slug="missing",
            page_kind="MARKET",
            locale="en",
        )
        is None
    )
    attach(repository, Cursor(many=[[result]]))
    assert repository.sitemap() == [result]
    attach(repository, Cursor(one=[{"citation_event_id": ENTITY}]))
    assert (
        repository.record_citation(
            actor_subject="founder",
            provider="search",
            surface="web",
            cited_url="https://axignal.test/page",
            query_hmac="query",
            source="test",
            metadata={"rank": 1},
            observed_at=NOW,
        )
        == ENTITY
    )
    plan = attach(repository, Cursor())
    repository.test_bootstrap_founder(subject="founder")
    assert plan.contexts == [{"application_role": False}]

    for invoke in [
        calls[0],
        calls[3],
        lambda: repository.record_citation(
            actor_subject="founder",
            provider="search",
            surface="web",
            cited_url="https://axignal.test",
            query_hmac="query",
            source="test",
            metadata={},
            observed_at=NOW,
        ),
    ]:
        attach(repository, Cursor(one=[None]))
        with pytest.raises(RuntimeError):
            invoke()


def test_retention_repository_roles_lifecycle_and_tombstones() -> None:
    repository = RetentionRepository("postgresql://retention")
    row = {"tenant_id": TENANT, "state": "ACTIVE"}
    plan = attach(repository, Cursor(one=[row]))
    assert repository.lifecycle(tenant_id=TENANT) == row
    assert plan.contexts == [{"role": "axignal_app", "tenant_id": TENANT}]

    plan = attach(repository, Cursor(one=[row]))
    assert (
        repository.request_deletion(
            tenant_id=TENANT,
            actor_subject="owner",
            retention_seconds=3600,
            now=NOW,
        )
        == row
    )
    assert plan.contexts[0]["role"] == "axignal_app"
    plan = attach(repository, Cursor(one=[row]))
    assert (
        repository.suspend(
            tenant_id=TENANT,
            reason_code="SECURITY",
            actor_subject="operator",
            now=NOW,
        )
        == row
    )
    assert plan.contexts == [{"role": "axignal_operator"}]
    plan = attach(repository, Cursor(one=[{"queued": 2}]))
    assert repository.queue_due(now=NOW) == 2
    assert plan.contexts == [{"role": "axignal_retention_worker"}]
    attach(repository, Cursor(one=[None]))
    assert repository.queue_due(now=NOW) == 0
    attach(repository, Cursor(one=[row]))
    assert repository.claim(worker_id="worker", lease_seconds=30, now=NOW) == row
    attach(repository, Cursor(one=[row]))
    assert repository.purge(deletion_id=ENTITY, worker_id="worker", now=NOW) == row
    attach(repository, Cursor(one=[{"result": row}]))
    assert repository.reapply_tombstone(tenant_id=TENANT, now=NOW) == row

    for invoke in [
        lambda: repository.request_deletion(
            tenant_id=TENANT,
            actor_subject="owner",
            retention_seconds=1,
            now=NOW,
        ),
        lambda: repository.suspend(
            tenant_id=TENANT,
            reason_code="SECURITY",
            actor_subject="operator",
            now=NOW,
        ),
        lambda: repository.purge(deletion_id=ENTITY, worker_id="worker", now=NOW),
        lambda: repository.reapply_tombstone(tenant_id=TENANT, now=NOW),
    ]:
        attach(repository, Cursor(one=[None]))
        with pytest.raises(RuntimeError):
            invoke()
