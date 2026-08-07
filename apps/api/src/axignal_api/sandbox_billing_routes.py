"""Sandbox billing HTTP API (Prioridad 6).

Server-side checkout with persistent idempotency, signatures, replay
protection, entitlement reconciliation, cancellation, dunning and refund
audit — all backed by PostgreSQL (SandboxBillingRepository). Live Stripe
remains disabled; the adapter contract is the sandbox runtime.

Endpoints:

- GET  /v1/billing/sandbox/catalog
- GET  /v1/billing/sandbox/plans/{product_id}
- POST /v1/billing/sandbox/checkout          (idempotent)
- GET  /v1/billing/sandbox/subscription
- POST /v1/billing/sandbox/subscription/cancel
- POST /v1/billing/sandbox/subscription/change-plan
- POST /v1/billing/sandbox/subscription/dunning
- POST /v1/billing/sandbox/subscription/recover
- POST /v1/billing/sandbox/refund            (audit trail)
- GET  /v1/billing/sandbox/entitlements
- POST /v1/billing/sandbox/webhooks          (HMAC + replay guard)
- GET  /v1/billing/sandbox/webhook-events
"""

from __future__ import annotations

import hashlib
import hmac
import os
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from axignal_api.identity import AuthenticatedIdentity, require_identity
from axignal_api.sandbox_billing_repository import SandboxBillingRepository

router = APIRouter(prefix="/v1/billing/sandbox", tags=["billing-sandbox"])
Authenticated = Annotated[AuthenticatedIdentity, Depends(require_identity)]

SHELL_1 = "AXIGNAL_OPPORTUNITY_INTELLIGENCE"
SHELL_2 = "AXIGNAL_PUBLIC_EMPLOYMENT"

# Canonical sandbox catalogue (hypotheses; never live).
CATALOGUE: dict[str, object] = {
    "products": [
        {"product_id": SHELL_1, "shell_id": SHELL_1},
        {"product_id": SHELL_2, "shell_id": SHELL_2},
    ],
    "plans": [
        {"plan_id": "plan-oi-professional", "product_id": SHELL_1,
         "name": "Professional", "seats": 3, "status": "ACTIVE"},
        {"plan_id": "plan-oi-team", "product_id": SHELL_1,
         "name": "Team", "seats": 15, "status": "ACTIVE"},
        {"plan_id": "plan-pe-academy", "product_id": SHELL_2,
         "name": "Academy", "seats": 1, "status": "DRAFT", "is_academy": True},
    ],
    "prices": [
        {"price_id": "price-oi-professional", "product_id": SHELL_1,
         "plan_id": "plan-oi-professional", "amount_cents": 14900,
         "currency": "EUR", "interval_unit": "month", "tax_mode": "EXCLUSIVE"},
        {"price_id": "price-oi-team", "product_id": SHELL_1,
         "plan_id": "plan-oi-team", "amount_cents": 39900,
         "currency": "EUR", "interval_unit": "month", "tax_mode": "EXCLUSIVE"},
        {"price_id": "price-pe-academy", "product_id": SHELL_2,
         "plan_id": "plan-pe-academy", "amount_cents": 9900,
         "currency": "EUR", "interval_unit": "month", "tax_mode": "EXCLUSIVE",
         "active": False},
    ],
}


def _repository() -> SandboxBillingRepository:
    dsn = os.environ.get(
        "AXIGNAL_DATABASE_URL",
        "postgresql://axignal:axignal-local@localhost:5432/axignal",
    )
    return SandboxBillingRepository(dsn)


def _webhook_key(product_id: str) -> str:
    # Deterministic sandbox key (no live secrets). Rotation is out of scope.
    return f"sandbox-hmac-key-{product_id}"


def _sign(product_id: str, payload: str) -> str:
    key = _webhook_key(product_id).encode("utf-8")
    return hmac.new(key, payload.encode("utf-8"), hashlib.sha256).hexdigest()


class CheckoutRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    checkout_id: str = Field(min_length=3, max_length=200)
    product_id: str
    plan_id: str
    price_id: str
    idempotency_key: str = Field(min_length=8, max_length=200)
    customer_context: str = Field(min_length=3, max_length=300)
    trial: bool = False


class CancelRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    at_period_end: bool = True


class ChangePlanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    new_plan_id: str
    new_price_id: str


class DunningRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    grace_days: int = Field(ge=1, le=30, default=7)


class RefundRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    refund_id: str = Field(min_length=3, max_length=200)
    amount_cents: int = Field(ge=1)
    reason: str = Field(min_length=3, max_length=500)


class WebhookRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: str
    event_type: str = Field(min_length=2, max_length=80)
    payload: dict[str, object]
    signature: str = Field(min_length=16, max_length=256)
    replay_guard: str


