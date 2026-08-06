# P23-T02 — Message & Copy Validation E2E

Task: `AX-GE2E-P23-T02`

Baseline: P24 exact head `ce9900dc7372db4499205a87ccb1cad4f2b08527`.

Status: `DESK_RESEARCH_VALIDATED_IMPLEMENTED / BUYER AND CONVERSION EVIDENCE PENDING`.

## Objective

Replace architecture-first landing copy with a buyer-outcome narrative, implement it in the real AXIGNAL landing, preserve claim boundaries, bind displayed plans to the versioned server-side price book, qualify controlled-access demand and verify the result through production build and browser tests.

This task does not describe a mockup. The source of truth is the running `apps/landing` application.

## Research completed

Research date: 31 July 2026.

### Current category messaging

| Product | Current message pattern | Implication for AXIGNAL |
|---|---|---|
| Glean | Find answers and move from query to action across company knowledge | Lead with the job and speed, then prove permissions and governance |
| Perplexity Research | Search more sources, cross-reference information and produce professional reports | Buyers already understand deep research; AXIGNAL must explain the persistent evidence and review advantage |
| AlphaSense | Replace fragmented research with a unified workflow and accelerate smarter decisions | Fragmentation and research workflow are validated category problems |
| Hebbia Matrix | Execute serious multi-step work across large data sets with transparency | Transparency is valuable proof, but the headline still leads with the work outcome |

Sources reviewed:

- https://www.glean.com/enterprise-search
- https://www.glean.com/
- https://www.perplexity.ai/help-center/en/articles/13600190-what-s-new-in-advanced-deep-research
- https://www.alpha-sense.com/platform/
- https://www.hebbia.com/product
- https://www.hebbia.com/blog/5-ways-equity-research-teams-use-hebbia-to-drive-speed-and-insight

### Voice-of-customer themes

Verified review aggregates and recent reviewer narratives consistently identify:

- value from faster search and synthesis;
- value from combining external and internal information;
- value from cited or traceable outputs;
- frustration with information overload;
- frustration with steep learning curves and complex interfaces;
- risk from low-quality or incomplete retrieval;
- need to audit extracted or generated information.

Sources reviewed:

- https://www.g2.com/products/alphasense/reviews
- https://www.g2.com/products/alphasense/reviews?qs=pros-and-cons
- https://www.g2.com/es/products/hebbia-ai-2026-02-24/reviews

These observations are directional desk research. They do not substitute for interviews with AXIGNAL buyers or measured conversion.

## Message decision

### Category

**Evidence-backed research workspace**

This category is concrete enough for first-screen comprehension and broad enough to support strategy, investment, corporate development, competitive intelligence and research operations.

### Winner

**Eyebrow**

> EVIDENCE-BACKED RESEARCH FOR HIGH-STAKES DECISIONS

**Headline**

> Turn scattered sources into a decision your team can verify.

**Supporting headline**

> Keep the evidence trail intact.

**Subheadline**

> AXIGNAL brings research questions, sources, claims, uncertainty and review into one governed workspace. Strategy, investment and intelligence teams can move faster without rebuilding the trail in slides, chats and spreadsheets.

**Primary CTA**

> Request a research workspace

**Secondary CTA**

> See the research workflow

**Proof line**

> Sources stay attached · Uncertainty stays visible · Review stays human

### Rejected as primary hero positioning

- `Global Opportunity Intelligence`
- `Research intelligence with an evidence trail`
- `Evidence infrastructure for high-stakes research and decisions`

These formulations remain useful as product architecture or category explanation, but they ask the visitor to decode AXIGNAL before understanding the job it performs.

## Copy hierarchy

1. **Outcome:** convert scattered research into a verifiable decision record.
2. **Problem:** evidence, contradictions and context are lost across tools.
3. **Workflow:** define the decision, investigate, attach support, surface counter-evidence and review.
4. **Differentiation:** proposal, evidence admission and human authority remain separate.
5. **Commercial boundary:** candidate packages exist, but public live checkout does not.
6. **Conversion:** request a controlled research workspace around one real decision.

## Priority buyer groups

1. Corporate strategy and corporate development.
2. Investment research and diligence teams.
3. Competitive and market intelligence teams.
4. Knowledge and research operations.

The intake form now captures the role in the decision and asks:

> What must your team decide, and where does the current research workflow break?

This produces more useful qualification evidence than a generic request for a use case.

## Objection handling

| Objection | Landing response |
|---|---|
| Another AI search or summary tool? | AXIGNAL keeps the question, sources, claims, uncertainty and review in one persistent workflow. |
| Can the conclusion be trusted? | No truth guarantee is made; support, limits and contradictions remain inspectable. |
| Does AI make the decision? | Models propose; policy and human review retain authority. |
| Can private information be used? | Private use is governed by tenant, rights, retention and security controls. |
| Can we buy it now? | Professional and Team are candidate controlled-access packages; Stripe live remains disabled. |

## Real implementation

The winner has been implemented in:

- `apps/landing/components/landing-experience.tsx`
- `apps/landing/lib/landing-data.ts`
- `apps/landing/components/pilot-access-form.tsx`
- `apps/landing/app/api/pilot-intake/route.ts`
- `apps/landing/app/layout.tsx`
- `apps/landing/app/message-copy.css`

The implementation adds:

- buyer-outcome hero and navigation;
- explicit problem section;
- rewritten eight-step research story;
- evidence and authority explanation in plain language;
- outcome cards;
- candidate Professional and Team plan presentation;
- security and authority boundaries;
- FAQ and objection handling;
- decision-qualified controlled-access form;
- message-version attribution on intake records;
- noindex publication gate.

## Pricing integrity

The landing does not own the price values. `apps/landing/lib/candidate-pricing.ts` reads:

`data/commercial/commercial-runtime-pricing-stripe-runtime.v0.1.json`

and fails closed unless:

- the price book is `CANDIDATE_ONLY`;
- currency is EUR;
- Professional and Team are recurring monthly plans;
- amounts and seat limits are complete;
- commercial activation remains false.

This prevents the landing from drifting away from the server-side commercial contract.

## Evidence states

| Evidence | State |
|---|---|
| Current market and competitor desk research | Complete |
| Verified review theme analysis | Complete |
| Product-truth and claim mapping | Complete |
| Winner implemented in real landing | Complete |
| Production build | CI gate |
| Desktop and tablet browser acceptance | CI gate |
| Intake failure and persistence boundary | CI gate |
| Direct buyer interviews | Pending |
| First-screen comprehension sessions | Pending |
| Controlled conversion sample | Pending |
| Paid-customer activation and value evidence | P24 pending |

## Truth boundary

```text
current market research != product-market fit
review themes           != direct buyer interview
implemented copy        != conversion winner
controlled request      != accepted pilot
accepted pilot          != paid customer
paid invoice            != completed customer value
```

## Launch boundary

The message is implemented and testable, but the landing remains `noindex`, public publication remains unauthorized, paid media remains off and Stripe live remains blocked.

The next market evidence must come from real buyer behaviour: qualified interviews, comprehension, controlled-access requests, accepted pilots, activation and completed value workflows.
