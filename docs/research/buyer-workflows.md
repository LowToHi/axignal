# ASIGNAL Buyer Workflows

Version: `0.1.0`
Status: `RESEARCH / HYPOTHESIS`
Date: `2026-07-26`

## 1. Purpose

These workflows translate the buyer hypothesis into observable product tasks. They are not validated personas. Each must be tested with qualified users before the UI contract is frozen.

## 2. Primary user model

Canonical working persona:

> An active multi-asset wealth operator who repeatedly scans several platforms, moves between public and private opportunities and needs to understand what changed, why it matters and which evidence supports the interpretation.

This user typically:

- has limited attention relative to the volume of available information;
- already knows how to use charts, filters and research tools;
- values speed but rejects unexplained automation;
- moves between geography, sector, company, regulation and asset type;
- expects source-level verification before acting;
- revisits theses over weeks or months;
- may collaborate with advisers or a small internal team.

## 3. Job 1 — Discover material change without a preformed query

### Trigger

The user begins a research session and wants to know whether anything materially relevant has changed across watched markets or adjacent opportunities.

### Current fragmented behaviour

- open several market and news platforms;
- scan watchlists and newsletters;
- inspect maps or macro dashboards;
- compare with personal notes;
- decide manually whether a signal deserves deeper research.

### ASIGNAL target flow

```text
Open Globe
→ inspect “changes since last visit”
→ select a geographic or thematic cluster
→ review opportunity summaries
→ open one opportunity
→ inspect supporting and contradicting claims
→ save or dismiss the investigation trail
```

### Success criteria

- first material opportunity reached in under 90 seconds;
- user can explain why the cluster is visible;
- user understands the heatmap metric and time window;
- no search term is required;
- irrelevant regions or universes can be suppressed without rebuilding the workspace.

## 4. Job 2 — Investigate why an opportunity is strengthening

### Trigger

A watched opportunity changes state or appears in a new geography.

### Target flow

```text
Open alert
→ preserve alert time and trigger
→ inspect current opportunity state
→ compare with previous state
→ switch to Evidence lens
→ inspect new claims and source independence
→ switch to Contradiction lens
→ inspect invalidation conditions
→ update watchlist threshold or save note
```

### Success criteria

- the exact change trigger remains visible;
- new evidence is distinguishable from old evidence;
- source duplication is not mistaken for corroboration;
- user can identify at least one condition that would weaken the thesis;
- the system does not force a decision or recommendation.

## 5. Job 3 — Trace cross-market transmission

### Trigger

The user believes an event in one domain may create opportunities elsewhere.

Example hypothesis:

```text
regulatory change
→ required industrial investment
→ supplier demand
→ property or infrastructure pressure
→ related public and private assets
```

### Target flow

```text
Select regulation or event
→ activate Transmission lens
→ expand bounded relation paths
→ filter by geography and horizon
→ inspect edge claims
→ compare two candidate transmission paths
→ save one path as an investigation trail
```

### Success criteria

- every edge has an explicit semantic type;
- causal hypotheses are visually distinct from observed relations;
- graph expansion is bounded and reversible;
- switching back to map preserves the selected path;
- the user can identify where evidence becomes inference.

## 6. Job 4 — Audit a claim before external action

### Trigger

The user intends to use an ASIGNAL finding in a meeting, investment memo, acquisition review or commercial decision.

### Target flow

```text
Open claim
→ inspect canonical assertion and scope
→ verify observation/event time
→ inspect evidence extract
→ open original source
→ inspect method and dependency history
→ review contradictions and corrections
→ export permitted citation or research note
```

### Success criteria

- source reached in two interactions or fewer from claim detail;
- rights and export restrictions are visible before export;
- assertion, calculation and forecast types cannot be confused;
- correction history is understandable;
- export preserves claim ID, as-of time and source attribution.

## 7. Job 5 — Reconstruct what was known at a past decision point

### Trigger

The user reviews why a prior thesis succeeded or failed.

### Target flow

```text
Open saved trail
→ set historical “as of” date
→ view claims and scenario available then
→ replay subsequent material events
→ compare historical forecast with outcome
→ identify invalidation signals and missed contradictions
```

### Success criteria

- no future evidence leaks into the historical view;
- current interpretation remains available as a comparison, not a replacement;
- user can see forecast calibration and outcome;
- the investigation produces a reusable learning record.

## 8. Job 6 — Monitor a portfolio of interests without receiving advice

### Trigger

The user wants a recurring summary of changes across selected markets, sectors, entities and opportunities.

### Target flow

```text
Open Watchlists
→ review grouped changes since last visit
→ sort by type of change rather than generic score
→ inspect weakened and invalidated items first or by preference
→ open one investigation
→ acknowledge, annotate or change alert conditions
```

### Success criteria

- personalisation reflects observation interests rather than suitability;
- positive and negative changes receive equal visibility;
- alert volume is controllable;
- every alert explains its trigger and data freshness;
- the user can dismiss noise without suppressing material contradictions.

## 9. Job 7 — Ask the system to explain the current view

### Trigger

The user sees a complex pattern but wants a concise synthesis.

### Target flow

```text
Select scope on map or graph
→ invoke “Explain current view”
→ receive bounded explanation
→ inspect cited claim chips
→ expand supporting, contradicting or unknown sections
→ refine scope without losing context
```

### Success criteria

- explanation is limited to authorised visible state;
- generated inferences are labelled;
- all material statements cite claim IDs;
- user can move from prose to graph or evidence;
- conversation does not become a separate hidden research state.

## 10. Required user-research participants

Minimum formative sample before contract freeze:

- 2 entrepreneurs with investible liquidity;
- 2 sophisticated independent multi-asset users;
- 2 advisers or research professionals;
- 1 small family-office or holding participant.

At least five sessions must use an interactive prototype. The broader seven-person target is preferred because workflows differ materially by role.

## 11. Research tasks

Each participant should attempt:

1. find a material change without search;
2. explain why an opportunity is visible;
3. identify one supporting and one contradicting claim;
4. inspect the original source;
5. move from map to graph and back without losing context;
6. reconstruct a historical view;
7. save an investigation trail;
8. explain the difference between observed, inferred and predicted content.

## 12. Measures

Quantitative:

- time to first relevant opportunity;
- task completion;
- navigation reversals and dead ends;
- source drill-down completion;
- claim-type comprehension;
- context-loss incidents;
- graph expansion errors;
- number of controls used;
- System Usability Scale or equivalent lightweight score.

Qualitative:

- perceived authority;
- perceived overload;
- trust in heatmap and states;
- whether exploration feels useful or decorative;
- whether AI explanation clarifies or conceals;
- willingness to return weekly;
- willingness to pay at proposed tiers.

## 13. Falsification criteria

The map-first model must be reconsidered if:

- most users begin with search and ignore spatial discovery;
- geography is irrelevant to the initial commercial universe;
- map interaction increases time to evidence materially;
- the graph is consistently treated as decorative;
- qualified users prefer a structured list as their persistent home surface;
- accessibility alternatives become the primary interface for reasons unrelated to accessibility;
- users cannot understand the layer metric after onboarding.