@router.get("/catalog")
def get_catalog() -> dict[str, object]:
    repository = _repository()
    repository.seed_catalogue(
        CATALOGUE["products"],  # type: ignore[arg-type]
        CATALOGUE["plans"],  # type: ignore[arg-type]
        CATALOGUE["prices"],  # type: ignore[arg-type]
    )
    # Normalise: prices without an explicit active flag default to active.
    prices = []
    for price in CATALOGUE["prices"]:  # type: ignore[union-attr]
        normalized = dict(price)  # type: ignore[arg-type]
        normalized.setdefault("active", True)
        prices.append(normalized)
    return {"products": CATALOGUE["products"], "plans": CATALOGUE["plans"], "prices": prices}


@router.get("/plans/{product_id}")
def get_plans(product_id: str) -> list[dict[str, object]]:
    return _repository().list_plans(product_id)  # type: ignore[return-value]


@router.post("/checkout", status_code=status.HTTP_201_CREATED)
def checkout(
    request: CheckoutRequest,
    identity: Authenticated,
) -> dict[str, object]:
    repository = _repository()

    # Idempotency: same key -> replay response, no double charge.
    if repository.has_idempotency_key(
        tenant_id=identity.tenant_id, idempotency_key=request.idempotency_key
    ):
        return {
            "status": "IDEMPOTENT_REPLAY",
            "checkout_id": request.checkout_id,
            "replayed": True,
        }

    price = repository.get_price(request.price_id)
    if price is None:
        raise HTTPException(status_code=422, detail="unknown price")
    if not price["active"]:
        raise HTTPException(status_code=422, detail="inactive price cannot be checked out")
    if price["product_id"] != request.product_id:
        raise HTTPException(
            status_code=422,
            detail=(
                f"cross-shell checkout rejected: price product "
                f"{price['product_id']!r} != request product {request.product_id!r}"
            ),
        )
    if price["plan_id"] != request.plan_id:
        raise HTTPException(status_code=422, detail="plan_id does not match price")

    subscription = repository.create_subscription(
        tenant_id=identity.tenant_id,
        product_id=request.product_id,
        plan_id=request.plan_id,
        price_id=request.price_id,
        trial=request.trial,
    )
    repository.record_idempotency_key(
        tenant_id=identity.tenant_id,
        idempotency_key=request.idempotency_key,
        checkout_id=request.checkout_id,
        product_id=request.product_id,
    )
    if not request.trial:
        # Activate ONLY the acquired shell.
        repository.set_entitlement(
            tenant_id=identity.tenant_id, product_id=request.product_id, allowed=True
        )
    return {
        "status": "CHECKOUT_OK",
        "subscription_id": subscription["subscription_id"],
        "product_id": request.product_id,
        "trial": request.trial,
    }


@router.get("/subscription")
def get_subscription(identity: Authenticated) -> dict[str, object]:
    row = _repository().get_subscription(tenant_id=identity.tenant_id)
    if row is None:
        raise HTTPException(status_code=404, detail="no subscription")
    return row


@router.post("/subscription/cancel")
def cancel_subscription(
    request: CancelRequest,
    identity: Authenticated,
) -> dict[str, object]:
    repository = _repository()
    subscription = repository.get_subscription(tenant_id=identity.tenant_id)
    if subscription is None:
        raise HTTPException(status_code=404, detail="no subscription")
    if request.at_period_end:
        result = repository.update_subscription_status(
            tenant_id=identity.tenant_id, status="CANCELLED_AT_PERIOD_END"
        )
    else:
        result = repository.update_subscription_status(
            tenant_id=identity.tenant_id, status="CANCELLED_IMMEDIATE"
        )
        repository.set_entitlement(
            tenant_id=identity.tenant_id,
            product_id=subscription["product_id"],
            allowed=False,
        )
    return result  # type: ignore[return-value]


@router.post("/subscription/change-plan")
def change_plan(
    request: ChangePlanRequest,
    identity: Authenticated,
) -> dict[str, object]:
    repository = _repository()
    price = repository.get_price(request.new_price_id)
    if price is None or price["plan_id"] != request.new_plan_id:
        raise HTTPException(status_code=422, detail="unknown plan/price")
    subscription = repository.get_subscription(tenant_id=identity.tenant_id)
    if subscription is None:
        raise HTTPException(status_code=404, detail="no subscription")
    if price["product_id"] != subscription["product_id"]:
        raise HTTPException(
            status_code=422, detail="plan change is scoped to the subscribed product"
        )
    return repository.change_plan(  # type: ignore[return-value]
        tenant_id=identity.tenant_id,
        new_plan_id=request.new_plan_id,
        new_price_id=request.new_price_id,
    )


