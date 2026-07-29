from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Annotated, Any, Literal
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field

from axignal_api.billing_config import BillingSettings
from axignal_api.billing_repository import BillingRepository
from axignal_api.identity import AuthenticatedIdentity, require_identity
from axignal_api.stripe_gateway import StripeGateway
from axignal_api.stripe_signature import verify_stripe_signature

router = APIRouter(prefix="/v1/billing", tags=["billing"])
Authenticated = Annotated[AuthenticatedIdentity, Depends(require_identity)]
PlanCode = Literal["PROFESSIONAL_MONTHLY", "TEAM_MONTHLY"]
SUPPORTED_EVENTS = {
    "checkout.session.completed",
    "checkout.session.expired",
    "customer.subscription.created",
    "customer.subscription.updated",
    "customer.subscription.deleted",
    "invoice.paid",
    "invoice.payment_failed",
}


class PaidSelectionCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operation_id: str = Field(pattern=r"^op_[A-Za-z0-9_-]{8,}$", max_length=200)
    plan_code: PlanCode
    confirm_paid_selection: Literal[True]


class PaidUpgradeCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operation_id: str = Field(pattern=r"^op_[A-Za-z0-9_-]{8,}$", max_length=200)
    target_plan_code: Literal["TEAM_MONTHLY"]
    billing_effect: Literal["IMMEDIATE_WITHOUT_PRORATION"]
    confirm_upgrade: Literal[True]


class PaidCancellationCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operation_id: str = Field(pattern=r"^op_[A-Za-z0-9_-]{8,}$", max_length=200)
    cancel_at_period_end: bool
    confirm_cancellation: Literal[True]


class CheckoutSessionView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    selection_id: UUID
    plan_code: PlanCode
    state: str
    checkout_url: str


class BillingSelectionView(BaseModel):
    model_config = ConfigDict(extra="ignore")

    selection_id: UUID
    plan_code: PlanCode
    pending_plan_code: PlanCode | None
    state: str
    current_period_end: datetime | None
    cancel_at_period_end: bool


class ProviderCommandView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    selection_id: UUID
    state: str
    provider_status: str
    cancel_at_period_end: bool


def _settings_repository() -> tuple[BillingSettings, BillingRepository]:
    settings = BillingSettings.from_env()
    try:
        settings.require_store()
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    assert settings.database_url is not None
    return settings, BillingRepository(settings.database_url)


def _store_error(exc: Exception) -> None:
    message = str(exc)
    known = {
        "billing_operation_id_conflict": (409, "Billing operation id conflict"),
        "paid_entitlement_already_exists": (409, "Paid entitlement already exists"),
        "billing_selection_not_found": (404, "Billing selection not found"),
        "active_billing_subscription_required": (403, "Active paid subscription required"),
        "unsupported_upgrade": (422, "Unsupported upgrade path"),
        "upgrade_path_not_allowed": (409, "Upgrade path is not allowed"),
    }
    for marker, (code, detail) in known.items():
        if marker in message:
            raise HTTPException(status_code=code, detail=detail) from exc
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=f"Billing runtime unavailable: {exc.__class__.__name__}",
    ) from exc


def _selection_view(row: dict[str, Any]) -> BillingSelectionView:
    return BillingSelectionView.model_validate(row)


@router.post(
    "/checkout-sessions",
    response_model=CheckoutSessionView,
    status_code=status.HTTP_201_CREATED,
)
def create_checkout_session(
    command: PaidSelectionCommand,
    identity: Authenticated,
) -> CheckoutSessionView:
    settings, repository = _settings_repository()
    try:
        settings.require_checkout()
        assert settings.stripe_account_id is not None
        selection = repository.request_selection(
            tenant_id=identity.tenant_id,
            operation_id=command.operation_id,
            plan_code=command.plan_code,
            provider_account_id=settings.stripe_account_id,
            actor_subject=identity.subject,
        )
        result = StripeGateway(settings).create_checkout_session(
            selection_id=selection["selection_id"],
            plan_code=command.plan_code,
            customer_email=identity.email,
            operation_id=command.operation_id,
        )
        updated = repository.mark_checkout_created(
            tenant_id=identity.tenant_id,
            selection_id=selection["selection_id"],
            checkout_session_id=result.session_id,
            price_id=result.price_id,
            actor_subject=identity.subject,
        )
    except RuntimeError as exc:
        if "disabled" in str(exc) or "required" in str(exc) or "mismatch" in str(exc):
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        _store_error(exc)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Stripe sandbox request failed") from exc
    return CheckoutSessionView(
        selection_id=updated["selection_id"],
        plan_code=updated["plan_code"],
        state=updated["state"],
        checkout_url=result.url,
    )


