# Landing Globe Production v0.1

## Status

`IMPLEMENTED / LOCKFILE FROZEN / CI GREEN / VISUAL REVIEW PASS / READY FOR REVIEW / NOT DEPLOYED`

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

Implementation evidence head: `8b0650418994f2203d0e2e0b97d64472d892542e`.

- `Contract Validation`: PASS;
- `F1 Controlled Study Protocol`: PASS;
- `Human Review Acceptance`: PASS;
- `Executable Spine`: PASS;
- `Landing Globe`: PASS;
- `python scripts/verify_landing_foundation.py`: PASS;
- `python scripts/verify_landing_implementation.py`: PASS;
- `pnpm --filter @axignal/landing typecheck`: PASS;
- `pnpm --filter @axignal/landing build`: PASS;
- desktop and mobile Playwright browser contracts: PASS;
- reduced-motion and direct-access contracts: PASS;
- evidence artifact: `landing-globe-evidence`, SHA-256 `4cdbb2a90f1edb8cdb28145dc1739d9f70643e837010203fa8970c9df5bb6920`.

## Visual review

Human review of browser-generated evidence passed after two corrective iterations.

- desktop hero at 1280×720 preserves the primary and secondary CTA inside the first viewport;
- the Globe remains the dominant analytical surface while the narrative occupies a dedicated high-contrast rail;
- Navigator, location context, state transitions and synthetic-data disclosure remain legible;
- compact-height desktop presentation keeps the complete private-pilot form and submit action visible;
- mobile hero, story cards and private-pilot anchor render without horizontal overflow or fixed-header clipping;
- synthetic demonstration labels remain present on desktop and mobile.

## Dependency evidence

The production dependencies and their transitive graph are frozen in `pnpm-lock.yaml`. Temporary bootstrap and correction workflows retired themselves and are not part of the proposed tree.

## Remaining gates

- review and merge the exact final PR head;
- configure a real intake delivery endpoint before treating the form as operational;
- deploy the public landing only under a separately authorised release gate.
