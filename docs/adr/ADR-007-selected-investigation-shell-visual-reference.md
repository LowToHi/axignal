# ADR-007 — Selected AXIGNAL Investigation Shell visual reference

Status: `ACCEPTED FOR PROTOTYPE FIDELITY / PRODUCTION TOKENS NOT FROZEN`
Date: `2026-07-27`
Goal ID: `AXIGNAL-GOAL-001`

## Context

Multiple visual directions were explored for the AXIGNAL Investigation Shell. The selected direction combines:

- the cinematic dark Signal Teal product shell;
- a faithful light counterpart derived from the Mineral Intelligence direction;
- a persistent conversational Navigator;
- an always-visible `AUTO / GLOBE / GRAPH / DUAL` lens switch;
- a dominant Globe or Graph canvas;
- opportunity ranking;
- Claim and Evidence Rail;
- Timeline;
- professional information density;
- restrained institutional motion.

The selected composition is materially stronger than treating AXIGNAL as a generic dashboard or as a chatbot with a decorative map.

## Decision

The selected Investigation Shell visual reference is normative for prototype implementation fidelity.

The prototype and subsequent product implementation MUST preserve the following composition unless a superseding ADR demonstrates a better validated solution:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ AXIGNAL | Investigation context | AUTO GLOBE GRAPH DUAL | Search | Account │
├────┬───────────────────┬───────────────────────────────┬─────────────────────┤
│Nav │ Navigator / chat  │ Primary Globe or Graph canvas │ Opportunities       │
│    │                   │                               ├─────────────────────┤
│    │ command history   │ contextual overlays           │ Claim/Evidence Rail │
│    │ interpretation    │                               │                     │
│    │ questions         │                               │                     │
│    │ input composer    │                               │                     │
├────┴───────────────────┼───────────────────────────────┼─────────────────────┤
│                       │ Timeline / as-of controls      │                     │
├───────────────────────┴───────────────────────────────┴─────────────────────┤
│ Optional metrics, Trails, Knowledge Tides or contextual secondary surfaces │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Required product behaviours

### Navigator

Navigator MUST be a real persistent chat and command surface, not merely an intent-summary card.

It MUST support:

- user messages;
- AXIGNAL navigation responses;
- visible command interpretation;
- follow-up questions;
- claim-grounded explanations;
- correction and undo;
- direct commands such as `change to graph` or `show contradictions`;
- persistent input composer.

### Lens switching

`AUTO / GLOBE / GRAPH / DUAL` MUST remain visible in the primary context bar.

The switch MUST preserve:

- selected geography or entity;
- opportunity;
- claims and evidence;
- filters;
- as-of time;
- comparison state;
- Navigator history;
- Investigation Trail.

### Primary canvas

The Globe or Graph MUST remain the visual centre of gravity. The interface MUST NOT reduce it to a small decorative card.

### Opportunity and evidence surfaces

Opportunity ranking and Claim/Evidence Rail MUST remain simultaneously discoverable without hiding contradiction or unknown coverage.

### Timeline

Timeline MUST be persistent or immediately available in the primary workspace and MUST share the same InvestigationContext.

## Dark theme reference

The candidate default product theme is the selected Signal Teal dark direction:

- deep neutral canvas;
- restrained teal signature accent;
- strong but calm Globe illumination;
- neutral professional surfaces;
- semantic support, contradiction, inference and critical colours governed by Contract 20;
- minimal glass, glow and decorative effects;
- high legibility and sustained-use density.

## Light theme reference

The candidate light theme is a first-class counterpart derived from Mineral Intelligence:

- warm or neutral light canvas;
- slate text and structure;
- restrained teal interaction and brand signal;
- preserved semantic meanings;
- no naive inversion of dark tokens;
- suitable for reading, reports and long daytime sessions.

Dark and light themes MUST implement the same product hierarchy, capabilities and epistemic grammar.

## Fidelity rule

Implementation MUST reproduce the selected reference faithfully in:

- region proportions;
- hierarchy;
- component density;
- Navigator prominence;
- Globe/Graph prominence;
- persistent evidence and time context;
- restrained visual language;
- dark/light parity.

A development agent MUST NOT replace the selected shell with:

- a generic shadcn dashboard;
- a card grid;
- a full-screen chatbot;
- a terminal imitation;
- a table-first application;
- a decorative globe with unrelated panels.

## What remains unfrozen

This ADR does not freeze:

- exact hex values;
- final typeface;
- exact panel dimensions;
- exact radii or shadows;
- exact motion duration and interpolation;
- final responsive breakpoints;
- final density defaults;
- final chart palettes.

Those remain governed by Contract 20 and validation evidence.

## Landing relationship

The public marketing site MUST share this visual identity and use faithful product demonstrations. It MAY use more editorial spacing and narrative motion, but MUST NOT invent a different product or show impossible UI states.

Contracts 21–24 govern the conversion, pricing, acquisition and trust system.

## Consequences

### Positive

- implementation now has a clear fidelity target;
- Navigator, Globe/Graph, evidence and Timeline cannot be accidentally deprioritised;
- dark and light themes form one product system;
- the landing can demonstrate the real product faithfully;
- visual iteration remains possible without losing the approved composition.

### Negative

- implementation requires custom composition beyond default component-library layouts;
- faithful Globe and Graph performance is demanding;
- responsive adaptation requires dedicated design rather than simple stacking;
- reference screenshots must eventually be stored as versioned design evidence.

## Evidence requirement

Before production freeze, the repository MUST include versioned visual reference assets or reproducible captures for:

- selected dark shell;
- selected light shell;
- Globe state;
- Graph state;
- Dual state;
- Navigator conversation;
- Claim/Evidence Rail;
- Timeline;
- responsive and reduced-motion states.

## Supersession rule

A later design may supersede this ADR only when comparative evidence demonstrates a material improvement in:

- workflow comprehension;
- professional trust;
- accessibility;
- sustained readability;
- multilingual resilience;
- performance;
- conversion without product misrepresentation.

Aesthetic novelty alone is insufficient.