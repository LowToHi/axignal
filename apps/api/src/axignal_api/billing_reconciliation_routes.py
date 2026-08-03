from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from typing import Annotated, Literal

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict

from axignal_api.billing_config import BillingSettings
from axignal_api.billing_repository import BillingRepository
from axignal_api.identity import AuthenticatedIdentity, require_identity
from axignal_api.seat_repository import SeatRepository
from axignal_api.stripe_gateway import StripeGateway

router = APIRouter(prefix="/v1/billing", tags=["billing-reconciliation"])
Authenticated = Annotated[AuthenticatedIdentity, Depends(require_identity)]
ADMIN_ROLES = {"ORG_OWNER", "ORG_ADMIN", "BILLING_ADMIN"}


class ReconciliationView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result: Literal["MATCH", "REPAIRED"]
    provider: Literal["STRIPE", "DETERMINISTIC_TEST_PROVIDER"]
    selection_id: str
    subscription_id: str
    plan_code: str
    local_state: str
    provider_state: str
    drift_fields: list[str]
    snapshot_digest: str
    repair_disposition: str | None
    seat_capacity: int
    occupied_seats: int
    available_seats: int
    browser_entitlement_authority: Literal[False] = False


def _expected_state(status_value: str, cancel_at_period_end: bool) -> str:
    if status_value == "active":
        return "CANCEL_AT_PERIOD_END" if cancel_at_period_end else "ACTIVE"
    if status_value in {"past_due", "unpaid"}:
        return "SUSPENDED"
    if status_value == "canceled":
        return "CANCELLED"
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Stripe subscription status is not reconcilable",
    )


def _authorise(identity: AuthenticatedIdentity, selected_by: str) -> None:
    if identity.subject == selected_by:
        return
    if ADMIN_ROLES.intersection(identity.role_ids):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Billing administration role required",
    )


@router.post("/subscription/reconcile", response_model=ReconciliationView)
def reconcile_subscription(identity: Authenticated) -> ReconciliationView:
    settings = BillingSettings.from_env()
    try:
        settings.require_lifecycle()
        assert settings.database_url is not None
        repository = BillingRepository(settings.database_url)
        current = repository.current_selection(tenant_id=identity.tenant_id)
        if current is None:
            raise HTTPException(status_code=404, detail="No billing selection found")
        _authorise(identity, str(current["selected_by"]))

        subscription_id = str(current.get("stripe_subscription_id") or "")
        if not subscription_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Stripe subscription identifier is unavailable",
            )
        snapshot = StripeGateway(settings).retrieve_subscription_snapshot(
            subscription_id=subscription_id,
            expected_plan_code=str(current["plan_code"]),
            expected_customer_id=(
                str(current["stripe_customer_id"])
                if current.get("stripe_customer_id")
                else None
            ),
            expected_item_id=(
                str(current["stripe_subscription_item_id"])
                if current.get("stripe_subscription_item_id")
                else None
            ),
            expected_period_end=current.get("current_period_end"),
        )
        provider_plan = settings.plan_for_price(snapshot.price_id)
        if provider_plan is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Stripe price is not mapped to an AXIGNAL plan",
            )
        provider_state = _expected_state(
            snapshot.status,
            snapshot.cancel_at_period_end,
        )
        canonical = {
            "subscription_id": snapshot.subscription_id,
            "customer_id": snapshot.customer_id,
            "subscription_item_id": snapshot.subscription_item_id,
            "price_id": snapshot.price_id,
            "plan_code": provider_plan,
            "status": snapshot.status,
            "current_period_end": (
                snapshot.current_period_end.isoformat()
                if snapshot.current_period_end is not None
                else None
            ),
            "cancel_at_period_end": snapshot.cancel_at_period_end,
        }
        canonical_bytes = json.dumps(
            canonical,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        digest = hashlib.sha256(canonical_bytes).hexdigest()

        comparisons = {
            "stripe_subscription_id": snapshot.subscription_id,
            "stripe_customer_id": snapshot.customer_id,
            "stripe_subscription_item_id": snapshot.subscription_item_id,
            "stripe_price_id": snapshot.price_id,
            "plan_code": provider_plan,
            "state": provider_state,
            "cancel_at_period_end": snapshot.cancel_at_period_end,
            "current_period_end": snapshot.current_period_end,
        }
        drift_fields = sorted(
            key for key, provider_value in comparisons.items() if current.get(key) != provider_value
        )
        repair_disposition: str | None = None
        if drift_fields:
            now = datetime.now(UTC).replace(microsecond=0)
            previous = current.get("last_provider_event_created_at")
            event_time = (
                max(now, previous.astimezone(UTC) + timedelta(seconds=1))
                if isinstance(previous, datetime)
                else now
            )
            event_type = (
                "customer.subscription.deleted"
                if snapshot.status == "canceled"
                else "customer.subscription.updated"
            )
            result = repository.apply_stripe_event(
                event_id=f"reconcile_{digest}",
                event_type=event_type,
                event_created_at=event_time,
                livemode=False,
                payload_digest=digest,
                provider_account_id=settings.stripe_account_id or "",
                selection_id=current["selection_id"],
                checkout_session_id=current.get("stripe_checkout_session_id"),
                customer_id=snapshot.customer_id,
                subscription_id=snapshot.subscription_id,
                subscription_item_id=snapshot.subscription_item_id,
                price_id=snapshot.price_id,
                plan_code=provider_plan,
                subscription_status=snapshot.status,
                current_period_end=snapshot.current_period_end,
                cancel_at_period_end=snapshot.cancel_at_period_end,
                amount_minor=None,
                currency=None,
                actor_subject="stripe-reconciliation",
            )
            repair_disposition = str(result["disposition"])
            current = repository.current_selection(tenant_id=identity.tenant_id)
            assert current is not None

        seats = SeatRepository(settings.database_url).summary(tenant_id=identity.tenant_id)
        seat_entitlement = seats["seat_entitlement"]
        return ReconciliationView(
            result="REPAIRED" if drift_fields else "MATCH",
            provider=(
                "DETERMINISTIC_TEST_PROVIDER"
                if settings.billing_provider == "test"
                else "STRIPE"
            ),
            selection_id=str(current["selection_id"]),
            subscription_id=subscription_id,
            plan_code=str(current["plan_code"]),
            local_state=str(current["state"]),
            provider_state=provider_state,
            drift_fields=drift_fields,
            snapshot_digest=digest,
            repair_disposition=repair_disposition,
            seat_capacity=int(seat_entitlement["seat_capacity"]),
            occupied_seats=int(seats["occupied_seats"]),
            available_seats=int(seats["available_seats"]),
        )
    except HTTPException:
        raise
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Stripe reconciliation request failed",
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Billing reconciliation unavailable: {exc}",
        ) from exc