@router.post("/subscription/dunning")
def enter_dunning(
    request: DunningRequest,
    identity: Authenticated,
) -> dict[str, object]:
    subscription = _repository().get_subscription(tenant_id=identity.tenant_id)
    if subscription is None:
        raise HTTPException(status_code=404, detail="no subscription")
    grace_until = datetime.now(UTC) + timedelta(days=request.grace_days)
    return _repository().update_subscription_status(  # type: ignore[return-value]
        tenant_id=identity.tenant_id,
        status="DUNNING",
        grace_until=grace_until,
    )


@router.post("/subscription/recover")
def recover_from_dunning(identity: Authenticated) -> dict[str, object]:
    repository = _repository()
    subscription = repository.get_subscription(tenant_id=identity.tenant_id)
    if subscription is None:
        raise HTTPException(status_code=404, detail="no subscription")
    if subscription["status"] != "DUNNING":
        raise HTTPException(status_code=422, detail="not in dunning")
    result = repository.update_subscription_status(
        tenant_id=identity.tenant_id, status="ACTIVE"
    )
    repository.set_entitlement(
        tenant_id=identity.tenant_id,
        product_id=subscription["product_id"],
        allowed=True,
    )
    return result  # type: ignore[return-value]


@router.post("/refund")
def record_refund(
    request: RefundRequest,
    identity: Authenticated,
) -> dict[str, object]:
    from psycopg.types.json import Jsonb

    repository = _repository()
    # Append-only refund audit (tenant-scoped table reuse via repository).
    with repository._cursor(role="axignal_worker", tenant_id=identity.tenant_id) as cursor:
        cursor.execute(
            """
            INSERT INTO tenant_private.billing_webhook_events
              (webhook_event_id, tenant_id, product_id, event_type, payload, signature)
            VALUES (gen_random_uuid(), %s, %s, 'refund_recorded', %s, 'sandbox-refund')
            """,
            (
                identity.tenant_id,
                "REFUND",
                Jsonb({"refund_id": request.refund_id, "amount_cents": request.amount_cents,
                       "reason": request.reason}),
            ),
        )
    return {
        "refund_id": request.refund_id,
        "amount_cents": request.amount_cents,
        "recorded": True,
    }


@router.get("/entitlements")
def get_entitlements(identity: Authenticated) -> dict[str, bool]:
    return _repository().entitlements(tenant_id=identity.tenant_id)


@router.post("/subscription/renew")
def renew_subscription(identity: Authenticated) -> dict[str, object]:
    try:
        return _repository().renew_subscription(tenant_id=identity.tenant_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="no renewable subscription") from exc


@router.post("/subscription/change-plan-directional")
def change_plan_directional(
    request: ChangePlanRequest, identity: Authenticated
) -> dict[str, object]:
    try:
        return _repository().change_plan_directional(
            tenant_id=identity.tenant_id,
            new_plan_id=request.new_plan_id,
            new_price_id=request.new_price_id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="no subscription") from exc


@router.post("/reconcile")
def reconcile(identity: Authenticated) -> dict[str, object]:
    return _repository().reconcile_entitlements(tenant_id=identity.tenant_id)


@router.get("/events")
def event_sequence(identity: Authenticated) -> list[dict[str, object]]:
    return _repository().event_sequence(tenant_id=identity.tenant_id)


@router.post("/webhooks")
def receive_webhook(
    request: WebhookRequest,
    identity: Authenticated,
) -> dict[str, object]:
    """HMAC-verified webhook with replay protection (persisted)."""
    import json as _json

    payload_text = _json.dumps(request.payload, sort_keys=True)
    expected = _sign(request.product_id, payload_text)
    if not hmac.compare_digest(expected, request.signature):
        raise HTTPException(status_code=401, detail="invalid signature")
    try:
        guard_time = datetime.fromisoformat(request.replay_guard)
    except ValueError as error:
        raise HTTPException(status_code=401, detail="invalid replay guard") from error
    if abs((datetime.now(UTC) - guard_time).total_seconds()) > 300:
        raise HTTPException(status_code=401, detail="stale replay guard")

    event_id = _repository().record_webhook_event(
        tenant_id=identity.tenant_id,
        product_id=request.product_id,
        event_type=request.event_type,
        payload=request.payload,
        signature=request.signature,
    )
    return {"webhook_event_id": str(event_id), "verified": True}


@router.get("/webhook-events")
def list_webhook_events(identity: Authenticated) -> list[dict[str, object]]:
    return _repository().list_webhook_events(tenant_id=identity.tenant_id)  # type: ignore[return-value]
