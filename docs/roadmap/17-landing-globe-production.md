# Landing Globe Production v0.1

## Status

`IMPLEMENTED CANDIDATE / LOCKFILE FROZEN / CI EVIDENCE REQUIRED / VISUAL REVIEW REQUIRED / NOT DEPLOYED`

## Goal

Replace the provisional static marketing page with AXIGNAL's production-grade Globe narrative while preserving epistemic, commercial and private-pilot boundaries.

## Tasks advanced

- `AX-F2-T10` — production marketing application using shared design-system primitives;
- `AX-F2-T11` — consent-aware private-pilot acquisition boundary;
- `AX-F2-T12` — accessibility, browser, responsive and reduced-motion validation.

## Delivered experience

- eight-act GSAP ScrollTrigger scrollytelling;
- React Three Fiber semantic Globe with GLSL surface treatment;
- canonical synthetic demonstration across Madrid, London, Paris and Berlin;
- persistent Navigator, signal-state and location HUD;
- claims, evidence, contradiction and deterministic-admission narrative;
- responsive mobile/tablet/desktop layouts;
- semantic HTML, keyboard focus, reduced-motion mode and WebGL fallback;
- private-pilot request form with server validation, consent, honeypot and configurable webhook;
- deterministic verifier and Playwright browser contract.

## Truth boundaries

- all displayed opportunity values are synthetic and labelled;
- no live source, investment return or deployment claim is made;
- the landing does not link to `pilot.axignal.com`;
- the intake endpoint reports failure when no delivery channel is configured;
- submitting the form does not create a subscription;
- public launch, pricing and private-pilot acceptance remain separate gates.

## Required environment

```text
AXIGNAL_PILOT_INTAKE_WEBHOOK_URL=<server-side delivery endpoint>
AXIGNAL_PILOT_INTAKE_BEARER_TOKEN=<optional server-side bearer token>
AXIGNAL_PILOT_CONTACT_EMAIL=<fallback contact address>
```

These values remain outside Git. Only the webhook URL and token are secret-bearing configuration; no environment value is exposed to the client bundle.

## Acceptance evidence

- `python scripts/verify_landing_foundation.py`;
- `python scripts/verify_landing_implementation.py`;
- `pnpm --filter @axignal/landing typecheck`;
- `pnpm --filter @axignal/landing build`;
- `pnpm exec playwright test -c playwright.landing.config.ts`;
- human visual review of scroll pacing, Globe framing, mobile composition and final conversion surface.

## Dependency evidence

The production dependencies and their transitive graph are frozen in `pnpm-lock.yaml`. The temporary lockfile and identifier-correction workflows have retired themselves and are not part of the proposed tree.

## Remaining gates

- obtain green GitHub Actions evidence;
- complete human visual review from browser screenshots;
- merge the exact reviewed SHA;
- configure a real intake delivery endpoint before treating the form as operational;
- deploy the public landing only under a separately authorised release gate.
