# Global Discovery Flow

Version: `0.1.0`
Status: `DESIGN CANDIDATE`

## 1. Objective

Define the complete desktop interaction from global change discovery to source evidence without losing geography, time, filters or investigation history.

Canonical flow:

```text
Globe
→ opportunity
→ claims
→ evidence
```

## 2. Shell anatomy

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ AXIGNAL | Context stack | Command/Search | Explain view | Save trail | User │
├────────────┬──────────────────────────────────────────────┬─────────────────┤
│ Universe & │                                              │ Evidence rail   │
│ lens rail  │               Primary canvas                 │                 │
│            │               Globe / Atlas                  │ Context         │
│            │                                              │ Opportunity     │
│            │                                              │ Claims          │
│            │                                              │ Evidence        │
├────────────┴──────────────────────────────────────────────┴─────────────────┤
│ Time machine: as-of | material changes | scrubber | playback | comparison  │
└─────────────────────────────────────────────────────────────────────────────┘
```

The shell is persistent. Pages may have shareable URLs, but navigation MUST feel like moving through one investigation rather than opening unrelated dashboards.

## 3. State model

The client and API MUST share an explicit `InvestigationContext`:

```text
context_id
selected_subject_id
selected_subject_type
geography_scope
universe_scope
sector_scope
active_lens
primary_metric
overlay_metric
as_of
comparison_as_of
claim_status_filter
source_filter
confidence_filter
selected_path
history_stack
forward_stack
```

Any surface transition MUST preserve compatible fields and explicitly clear incompatible fields.

## 4. Entry state — Globe

### Visible by default

- global or selected regional map;
- one primary heat layer;
- compact universe rail;
- metric legend;
- coverage and freshness strip;
- persistent time machine;
- “changes since last visit” markers;
- evidence rail showing global summary, not cards for every feature.

### Default primary layer

The first commercial universe MUST define the default metric. The generic contract does not prescribe “opportunity intensity” if that metric is not validated.

The default layer MUST answer one concrete question, for example:

> Where has the volume of newly corroborated opportunity claims increased during the selected window?

### User action

The user selects a cluster, region or market object.

### System response

- camera moves only as much as needed;
- selected object receives a stable outline or marker;
- evidence rail shows the object's climate summary;
- URL and context stack update;
- layer, time and filters remain unchanged;
- related opportunity markers become inspectable.

## 5. Semantic zoom

Zoom MUST change the meaning and aggregation of visible objects.

Example hierarchy:

```text
Global
→ macro regions
→ countries / economic regions
→ sectors / markets
→ opportunity clusters
→ individual opportunities
→ entities / locations where appropriate
```

Rules:

- aggregation level is always visible;
- counts and scores MUST NOT be compared across different aggregation levels without an explicit normalisation;
- zooming does not automatically open detail;
- the user may lock aggregation to compare regions at one level;
- non-geographic opportunities remain accessible through thematic clusters and search.

## 6. Opportunity selection

### Trigger

The user selects an opportunity marker, list row or graph node.

### Primary canvas

The map remains visible and preserves geographic context.

### Evidence rail

The rail transitions to opportunity state and shows:

1. title and maturity;
2. concise thesis;
3. material change since prior state;
4. dimensional climate strip;
5. supporting / contradicting / unknown counts;
6. invalidation conditions;
7. principal claims;
8. source and coverage footer.

### Actions

- inspect claims;
- switch lens;
- save trail;
- add to watchlist;
- compare time;
- share research link;
- explain current view.

No investment or transaction action is present.

## 7. Lens switch

Canonical lenses:

- `OPPORTUNITY`
- `EVIDENCE`
- `CONTRADICTION`
- `TRANSMISSION`
- `HISTORY`

Only one lens is primary at a time.

### Opportunity lens

Map stays primary. Shows the selected opportunity in geographic and market context.

### Evidence lens

Central canvas may show evidence distribution or a bounded evidence graph. Evidence rail prioritises claim groups and source independence.

### Contradiction lens

Contradicting claims and invalidation conditions become visually primary. Supporting claims remain available but visually secondary.

### Transmission lens

Central canvas switches to a bounded relation graph. Geographic anchors remain visible through mini-map or node geography. Expansion is user-controlled.

### History lens

Time machine expands. Central canvas shows state change, claims available at each date and forecast/outcome comparisons.

Switching lens MUST NOT change the selected subject, time or investigation trail.

## 8. Claim inspection

### Trigger

The user selects a claim in the evidence rail or graph.

### Behaviour

- claim detail replaces the lower portion of the evidence rail or opens a nested rail state;
- the central canvas highlights affected geography, entities and graph edges;
- context stack adds the claim;
- back returns to the exact opportunity scroll and lens state.

### Required visible fields

- assertion;
- claim type;
- epistemic state;
- subject, predicate and value;
- observation, event and validity times;
- evidence strength dimensions;
- source lineage and independence;
- supporting and contradicting relations;
- method version;
- correction and expiry history;
- rights and export limitations.

## 9. Evidence inspection

### Trigger

The user selects an evidence object.

### Behaviour

Evidence detail MUST remain inside the AXIGNAL context while providing a clear path to the original source.

Visible content:

- source name and authority class;
- publication and retrieval times;
- relevant extract or structured value;
- content hash or immutable reference;
- extraction method and confidence;
- attribution;
- rights restrictions;
- claims derived from the evidence;
- open-original-source action.

The original source MAY open in a new tab so that the AXIGNAL investigation state remains intact.

## 10. Context stack

Example:

```text
Global
› Europe
› Energy transition
› Grid connection constraints
› Claim clm_...
› Evidence evd_...
```

Rules:

- every level is selectable;
- selecting a prior level restores its exact view state;
- stack items display type as well as label when ambiguity exists;
- the stack can collapse visually but not semantically;
- browser back and forward mirror the context history;
- opening a new investigation creates a branch rather than destroying the old trail.

## 11. Time machine

The bottom time control is always visible in compact form.

Modes:

- `CURRENT`
- `AS_OF`
- `COMPARE`
- `PLAYBACK`

### Current

Displays the latest admissible state and exact source-relative freshness.

### As of

Reconstructs only claims and scenarios available by the selected time.

### Compare

Shows material state differences between two times.

### Playback

Animates only material state changes. The user controls speed and may pause at change markers.

Rules:

- movement through time updates map, graph and rail together;
- future evidence never appears in historical state;
- current interpretation may be overlaid only when explicitly enabled;
- animation must respect reduced-motion settings.

## 12. Search and command palette

The command input serves both discovery and acceleration.

Supported intents:

- find an entity, market, geography, opportunity or claim;
- change lens or layer;
- set time;
- open a saved trail;
- run a bounded query;
- invoke “Explain current view”.

Search results MUST preserve current context unless the user explicitly starts a new investigation.

Keyboard contract:

- `/` focus command palette;
- `Esc` close transient surface or return one nested rail level;
- `[` and `]` move backward/forward in investigation history where not captured by browser;
- `G` Globe lens;
- `A` Atlas / Transmission lens;
- `H` History lens;
- `E` Evidence lens;
- `C` Contradiction lens;
- `S` save current trail.

Shortcuts MUST be discoverable and remappable where feasible.

## 13. Explain current view

The AI explanation receives only the authorised `InvestigationContext` and canonical resources currently in scope.

Output sections:

- what is visible;
- what materially changed;
- strongest supporting claims;
- strongest contradictions;
- unknowns;
- source coverage;
- optional follow-up questions.

Every substantive statement MUST cite claim IDs. Generated synthesis is labelled as generated and cannot alter canonical state.

## 14. Saved investigation trail

A trail stores:

- context state;
- selected path;
- time and comparison;
- filters;
- pinned claims and evidence;
- user annotations;
- generated explanations with cited resource versions;
- creation and last-review times.

A trail is not merely a bookmark to one URL. It is a reproducible research state.

## 15. Empty and failure states

### No data

State whether:

- no admitted claims exist;
- the source does not cover the scope;
- the user's plan lacks entitlement;
- filters removed all results;
- the source is delayed or suspended.

### Partial coverage

Use visible hatching, boundary treatment or uncertainty veil and a textual explanation.

### Source degradation

Show affected claims and when the state was last reliable.

### Graph density limit

Replace additional nodes with a labelled aggregate. Never silently omit relationships.

### Historical reconstruction unavailable

State the earliest valid date and why earlier state cannot be reconstructed.

## 16. Mobile adaptation

Mobile supports review rather than full investigation construction.

- map as compact context surface;
- bottom sheet replaces evidence rail;
- claims and evidence remain fully readable;
- watchlists, alerts and saved trails are primary;
- graph is reduced to bounded path or textual relationship list;
- complex comparison may hand off to desktop.

## 17. Accessibility

- evidence rail is represented as a logical document outline;
- map state has a synchronised region/opportunity list;
- graph state has a relationship list;
- focus follows explicit user actions, not animation;
- timeline can be operated through buttons and date inputs;
- every visual encoding includes text or shape redundancy;
- reduced-motion mode uses discrete transitions.

## 18. Prototype validation scenarios

1. Find a material opportunity without search.
2. Explain why it is visible on the map.
3. Identify supporting and contradicting claims.
4. Reach original evidence.
5. Return to the exact map state.
6. Switch to Transmission lens and inspect one path.
7. Move to a historical date without future-evidence leakage.
8. Save and reopen the investigation trail.

## 19. Gate to freeze

This flow becomes normative only when:

- at least five qualified users complete the critical tasks;
- median time to first evidence is acceptable against a list-first control;
- context-loss incidents are rare and understood;
- users correctly distinguish claim types;
- users understand heatmap metric and coverage;
- map-first discovery outperforms or complements search-first behaviour;
- accessibility alternatives are validated;
- technical performance is feasible with contract fixtures.
