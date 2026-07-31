from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from axignal_api.application import app
from axignal_api.identity import build_identity_assertion

TENANT_ID = UUID("11111111-1111-4111-8111-111111111111")
IDENTITY_SECRET = "seat-test-identity-secret-with-at-least-32-bytes"


def headers(subject: str = "usr_owner", email: str = "owner@example.test") -> dict[str, str]:
    return {
        "X-AXIGNAL-Identity-Assertion": build_identity_assertion(
            secret=IDENTITY_SECRET,
            subject=subject,
            email=email,
            tenant_id=TENANT_ID,
        )
    }


class FakeSeatRepository:
    invitation_id = uuid4()
    member_id = uuid4()

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    def access_decision(self, **_: object) -> dict[str, object]:
        return {
            "decision": "ALLOW",
            "reason": "active_membership",
            "membership_id": str(self.member_id),
            "seat_state": "ACTIVE",
            "plan_code": "PROFESSIONAL_MONTHLY",
            "roles": ["ORG_OWNER"],
        }

    def bootstrap_owner(self, **_: object) -> dict[str, object]:
        return {"membership_id": self.member_id}

    def invitation_by_operation(self, **_: object) -> dict[str, object] | None:
        return None

    def reserve_invitation(self, **kwargs: object) -> dict[str, object]:
        now = datetime.now(UTC)
        return {
            "invitation_id": self.invitation_id,
            "operation_id": kwargs["operation_id"],
            "email_normalized": kwargs["email"],
            "requested_role_id": kwargs["role_id"],
            "token_digest": kwargs["token_digest"],
            "status": "PENDING",
            "delivery_provider": kwargs["delivery_provider"],
            "invited_at": now,
            "expires_at": kwargs["expires_at"],
            "accepted_at": None,
            "revoked_at": None,
        }

    def accept_invitation(self, **_: object) -> dict[str, object]:
        return {"membership_id": self.member_id}

    def revoke_invitation(self, **_: object) -> dict[str, object]:
        return {"invitation_id": self.invitation_id}

    def revoke_membership(self, **_: object) -> dict[str, object]:
        return {"membership_id": self.member_id}

    def change_role(self, **_: object) -> dict[str, object]:
        return {"membership_id": self.member_id}

    def summary(self, **_: object) -> dict[str, object]:
        now = datetime.now(UTC)
        return {
            "seat_entitlement": {
                "seat_entitlement_id": uuid4(),
                "plan_code": "PROFESSIONAL_MONTHLY",
                "billing_model": "FLAT_TIER",
                "seat_capacity": 3,
                "state": "ACTIVE",
                "policy_version": "seat-governance-policy@0.1.0",
                "valid_from": now,
                "valid_until": None,
            },
            "active_seats": 1,
            "reserved_seats": 0,
            "occupied_seats": 1,
            "available_seats": 2,
            "members": [
                {
                    "membership_id": self.member_id,
                    "principal_id": "usr_owner",
                    "email_normalized": "owner@example.test",
                    "status": "ACTIVE",
                    "roles": ["ORG_OWNER"],
                    "joined_at": now,
                    "revoked_at": None,
                }
            ],
            "invitations": [],
            "audit": [],
        }


def configure(monkeypatch) -> None:
    monkeypatch.setenv("AXIGNAL_IDENTITY_ASSERTION_SECRET", IDENTITY_SECRET)
    monkeypatch.setenv("AXIGNAL_SEAT_GOVERNANCE_ENABLED", "true")
    monkeypatch.setenv("AXIGNAL_DATABASE_URL", "postgresql://example.invalid/axignal")
    monkeypatch.setenv("AXIGNAL_ORGANISATION_OWNER_SUBJECTS", "usr_owner")
    monkeypatch.setenv("AXIGNAL_SEAT_INVITATION_PROVIDER", "test")
    monkeypatch.setenv("AXIGNAL_SEAT_INVITATION_TTL_HOURS", "72")
    monkeypatch.setenv("AXIGNAL_ENVIRONMENT", "test")
    monkeypatch.setenv("AXIGNAL_TEST_RUNTIME_ENABLED", "true")
    monkeypatch.setattr("axignal_api.identity.SeatRepository", FakeSeatRepository)
    monkeypatch.setattr("axignal_api.seat_routes.SeatRepository", FakeSeatRepository)


def test_seat_summary_requires_identity(monkeypatch) -> None:
    configure(monkeypatch)
    response = TestClient(app).get("/v1/organisation/seats")
    assert response.status_code == 401


def test_owner_bootstrap_is_bound_to_configured_subject(monkeypatch) -> None:
    configure(monkeypatch)
    response = TestClient(app).post(
        "/v1/organisation/seats/bootstrap-owner",
        headers=headers(subject="usr_not_owner", email="other@example.test"),
        json={"confirm_owner_bootstrap": True},
    )
    assert response.status_code == 403


def test_invitation_rejects_client_tenant_and_returns_test_token(monkeypatch) -> None:
    configure(monkeypatch)
    client = TestClient(app)
    injected = client.post(
        "/v1/organisation/seats/invitations",
        headers=headers(),
        json={
            "operation_id": "op_invite_tenant_injection",
            "email": "member@example.test",
            "role_id": "BID_REVIEWER",
            "tenant_id": str(uuid4()),
        },
    )
    assert injected.status_code == 422

    response = client.post(
        "/v1/organisation/seats/invitations",
        headers=headers(),
        json={
            "operation_id": "op_invite_member_0001",
            "email": "member@example.test",
            "role_id": "BID_REVIEWER",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["delivery_provider"] == "TEST"
    assert body["delivery_status"] == "DELIVERED"
    assert isinstance(body["test_acceptance_token"], str)
    assert len(body["test_acceptance_token"]) >= 20


def test_write_access_is_enriched_with_membership(monkeypatch) -> None:
    configure(monkeypatch)
    response = TestClient(app).get(
        "/v1/organisation/seats",
        headers=headers(),
    )
    assert response.status_code == 200
    assert response.json()["seat_entitlement"]["seat_capacity"] == 3
    assert response.json()["available_seats"] == 2