@router.get("/current", response_model=BillingSelectionView)
def current_billing(identity: Authenticated) -> BillingSelectionView:
    _, repository = _settings_repository()
    row = repository.current_selection(tenant_id=identity.tenant_id)
    if row is None:
        raise HTTPException(status_code=404, detail="No billing selection found")
    return _selection_view(row)


@router.post("/subscription/upgrade", response_model=ProviderCommandView)
def upgrade_subscription(
    command: PaidUpgradeCommand,
    identity: Authenticated,
) -> ProviderCommandView:
    settings, repository = _settings_repository()
    try:
        settings.require_lifecycle()
        current = repository.current_selection(tenant_id=identity.tenant_id)
        if current is None:
            raise RuntimeError("active_billing_subscription_required")
        if (
            current["state"] == "UPGRADE_PENDING"
            and current.get("pending_plan_code") == command.target_plan_code
        ):
            pending = current
        else:
            pending = repository.request_upgrade(
                tenant_id=identity.tenant_id,
                target_plan_code=command.target_plan_code,
                target_price_id=settings.price_for_plan(command.target_plan_code),
                actor_subject=identity.subject,
            )
        subscription_id = pending.get("stripe_subscription_id")
        item_id = pending.get("stripe_subscription_item_id")
        if not subscription_id or not item_id:
            raise RuntimeError("Stripe subscription identifiers are unavailable")
        result = StripeGateway(settings).upgrade_subscription(
            subscription_id=str(subscription_id),
            subscription_item_id=str(item_id),
            target_plan_code=command.target_plan_code,
            operation_id=command.operation_id,
        )
    except RuntimeError as exc:
        if "disabled" in str(exc) or "required" in str(exc) or "unavailable" in str(exc):
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        _store_error(exc)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Stripe sandbox request failed") from exc
    return ProviderCommandView(
        selection_id=pending["selection_id"],
        state=pending["state"],
        provider_status=result.status,
        cancel_at_period_end=result.cancel_at_period_end,
    )


@router.post("/subscription/cancel", response_model=ProviderCommandView)
def cancel_subscription(
    command: PaidCancellationCommand,
    identity: Authenticated,
) -> ProviderCommandView:
    settings, repository = _settings_repository()
    try:
        settings.require_lifecycle()
        current = repository.current_selection(tenant_id=identity.tenant_id)
        if current is None:
            raise RuntimeError("active_billing_subscription_required")
        if (
            current["state"] == "CANCEL_PENDING"
            and bool(current["cancel_at_period_end"]) == command.cancel_at_period_end
        ):
            pending = current
        else:
            pending = repository.request_cancellation(
                tenant_id=identity.tenant_id,
                cancel_at_period_end=command.cancel_at_period_end,
                actor_subject=identity.subject,
            )
        subscription_id = pending.get("stripe_subscription_id")
        if not subscription_id:
            raise RuntimeError("Stripe subscription identifier is unavailable")
        result = StripeGateway(settings).cancel_subscription(
            subscription_id=str(subscription_id),
            cancel_at_period_end=command.cancel_at_period_end,
            operation_id=command.operation_id,
        )
    except RuntimeError as exc:
        if "disabled" in str(exc) or "required" in str(exc) or "unavailable" in str(exc):
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        _store_error(exc)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Stripe sandbox request failed") from exc
    return ProviderCommandView(
        selection_id=pending["selection_id"],
        state=pending["state"],
        provider_status=result.status,
        cancel_at_period_end=result.cancel_at_period_end,
    )


def _as_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _selection_id(obj: dict[str, Any]) -> UUID | None:
    metadata = _as_dict(obj.get("metadata"))
    candidate = obj.get("client_reference_id") or metadata.get("axignal_selection_id")
    if candidate is None:
        parent = _as_dict(obj.get("parent"))
        subscription_details = _as_dict(parent.get("subscription_details"))
        candidate = _as_dict(subscription_details.get("metadata")).get(
            "axignal_selection_id"
        )
    if candidate is None:
        return None
    try:
        return UUID(str(candidate))
    except ValueError as exc:
        raise ValueError("stripe_selection_id_invalid") from exc


def _subscription_id(obj: dict[str, Any]) -> str | None:
    value = obj.get("subscription")
    if isinstance(value, str):
        return value
    if obj.get("object") == "subscription" and isinstance(obj.get("id"), str):
        return str(obj["id"])
    parent = _as_dict(obj.get("parent"))
    subscription_details = _as_dict(parent.get("subscription_details"))
    nested = subscription_details.get("subscription")
    return str(nested) if isinstance(nested, str) else None


