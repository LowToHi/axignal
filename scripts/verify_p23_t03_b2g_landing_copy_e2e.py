#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PATH = ROOT / "data/experience/b2g-landing-copy-e2e-runtime.v0.1.json"
PREVIOUS_RUNTIME_PATH = ROOT / "data/experience/message-copy-validation-e2e-runtime.v0.1.json"
LANDING_PATH = ROOT / "apps/landing/components/landing-experience.tsx"
DATA_PATH = ROOT / "apps/landing/lib/landing-data.ts"
FORM_PATH = ROOT / "apps/landing/components/pilot-access-form.tsx"
INTAKE_PATH = ROOT / "apps/landing/app/api/pilot-intake/route.ts"
LAYOUT_PATH = ROOT / "apps/landing/app/layout.tsx"
PRICING_PATH = ROOT / "apps/landing/lib/candidate-pricing.ts"
PAGE_PATH = ROOT / "apps/landing/app/page.tsx"
TEST_PATH = ROOT / "tests/landing/landing.spec.ts"
PRICE_BOOK_PATH = ROOT / "data/commercial/commercial-runtime-pricing-stripe-runtime.v0.1.json"


def normalize(value: str) -> str:
    return " ".join(value.split())


runtime = json.loads(RUNTIME_PATH.read_text(encoding="utf-8"))
previous_runtime = json.loads(PREVIOUS_RUNTIME_PATH.read_text(encoding="utf-8"))
price_book = json.loads(PRICE_BOOK_PATH.read_text(encoding="utf-8"))
landing = LANDING_PATH.read_text(encoding="utf-8")
data = DATA_PATH.read_text(encoding="utf-8")
form = FORM_PATH.read_text(encoding="utf-8")
intake = INTAKE_PATH.read_text(encoding="utf-8")
layout = LAYOUT_PATH.read_text(encoding="utf-8")
pricing = PRICING_PATH.read_text(encoding="utf-8")
page = PAGE_PATH.read_text(encoding="utf-8")
tests = TEST_PATH.read_text(encoding="utf-8")
normalized_landing = normalize(landing)

assert runtime["task_id"] == "AX-GE2E-P23-T03"
assert runtime["baseline_sha"] == "4301d02880b65a59fb5aa9fed01abad963a23ffd"
assert runtime["supersedes_task"] == previous_runtime["task_id"] == "AX-GE2E-P23-T02"
assert runtime["state"] == "B2G_VERTICAL_MESSAGE_IMPLEMENTED"
assert runtime["message_version"] == "b2g-opportunity-v1.0"
assert runtime["market_category"] == "BUSINESS_TO_GOVERNMENT_OPPORTUNITY_INTELLIGENCE"
assert runtime["market_wedge"] == "GLOBAL_PUBLIC_CONTRACTS_AND_TENDERS"
assert runtime["ted_narrative_status"] == "REMOVED_FROM_PUBLIC_NARRATIVE"
assert runtime["engineering_evidence_ready"] is True
assert runtime["implemented_in_real_landing"] is True
assert runtime["controlled_trial_visible"] is True
assert runtime["direct_buyer_interview_validation_complete"] is False
assert runtime["conversion_validation_complete"] is False
assert runtime["public_publication_authorised"] is False
assert runtime["paid_media_authorised"] is False
assert runtime["stripe_live_authorised"] is False
assert runtime["market_validated_claim_authorised"] is False

message = runtime["message_decision"]
for field in ("eyebrow", "headline", "supporting_headline", "subheadline", "primary_cta", "secondary_cta"):
    assert normalize(message[field]) in normalized_landing, field

assert "BUSINESS-TO-GOVERNMENT (B2G) OPPORTUNITY INTELLIGENCE" in landing
assert "Business-to-Government teams" in landing
assert "public contracts" in landing.lower()
assert "global procurement" in landing.lower()
assert "bid / no-bid" in landing.lower()
assert runtime["message_version"] in data
assert "data-message-version={MESSAGE_VERSION}" in landing

public_copy = "\n".join((landing, data, form, layout))
assert re.search(r"\bTED\b", public_copy, flags=re.IGNORECASE) is None

assert "messageVersion" in form
assert "messageVersion" in intake
assert "landing_b2g_opportunity_v1_0" in form
assert "landing_b2g_opportunity_v1_0" in intake
assert "axignal.b2g-trial-intake.v1" in intake
assert "controlled B2G trial channel is not configured" in intake
assert "No request was stored" in intake
assert "Bid or proposal management" in form
assert "Bid or proposal management" in intake

assert "index: false" in layout
assert "follow: false" in layout
assert "Business-to-Government (B2G) Opportunity Intelligence" in layout
assert "commercial-runtime-pricing-stripe-runtime.v0.1.json" in pricing
assert 'pricing?.status !== "CANDIDATE_ONLY"' in pricing
assert 'plan.plan_code === "CONTROLLED_TRIAL_7D"' in pricing
assert 'plan.self_service_activation !== false' in pricing
assert "getCandidatePlans" in page

pricing_contract = price_book["pricing_contract"]
assert pricing_contract["status"] == "CANDIDATE_ONLY"
assert pricing_contract["currency"] == "EUR"
plans = {plan["plan_code"]: plan for plan in pricing_contract["plans"]}
trial = plans["CONTROLLED_TRIAL_7D"]
assert trial["amount_minor"] == 0
assert trial["duration_days"] == 7
assert trial["ai_token_budget"] == 1_000_000
assert trial["self_service_activation"] is False
assert trial["commercial_activation_authorised"] is False
assert plans["PROFESSIONAL_MONTHLY"]["amount_minor"] == 14900
assert plans["TEAM_MONTHLY"]["amount_minor"] == 39900
assert plans["PROFESSIONAL_MONTHLY"]["commercial_activation_authorised"] is False
assert plans["TEAM_MONTHLY"]["commercial_activation_authorised"] is False

application_copy = public_copy.lower()
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

assert "plan-controlled_trial_7d" in tests
assert "b2g-opportunity-v1.0" in tests
assert "Request 7-day B2G trial" in tests
assert "Business-to-Government" in tests
assert len(runtime["market_patterns"]) == 6
assert len(runtime["priority_buyers"]) == 7
assert len(runtime["buyer_jobs"]) == 7
assert len(runtime["buyer_pains"]) == 8
assert len(runtime["narrative_architecture"]) == 10
assert len(runtime["objection_map"]) == 7
assert len(runtime["e2e_gates"]) == 15
assert len(runtime["next_real_evidence"]) == 6

print(
    json.dumps(
        {
            "status": "PASS_B2G_ENGINEERING_AND_REAL_LANDING_IMPLEMENTATION",
            "task_id": runtime["task_id"],
            "message_version": runtime["message_version"],
            "market_category": runtime["market_category"],
            "real_landing_implemented": runtime["implemented_in_real_landing"],
            "controlled_trial_visible": runtime["controlled_trial_visible"],
            "trial_terms_match_price_book": True,
            "professional_and_team_prices_match": True,
            "ted_in_public_narrative": False,
            "publication_authorised": runtime["public_publication_authorised"],
            "buyer_interviews": "PENDING",
            "conversion_validation": "PENDING",
        },
        sort_keys=True,
    )
)
