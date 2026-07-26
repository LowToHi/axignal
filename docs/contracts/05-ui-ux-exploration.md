# 05 — UI and UX Exploration Contract

Version: `0.1.0`
Status: `NORMATIVE`

## 1. Experience thesis

ASIGNAL MUST make global economic intelligence explorable as a spatial and temporal world model.

The experience MUST avoid reducing the product to tables, static dashboards or an empty chatbot. Numerical detail remains essential, but navigation MUST support discovery through maps, graphs, time and semantic relationships.

The intended feeling is not casino-style gamification. It is **discovery-driven exploration**: the user should experience the satisfaction of revealing meaningful relationships while retaining analytical seriousness.

## 2. Core design principles

### 2.1 Explore before query

The home surface MUST immediately expose meaningful global state. A user SHOULD be able to discover change without knowing the right search term.

### 2.2 Progressive epistemic depth

Every visible opportunity MUST support drill-down:

```text
world or universe
→ geography or market
→ sector or entity
→ opportunity
→ scenario
→ claim
→ evidence
→ source and method
```

### 2.3 No decorative certainty

Visual polish MUST NOT conceal uncertainty. Confidence, contradiction, staleness and partial coverage MUST be visible.

### 2.4 Spatial, temporal and relational continuity

Moving between map, graph, timeline and detail MUST preserve current context and filters.

### 2.5 Dense but calm

The product targets sophisticated users. It MAY present high information density but MUST preserve hierarchy, legibility and predictable interaction.

## 3. Information architecture

Primary navigation:

- `Globe`
- `Explorer`
- `Atlas`
- `Climate`
- `Opportunities`
- `Claims`
- `Watchlists`
- `Research`
- `API & Exports`

Account and workspace controls MUST remain separate from exploration navigation.

## 4. ASIGNAL Globe

The Globe is the primary discovery surface.

Required capabilities:

- world map and globe projection;
- zoom from global to regional context;
- heatmaps;
- clusters and density layers;
- choropleths where country or region data supports them;
- flow and relationship overlays;
- time slider and historical replay;
- layer controls;
- universe and sector filters;
- explicit coverage boundaries;
- freshness legend;
- keyboard-accessible geographic summaries.

Supported semantic layers MAY include:

- opportunity intensity;
- claim velocity;
- evidence density;
- contradiction pressure;
- scenario change;
- regulation-created demand;
- procurement activity;
- capital or trade flows;
- property or real-asset conditions;
- macroeconomic regime state.

A heatmap MUST always state the metric, unit, time window and coverage.

## 5. ASIGNAL Atlas

The Atlas is the graph exploration surface.

Node categories:

- entities;
- markets;
- sectors;
- assets;
- geographies;
- regulations;
- technologies;
- opportunities;
- scenarios;
- claims;
- evidence and sources.

Required interactions:

- expand neighbours by relation type;
- pin nodes;
- inspect edge semantics;
- trace shortest or strongest paths;
- compare two nodes;
- isolate supporting or contradicting paths;
- filter by time and claim status;
- transition to geographic context;
- save graph views to a watchlist or research collection.

Graph layouts MUST remain interpretable. The UI MUST limit uncontrolled node explosions and provide summaries when a subgraph is too dense.

## 6. ASIGNAL Climate

Climate views MUST communicate the current state and change trajectory of a market, geography, sector, asset or opportunity.

Canonical dimensions:

- momentum;
- evidence strength;
- source independence;
- freshness;
- persistence;
- contradiction pressure;
- scenario stability;
- liquidity or accessibility where relevant;
- regulatory complexity;
- AI-absorption risk where relevant.

The UI MUST show dimensions separately. A composite ordering score MAY be displayed only as secondary navigation.

Example state vocabulary:

- `EMERGING`
- `STRENGTHENING`
- `MATURE`
- `STABLE`
- `CONTESTED`
- `WEAKENING`
- `DISLOCATED`
- `EXPIRED`
- `INSUFFICIENT_EVIDENCE`

## 7. Time Machine

Historical replay MUST preserve what the system knew at each point in time.

The user MUST be able to inspect:

- claims available on a historical date;
- claim state at that time;
- scenario issued at that time;
- subsequent corrections;
- eventual outcome where known;
- difference between historical and current interpretation.

The system MUST NOT reconstruct old views using future evidence without clearly labelling the reconstruction.

## 8. Opportunity detail

An opportunity detail surface MUST include:

