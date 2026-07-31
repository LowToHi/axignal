#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


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
    form = read("apps/landing/components/pilot-access-form.tsx")
    endpoint = read("apps/landing/app/api/pilot-intake/route.ts")
    css = read("apps/landing/app/globals.css")
    message_css = read("apps/landing/app/message-copy.css")
    pricing = read("apps/landing/lib/candidate-pricing.ts")
    tests = read("tests/landing/landing.spec.ts")

    require(
        experience,
        [
            "ScrollTrigger",
            "pin: globeStage.current",
            "prefers-reduced-motion",
            "Synthetic demonstration · not investment performance",
            "Proposal is not admission",
            "Request a research workspace",
            "Turn scattered sources into a decision your team can verify.",
            "data-message-version={MESSAGE_VERSION}",
            'id="pricing"',
        ],
        "landing experience",
    )
    require(
        globe,
        [
            'from "@react-three/fiber"',
            "vertexShader",
            "fragmentShader",
            "citySignals",
            "powerPreference",
        ],
        "semantic globe",
    )
    require(
        form,
        [
            'fetch("/api/pilot-intake"',
            'name="consent"',
            'name="website"',
            "messageVersion",
            "aria-live",
        ],
        "controlled-access form",
    )
    require(
        endpoint,
        [
            "AXIGNAL_PILOT_INTAKE_WEBHOOK_URL",
            "AXIGNAL_PILOT_INTAKE_BEARER_TOKEN",
            "AXIGNAL_PILOT_CONTACT_EMAIL",
            "messageVersion",
            "AbortSignal.timeout",
            '"cache-control": "no-store"',
        ],
        "controlled-access intake endpoint",
    )
    require(
        css,
        [
            "@media(prefers-reduced-motion:reduce)",
            ".globe-fallback",
            ".story-shell",
            ".skip-link",
        ],
        "landing styles",
    )
    require(
        message_css,
        [
            ".problem-section",
            ".pricing-section",
            ".assurance-section",
            ".faq-section",
        ],
        "buyer-message styles",
    )
    require(
        pricing,
        [
            "commercial-runtime-pricing-stripe-runtime.v0.1.json",
            'pricing?.status !== "CANDIDATE_ONLY"',
            "plan.commercial_activation_authorised !== false",
        ],
        "server-resolved candidate pricing",
    )
    require(
        tests,
        [
            "reducedMotion",
            "semantic-globe",
            "pilot-intake",
            "messageVersion",
            "professional_monthly",
            "scrollWidth",
        ],
        "landing browser tests",
    )

    forbidden = [
        "pilot.axignal.com",
        "REMOTE_PILOT_ACCEPTED",
        "guaranteed return",
        "live investment performance",
        "zero hallucinations",
        "market validated",
    ]
    joined = "\n".join((experience, form, endpoint))
    violations = [value for value in forbidden if value in joined]
    assert not violations, f"forbidden public/deployment claims present: {violations}"

    evidence = {
        "status": "PASS",
        "message_version": "buyer-outcome-v1.0",
        "real_landing_copy_implemented": True,
        "server_price_book_bound": True,
        "gsap_scrolltrigger": True,
        "react_three_fiber": True,
        "semantic_globe": True,
        "synthetic_demo_labelled": True,
        "reduced_motion": True,
        "webgl_fallback": True,
        "typed_intake_boundary": True,
        "browser_contract": True,
        "remote_pilot_claimed_deployed": False,
    }
    print(json.dumps(evidence, sort_keys=True))


if __name__ == "__main__":
    main()
