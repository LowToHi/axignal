# ADR-013 — B2G Procurement Commercial and Global Source Program

Status: `PROPOSED / VALIDATION REQUIRED`
Date: `2026-07-29`
Goal ID: `AXIGNAL-GOAL-001`
Supersedes: no accepted ADR; narrows and operationalises ADR-012
Governing contract: `docs/contracts/28-b2g-procurement-commercial-and-global-source-program.md`

## Context

ADR-012 selected European Public Procurement Intelligence as AXIGNAL's sole first commercial implementation wedge. Subsequent technical work established a version-pinned TED eForms parser, deterministic sandbox admission, notice-lifecycle lineage, immutable Evidence Objects and a traceable dossier while correctly keeping TED outside `PRODUCT_ADMITTED` state.

The commercial and source-expansion questions remained unresolved:

- how to describe the product category and buyer;
- how to price a professional B2G product without appearing either inaccessible or commodity-grade;
- whether a seven-day free trial can demonstrate value safely;
- how to expand from TED to public-procurement systems in other jurisdictions without violating progressive source admission;
- how to preserve AXIGNAL's authority boundary while adding document analysis, global taxonomies and commercial entitlements.

Current market evidence shows that public-procurement intelligence is sold through both low-friction entry surfaces and premium team or enterprise offerings. This supports testing professional recurring prices and a controlled trial, but does not validate AXIGNAL's exact prices, conversion or product-market fit.

## Decision

AXIGNAL will use **B2G Public Procurement Intelligence** as the first commercial implementation category inside the broader **Global Opportunity Intelligence** architecture.

The primary commercial narrative will focus on organisations that sell to government and need to find, qualify and investigate opportunities with source-linked evidence.

AXIGNAL will adopt the following candidate commercial architecture:

- paid Design Partner access at a bounded preferential price;
- Professional pricing hypothesised at `€349–€499/month`;
- Team / Growth pricing hypothesised at `€899–€1,499/month`;
- Enterprise pricing hypothesised from `€18,000–€45,000/year`, subject to seats, data, API, security, support and integration obligations;
- no permanent full-product low-cost tier during the initial B2G launch;
- value metrics based on ResearchRuns, dossiers, monitored opportunities, collaboration and admitted coverage rather than model tokens or chat messages.

AXIGNAL will design a **seven-day controlled free trial**, disabled until its gates pass. The initial trial candidate will:

- verify an organisation and resolve a tenant server-side;
- expose TED / admitted European procurement only;
- cap ResearchRuns, dossiers, documents, pages, saved opportunities and exports;
- exclude API, bulk redistribution, private connectors, unlimited AI, enterprise administration and predictions;
- avoid silent conversion and initially prefer no card requirement;
- stop execution at expiry, move to a declared read-only state and delete tenant-private trial data under a tested retention policy;
- enforce cost, abuse, rights, privacy and tenant-isolation controls.

AXIGNAL will interpret “all TEDs globally” as a **federated Global Public Procurement Source Program**. Each official portal, API, bulk dataset or feed will be treated as an independent source with its own rights, parser, quality, lifecycle, attribution, privacy, cost and kill-switch record.

The programme will:

1. preserve TED as the sole current implementation wedge;
2. complete the TED product-admission and persistent ResearchRun loop first;
3. catalogue global official systems without claiming support;
4. use bounded technical probes;
5. admit sources independently;
6. map them into a canonical procurement model while preserving source-native taxonomies and semantics;
7. expand commercial jurisdiction packs only after buyer-demand and economic gates pass.

OCDS may be used as an interoperability envelope, but not as evidence that one parser, one licence or one lifecycle model fits every publisher.

## Authority boundary

This ADR does not:

- promote TED or any other source to `PRODUCT_ADMITTED`;
- enable billing, trial, Stripe, API or private connectors;
- grant AI admission authority;
- authorise predictive win, margin, eligibility or legal conclusions;
- authorise scraping;
- authorise public claims of global procurement coverage;
- change the next implementation priority from the authenticated, tenant-scoped, persistent ResearchRun loop.

## Alternatives considered

### A. Low-cost freemium as the primary launch

Rejected as the default because it risks anchoring AXIGNAL as a commodity alert or data-search product before evidence-led workflow value is demonstrated. A bounded public or free surface remains possible.

### B. Enterprise-only sales from launch

Rejected as the only route because it lengthens sales cycles and prevents efficient testing with qualified SMEs, bid professionals and consultancies. Enterprise remains an annual governed tier.

### C. Unlimited seven-day trial

Rejected because unbounded document processing, exports and model use create source-right, abuse, privacy and gross-margin risk and reveal no reliable willingness-to-pay signal.

### D. Require a card and auto-convert every trial

Rejected for the initial validation state because it may optimise billing mechanics before trust and product value are established. It can be tested later only with transparent consent and evidence.

### E. Ingest all global portals immediately

Rejected because breadth before source admission would violate Contracts 03 and 28, dilute the TED E2E priority and create superficial, legally ambiguous coverage.

### F. Treat OCDS as a universal connector

Rejected because publisher implementations differ in completeness, lifecycle, extensions, identifiers, rights and quality.

### G. Build a universal scraper for portal-only systems

Rejected. Portal-only sources require an official export, partnership, documented lawful basis or user-authorised connector.

## Consequences

### Positive

- commercial narrative now matches the selected first universe;
- prices can be tested within a credible professional B2G range without being represented as validated;
- the trial has an explicit value loop and safety boundary;
- global ambition is retained without weakening progressive source admission;
- global adapters can share a canonical model while preserving native semantics;
- the programme creates a defensible source, lifecycle and evidence graph rather than a shallow notice aggregator.

### Negative and cost

- global coverage will progress more slowly than a scraping-first approach;
- source-specific legal, parser and quality work increases implementation cost;
- premium positioning requires a stronger dossier and workflow proof than commodity alerts;
- the trial requires entitlements, metering, deletion, abuse controls and support before launch;
- exact packaging cannot be frozen until paid evidence exists.

### Risks

- users may value only alerts and refuse professional pricing;
- a seven-day window may be too short for low-frequency procurement workflows;
- the entry price may still be too high for some SMEs or too low for the desired premium signal;
- source fragmentation may make cross-jurisdiction comparisons expensive;
- document availability and rights may constrain promised evidence depth;
- global expansion may distract from European product-market validation.

Each risk is controlled through explicit hypotheses, staged source admission, paid design partners, measurable trial economics and kill conditions.

## Validation obligations

This decision advances only when:

- the TED end-to-end loop reaches its applicable product-admission and operational gates;
- qualified B2G buyers understand the narrative;
- paid Design Partner or equivalent annual-contract evidence exists;
- at least two pricing/packaging offers are tested;
- the seven-day trial passes server-side entitlement, expiry, deletion, rights, security, privacy, abuse and cost tests;
- the global catalogue records source-specific official evidence and avoids unsupported availability claims;
- at least one non-TED official source completes a bounded technical probe before any global product claim;
- every admitted jurisdiction pack demonstrates user demand and acceptable margin.

## Migration

This ADR initially changes documentation, hypotheses, source catalogue and roadmap only. It creates no runtime, schema, source-state, billing, customer-data or public-price migration.

## Rollback

If validation fails:

- mark ADR-013 `SUPERSEDED` or `REJECTED` without erasing evidence;
- retire Contract 28 or replace its commercial hypotheses;
- disable the trial feature flag and preserve no active automatic conversion;
- leave all candidate global sources disabled;
- retain TED as the only selected implementation wedge unless ADR-012 is independently superseded;
- restore the previous packaging hypothesis only through a new recorded decision.
