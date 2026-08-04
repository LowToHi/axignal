#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PATH = ROOT / "data/experience/b2g-landing-copy-e2e-runtime.v0.1.json"
PREVIOUS_RUNTIME_PATH = (
    ROOT / "data/experience/message-copy-validation-e2e-runtime.v0.1.json"
)
CANONICAL_PATH = ROOT / "apps/landing/lib/canonical-commercial-contract.ts"
I18N_PATH = ROOT / "apps/landing/lib/i18n.ts"
LANDING_PATH = ROOT / "apps/landing/components/landing-experience.tsx"
FORM_PATH = ROOT / "apps/landing/components/pilot-access-form.tsx"
INTAKE_PATH = ROOT / "apps/landing/app/api/pilot-intake/route.ts"
METADATA_PATH = ROOT / "apps/landing/lib/metadata.ts"
ROBOTS_PATH = ROOT / "apps/landing/app/robots.ts"
PRICING_ADAPTER_PATH = ROOT / "apps/landing/lib/candidate-pricing.ts"
PRICING_CONTRACT_PATH = ROOT / "apps/landing/lib/candidate-pricing-contract.ts"
PAGE_PATH = ROOT / "apps/landing/app/page.tsx"
STATIC_TEST_PATH = ROOT / "tests/landing/landing-contract.test.mjs"
BROWSER_TEST_PATH = ROOT / "tests/landing/landing.spec.ts"
PRICE_BOOK_PATH = (
    ROOT / "data/commercial/commercial-runtime-pricing-stripe-runtime.v0.1.json"
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def normalize(value: str) -> str:
    return " ".join(value.split())


runtime = json.loads(read(RUNTIME_PATH))
previous_runtime = json.loads(read(PREVIOUS_RUNTIME_PATH))
price_book = json.loads(read(PRICE_BOOK_PATH))
canonical = read(CANONICAL_PATH)
i18n = read(I18N_PATH)
landing = read(LANDING_PATH)
form = read(FORM_PATH)
intake = read(INTAKE_PATH)
metadata = read(METADATA_PATH)
robots = read(ROBOTS_PATH)
pricing_adapter = read(PRICING_ADAPTER_PATH)
pricing_contract_source = read(PRICING_CONTRACT_PATH)
page = read(PAGE_PATH)
static_tests = read(STATIC_TEST_PATH)
browser_tests = read(BROWSER_TEST_PATH)
normalized_canonical = normalize(canonical)

assert runtime["task_id"] == "AX-GE2E-P23-T03"
assert runtime["baseline_sha"] == "4301d02880b65a59fb5aa9fed01abad963a23ffd"
assert runtime["supersedes_task"] == previous_runtime["task_id"]
assert previous_runtime["task_id"] == "AX-GE2E-P23-T02"
assert runtime["state"] == "B2G_VERTICAL_MESSAGE_IMPLEMENTED"
assert runtime["message_version"] == "b2g-opportunity-v1.0"
assert runtime["market_category"] == (
    "BUSINESS_TO_GOVERNMENT_OPPORTUNITY_INTELLIGENCE"
)
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
for field in (
    "eyebrow",
    "headline",
    "supporting_headline",
    "primary_cta",
    "secondary_cta",
):
    assert normalize(message[field]) in normalized_canonical, field

# C0 admits one bounded lexical projection inside the same message version:
# the expanded buyer label is rendered with its already-defined acronym.
projected_subheadline = message["subheadline"].replace(
    "Business-to-Government teams",
    "B2G teams",
)
assert normalize(projected_subheadline) in normalized_canonical
assert 'messageVersion: "b2g-opportunity-v1.0"' in canonical
assert 'source: "landing_b2g_opportunity_v1_0"' in canonical
assert 'schema: "axignal.b2g-trial-intake.v1"' in canonical

for locale in ("en", "es", "fr", "pt", "de", "it"):
    assert f"\n  {locale}: {{" in canonical
assert "canonicalCommercialCopy[locale]" in i18n
assert "hero: { ...base.hero, ...canonical.hero }" in i18n
assert "pricing: { ...base.pricing, ...canonical.pricing }" in i18n
assert "faq: { ...base.faq, items: canonical.faqItems }" in i18n
assert "form: { ...base.form, ...canonical.form }" in i18n

for binding in (
    "m.hero.eyebrow",
    "m.hero.title",
    "m.hero.accent",
    "m.hero.descriptor",
    "m.hero.summary",
    "m.hero.primary",
    "m.hero.secondary",
):
    assert binding in landing

assert "messageVersion: AXIGNAL_TRIAL_INTAKE.messageVersion" in form
assert "source: AXIGNAL_TRIAL_INTAKE.source" in form
assert "schema: AXIGNAL_TRIAL_INTAKE.schema" in form
assert "governmentOffer:" in form
assert "qualificationBottleneck:" in form
assert 'fetch("/api/pilot-intake"' in form
assert "AXIGNAL_TRIAL_INTAKE" in intake
assert "allowedPlans" in intake
assert "No request was stored" in intake
assert "idempotencyKeyHash" in intake

assert 'category: "Business-to-Government Opportunity Intelligence"' in metadata
assert "index: false" in metadata
assert "follow: false" in metadata
assert "noarchive: true" in metadata
assert 'disallow: "/"' in robots
assert "sitemap:" not in robots
assert "buildLandingMetadata(\"en\")" in page
assert "getMessages(\"en\")" in page

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

public_copy = "\n".join((canonical, landing, i18n, form, metadata))
assert re.search(r"\bTED\b", public_copy, flags=re.IGNORECASE) is None
for phrase in runtime["prohibited_claims"]:
    assert phrase.lower() not in public_copy.lower(), phrase

for contract_name in (
    "canonical B2G copy overrides every supported locale",
    "price book is versioned",
    "public landing removes source-brand identity",
    "B2G trial intake persists canonical schema",
    "landing stays fail-closed for indexing",
):
    assert contract_name in static_tests
for browser_marker in (
    "Controlled Trial",
    "€149",
    "€399",
    "ADMITTED PUBLIC-SOURCE PROFILE",
    "reducedMotion",
    "semantic-globe",
):
    assert browser_marker in browser_tests

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
            "status": "PASS_CANONICAL_B2G_CONTRACT_PROJECTION",
            "task_id": runtime["task_id"],
            "message_version": runtime["message_version"],
            "market_category": runtime["market_category"],
            "canonical_authority": str(CANONICAL_PATH.relative_to(ROOT)),
            "projection_authority": str(I18N_PATH.relative_to(ROOT)),
            "bounded_lexical_projection": {
                "from": "Business-to-Government teams",
                "to": "B2G teams",
            },
            "controlled_trial_visible": runtime["controlled_trial_visible"],
            "trial_terms_match_price_book": True,
            "professional_and_team_prices_match": True,
            "pricing_adapter_subordinate_to_canonical_price_book": True,
            "ted_in_public_narrative": False,
            "publication_authorised": runtime["public_publication_authorised"],
            "buyer_interviews": "PENDING",
            "conversion_validation": "PENDING",
        },
        sort_keys=True,
    )
)
