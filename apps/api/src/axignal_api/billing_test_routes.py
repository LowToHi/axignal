from __future__ import annotations

import json
import time
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict

from axignal_api.billing_config import BillingSettings
from axignal_api.billing_repository import BillingRepository
from axignal_api.billing_routes import stripe_webhook
from axignal_api.identity import AuthenticatedIdentity, require_identity
from axignal_api.stripe_signature import build_test_stripe_signature

router = APIRouter(prefix="/v1/billing/test", tags=["billing-test"])
Authenticated = Annotated[AuthenticatedIdentity, Depends(require_identity)]
TestAction = Literal[
    "COMPLETE_CHECKOUT",
    "CONFIRM_UPGRADE",
    "CONFIRM_CANCELLATION",
    "ROLLBACK",
]


class DeterministicProviderEventCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: TestAction


def _test_runtime() -> tuple[BillingSettings, BillingRepository]:
    settings = BillingSettings.from_env()
    try:
        settings.require_test_provider()
        settings.require_webhooks()
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    assert settings.database_url is not None
    return settings, BillingRepository(settings.database_url)


def _next_event_time(current: dict[str, Any], now: datetime) -> datetime:
    previous = current.get("last_provider_event_created_at")
    if not isinstance(previous, datetime):
        return now
    previous = previous.astimezone(UTC)
    return max(now, previous + timedelta(seconds=1))


def _subscription_object(
    *,
    selection_id: UUID,
    subscription_id: str,
    item_id: str,
    price_id: str,
    cancel_at_period_end: bool,
    event_time: datetime,
    status_value: str = "active",
) -> dict[str, object]:
    return {
        "id": subscription_id,
        "object": "subscription",
        "status": status_value,
        "customer": f"cus_test_axignal_{selection_id.hex}",
        "metadata": {"axignal_selection_id": str(selection_id)},
        "items": {"data": [{"id": item_id, "price": {"id": price_id}}]},
        "current_period_end": int((event_time + timedelta(days=30)).timestamp()),
        "cancel_at_period_end": cancel_at_period_end,
    }


