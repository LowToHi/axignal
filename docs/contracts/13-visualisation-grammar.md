# 13 — Visualisation Grammar Contract

Version: `0.2.0-candidate`
Status: `NORMATIVE CANDIDATE / USER VALIDATION REQUIRED`

## 1. Purpose

This contract defines how ASIGNAL represents evidence, uncertainty, contradiction, geography, relations and time. It prevents each universe or frontend component from inventing incompatible visual semantics.

## 2. General rule

A visual mark MUST communicate a declared variable. Decorative intensity MUST NOT be confused with analytical importance.

Every analytical visual MUST expose:

- metric or relation;
- unit where applicable;
- aggregation level;
- time or as-of state;
- source coverage;
- freshness;
- uncertainty or incomplete coverage;
- method version where derived.

## 3. Colour roles

Colour MUST NOT be the only carrier of meaning.

Canonical semantic roles:

- primary selection;
- supporting evidence;
- contradicting evidence;
- unknown or incomplete;
- expired or unavailable;
- inferred or predicted;
- neutral context.

The production design system MUST assign theme-aware tokens. This contract does not freeze exact hex values.

Red and green MUST NOT be used as the sole universal negative/positive pair because:

- accessibility is reduced;
- financial gain/loss semantics may conflict with epistemic support/contradiction;
- cultural and product contexts differ.

Use combinations of colour, icon, line style, pattern, label and position.

## 4. Heat layers

A heat layer MUST represent one primary continuous or ordinal metric.

Required metadata:

- metric name;
- definition;
- value range;
- unit;
- time window;
- aggregation;
- normalisation;
- missing-data treatment;
- coverage.

Rules:

- no more than one primary heat palette;
- quantile, linear, logarithmic or categorical scale MUST be stated;
- missing coverage MUST use hatching, mask or explicit boundary, not the lowest heat colour;
- legend remains visible while the layer is active;
- zoom-level aggregation changes MUST be declared;
- extreme values MUST not compress all other differences without an alternate scale or clipping disclosure.

## 5. Opportunity markers

Opportunity markers MUST encode only stable, explainable dimensions.

Recommended candidate encodings:

- size: bounded opportunity scope, evidence volume or another declared quantity;
- shape: universe or object type;
- outline: selected, watched or contested state;
- internal pattern: insufficient or partial coverage;
- small directional mark: material recent change.

Marker animation MUST be limited to a recent material state transition and stop automatically.

## 6. Claim representation

Claim chips, rows and nodes MUST expose:

- claim type;
- epistemic status;
- temporal validity;
- evidence-strength summary;
- contradiction state;
- source count or independence where space permits.

Canonical type labels MUST remain textual. Icons MAY supplement but not replace them.

Observed, calculated, inferred and predicted claims MUST have visually distinct treatment.

## 7. Confidence representation

ASIGNAL MUST NOT present confidence as one opaque percentage.

Where space permits, show dimensions separately:

- evidence strength;
- source authority;
- source independence;
- freshness;
- reproducibility;
- scope completeness;
- contradiction pressure;
- forecast uncertainty.

Compact summaries MAY use a small multi-segment strip, but detail MUST remain available.

Avoid gauges that imply a physical measurement precision unsupported by the method.

## 8. Contradiction representation

Contradiction is first-class and MUST not be hidden behind an expandable warning.

Visual treatments MAY include:

- opposing lane;
- distinct edge style;
- paired claim comparison;
- contradiction-pressure strip;
- invalidation marker on timeline.

The interface MUST distinguish direct contradiction from scope, time, methodology and value disagreement.

## 9. Graph grammar

Node appearance MUST primarily encode node type.

Edge appearance MUST encode relation type and epistemic basis.

Required graph behaviours:

- direct labels or an always-visible relation legend;
- bounded expansion;
- selected path emphasis;
- unrelated context de-emphasis without disappearance;
- edge direction where semantically meaningful;
- time validity filter;
- aggregate nodes when density limits are reached;
- accessible relationship list.

