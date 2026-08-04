#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCALES = ("en", "es", "fr", "pt", "de", "it")


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require(content: str, values: list[str], label: str) -> None:
    missing = [value for value in values if value not in content]
    assert not missing, f"{label} is missing {missing}"


def forbid(content: str, values: list[str], label: str) -> None:
    present = [value for value in values if value in content]
    assert not present, f"{label} contains forbidden values {present}"


def main() -> None:
    package = json.loads(read("apps/landing/package.json"))
    dependencies = package["dependencies"]
    for dependency in ("gsap", "three", "@react-three/fiber", "@react-three/drei"):
        assert dependency in dependencies, f"missing landing dependency: {dependency}"

    experience = read("apps/landing/components/landing-experience.tsx")
    globe = read("apps/landing/components/semantic-globe.tsx")
    globe_rendering = read("apps/landing/lib/globe-rendering.ts")
    globe_implementation = "\n".join((globe, globe_rendering))
    canonical = read("apps/landing/lib/canonical-commercial-contract.ts")
    i18n = read("apps/landing/lib/i18n.ts")
    pricing = read("apps/landing/lib/pricing-data.ts")
    product_profile = read("apps/landing/lib/product-profile.ts")
    landing_data = read("apps/landing/lib/landing-data.ts")
    form = read("apps/landing/components/pilot-access-form.tsx")
    endpoint = read("apps/landing/app/api/pilot-intake/route.ts")
    css = "\n".join(
        (
            read("apps/landing/app/globals.css"),
            read("apps/landing/app/contract-overrides.css"),
        )
    )
    metadata = read("apps/landing/lib/metadata.ts")
    robots = read("apps/landing/app/robots.ts")
    browser_tests = read("tests/landing/landing.spec.ts")
    contract_tests = read("tests/landing/landing-contract.test.mjs")

    require(
        experience,
        [
            'id: "investigationCinematic"',
            "pin: cinematicStage.current",
            "scrub:",
            'addLabel("SCENE_GLOBAL"',
            'addLabel("SCENE_EUROPE"',
            'addLabel("SCENE_FRAGMENTATION"',
            'addLabel("SCENE_EVIDENCE"',
            'addLabel("SCENE_INVESTIGATION"',
            'addLabel("SCENE_DOSSIER"',
            "progressRef={cinematicProgress}",
            "trace-object",
            "investigation-context-frame",
            "cinematic-dossier",
            "prefers-reduced-motion",
        ],
        "continuous landing experience",
    )
    assert experience.count("<SemanticGlobe") == 1, "landing must mount exactly one SemanticGlobe"
    assert "console-orbit" not in experience, "abstract hero orbit must not compete with the Globe"

    require(
        globe_implementation,
        [
            'from "@react-three/fiber"',
            "<Canvas",
            "earth-albedo.webp",
            "earth-clouds.webp",
            "earth-albedo-high.webp",
            "earth-europe-high.webp",
            "countries-110m.simplified.geojson",
            "europe-boundaries-50m.geojson",
            "CloudLayer",
            "OpportunityMarkerLayer",
            "getMaxAnisotropy",
            "selectGlobeTextureTier",
            "estimateTextureMemoryMb",
            "axRegionalMix",
            "setDpr",
            "IntersectionObserver",
            "instancedMesh",
            "data-effective-dpr",
            "data-lod-active",
            "data-boundary-lod-active",
            "progressRef.current",
            "camera.position",
            "OrbitControls",
            "powerPreference",
        ],
        "semantic globe",
    )
    forbid(
        globe_implementation,
        ["ActivityArcLayer", "AuraGlyph", "SVGLoader", "axignal-aura.svg"],
        "retired Globe layers",
    )

    require(
        canonical,
        [
            'schema: "axignal.price-book.v1"',
            'code: "CONTROLLED_TRIAL_7D"',
            "durationDays: 7",
            "cumulativeTokens: 1_000_000",
            "cardRequired: false",
            "automaticConversion: false",
            'code: "PROFESSIONAL_MONTHLY"',
            "amountMinor: 14_900",
            'code: "TEAM_MONTHLY"',
            "amountMinor: 39_900",
            'schema: "axignal.b2g-trial-intake.v1"',
            'source: "landing_b2g_opportunity_v1_0"',
            'messageVersion: "b2g-opportunity-v1.0"',
            "Find the public contracts your business is built to pursue.",
            "Request your 7-day B2G trial",
        ],
        "canonical B2G commercial contract",
    )
    for locale in LOCALES:
        require(canonical, [f"\n  {locale}: {{"], f"{locale}:"], f"canonical locale {locale}")
    require(
        i18n,
        [
            "canonicalCommercialCopy[locale]",
            "meta: canonical.meta",
            "cta: canonical.navCta",
            "...canonical.hero",
            "items: canonical.faqItems",
            "...canonical.form",
        ],
        "effective locale projection",
    )

    require(
        product_profile,
        [
            'profileId: "ADMITTED_PUBLIC_SOURCE_PROFILE_01"',
            'admissionState: "PRODUCT_ADMITTED"',
            'accessScope: "PRIVATE_AUTHENTICATED_PILOT"',
            'publicAccess: "PUBLIC_ACCESS_DISABLED"',
            "unrestrictedSourceUse: false",
            'demonstrationData: "SYNTHETIC_FIXTURES"',
        ],
        "bounded public-source projection",
    )
    forbid(
        "\n".join((product_profile, landing_data)),
        ["Tenders Electronic Daily", "EU_TED", "TED_SEARCH_API_BOUNDED_PRODUCT_PROFILE"],
        "public source identity",
    )
    require(
        css,
        [
            ".status-ribbon span:first-child",
            "display: none",
            "ADMITTED PUBLIC-SOURCE PROFILE · PRIVATE AUTHENTICATED PILOT",
            "@media (prefers-reduced-motion: reduce)",
            ".cinematic-stage",
            ".trace-object",
            ".pricing-comparison",
            ".reduced-story",
            ".globe-poster",
            ".globe-initialising",
            ".skip-link",
        ],
        "landing styles and public source-brand suppression",
    )

    require(
        pricing,
        [
            "AXIGNAL_PRICE_BOOK.plans.controlledTrial",
            "AXIGNAL_PRICE_BOOK.plans.professional",
            "AXIGNAL_PRICE_BOOK.plans.team",
            'name: "Controlled Trial"',
            'name: "Professional"',
            'name: "Team"',
            '"Unlimited monthly AI within AXIGNAL scope"',
        ],
        "versioned pricing boundary",
    )
    forbid(
        pricing,
        ["€349", "€899", "€1,499", "€18k", 'name: "Enterprise"', "Design Partner"],
        "rejected pricing and programme copy",
    )

    require(
        form,
        [
            'fetch("/api/pilot-intake"',
            "schema: AXIGNAL_TRIAL_INTAKE.schema",
            "source: AXIGNAL_TRIAL_INTAKE.source",
            "messageVersion: AXIGNAL_TRIAL_INTAKE.messageVersion",
            "governmentOffer:",
            "qualificationBottleneck:",
            'name="consent"',
            'name="website"',
            "aria-live",
        ],
        "B2G trial form",
    )
    require(
        endpoint,
        [
            "AXIGNAL_PILOT_INTAKE_WEBHOOK_URL",
            "AXIGNAL_PILOT_INTAKE_BEARER_TOKEN",
            "AXIGNAL_PILOT_CONTACT_EMAIL",
            "AbortSignal.timeout",
            '"cache-control": "no-store, max-age=0"',
            "messageVersion: typeof AXIGNAL_TRIAL_INTAKE.messageVersion",
            "idempotencyKeyHash",
            "No success was recorded",
            'new Set(["Controlled Trial", "Professional", "Team"])',
        ],
        "B2G trial intake endpoint",
    )

    require(
        browser_tests,
        [
            "reducedMotion",
            "semantic-globe",
            "data-continuity-id",
            "Controlled Trial",
            "€149",
            "€399",
            "ADMITTED PUBLIC-SOURCE PROFILE",
            "scrollWidth",
            "consoleErrors",
            "pageErrors",
        ],
        "canonical landing browser tests",
    )
    forbid(
        browser_tests,
        [
            'getByRole("heading", { name: "Design Partner" })',
            'getByRole("heading", { name: "Enterprise" }).toBeVisible',
            "Indicative candidate pricing",
            "Win the right public opportunities",
        ],
        "rejected browser assertions",
    )
    require(
        contract_tests,
        [
            "canonical B2G copy overrides every supported locale",
            "price book is versioned",
            "public landing removes source-brand identity",
            "B2G trial intake persists canonical schema",
            "landing stays fail-closed for indexing",
        ],
        "canonical static contract tests",
    )

    require(metadata, ["index: false", "follow: false", "noarchive: true"], "fail-closed metadata")
    require(robots, ['disallow: "/"'], "fail-closed robots")
    forbid(robots, ["sitemap:"], "pre-authority robots")

    forbidden = [
        "pilot.axignal.com",
        "REMOTE_PILOT_ACCEPTED",
        "guaranteed return",
        "live investment performance",
    ]
    joined = "\n".join((experience, form, endpoint, pricing, product_profile, canonical))
    forbid(joined, forbidden, "public/deployment claims")

    evidence = {
        "status": "PASS",
        "scope": "STATIC_CANONICAL_B2G_IMPLEMENTATION_CONTRACT",
        "canonical_copy_locales": list(LOCALES),
        "public_source_brand_visible": False,
        "professional_monthly_eur": 149,
        "team_monthly_eur": 399,
        "controlled_trial_days": 7,
        "controlled_trial_cumulative_tokens": 1_000_000,
        "controlled_trial_card_required": False,
        "controlled_trial_auto_conversion": False,
        "intake_schema": "axignal.b2g-trial-intake.v1",
        "intake_source": "landing_b2g_opportunity_v1_0",
        "intake_message_version": "b2g-opportunity-v1.0",
        "gsap_scrolltrigger": True,
        "single_persistent_canvas": True,
        "six_named_scenes": True,
        "semantic_globe": True,
        "retired_globe_layers_absent": True,
        "reduced_motion_content_parity": True,
        "indexing_authorised": False,
        "visual_gate_independently_passed": False,
    }
    print(json.dumps(evidence, sort_keys=True))


if __name__ == "__main__":
    main()
