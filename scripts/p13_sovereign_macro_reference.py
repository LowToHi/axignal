#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json
from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import Any

def canonical_digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def indicator_current(*, value_class:str, vintage_current:bool, withdrawn:bool, rights_active:bool)->str:
    if withdrawn or not rights_active: return "DENY"
    if not vintage_current or value_class in {"FORECAST","SCENARIO","TARGET","UNKNOWN"}: return "REVIEW_REQUIRED"
    return "PASS" if value_class in {"OBSERVED","PROVISIONAL","ESTIMATED","REVISED","BENCHMARK","DERIVED"} else "DENY"

def comparability_decision(*, unit:bool, scale:bool, currency:bool, price_basis:bool, frequency:bool, lineage:bool)->str:
    if not lineage: return "DENY"
    return "PASS" if all((unit,scale,currency,price_basis,frequency)) else "REVIEW_REQUIRED"

def public_finance_decision(*, state:str, amount:Decimal|None, observed:bool, rights_active:bool)->str:
    if not rights_active or state=="CANCELLED" or (amount is not None and amount<0): return "DENY"
    if state in {"DISBURSED","PAID"} and observed and amount is not None: return "PASS"
    return "REVIEW_REQUIRED"

def strategy_readiness(gates:Mapping[str,str], required:Sequence[str])->str:
    if not gates or any(g not in gates for g in required): return "NOT_READY"
    values=[gates[g] for g in required]
    if "DENY" in values: return "DENY"
    return "READY" if all(v=="PASS" for v in values) else "REVIEW_REQUIRED"

def may_execute_external_action(*, actor_type:str, readiness:str, approvals:bool, rights:bool, document:bool, recipient:bool, channel:bool, audit:bool, kill_switch:bool)->bool:
    return all((actor_type=="HUMAN_EXTERNAL_ACTION_AUTHORITY",readiness=="READY",approvals,rights,document,recipient,channel,audit,not kill_switch))

def normalize_outcome(outcome:str, *, observed:bool)->str:
    allowed={"NO_ACTION","MONITORING","STRATEGY_APPROVED","BRIEF_PUBLISHED","MEETING_HELD","MARKET_REVIEW_OPENED","PILOT_AUTHORISED","BUDGET_ALLOCATED","CAPITAL_COMMITTED","MARKET_ENTRY_STARTED","DECLINED","CLOSED"}
    return outcome if observed and outcome in allowed else "UNKNOWN"

def imported_authority(_:str)->str:
    return "CANDIDATE_ONLY"
