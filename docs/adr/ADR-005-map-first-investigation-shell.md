# ADR-005 — Map-first Investigation Shell

- Status: `PROPOSED / VALIDATION REQUIRED`
- Date: `2026-07-26`

## Context

AXIGNAL needs an interaction model capable of supporting discovery, spatial context, cross-market relationships, temporal replay and source-level evidence.

Three primary directions were evaluated:

1. configurable terminal;
2. conversational research workspace;
3. map-first investigation shell.

The configurable terminal provides density but repeats existing product patterns and shifts layout work to users. The conversational workspace reduces initial friction but is linear, weak at contradiction and highly exposed to absorption by general AI platforms.

The map-first shell best expresses the product's opportunity-climate metaphor and supports discovery before query, but it requires validation because not every opportunity is geographic and maps can become decorative or misleading.

## Decision candidate

Prototype AXIGNAL with:

- a map or globe as the primary discovery canvas;
- a persistent evidence rail;
- a persistent time machine;
- one shared `InvestigationContext`;
- Opportunity, Evidence, Contradiction, Transmission and History lenses;
- graph and history as reversible views of the selected subject;
- AI as “Explain current view”, not the primary product state;
- saved investigation trails distinct from watchlists.

## Consequences

- The frontend must preserve context across map, graph, claims and evidence.
- The API must support reproducible investigation-state deep links.
- Geographic and non-geographic objects require a common subject model.
- The design system needs a strict visualisation grammar for missing data, contradiction and inference.
- A synchronised list or table view is mandatory for accessibility and precise comparison.
- The architecture is not accepted until qualified-user tests pass.

## Validation gate

This ADR becomes `ACCEPTED` only when:

- at least five qualified users test an interactive prototype;
- map-first discovery proves useful relative to a list-first control;
- users correctly understand heat, coverage, claim type and contradiction;
- global-to-evidence navigation succeeds without material context loss;
- technical performance is feasible with representative fixtures.

## Rejection conditions

Reject or materially revise the decision if:

- geography is not central to the initial commercial universe;
- users consistently bypass the map;
- evidence auditing is slower than a simpler alternative;
- graph and timeline are misunderstood;
- the shell implies personalised investment recommendations;
- accessibility cannot be achieved without a structurally different primary interface.

## Evidence

- `docs/research/ux-competitive-benchmark.md`
- `docs/research/buyer-workflows.md`
- `docs/research/prototype-test-plan.md`
- `docs/flows/global-discovery-flow.md`
- `docs/prototypes/globe-opportunity-claims-v0.1.html`
