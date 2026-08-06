#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREVIOUS_RUNTIME_PATH = (
    ROOT / "data/experience/message-copy-validation-e2e-runtime.v0.1.json"
)
CURRENT_RUNTIME_PATH = (
    ROOT / "data/experience/b2g-landing-copy-e2e-runtime.v0.1.json"
)
CANONICAL_PATH = ROOT / "apps/landing/lib/canonical-commercial-contract.ts"
I18N_PATH = ROOT / "apps/landing/lib/i18n.ts"
FORM_PATH = ROOT / "apps/landing/components/pilot-access-form.tsx"
INTAKE_PATH = ROOT / "apps/landing/app/api/pilot-intake/route.ts"
METADATA_PATH = ROOT / "apps/landing/lib/metadata.ts"
ROBOTS_PATH = ROOT / "apps/landing/app/robots.ts"
PRICING_ADAPTER_PATH = ROOT / "apps/landing/lib/candidate-pricing.ts"
PRICING_CONTRACT_PATH = ROOT / "apps/landing/lib/candidate-pricing-contract.ts"
PRICE_BOOK_PATH = (
    ROOT / "data/commercial/commercial-runtime-pricing-stripe-runtime.v0.1.json"
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


previous = json.loads(read(PREVIOUS_RUNTIME_PATH))
current = json.loads(read(CURRENT_RUNTIME_PATH))
price_book = json.loads(read(PRICE_BOOK_PATH))
canonical = read(CANONICAL_PATH)
i18n = read(I18N_PATH)
form = read(FORM_PATH)
intake = read(INTAKE_PATH)
metadata = read(METADATA_PATH)
robots = read(ROBOTS_PATH)
pricing_adapter = read(PRICING_ADAPTER_PATH)
pricing_contract_source = read(PRICING_CONTRACT_PATH)

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

# P23-T02 remains immutable history. Its active successor is now represented by
# the canonical commercial contract and projected through the locale adapter.
assert 'messageVersion: "b2g-opportunity-v1.0"' in canonical
assert "BUSINESS-TO-GOVERNMENT (B2G) OPPORTUNITY INTELLIGENCE" in canonical
assert "Find the public contracts your business is built to pursue." in canonical
assert "Request your 7-day B2G trial" in canonical
assert "canonicalCommercialCopy[locale]" in i18n
assert "hero: { ...base.hero, ...canonical.hero }" in i18n
assert "form: { ...base.form, ...canonical.form }" in i18n

assert "messageVersion: AXIGNAL_TRIAL_INTAKE.messageVersion" in form
assert "source: AXIGNAL_TRIAL_INTAKE.source" in form
assert "schema: AXIGNAL_TRIAL_INTAKE.schema" in form
assert "AXIGNAL_TRIAL_INTAKE" in intake
assert "No request was stored" in intake

assert "index: false" in metadata
assert "follow: false" in metadata
assert "noarchive: true" in metadata
assert 'disallow: "/"' in robots
assert "sitemap:" not in robots

assert "commercial-runtime-pricing-stripe-runtime.v0.1.json" in pricing_adapter
assert "parseCandidatePlans" in pricing_adapter
assert 'from "./canonical-commercial-contract"' in pricing_contract_source
assert "AXIGNAL_PRICE_BOOK" in pricing_contract_source
assert 'pricing?.status !== "CANDIDATE_ONLY"' in pricing_contract_source
assert "plan.self_service_activation !== false" in pricing_contract_source
assert "plan.commercial_activation_authorised !== false" in pricing_contract_source
assert 'from "./landing-data"' not in pricing_contract_source
assert 'from "./landing-data"' not in pricing_adapter

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
            "status": "PASS_HISTORICAL_MESSAGE_SUPERSEDED_BY_CANONICAL_B2G_CONTRACT",
            "historical_task_id": previous["task_id"],
            "historical_message_version": previous["message_version"],
            "superseding_task_id": current["task_id"],
            "active_message_version": current["message_version"],
            "canonical_authority": str(CANONICAL_PATH.relative_to(ROOT)),
            "projection_authority": str(I18N_PATH.relative_to(ROOT)),
            "controlled_trial_visible": current["controlled_trial_visible"],
            "pricing_adapter_subordinate_to_canonical_price_book": True,
            "publication_authorised": current["public_publication_authorised"],
        },
        sort_keys=True,
    )
)