def _subscription_item(obj: dict[str, Any]) -> tuple[str | None, str | None]:
    items = _as_dict(obj.get("items"))
    data = items.get("data")
    if not isinstance(data, list) or not data:
        lines = _as_dict(obj.get("lines"))
        data = lines.get("data")
    if not isinstance(data, list) or not data or not isinstance(data[0], dict):
        return None, None
    item = data[0]
    price = _as_dict(item.get("price"))
    return (
        str(item["id"]) if isinstance(item.get("id"), str) else None,
        str(price["id"]) if isinstance(price.get("id"), str) else None,
    )


def _timestamp(value: object) -> datetime | None:
    if isinstance(value, int):
        return datetime.fromtimestamp(value, tz=UTC)
    return None


@router.post("/stripe/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: Annotated[str | None, Header(alias="Stripe-Signature")] = None,
) -> dict[str, object]:
    settings, repository = _settings_repository()
    try:
        settings.require_webhooks()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    body = await request.body()
    try:
        verify_stripe_signature(
            payload=body,
            header=stripe_signature or "",
            secret=settings.stripe_webhook_secret or "",
            tolerance_seconds=settings.webhook_tolerance_seconds,
        )
        event = json.loads(body)
    except (ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail="Invalid Stripe webhook") from exc
    if not isinstance(event, dict):
        raise HTTPException(status_code=400, detail="Invalid Stripe event")
    event_id = event.get("id")
    event_type = event.get("type")
    created = event.get("created")
    livemode = event.get("livemode")
    if (
        not isinstance(event_id, str)
        or not isinstance(event_type, str)
        or not isinstance(created, int)
        or not isinstance(livemode, bool)
    ):
        raise HTTPException(status_code=400, detail="Incomplete Stripe event envelope")
    if event_type not in SUPPORTED_EVENTS:
        return {"received": True, "disposition": "IGNORED_UNSUPPORTED"}
    if settings.stripe_sandbox_only and livemode:
        raise HTTPException(status_code=400, detail="Live Stripe events are forbidden")

    data = _as_dict(event.get("data"))
    obj = _as_dict(data.get("object"))
    try:
        selection_id = _selection_id(obj)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid AXIGNAL selection id") from exc
    item_id, price_id = _subscription_item(obj)
    plan_code = settings.plan_for_price(price_id)
    subscription_status = (
        str(obj.get("status")) if event_type.startswith("customer.subscription.") else None
    )
    amount = obj.get("amount_paid")
    if not isinstance(amount, int):
        amount = obj.get("amount_due") if isinstance(obj.get("amount_due"), int) else None
    currency = str(obj["currency"]) if isinstance(obj.get("currency"), str) else None
    payload_digest = hashlib.sha256(body).hexdigest()
    assert settings.stripe_account_id is not None
    try:
        result = repository.apply_stripe_event(
            event_id=event_id,
            event_type=event_type,
            event_created_at=datetime.fromtimestamp(created, tz=UTC),
            livemode=livemode,
            payload_digest=payload_digest,
            provider_account_id=settings.stripe_account_id,
            selection_id=selection_id,
            checkout_session_id=(
                str(obj["id"])
                if event_type.startswith("checkout.session.")
                and isinstance(obj.get("id"), str)
                else None
            ),
            customer_id=(
                str(obj["customer"]) if isinstance(obj.get("customer"), str) else None
            ),
            subscription_id=_subscription_id(obj),
            subscription_item_id=item_id,
            price_id=price_id,
            plan_code=plan_code,
            subscription_status=subscription_status,
            current_period_end=_timestamp(obj.get("current_period_end")),
            cancel_at_period_end=bool(obj.get("cancel_at_period_end", False)),
            amount_minor=amount,
            currency=currency,
            actor_subject="stripe-signed-webhook",
        )
    except Exception as exc:
        message = str(exc)
        if "stripe_event_id_payload_conflict" in message:
            raise HTTPException(status_code=409, detail="Stripe event conflict") from exc
        if "billing_selection_not_found_for_event" in message:
            raise HTTPException(status_code=409, detail="Stripe event is not mapped") from exc
        if "mismatch" in message or "forbidden" in message:
            raise HTTPException(status_code=400, detail="Stripe event rejected") from exc
        raise HTTPException(status_code=503, detail="Stripe event processing failed") from exc
    return {"received": True, **result}
