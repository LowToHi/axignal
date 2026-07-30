from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict

from axignal_api.billing_config import BillingSettings
from axignal_api.billing_repository import BillingRepository
from axignal_api.entitlement_repository import EntitlementRepository
from axignal_api.identity import AuthenticatedIdentity, require_identity

router = APIRouter(prefix="/v1/billing", tags=["billing"])
Authenticated = Annotated[AuthenticatedIdentity, Depends(require_identity)]


class BillingSelectionSummary(BaseModel):
    model_config = ConfigDict(extra="ignore")

    selection_id: UUID
    plan_code: str
    pending_plan_code: str | None
    state: str
    current_period_end: datetime | None
    cancel_at_period_end: bool


class EntitlementSummary(BaseModel):
    model_config = ConfigDict(extra="ignore")

    entitlement_id: UUID
    entitlement_kind: Literal["TRIAL", "PAID_MONTHLY"]
    plan_code: str
    state: Literal["ACTIVE", "READ_ONLY", "SUSPENDED", "CANCELLED"]
    expires_at: datetime | None
    unlimited_ai_tokens: bool
    token_budget_total: int | None
    token_budget_reserved: int
    token_budget_consumed: int


class BillingLedgerSummary(BaseModel):
    model_config = ConfigDict(extra="ignore")

    ledger_entry_id: UUID
    occurred_at: datetime
    event_type: str
    plan_code: str | None
    previous_state: str | None
    new_state: str | None
    provider_event_id: str | None
    payload_digest: str | None
    operation_actor: Literal["USER", "PROVIDER", "SYSTEM"]


class BillingSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: Literal["STRIPE", "DETERMINISTIC_TEST_PROVIDER"]
    runtime_enabled: bool
    checkout_enabled: bool
    lifecycle_enabled: bool
    external_stripe_verified: Literal[False] = False
    commercial_payment_evidence: Literal[False] = False
    selection: BillingSelectionSummary | None
    entitlement: EntitlementSummary | None
    ledger: list[BillingLedgerSummary]


def _actor_classification(row: dict[str, Any]) -> Literal["USER", "PROVIDER", "SYSTEM"]:
    actor = str(row.get("actor_subject") or "").casefold()
    if row.get("provider_event_id") is not None or "webhook" in actor:
        return "PROVIDER"
    if actor.startswith(("system", "deterministic-test")):
        return "SYSTEM"
    return "USER"


@router.get("/summary", response_model=BillingSummary)
def billing_summary(identity: Authenticated) -> BillingSummary:
    settings = BillingSettings.from_env()
    try:
        settings.require_store()
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    assert settings.database_url is not None
    billing = BillingRepository(settings.database_url)
    entitlements = EntitlementRepository(settings.database_url)
    selection_row = billing.current_selection(tenant_id=identity.tenant_id)
    entitlement_row = entitlements.current_entitlement(tenant_id=identity.tenant_id)
    ledger_rows = billing.ledger(tenant_id=identity.tenant_id)

    selection = (
        BillingSelectionSummary.model_validate(selection_row)
        if selection_row is not None
        else None
    )
    entitlement = (
        EntitlementSummary.model_validate(entitlement_row)
        if entitlement_row is not None
        else None
    )
    ledger = [
        BillingLedgerSummary(
            ledger_entry_id=row["ledger_entry_id"],
            occurred_at=row["occurred_at"],
            event_type=str(row["ledger_event_type"]),
            plan_code=(str(row["plan_code"]) if row.get("plan_code") else None),
            previous_state=(
                str(row["previous_state"]) if row.get("previous_state") else None
            ),
            new_state=(str(row["new_state"]) if row.get("new_state") else None),
            provider_event_id=(
                str(row["provider_event_id"])
                if row.get("provider_event_id")
                else None
            ),
            payload_digest=(
                str(row["payload_digest"]) if row.get("payload_digest") else None
            ),
            operation_actor=_actor_classification(row),
        )
        for row in ledger_rows
    ]
    return BillingSummary(
        provider=(
            "DETERMINISTIC_TEST_PROVIDER"
            if settings.billing_provider == "test"
            else "STRIPE"
        ),
        runtime_enabled=settings.billing_runtime_enabled,
        checkout_enabled=settings.stripe_checkout_enabled,
        lifecycle_enabled=settings.stripe_lifecycle_enabled,
        selection=selection,
        entitlement=entitlement,
        ledger=ledger,
    )
