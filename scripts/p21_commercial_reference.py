#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Iterable

AUTHORITY_ORDER = (
    "CATALOG_READ",
    "PRICE_PROPOSAL",
    "CHECKOUT_REQUEST",
    "BILLING_LEDGER_WRITE",
    "ENTITLEMENT_DERIVATION",
    "BOUNDED_ENTITLEMENT_ACTIVATION",
    "CANCELLATION_REQUEST",
    "HUMAN_COMMERCIAL_ACTIVATION",
)


def canonical_digest(value: Any) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def money_minor(value: str | int | Decimal, exponent: int = 2) -> int:
    if exponent < 0 or exponent > 4:
        raise ValueError("currency_exponent_out_of_range")
    quant = Decimal(10) ** -exponent
    amount = Decimal(str(value)).quantize(quant, rounding=ROUND_HALF_UP)
    return int(amount * (10**exponent))


def server_price_decision(
    *,
    requested_plan_code: str,
    client_price_id: str | None,
    server_mapping: dict[str, dict[str, Any]],
    currency: str,
) -> dict[str, Any]:
    mapping = server_mapping.get(requested_plan_code)
    if mapping is None:
        return {"decision": "DENY", "reason": "unknown_plan"}
    if mapping.get("currency") != currency:
        return {"decision": "DENY", "reason": "currency_mismatch"}
    if client_price_id and client_price_id != mapping.get("provider_price_id"):
        return {"decision": "DENY", "reason": "client_price_tampering"}
    if mapping.get("status") != "ACTIVE_SANDBOX":
        return {"decision": "DENY", "reason": "price_mapping_not_active"}
    return {
        "decision": "ALLOW_CHECKOUT_REQUEST",
        "provider_price_id": mapping["provider_price_id"],
        "amount_minor": int(mapping["amount_minor"]),
        "currency": currency,
    }


def provider_event_decision(
    *,
    signature_valid: bool,
    event_id: str,
    seen_event_ids: set[str],
    provider_account_match: bool,
    livemode: bool,
    expected_livemode: bool,
    event_created_at: int,
    last_applied_created_at: int | None,
) -> dict[str, Any]:
    if not signature_valid:
        return {"decision": "QUARANTINE", "reason": "invalid_signature"}
    if event_id in seen_event_ids:
        return {"decision": "IGNORE_IDEMPOTENT", "reason": "duplicate_event"}
    if not provider_account_match:
        return {"decision": "DENY", "reason": "provider_account_mismatch"}
    if livemode != expected_livemode:
        return {"decision": "DENY", "reason": "livemode_mismatch"}
    if last_applied_created_at is not None and event_created_at < last_applied_created_at:
        return {"decision": "STALE", "reason": "out_of_order_event"}
    return {"decision": "APPLY_TO_LEDGER", "reason": "verified_new_event"}


def derive_entitlement_state(
    *,
    subscription_state: str,
    invoice_state: str,
    tenant_active: bool,
    policy_current: bool,
    rights_current: bool,
    period_end_reached: bool = False,
) -> str:
    if not tenant_active or not policy_current or not rights_current:
        return "DENY"
    if subscription_state == "ACTIVE" and invoice_state == "PAID_VERIFIED":
        return "ACTIVE_LIMITED"
    if subscription_state == "CANCEL_AT_PERIOD_END" and not period_end_reached:
        return "ACTIVE_LIMITED"
    if subscription_state in {"PAST_DUE", "DISPUTED"}:
        return "SUSPENDED"
    if subscription_state in {"CANCELLED", "REFUNDED"} or period_end_reached:
        return "READ_ONLY_RETENTION"
    return "DENY"


def cancellation_decision(
    *,
    request_id: str,
    seen_request_ids: set[str],
    mode: str,
    human_approved: bool,
) -> dict[str, str]:
    if request_id in seen_request_ids:
        return {"decision": "IDEMPOTENT_REPLAY"}
    if mode == "PERIOD_END":
        return {"decision": "CANCEL_AT_PERIOD_END"}
    if mode == "IMMEDIATE" and human_approved:
        return {"decision": "CANCEL_IMMEDIATE_BOUNDED"}
    return {"decision": "HUMAN_REVIEW_REQUIRED"}


def refund_decision(
    *,
    payment_verified: bool,
    amount_minor: int,
    refundable_minor: int,
    independent_approval: bool,
) -> dict[str, Any]:
    if not payment_verified:
        return {"decision": "DENY", "reason": "payment_not_verified"}
    if amount_minor <= 0 or amount_minor > refundable_minor:
        return {"decision": "DENY", "reason": "refund_amount_invalid"}
    if not independent_approval:
        return {"decision": "HUMAN_REVIEW_REQUIRED"}
    return {"decision": "ALLOW_PROVIDER_REFUND_REQUEST", "amount_minor": amount_minor}


def tax_decision(
    *,
    automatic_tax_requested: bool,
    active_registration: bool,
    customer_location_evidence: bool,
) -> str:
    if automatic_tax_requested and not active_registration:
        return "DENY_REGISTRATION_REQUIRED"
    if not customer_location_evidence:
        return "HUMAN_TAX_REVIEW"
    return "ALLOW_TAX_CALCULATION_EVIDENCE_ONLY"


def margin_scenario(
    *,
    net_revenue_minor: int,
    variable_costs_minor: Iterable[int],
    contribution_margin_floor_bps: int,
) -> dict[str, Any]:
    if net_revenue_minor <= 0:
        raise ValueError("net_revenue_must_be_positive")
    total_cost = sum(int(value) for value in variable_costs_minor)
    contribution = net_revenue_minor - total_cost
    bps = int(
        (Decimal(contribution) / Decimal(net_revenue_minor) * Decimal(10000)).quantize(
            Decimal("1"),
            rounding=ROUND_HALF_UP,
        )
    )
    return {
        "net_revenue_minor": net_revenue_minor,
        "variable_cost_minor": total_cost,
        "contribution_margin_minor": contribution,
        "contribution_margin_bps": bps,
        "decision": (
            "PASS_CANDIDATE" if bps >= contribution_margin_floor_bps else "BLOCK"
        ),
    }


def commercial_readiness(gates: dict[str, str]) -> str:
    if not gates:
        return "DENY"
    return (
        "READY_ENGINEERING_ONLY"
        if all(value == "PASS" for value in gates.values())
        else "DENY"
    )


def may_activate_paid_entitlement(
    *,
    provider_event_verified: bool,
    ledger_reconciled: bool,
    policy_current: bool,
    tenant_match: bool,
    rights_current: bool,
    human_commercial_activation: bool,
) -> bool:
    return all(
        (
            provider_event_verified,
            ledger_reconciled,
            policy_current,
            tenant_match,
            rights_current,
            human_commercial_activation,
        )
    )


def may_launch_commercially(*, canonical_activation: bool, launch_authority: bool) -> bool:
    return canonical_activation and launch_authority


def normalize_commercial_outcome(value: str) -> str:
    value = value.strip().upper()
    aliases = {
        "PAID": "PAID_VERIFIED",
        "ACTIVE": "ACTIVE_LIMITED",
        "CANCEL": "CANCEL_AT_PERIOD_END",
        "REFUND": "REFUND_PENDING",
    }
    return aliases.get(value, value)
