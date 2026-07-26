# 12 — Interaction Model Contract

Version: `0.2.0-candidate`
Status: `NORMATIVE CANDIDATE / USER VALIDATION REQUIRED`

## 1. Scope

This contract defines the candidate interaction model for the AXIGNAL research shell.

It refines the conceptual requirements in `05-ui-ux-exploration.md` but MUST NOT be described as final until the prototype validation gate passes.

Canonical research flow:

```text
Globe
→ opportunity
→ claims
→ evidence
```

## 2. Selected interaction architecture

AXIGNAL MUST prototype a **Map-first Investigation Shell**.

The shell MUST contain four persistent regions:

1. global command and context header;
2. universe and lens rail;
3. primary spatial or relational canvas;
4. evidence rail;
5. persistent time machine.

The evidence rail and time machine are not optional secondary pages. They preserve epistemic and temporal context while the central canvas changes.

## 3. Primary product state

All core surfaces MUST bind to one versioned `InvestigationContext`.

Minimum fields:

- selected subject;
- subject type;
- geography scope;
- universe and sector scope;
- active lens;
- primary and overlay metrics;
- as-of time;
- comparison time;
- claim-state and confidence filters;
- source filters;
- selected graph path;
- navigation history;
- entitlement scope.

A surface MUST NOT maintain a hidden conflicting selection state.

## 4. Context continuity

Moving among map, graph, opportunity, claim, evidence and history MUST preserve all compatible context.

The application MUST implement:

- browser-compatible back and forward;
- typed context breadcrumbs;
- reversible nested rail states;
- deep links to reproducible research state;
- explicit “start new investigation” behaviour;
- saved investigation trails.

Closing a claim or evidence detail MUST return the user to the exact preceding scroll, lens, time and map position.

## 5. Globe behaviour

The Globe MUST:

- begin with one meaningful primary metric;
- state metric, unit, aggregation, time window, source coverage and freshness;
- support semantic zoom;
- expose a synchronised non-map result list;
- reveal opportunity clusters without requiring search;
- preserve user orientation during camera movement;
- support a flat map mode for quantitative comparison;
- avoid decorative globe rotation or forced camera tours.

## 6. Semantic zoom

Zoom MUST change the aggregation and object vocabulary according to an explicit hierarchy.

The current aggregation level MUST always be visible.

The product MUST NOT compare values across aggregation levels without a declared normalisation.

Zooming and selecting are separate actions.

## 7. Evidence rail

The evidence rail MUST remain present in desktop investigation flows.

Rail states:

- global or scoped summary;
- region or market climate;
- opportunity;
- claim;
- evidence;
- AI explanation.

The rail MUST support nested inspection without losing the central canvas context.

Opportunity state MUST give equal structural access to:

- supporting claims;
- contradicting claims;
- unknowns;
- invalidation conditions.

## 8. Lens model

Canonical primary lenses:

- `OPPORTUNITY`
- `EVIDENCE`
- `CONTRADICTION`
- `TRANSMISSION`
- `HISTORY`

Only one primary lens may be active.

A lens changes the representation of the selected subject; it does not create a new unrelated workspace.

### Transmission lens

Transmission MUST use a bounded graph over the same selected subject and time.

Edges MUST state their semantic type and epistemic basis.

The graph MUST distinguish:

- observed relationships;
- calculated relationships;
- inferred associations;
- causal hypotheses;
- contradictions.

### History lens

History MUST reconstruct what the system knew at the selected time and MUST prevent future-evidence leakage.

## 9. Layer model

At most one heat-based primary layer SHOULD be active.

An optional overlay MAY use:

- paths;
- symbols;
- boundaries;
- hatching;
- isolines;
- sparse annotations.

Two competing heat palettes MUST NOT be combined.

Every layer MUST have a visible legend and coverage state.

## 10. Time machine

The time machine MUST remain visible in compact desktop form.

Modes:

- `CURRENT`
- `AS_OF`
- `COMPARE`
- `PLAYBACK`

