# ADR-014 — B2G Landing International Runtime

Status: `PROPOSED / IMPLEMENTATION EVIDENCE REQUIRED`
Date: `2026-07-29`
Goal ID: `AXIGNAL-GOAL-001`
Governing contracts: `01–06`, `08`, `12–13`, `16`, `18`, `20–21`, `23`, `28`
Related decision: `ADR-013`

## Context

The deployed landing represents AXIGNAL's broad category but not its selected B2G procurement wedge. It is English-only, renders procedural pseudo-geography, uses a one-step investor-oriented pilot form and lacks localized commercial metadata, candidate pricing disclosure and a typed source-state legend.

## Decision

The public landing will use an SSR-first Next.js route architecture with canonical English at `/`, five explicit localized aliases (`/es`, `/fr`, `/pt`, `/de`, `/it`) and a permanent `/en` redirect. Locale dictionaries are versioned JSON files and metadata is generated from the same locale contract.

The initial HTML contains the full hero and commercial narrative. One client-mounted Globe Canvas remains the visual protagonist through six named GSAP `ScrollTrigger` scenes: global view, Europe focus, public-record fragmentation, evidence admission, InvestigationContext and traceable dossier. Desktop uses a pinned scrubbed timeline, tablet reduces geometry, mobile shortens the pinned distance, and reduced motion exposes the same states without prolonged scrub or continuous rotation.

The globe uses a local derivative of authorised real Earth imagery, typed catalogue/source states and an adjacent non-WebGL data equivalent. The landing consumes a current bounded projection—`TED Search API → PRODUCT_ADMITTED → PRIVATE_AUTHENTICATED_PILOT → PUBLIC_ACCESS_DISABLED`—without mutating historical technical-probe artifacts. Source state, not visual intensity, determines whether coverage is active.

The public conversion flow is a two-step Design Partner intake. The client collects only fit information needed for review. The server validates a strict allowlist, applies bounded abuse and duplicate controls, records only redacted operational logs and fails closed when persistence is unavailable. Lead fields never enter analytics.

Design Partner is presented as a separate paid validation programme. Pricing then compares Controlled Free Trial, Professional, Team / Growth and Enterprise across operational boundaries. Candidate ranges are explicitly indicative. The Controlled Free Trial is application-only, lasts seven days, grants 1,000,000 cumulative organisation tokens, requires no card, has no renewal or overage and becomes read-only at expiry. Public trial activation, checkout, subscription and automatic conversion are not implemented.

## Alternatives considered

### One client-only localized page

Rejected because it weakens initial HTML, metadata, crawlability and no-JavaScript resilience.

### One global English page with browser translation

Rejected because semantic parity, localized search intent and intentional terminology cannot be tested.

### Third-party map or analytics SDK

Rejected for this phase because it adds consent, data-transfer, runtime and dependency costs that native Three.js and a provider-agnostic event adapter avoid.

### Remote globe texture hotlink

Rejected because availability, provenance, caching and supply-chain control would be externalised.

### Active-looking global coverage demo

Rejected because the bounded TED pilot admission does not authorise global coverage or unrestricted source use.

## Tradeoffs

- JSON parity adds editorial maintenance but makes locale drift testable.
- A local compressed Earth texture adds bundle weight but removes pseudo-geography and hotlink risk.
- In-memory abuse controls are process-local and therefore a bounded pilot control, not a final distributed rate limiter.
- Server-rendering all copy increases HTML size but protects comprehension and SEO before enhancement.

## Consequences

- Every locale has explicit canonical and alternate metadata.
- The initial page remains useful without WebGL or animation.
- Visual source states match the bounded current product-profile boundary while historical evidence remains intact.
- Commercial leads can be qualified without enabling billing.
- Public source access, global coverage and validated pricing remain blocked.

## Rollback

Revert the landing application, public derivatives and route configuration. No database migration, canonical source-ledger transition, billing state or customer entitlement is created.