Causal hypotheses MUST NOT use the same edge treatment as observed relations.

Graph force or layout motion MUST settle quickly and preserve pinned positions.

## 10. Geographic flows

Flow lines MAY represent:

- trade or capital movement;
- regulatory or demand transmission;
- related opportunity propagation;
- supply-chain dependence.

Line width, opacity, direction and pattern MUST have explicit meanings.

A flow MUST NOT imply actual measured movement when it represents a hypothetical transmission path.

## 11. Timeline grammar

The time machine MUST distinguish:

- observation events;
- claim admission;
- corroboration;
- contradiction;
- scenario publication;
- invalidation;
- correction or retraction;
- outcome.

Event types MUST use redundant shape and label encoding.

The timeline MUST display:

- current as-of state;
- selected historical state;
- comparison state when active;
- source coverage interval;
- unavailable historical ranges.

Playback MUST advance by material state changes, not arbitrary animation frames, unless the underlying metric is a genuine continuous timeseries.

## 12. Scenario representation

Scenarios MUST be presented as alternatives, not a single deterministic forecast.

Required fields:

- scenario label;
- horizon;
- probability band or calibrated score;
- assumptions;
- supporting and contradicting claims;
- uncertainty;
- invalidation conditions;
- model version.

Probability values MUST not use unnecessary decimal precision.

Scenario colour MUST remain stable across history and comparisons.

## 13. Coverage and uncertainty

Canonical missingness states:

- not covered;
- source delayed;
- source suspended;
- insufficient evidence;
- model unavailable;
- entitlement restricted;
- intentionally filtered.

These states MUST not share one generic empty style.

The candidate **uncertainty veil** MAY use:

- hatching;
- desaturation;
- boundary pattern;
- reduced detail;
- explicit text.

It MUST not obscure selected objects or essential labels.

## 14. Tables and lists

Tables remain necessary for precision, accessibility and comparison.

They MUST:

- remain synchronised with map and graph selection;
- expose units and as-of dates;
- preserve sort explanation;
- distinguish unavailable from zero;
- allow keyboard navigation;
- avoid hidden horizontal meaning where possible;
- support stable shareable filters.

Tables are an alternate view, not an inferior fallback.

## 15. Change since last visit

A change marker MUST explain:

- previous state;
- current state;
- trigger time;
- material claim or metric change;
- whether the change is positive, negative, contradictory or only fresher.

Avoid generic “trending” badges without a declared comparison.

## 16. Microinteraction rules

Allowed:

- highlighting connected objects on hover or focus;
- previewing a claim before opening it;
- snapping timeline to material events;
- gentle selection transfer between map and rail;
- showing exact values in tooltips.

Prohibited:

- confetti;
- streaks;
- artificial scarcity countdowns;
- pulsing all high-ranked opportunities;
- sounds by default;
- score animations designed to trigger urgency;
- game-like rewards for inspecting financial information.

## 17. Label hierarchy

Labels MUST prioritise:

1. selected object;
2. material opportunities;
3. geography or market context;
4. supporting reference objects;
5. decorative basemap detail.

Collision handling MUST prefer suppression or aggregation over unreadable overlap.

## 18. Performance grammar

When representative data exceeds render limits, the UI MUST:

- aggregate;
- cluster;
- sample with disclosure;
- reduce detail by zoom;
- use server-generated tiles;
- cancel stale requests.

It MUST NOT freeze, silently drop high-impact objects or display a misleading partial layer.

## 19. Export grammar

Screenshots and reports MUST preserve:

- ASIGNAL identity;
- as-of time;
- metric and legend;
- source attribution;
- coverage statement;
- selected filters;
- method or claim IDs where relevant;
- export restrictions.

## 20. Prototype validation

The grammar is accepted only when qualified users can correctly answer:

- what the heat represents;
- which data is missing;
- whether an edge is observed or inferred;
- which claims support and contradict the thesis;
- what time the view represents;
- whether a scenario is a prediction or an observation;
- why an opportunity changed state.