1. concise thesis;
2. state and maturity;
3. temporal evolution;
4. supporting claim set;
5. contradicting claim set;
6. unknowns and missing evidence;
7. scenario set;
8. invalidation conditions;
9. geography and market context;
10. related opportunities and transmission paths;
11. sources and methodology;
12. freshness and coverage;
13. actions limited to observation, export, annotation and sharing.

It MUST NOT contain a default “Buy”, “Invest” or equivalent action.

## 9. Claim detail

A claim page MUST expose:

- canonical assertion;
- claim type and status;
- subject, predicate and value;
- scope;
- timestamps;
- source and evidence;
- extraction and method versions;
- supporting and contradicting claims;
- dependence graph;
- rights and export limitations;
- history of corrections, expiry or retraction;
- machine-readable representation.

## 10. Search and filters

Search MUST be hybrid:

- exact and lexical search;
- semantic search;
- entity search;
- geographic search;
- typed market and asset filters;
- time filters;
- claim-state filters;
- evidence-strength filters;
- source filters;
- rights and export filters.

The product MUST explain why a result matched when semantic retrieval materially affected ranking.

## 11. Personal Atlas and watchlists

User personalisation MUST represent observation interests, not suitability.

Users MAY save:

- markets;
- geographies;
- sectors;
- entities;
- assets;
- opportunities;
- claims;
- graph paths;
- filters;
- scenario conditions.

Watchlists SHOULD show changes since the last visit, including weakened or invalidated theses.

## 12. Alerts

Alerts MUST be event-based and explain the trigger.

Examples:

- evidence strength crossed a threshold;
- contradiction pressure increased;
- source freshness degraded;
- a scenario changed materially;
- an invalidation condition occurred;
- a watched geography gained a new opportunity cluster;
- a source was revoked or corrected.

Alerts MUST NOT use urgency language unsupported by the claim graph.

## 13. Conversational interface

A conversational layer MAY exist, but it MUST:

- query canonical resources;
- cite claims and evidence;
- distinguish retrieved facts from generated explanation;
- respect entitlements;
- refuse to manufacture unavailable certainty;
- expose query scope and relevant filters;
- avoid personalised investment recommendations in foundation scope.

The chatbot MUST NOT be the only route to core product functionality.

## 14. Visual language

The visual system SHOULD communicate:

- institutional credibility;
- precision;
- global scope;
- cartography;
- depth;
- evidence;
- calm motion;
- premium software quality.

Avoid:

- crypto neon clichés;
- stock-photo finance imagery;
- upward arrows as primary branding;
- red/green-only financial encodings;
- simulated trading interfaces;
- excessive glass effects;
- decorative 3D that harms comprehension.

## 15. Motion

Motion MAY reinforce spatial continuity, time change and graph expansion.

Motion MUST:

- be interruptible;
- respect reduced-motion settings;
- avoid blocking interaction;
- avoid implying certainty or urgency;
- preserve target positions during transitions.

## 16. Accessibility

All primary flows MUST satisfy WCAG 2.2 AA.

Requirements:

- keyboard navigation;
- visible focus;
- screen-reader alternatives for maps and graphs;
- tabular or textual summaries for spatial data;
- colour-independent encoding;
- contrast compliance;
- reduced-motion mode;
- scalable text;
- accessible tooltips and dialogs;
- understandable error and empty states.

## 17. Responsive behaviour

Desktop is the primary analytical surface, but mobile MUST support:

- watchlist review;
- alerts;
- opportunity and claim reading;
- saved research;
- limited map exploration;
- sharing.

Complex graph editing MAY be desktop-only if an accessible mobile summary is provided.

## 18. Performance

The UX MUST remain responsive with large datasets through:

- server aggregation;
- vector tiles;
- level-of-detail rendering;
- clustering;
- progressive loading;
- WebGL rendering;
- worker threads where appropriate;
- explicit sampling labels;
- cancellation of stale requests.

## 19. Product trust surfaces

Every material page MUST make it easy to find:

- methodology;
- data coverage;
- last update;
- source list;
- uncertainty;
- corrections;
- conflicts;
- export restrictions.

Trust information MUST not be hidden exclusively in legal footers.

## 20. Acceptance criteria

The UI/UX foundation is accepted when a prototype demonstrates:

1. global-to-claim navigation without context loss;
2. map, graph and timeline views driven by the same canonical fixtures;
3. supporting and contradicting claims displayed with equal structural status;
4. source and methodology drill-down;
5. historical replay using versioned data;
6. keyboard and reduced-motion operation;
7. textual alternatives for map and graph state;
8. no investment-action dark patterns;
9. user testing with at least five qualified target users;
10. evidence that users understand observed, inferred and predicted states.
