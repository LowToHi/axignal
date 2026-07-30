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


def main() -> None:
    package = json.loads(read("apps/landing/package.json"))
    dependencies = package["dependencies"]
    for dependency in ("gsap", "three", "@react-three/fiber", "@react-three/drei"):
        assert dependency in dependencies, f"missing landing dependency: {dependency}"

    experience = read("apps/landing/components/landing-experience.tsx")
    globe = read("apps/landing/components/semantic-globe.tsx")
    globe_rendering = read("apps/landing/lib/globe-rendering.ts")
    globe_implementation = "\n".join((globe, globe_rendering))
    pricing = read("apps/landing/lib/pricing-data.ts")
    product_profile = read("apps/landing/lib/product-profile.ts")
    form = read("apps/landing/components/pilot-access-form.tsx")
    endpoint = read("apps/landing/app/api/pilot-intake/route.ts")
    css = read("apps/landing/app/globals.css")
    tests = read("tests/landing/landing.spec.ts")

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
            "TubeGeometry",
            "ActivityArcLayer",
            "CloudLayer",
            "OpportunityMarkerLayer",
            "axignal-aura.svg",
            "AuraGlyph",
            "SVGLoader",
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
    require(
        product_profile,
        [
            'profileId: "TED_SEARCH_API_BOUNDED_PRODUCT_PROFILE"',
            'admissionState: "PRODUCT_ADMITTED"',
            'accessScope: "PRIVATE_AUTHENTICATED_PILOT"',
            'publicAccess: "PUBLIC_ACCESS_DISABLED"',
            "unrestrictedSourceUse: false",
            'demonstrationData: "SYNTHETIC_FIXTURES"',
        ],
        "current TED product projection",
    )
    require(
        pricing,
        [
            '"Controlled Free Trial"',
            '"7 days"',
            '"1,000,000 cumulative tokens / organisation · no overage"',
            "read-only at expiry",
            '"Apply for controlled trial"',
            '"Professional"',
            '"Team / Growth"',
            '"Enterprise"',
            '"Indicative candidate pricing"',
            '"Unlimited monthly AI within AXIGNAL scope"',
        ],
        "pricing boundary",
    )
    require(
        form,
        [
            'fetch("/api/pilot-intake"',
            'name="consent"',
            'name="website"',
            "aria-live",
        ],
        "pilot form",
    )
    require(
        endpoint,
        [
            "AXIGNAL_PILOT_INTAKE_WEBHOOK_URL",
            "AXIGNAL_PILOT_INTAKE_BEARER_TOKEN",
            "AXIGNAL_PILOT_CONTACT_EMAIL",
            "AbortSignal.timeout",
            '"cache-control": "no-store, max-age=0"',
        ],
        "pilot intake endpoint",
    )
    require(
        css,
        [
            "@media (prefers-reduced-motion: reduce)",
            ".cinematic-stage",
            ".trace-object",
            ".pricing-comparison",
            ".reduced-story",
            ".globe-poster",
            ".globe-initialising",
            ".skip-link",
        ],
        "landing styles",
    )
    require(
        tests,
        [
            "reducedMotion",
            "semantic-globe",
            "data-continuity-id",
            "Controlled Free Trial",
            "scrollWidth",
            "consoleErrors",
            "pageErrors",
        ],
        "landing browser tests",
    )

    for locale in LOCALES:
        messages = read(f"apps/landing/messages/{locale}.json")
        assert "TED remains TECHNICAL_PROBE" not in messages
        assert "TED sigue en TECHNICAL_PROBE" not in messages
        assert "TED reste TECHNICAL_PROBE" not in messages
        assert "TED continua TECHNICAL_PROBE" not in messages
        assert "TED bleibt TECHNICAL_PROBE" not in messages
        assert "TED resta TECHNICAL_PROBE" not in messages

    forbidden = [
        "pilot.axignal.com",
        "REMOTE_PILOT_ACCEPTED",
        "guaranteed return",
        "live investment performance",
    ]
    joined = "\n".join((experience, form, endpoint, pricing, product_profile))
    violations = [value for value in forbidden if value in joined]
    assert not violations, f"forbidden public/deployment claims present: {violations}"

    evidence = {
        "status": "PASS",
        "scope": "STATIC_IMPLEMENTATION_CONTRACT",
        "gsap_scrolltrigger": True,
        "single_persistent_canvas": True,
        "six_named_scenes": True,
        "semantic_globe": True,
        "texture_quality_tiers": True,
        "regional_europe_lod": True,
        "vector_boundaries": True,
        "adaptive_dpr_telemetry": True,
        "healthy_webgl_poster_isolated": True,
        "ted_bounded_product_projection": True,
        "historical_probe_rewrite_required": False,
        "controlled_trial_application_only": True,
        "pricing_operational_boundaries": True,
        "synthetic_demo_labelled": True,
        "reduced_motion_content_parity": True,
        "typed_intake_boundary": True,
        "visual_gate_independently_passed": False,
    }
    print(json.dumps(evidence, sort_keys=True))


if __name__ == "__main__":
    main()