def _event(
    *,
    event_id: str,
    event_type: str,
    created_at: datetime,
    obj: dict[str, object],
) -> bytes:
    return json.dumps(
        {
            "id": event_id,
            "object": "event",
            "type": event_type,
            "created": int(created_at.timestamp()),
            "livemode": False,
            "data": {"object": obj},
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


async def _deliver_signed_event(
    *,
    payload: bytes,
    secret: str,
) -> dict[str, object]:
    timestamp = int(time.time())
    signature = build_test_stripe_signature(
        payload=payload,
        secret=secret,
        timestamp=timestamp,
    )
    delivered = False

    async def receive() -> dict[str, object]:
        nonlocal delivered
        if delivered:
            return {"type": "http.request", "body": b"", "more_body": False}
        delivered = True
        return {"type": "http.request", "body": payload, "more_body": False}

    request = Request(
        {
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": "2.4"},
            "http_version": "1.1",
            "method": "POST",
            "scheme": "http",
            "path": "/v1/billing/stripe/webhook",
            "raw_path": b"/v1/billing/stripe/webhook",
            "query_string": b"",
            "headers": [],
            "client": ("127.0.0.1", 0),
            "server": ("127.0.0.1", 0),
        },
        receive,
    )
    return await stripe_webhook(request, signature)


@router.post("/provider-event")
async def deterministic_provider_event(
    command: DeterministicProviderEventCommand,
    identity: Authenticated,
) -> dict[str, object]:
    settings, repository = _test_runtime()
    current = repository.current_selection(tenant_id=identity.tenant_id)
    if current is None:
        raise HTTPException(status_code=404, detail="No billing selection found")

    selection_id = UUID(str(current["selection_id"]))
    subscription_id = str(
        current.get("stripe_subscription_id")
        or f"sub_test_axignal_{selection_id.hex}"
    )
    item_id = str(
        current.get("stripe_subscription_item_id")
        or f"si_test_axignal_{selection_id.hex}"
    )
    now = datetime.now(UTC)
    event_time = _next_event_time(current, now)
    assert settings.stripe_webhook_secret is not None

    if command.action == "ROLLBACK":
        rolled_back = repository.rollback(
            selection_id=selection_id,
            actor_subject="deterministic-test-rollback",
            now=now,
        )
        return {
            "provider": "DETERMINISTIC_TEST_PROVIDER",
            "external_stripe_verified": False,
            "state": str(rolled_back["state"]),
            "selection_id": str(selection_id),
            "events": [],
        }

    events: list[dict[str, object]] = []
    if command.action == "COMPLETE_CHECKOUT":
        if current["state"] not in {"CHECKOUT_CREATED", "CHECKOUT_COMPLETED"}:
            raise HTTPException(status_code=409, detail="Checkout is not pending")
        checkout_id = str(current.get("stripe_checkout_session_id") or "")
        checkout_payload = _event(
            event_id=f"evt_test_checkout_{selection_id.hex}",
            event_type="checkout.session.completed",
            created_at=event_time,
            obj={
                "id": checkout_id,
                "object": "checkout.session",
                "client_reference_id": str(selection_id),
                "customer": f"cus_test_axignal_{selection_id.hex}",
                "subscription": subscription_id,
                "metadata": {"axignal_selection_id": str(selection_id)},
            },
        )
        events.append(
            await _deliver_signed_event(
                payload=checkout_payload,
                secret=settings.stripe_webhook_secret,
            )
        )
        subscription_time = event_time + timedelta(seconds=1)
        subscription_payload = _event(
            event_id=f"evt_test_subscription_created_{selection_id.hex}",
            event_type="customer.subscription.created",
            created_at=subscription_time,
            obj=_subscription_object(
                selection_id=selection_id,
                subscription_id=subscription_id,
                item_id=item_id,
                price_id=settings.price_for_plan(str(current["plan_code"])),
                cancel_at_period_end=False,
                event_time=subscription_time,
            ),
        )
        events.append(
            await _deliver_signed_event(
                payload=subscription_payload,
                secret=settings.stripe_webhook_secret,
            )
        )
    elif command.action == "CONFIRM_UPGRADE":
        if current["state"] != "UPGRADE_PENDING":
            raise HTTPException(status_code=409, detail="Upgrade is not pending")
        target = str(current.get("pending_plan_code") or "")
        payload = _event(
            event_id=f"evt_test_upgrade_{selection_id.hex}",
            event_type="customer.subscription.updated",
            created_at=event_time,
            obj=_subscription_object(
                selection_id=selection_id,
                subscription_id=subscription_id,
                item_id=item_id,
                price_id=settings.price_for_plan(target),
                cancel_at_period_end=False,
                event_time=event_time,
            ),
        )
        events.append(
            await _deliver_signed_event(
                payload=payload,
                secret=settings.stripe_webhook_secret,
            )
        )
    elif command.action == "CONFIRM_CANCELLATION":
        if current["state"] not in {"CANCEL_PENDING", "CANCEL_AT_PERIOD_END"}:
            raise HTTPException(status_code=409, detail="Cancellation is not pending")
        cancel_at_period_end = bool(current.get("cancel_at_period_end"))
        event_type = (
            "customer.subscription.updated"
            if cancel_at_period_end and current["state"] == "CANCEL_PENDING"
            else "customer.subscription.deleted"
        )
        status_value = "active" if event_type.endswith("updated") else "canceled"
        payload = _event(
            event_id=(
                f"evt_test_cancel_period_end_{selection_id.hex}"
                if event_type.endswith("updated")
                else f"evt_test_cancel_terminal_{selection_id.hex}"
            ),
            event_type=event_type,
            created_at=event_time,
            obj=_subscription_object(
                selection_id=selection_id,
                subscription_id=subscription_id,
                item_id=item_id,
                price_id=settings.price_for_plan(str(current["plan_code"])),
                cancel_at_period_end=cancel_at_period_end,
                event_time=event_time,
                status_value=status_value,
            ),
        )
        events.append(
            await _deliver_signed_event(
                payload=payload,
                secret=settings.stripe_webhook_secret,
            )
        )

    updated = repository.current_selection(tenant_id=identity.tenant_id)
    assert updated is not None
    return {
        "provider": "DETERMINISTIC_TEST_PROVIDER",
        "external_stripe_verified": False,
        "state": str(updated["state"]),
        "selection_id": str(selection_id),
        "events": events,
    }
