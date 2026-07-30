#!/usr/bin/env python3
from __future__ import annotations
import json
from decimal import Decimal
from pathlib import Path
from jsonschema import Draft202012Validator
from p13_sovereign_macro_reference import canonical_digest, comparability_decision, imported_authority, indicator_current, may_execute_external_action, normalize_outcome, public_finance_decision, strategy_readiness

ROOT=Path(__file__).resolve().parents[1]
P={
"rs":ROOT/"schemas/sovereign-macro-strategy-workspace-runtime.schema.json",
"fs":ROOT/"schemas/sovereign-macro-strategy-workspace-fixtures.schema.json",
"cs":ROOT/"schemas/sovereign-macro-strategy-workspace-cases.schema.json",
"r":ROOT/"data/sovereign-macro/sovereign-macro-strategy-workspace-runtime.v0.1.json",
"f":ROOT/"data/sovereign-macro/p13-conformance-fixtures.v0.1.json",
"c":ROOT/"data/sovereign-macro/p13-adversarial-cases.v0.1.json",
"rb":ROOT/"data/sovereign-macro/p13-rollback-plan.v0.1.json",
"programme":ROOT/"data/programmes/global-e2e-tasks-p10-p14.v1.4.json",
"libs":ROOT/"data/ontology/library-contracts.v0.1.json",
"p05":ROOT/"data/foundations/foundational-library-runtime.v0.1.json",
"p06":ROOT/"data/document-intelligence/multilingual-document-intelligence-runtime.v0.1.json",
"p07":ROOT/"data/opportunity-operations/opportunity-operations-core-runtime.v0.1.json",
"p12":ROOT/"data/corporate/corporate-ownership-account-workspace-runtime.v0.1.json",
"catalogue":ROOT/"data/sources/sovereign-macro-public-investment-catalogue.v0.1.json"}
for path in P.values(): assert path.is_file(),f"missing {path.relative_to(ROOT)}"
load=lambda p:json.loads(p.read_text())
rs,fs,cs,r,f,c=[load(P[k]) for k in ("rs","fs","cs","r","f","c")]
for s in (rs,fs,cs): Draft202012Validator.check_schema(s)
Draft202012Validator(rs).validate(r); Draft202012Validator(fs).validate(f); Draft202012Validator(cs).validate(c)
programme,libs,p05,p06,p07,p12,catalogue=[load(P[k]) for k in ("programme","libs","p05","p06","p07","p12","catalogue")]
task=next(x for x in programme["tasks"] if x["task_id"]=="AX-GE2E-P13-T01")
assert task["phase"]=="P13" and task["state"]=="BLOCKED"
assert task["dependencies"]["tasks"]==["AX-GE2E-P07-T01"]
lib=next(x for x in libs["contracts"] if x["library_id"]=="AX-LIB-O06")
for k in ("library_id","workspace_type","canonical_name","entities","predicates","events","taxonomy_refs"): assert r["sovereign_macro_library_binding"][k]==lib[k]
assert p05["canonical_activation_authorised"] is False
assert p06["canonical_activation_authorised"] is False
assert r["languages"]==[x["language_tag"] for x in p06["language_profile"]["languages"]]
assert p07["canonical_activation_authorised"] is False
assert r["rights_dimensions"]==p07["rights_dimensions"]
assert set(r["required_approvals"]).issubset(set(p07["approval_contract"]["approval_types"]))
assert p12["task_id"]=="AX-GE2E-P12-T01" and p12["canonical_activation_authorised"] is False
assert r["dependency_status"]["p12_engineering_head"]=="96b89d8e7bdd7712dae476eeb97e1240c7846f22"
assert catalogue["catalogue_id"]=="AX-MACRO-SOURCE-CATALOGUE-001" and catalogue["library_id"]=="AX-LIB-O06"
assert len(catalogue["sources"])==7 and all(not s["product_admitted"] and s["rights_status"]=="UNREVIEWED" for s in catalogue["sources"])
mods=r["domain_modules"]; assert len(mods)==8 and len({m["module_id"] for m in mods})==8
assert sum(len(m["record_types"]) for m in mods)==32 and sum(len(m["invariants"]) for m in mods)==48
assert len(r["country_strategy_lifecycle"]["states"])==12 and len(r["operating_pipeline"]["stages"])==11
for k,n in (("macro_value_classes",10),("economic_transformations",10),("public_finance_states",10),("scenario_risk_classes",10),("readiness_gates",12),("rights_dimensions",10)): assert len(r[k])==n
fixture_count=len(f["modules"])*len(f["classes"]); assert fixture_count==40
assert all(not x["canonical_write"] and not x["external_action"] for x in f["expected_by_class"].values())
case_count=len(c["scopes"])*len(c["threats"]); assert case_count==72
assert all(x["canonical_delta"]==0 and x["external_action_delta"]==0 for x in c["expected_by_threat"].values())
assert canonical_digest({"b":2,"a":1})==canonical_digest({"a":1,"b":2})
assert indicator_current(value_class="OBSERVED",vintage_current=True,withdrawn=False,rights_active=True)=="PASS"
assert indicator_current(value_class="FORECAST",vintage_current=True,withdrawn=False,rights_active=True)=="REVIEW_REQUIRED"
assert indicator_current(value_class="OBSERVED",vintage_current=True,withdrawn=True,rights_active=True)=="DENY"
assert comparability_decision(unit=True,scale=True,currency=True,price_basis=True,frequency=True,lineage=True)=="PASS"
assert comparability_decision(unit=False,scale=True,currency=True,price_basis=True,frequency=True,lineage=True)=="REVIEW_REQUIRED"
assert comparability_decision(unit=True,scale=True,currency=True,price_basis=True,frequency=True,lineage=False)=="DENY"
assert public_finance_decision(state="DISBURSED",amount=Decimal("1"),observed=True,rights_active=True)=="PASS"
assert public_finance_decision(state="ALLOCATED",amount=Decimal("1"),observed=True,rights_active=True)=="REVIEW_REQUIRED"
assert public_finance_decision(state="CANCELLED",amount=Decimal("1"),observed=True,rights_active=True)=="DENY"
required=r["readiness_gates"]; passing={g:"PASS" for g in required}
assert strategy_readiness(passing,required)=="READY"
review=dict(passing); review[required[0]]="REVIEW_REQUIRED"; assert strategy_readiness(review,required)=="REVIEW_REQUIRED"
deny=dict(passing); deny[required[0]]="DENY"; assert strategy_readiness(deny,required)=="DENY"
assert strategy_readiness({},required)=="NOT_READY"
assert may_execute_external_action(actor_type="HUMAN_EXTERNAL_ACTION_AUTHORITY",readiness="READY",approvals=True,rights=True,document=True,recipient=True,channel=True,audit=True,kill_switch=False)
assert not may_execute_external_action(actor_type="MODEL",readiness="READY",approvals=True,rights=True,document=True,recipient=True,channel=True,audit=True,kill_switch=False)
assert normalize_outcome("MARKET_ENTRY_STARTED",observed=True)=="MARKET_ENTRY_STARTED"
assert normalize_outcome("MARKET_ENTRY_STARTED",observed=False)=="UNKNOWN"
assert imported_authority("APPROVED")=="CANDIDATE_ONLY"
for k,v in r["dependency_status"].items():
    if k.endswith("canonical_activation_authorised") or k in {"p01_dependency_satisfied","merge_to_main_allowed"}: assert v is False
assert r["canonical_activation_authorised"] is False and r["acceptance_gate"]["current_decision"]=="NOT_READY_FOR_CANONICAL_ACTIVATION"
print(json.dumps({"status":"PASS","task_id":"AX-GE2E-P13-T01","domain_modules":8,"record_types":32,"domain_invariants":48,"conformance_fixtures":fixture_count,"adversarial_cases":case_count,"canonical_activation_authorised":False},sort_keys=True))
