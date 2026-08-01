#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREVIOUS_RUNTIME_PATH = ROOT / "data/experience/message-copy-validation-e2e-runtime.v0.1.json"
CURRENT_RUNTIME_PATH = ROOT / "data/experience/b2g-landing-copy-e2e-runtime.v0.1.json"
LANDING_PATH = ROOT / "apps/landing/components/landing-experience.tsx"
DATA_PATH = ROOT / "apps/landing/lib/landing-data.ts"
FORM_PATH = ROOT / "apps/landing/components/pilot-access-form.tsx"
INTAKE_PATH = ROOT / "apps/landing/app/api/pilot-intake/route.ts"
LAYOUT_PATH = ROOT / "apps/landing/app/layout.tsx"
PRICING_ADAPTER_PATH = ROOT / "apps/landing/lib/candidate-pricing.ts"
PRICING_CONTRACT_PATH = ROOT / "apps/landing/lib/candidate-pricing-contract.ts"
PRICE_BOOK_PATH = ROOT / "data/commercial/commercial-runtime-pricing-stripe-runtime.v0.1.json"

previous = json.loads(PREVIOUS_RUNTIME_PATH.read_text(encoding="utf-8"))
current = json.loads(CURRENT_RUNTIME_PATH.read_text(encoding="utf-8"))
price_book = json.loads(PRICE_BOOK_PATH.read_text(encoding="utf-8"))
landing = LANDING_PATH.read_text(encoding="utf-8")
data = DATA_PATH.read_text(encoding="utf-8")
form = FORM_PATH.read_text(encoding="utf-8")
intake = INTAKE_PATH.read_text(encoding="utf-8")
layout = LAYOUT_PATH.read_text(encoding="utf-8")
pricing_adapter = PRICING_ADAPTER_PATH.read_text(encoding="utf-8")
pricing_contract_source = PRICING_CONTRACT_PATH.read_text(encoding="utf-8")

assert previous["task_id"] == "AX-GE2E-P23-T02"
assert previous["message_version"] == "buyer-outcome-v1.0"
assert previous["engineering_evidence_ready"] is True
assert previous["implemented_in_real_landing"] is True
assert previous["public_publication_authorised"] is False
assert previous["stripe_live_authorised"] is False

assert current["task_id"] == "AX-GE2E-P23-T03"
assert current["supersedes_task"] == previous["task_id"]
assert current["baseline_sha"] == "4301d02880b65a59fb5aa9fed01abad963a23ffd"
assert current["message_version"] == "b2g-opportunity-v1.0"
assert current["state"] == "B2G_VERTICAL_MESSAGE_IMPLEMENTED"
assert current["public_publication_authorised"] is False
assert current["stripe_live_authorised"] is False

assert current["message_version"] in data
assert "BUSINESS-TO-GOVERNMENT (B2G) OPPORTUNITY INTELLIGENCE" in landing
assert "Find the public contracts your business is built to pursue." in landing
assert "Request your 7-day B2G trial" in landing
assert "data-message-version={MESSAGE_VERSION}" in landing

assert "messageVersion" in form
assert "messageVersion" in intake
assert "landing_b2g_opportunity_v1_0" in form
assert "landing_b2g_opportunity_v1_0" in intake
assert "No request was stored" in intake

assert "index: false" in layout
assert "follow: false" in layout
assert "commercial-runtime-pricing-stripe-runtime.v0.1.json" in pricing_adapter
assert "parseCandidatePlans" in pricing_adapter
assert 'planCode === "CONTROLLED_TRIAL_7D"' in pricing_contract_source
assert "plan.self_service_activation !== false" in pricing_contract_source
assert "plan.commercial_activation_authorised !== false" in pricing_contract_source
assert "getCandidatePlans" in (ROOT / "apps/landing/app/page.tsx").read_text(encoding="utf-8")

pricing_contract = price_book["pricing_contract"]
plans = {plan["plan_code"]: plan for plan in pricing_contract["plans"]}
assert plans["CONTROLLED_TRIAL_7D"]["duration_days"] == 7
assert plans["CONTROLLED_TRIAL_7D"]["ai_token_budget"] == 1_000_000
assert plans["CONTROLLED_TRIAL_7D"]["self_service_activation"] is False
assert plans["PROFESSIONAL_MONTHLY"]["amount_minor"] == 14900
assert plans["TEAM_MONTHLY"]["amount_minor"] == 39900

print(
    json.dumps(
        {
            "status": "PASS_SUPERSEDED_BY_B2G_VERTICAL_MESSAGE",
            "historical_task_id": previous["task_id"],
            "historical_message_version": previous["message_version"],
            "superseding_task_id": current["task_id"],
            "active_message_version": current["message_version"],
            "real_landing_implemented": current["implemented_in_real_landing"],
            "controlled_trial_visible": current["controlled_trial_visible"],
            "pricing_contract_separated_from_io": True,
            "publication_authorised": current["public_publication_authorised"],
        },
        sort_keys=True,
    )
)
