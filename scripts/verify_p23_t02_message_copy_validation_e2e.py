#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PATH = ROOT / "data/experience/message-copy-validation-e2e-runtime.v0.1.json"
LANDING_PATH = ROOT / "apps/landing/components/landing-experience.tsx"
DATA_PATH = ROOT / "apps/landing/lib/landing-data.ts"
FORM_PATH = ROOT / "apps/landing/components/pilot-access-form.tsx"
INTAKE_PATH = ROOT / "apps/landing/app/api/pilot-intake/route.ts"
LAYOUT_PATH = ROOT / "apps/landing/app/layout.tsx"
PRICING_PATH = ROOT / "apps/landing/lib/candidate-pricing.ts"
PRICE_BOOK_PATH = (
    ROOT / "data/commercial/commercial-runtime-pricing-stripe-runtime.v0.1.json"
)


def normalize(value: str) -> str:
    return " ".join(value.split())


runtime = json.loads(RUNTIME_PATH.read_text(encoding="utf-8"))
price_book = json.loads(PRICE_BOOK_PATH.read_text(encoding="utf-8"))
landing = LANDING_PATH.read_text(encoding="utf-8")
data = DATA_PATH.read_text(encoding="utf-8")
form = FORM_PATH.read_text(encoding="utf-8")
intake = INTAKE_PATH.read_text(encoding="utf-8")
layout = LAYOUT_PATH.read_text(encoding="utf-8")
pricing = PRICING_PATH.read_text(encoding="utf-8")
normalized_landing = normalize(landing)

assert runtime["task_id"] == "AX-GE2E-P23-T02"
assert runtime["baseline_sha"] == "ce9900dc7372db4499205a87ccb1cad4f2b08527"
assert runtime["state"] == "DESK_RESEARCH_VALIDATED_IMPLEMENTED"
assert runtime["message_version"] == "buyer-outcome-v1.0"
assert runtime["engineering_evidence_ready"] is True
assert runtime["implemented_in_real_landing"] is True
assert runtime["buyer_interview_validation_complete"] is False
assert runtime["conversion_validation_complete"] is False
assert runtime["public_publication_authorised"] is False
assert runtime["paid_media_authorised"] is False
assert runtime["stripe_live_authorised"] is False
assert runtime["market_validated_claim_authorised"] is False

winner = runtime["message_decision"]
for field in ("headline", "supporting_headline", "subheadline", "primary_cta", "secondary_cta"):
    assert normalize(winner[field]) in normalized_landing, field
assert runtime["message_version"] in data
assert "data-message-version={MESSAGE_VERSION}" in landing

assert "messageVersion" in form
assert "messageVersion" in intake
assert "landing_buyer_outcome_v1_0" in form
assert "landing_buyer_outcome_v1_0" in intake
assert "controlled-access intake channel is not configured" in intake
assert "No request was stored" in intake

assert "index: false" in layout
assert "follow: false" in layout
assert "commercial-runtime-pricing-stripe-runtime.v0.1.json" in pricing
assert 'pricing?.status !== "CANDIDATE_ONLY"' in pricing
assert "plan.commercial_activation_authorised !== false" in pricing
assert "getCandidatePlans" in (ROOT / "apps/landing/app/page.tsx").read_text(
    encoding="utf-8"
)

pricing_contract = price_book["pricing_contract"]
assert pricing_contract["status"] == "CANDIDATE_ONLY"
assert pricing_contract["currency"] == "EUR"
plans = {plan["plan_code"]: plan for plan in pricing_contract["plans"]}
assert plans["PROFESSIONAL_MONTHLY"]["amount_minor"] == 14900
assert plans["TEAM_MONTHLY"]["amount_minor"] == 39900
assert plans["PROFESSIONAL_MONTHLY"]["commercial_activation_authorised"] is False
assert plans["TEAM_MONTHLY"]["commercial_activation_authorised"] is False

application_copy = "\n".join((landing, data, form, layout)).lower()
for phrase in runtime["prohibited_claims"]:
    assert phrase.lower() not in application_copy, phrase

required_sections = (
    'id="workflow"',
    'id="evidence"',
    'id="pricing"',
    'id="access"',
    'aria-labelledby="faq-title"',
)
for section in required_sections:
    assert section in landing, section

assert len(runtime["market_patterns"]) == 4
assert len(runtime["priority_buyers"]) == 4
assert len(runtime["buyer_jobs"]) == 5
assert len(runtime["buyer_pains"]) == 7
assert len(runtime["objection_map"]) == 5
assert len(runtime["e2e_gates"]) == 10
assert len(runtime["next_real_evidence"]) == 5

print(
    json.dumps(
        {
            "status": "PASS_ENGINEERING_AND_REAL_LANDING_IMPLEMENTATION",
            "task_id": runtime["task_id"],
            "message_version": runtime["message_version"],
            "real_landing_implemented": runtime["implemented_in_real_landing"],
            "server_price_book_bound": True,
            "publication_authorised": runtime["public_publication_authorised"],
            "buyer_interviews": "PENDING",
            "conversion_validation": "PENDING",
        },
        sort_keys=True,
    )
)