The map, graph, evidence rail and visible metrics MUST update from the same temporal context.

Playback MUST pause at material claim or opportunity-state changes and MUST support reduced-motion behaviour.

## 11. Command and search

The command interface MUST support both lexical discovery and expert acceleration.

It MAY:

- locate canonical resources;
- set geography, time, universe, layer or lens;
- open a saved investigation;
- invoke bounded AI explanation.

It MUST NOT become the sole route to product value.

Search-result ranking MUST disclose material semantic or graph contribution.

## 12. Conversational explanation

The primary AI action is **Explain current view**.

The model MUST receive a bounded, authorised context and canonical resource set.

The explanation MUST:

- distinguish retrieved facts and generated synthesis;
- cite claim IDs;
- expose contradictions and unknowns;
- preserve the current research state;
- remain a secondary lens.

Generated text MUST NOT create or change canonical claim state.

## 13. Saved investigation trail

A saved trail MUST preserve:

- selected resources;
- map position and aggregation;
- graph path;
- active lens and layers;
- time and comparison;
- filters;
- pinned claims and evidence;
- user notes;
- cited generated explanations and their resource versions.

A watchlist observes resources. An investigation trail preserves a reasoning path. They MUST be separate object types.

## 14. Density contract

AXIGNAL MAY be information-dense but MUST avoid card proliferation.

Hierarchy preference:

1. spacing and alignment;
2. typography;
3. dividers;
4. surface tint;
5. borders;
6. elevation only when functionally required.

The first-use experience MUST provide curated defaults. Blank-canvas dashboard construction is prohibited during initial onboarding.

## 15. Motion contract

Motion MAY communicate:

- spatial continuity;
- temporal change;
- graph expansion;
- selection transfer;
- state transition.

Motion MUST NOT:

- manufacture urgency;
- continuously animate without analytical value;
- move the camera unexpectedly;
- delay access to evidence;
- override reduced-motion preferences.

## 16. Keyboard contract

Desktop MUST support discoverable shortcuts for:

- command palette;
- lens switching;
- save trail;
- back and forward context;
- close nested rail;
- timeline stepping;
- layer control.

Shortcuts MUST not conflict with text editing and SHOULD be remappable for professional users.

## 17. Accessibility contract

Every map or graph state MUST have a synchronised textual representation.

The interface MUST provide:

- semantic headings in the evidence rail;
- keyboard selection and traversal;
- visible focus;
- colour-independent encodings;
- reduced motion;
- textual metric and coverage summaries;
- relationship lists for graph paths;
- date inputs and step controls for time;
- accessible announcements for material state changes.

## 18. Responsive contract

Desktop is the full investigation environment.

Mobile MUST support:

- alerts and watchlists;
- saved trail review;
- opportunity, claim and evidence reading;
- limited spatial inspection;
- simple bounded relationship paths;
- handoff to desktop for complex analysis.

The evidence rail becomes a bottom sheet or full-height detail surface on mobile.

## 19. Failure behaviour

The UI MUST distinguish:

- zero admitted claims;
- no source coverage;
- stale or suspended source;
- entitlement restriction;
- filter-empty result;
- graph density limit;
- historical reconstruction unavailable;
- model or explanation unavailable.

Missing data MUST NOT be rendered as neutral or low opportunity.

## 20. Prototype gate

This contract reaches `NORMATIVE` final status only when an interactive prototype proves:

1. global-to-evidence navigation;
2. exact context restoration;
3. shared state across map, graph and time;
4. understandable metric and coverage;
5. visible contradictions and unknowns;
6. no future-evidence leakage;
7. keyboard and reduced-motion operation;
8. textual alternatives;
9. acceptable performance with representative fixtures;
10. successful formative testing with at least five qualified users.

## 21. Falsification

The map-first shell MUST be reconsidered when controlled testing demonstrates that a list-first, search-first or another model materially improves the priority workflows without weakening discovery, context or evidence traceability.
