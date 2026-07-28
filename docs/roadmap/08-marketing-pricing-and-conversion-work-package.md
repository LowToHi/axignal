# 08 — Marketing, Pricing and Conversion Work Package

Version: `0.1.0-candidate`
Status: `CROSS-PHASE VALIDATION PLAN / NOT FROZEN`
Goal ID: `AXIGNAL-GOAL-001`
Primary issue: `#6`

## 1. Purpose

This work package converts Contracts 21–24 and ADR-007 into executable product, design, commercial and engineering work.

It treats the marketing site, pricing, Trust Center and acquisition system as part of AXIGNAL's end-to-end product rather than post-launch decoration.

## 2. Phase relationship

The work spans several phases:

- `F0` — contract and Goal Lock integration;
- `F1` — landing architecture, faithful product proof, visual and comprehension prototypes;
- `F2` — reproducible web, analytics and test infrastructure;
- `F6` — multilingual public surfaces;
- `F9` — paid design partners, pricing, billing and conversion;
- `F11` — enterprise trust, API and security surfaces;
- `F12` — repeatable acquisition, margin and expansion.

Work may be designed early, but production capability remains gated by the applicable phase.

## 3. Workstreams

### A. Selected product UI fidelity

- implement ADR-007 composition;
- reproduce dark and light reference shells;
- preserve Navigator, lens switch, Globe/Graph, opportunities, evidence and Timeline;
- create versioned reference captures;
- add visual-regression fixtures;
- prevent generic-dashboard drift.

### B. Marketing-site architecture

- define sitemap and global navigation;
- define hero and value proposition;
- build faithful product demonstration;
- define product-system explanation;
- create use-case routing;
- define differentiation and methodology sections;
- define CTA hierarchy;
- define responsive footer and legal surfaces.

### C. Pricing and packaging

- test Research, Professional and Enterprise positioning;
- define candidate value metric;
- build pricing and detailed comparison;
- define early-access and design-partner states;
- model entitlements and source-right interaction;
- test willingness to pay;
- validate gross margin and support burden.

### D. FAQ and objection handling

- collect objections from usability, sales and design-partner sessions;
- maintain product, functionality, privacy and commercial FAQ;
- link answers to current contracts and deployed capabilities;
- test comprehension and reduction in sales friction.

### E. Trust Center and methodology

- publish product methodology;
- explain claims, evidence, contradiction and unknown coverage;
- explain AI and Navigator authority;
- explain Knowledge Tides and user controls;
- publish coverage and source-right model;
- publish security, accessibility, status and correction surfaces;
- maintain review owners and dates.

### F. Acquisition analytics and experiments

- implement typed funnel events;
- connect landing activity to first-investigation completion;
- register experiments before exposure;
- implement consent-aware attribution;
- integrate CRM and scheduling;
- enforce guardrail metrics;
- validate channels before reinvestment.

### G. Multilingual conversion

- implement `en`, `es`, `fr`, `de`, `pt-BR`, `zh-Hans`;
- localise metadata, FAQ, pricing, tax and forms;
- test terminology and layout expansion;
- preserve legal and product meaning;
- add locale-specific structured data and hreflang.

## 4. Task additions

### F0

- `AX-F0-T07` — integrate Contracts 21–24 and ADR-007 into all indexes, gates and agent routing.

### F1

- `AX-F1-T13` — reproduce the selected dark Investigation Shell reference faithfully.
- `AX-F1-T14` — reproduce the selected light Investigation Shell reference faithfully.
- `AX-F1-T15` — create faithful Graph and Dual states using the same component system.
- `AX-F1-T16` — design the conversion landing architecture and full page flow.
- `AX-F1-T17` — prototype the hero and canonical product demonstration.
- `AX-F1-T18` — prototype Pricing, plan comparison, FAQ and Trust Center entry points.
- `AX-F1-T19` — compare conversion comprehension and trust across candidate landing variants.
- `AX-F1-T20` — store versioned reference assets and visual-regression fixtures.

### F2

- `AX-F2-T10` — scaffold marketing application or route group with shared design-system packages.
- `AX-F2-T11` — implement typed acquisition event schemas and consent-aware analytics adapter.
- `AX-F2-T12` — add landing performance, accessibility, SEO and visual-regression CI.
- `AX-F2-T13` — add CRM, scheduling and lead-routing interfaces without canonical-claim authority.

### F6

- `AX-F6-T09` — localise landing, pricing, FAQ, methodology and structured metadata.
- `AX-F6-T10` — validate six-language commercial and legal terminology.

### F9

- `AX-F9-T08` — validate package names and value metrics.
- `AX-F9-T09` — implement pricing, plan comparison and entitlement catalogue.
- `AX-F9-T10` — implement trial, sandbox or design-partner access flow.
- `AX-F9-T11` — implement self-service upgrade, downgrade and cancellation where applicable.
- `AX-F9-T12` — publish first validated FAQ and Trust Center.
- `AX-F9-T13` — instrument full acquisition-to-activation funnel.
- `AX-F9-T14` — execute willingness-to-pay and conversion tests.

### F11

- `AX-F11-T08` — publish enterprise Trust Center package and controlled evidence room.
- `AX-F11-T09` — expose API, private-source and security maturity accurately on public surfaces.

### F12

- `AX-F12-T07` — validate repeatable acquisition channel against activation, retention and margin.
- `AX-F12-T08` — operate experiment registry and reinvestment policy.
- `AX-F12-T09` — maintain public pricing, methodology, FAQ and Trust Center change control.

## 5. Required dynamic skills

Tasks SHOULD activate applicable skills such as:

- goal-keeper;
- contract-router;
- interaction-architect;
- visualisation-designer;
- frontend-architect;
- accessibility-auditor;
- multilingual-localiser;
- conversion-copy-strategist;
- pricing-and-packaging-analyst;
- entitlement-architect;
- growth-analyst;
- experimentation-engineer;
- analytics-engineer;
- consent-ux-reviewer;
- privacy-reviewer;
- security-reviewer;
- source-admission;
- legal-doc-coordinator;
- SEO-architect;
- CRM-automation-engineer;
- performance-engineer;
- gate-evaluator.

Missing skills MUST be added to the dynamic skill registry before task execution.

## 6. Shared fixtures

All landing and pricing prototypes MUST use the same truthful candidate product state:

- AXIGNAL brand and axignal.com;
- selected dark/light Investigation Shell;
- canonical Moscow real-estate synthetic investigation when used;
- labelled synthetic data;
- same capabilities and entitlement maturity;
- same supported languages;
- no invented customers, metrics or integrations.

## 7. Automated evidence

Required automated evidence includes:

- screenshot regression against approved reference captures;
- token and hard-coded semantic-colour audit;
- WCAG checks;
- reduced-motion captures;
- dark/light parity;
- six-language overflow tests;
- SEO and structured-data validation;
- Core Web Vitals or equivalent laboratory budgets;
- form validation and error-state tests;
- analytics event-schema tests;
- experiment-assignment tests;
- pricing and entitlement consistency tests;
- broken-link and Trust Center freshness checks.

## 8. Human evidence

Qualified participants MUST be able to:

- identify what AXIGNAL is within the initial landing experience;
- distinguish it from a chatbot, trading tool and personalised adviser;
- explain the Ask → Navigate → Discover → Verify → Compare → Track workflow;
- identify the primary CTA;
- understand plan differences and limits;
- locate methodology, privacy and Knowledge Tides information;
- complete an access or demo flow;
- begin and complete a sample investigation;
- identify claims, evidence, contradiction and unknown coverage.

## 9. Commercial evidence

Before public scale, evidence SHOULD include:

- qualified lead rate;
- demo or access-request conversion;
- meeting show rate;
- design-partner or paid conversion;
- first-investigation completion;
- retention and expansion;
- willingness to pay;
- acquisition cost;
- payback and gross margin;
- sales and support burden;
- lost-deal and cancellation reasons.

## 10. Non-negotiable constraints

- no fabricated proof;
- no impossible product UI;
- no fake urgency or discounting;
- no hidden limits or overages;
- no Knowledge Tide presented as economic truth;
- no acquisition experiment may weaken epistemic, privacy or accessibility controls;
- no scaled paid acquisition before channel and unit-economics validation;
- no production token freeze without the applicable ADR and evidence.

## 11. Gate outcomes

The gate evaluator may return:

- `ACCEPT_UI_FIDELITY_TARGET`;
- `REVISE_UI_IMPLEMENTATION`;
- `ACCEPT_LANDING_FOR_NEXT_PROTOTYPE`;
- `REVISE_LANDING_AND_RETEST`;
- `ACCEPT_PACKAGING_HYPOTHESIS`;
- `REJECT_PACKAGING_HYPOTHESIS`;
- `INSUFFICIENT_COMMERCIAL_EVIDENCE`;
- `AUTHORISE_LIMITED_DESIGN_PARTNER_LAUNCH`;
- `AUTHORISE_CHANNEL_REINVESTMENT`.

## 12. Rollback

All visual, copy, pricing and experiment variants MUST remain versioned. Rollback MUST preserve:

- previous product UI reference;
- previous landing content and routing;
- previous pricing and entitlements;
- previous FAQ and Trust Center version;
- experiment assignment and outcome history;
- customer contractual commitments.