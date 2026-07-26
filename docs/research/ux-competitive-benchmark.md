# AXIGNAL UX Competitive Benchmark

Version: `0.1.0`
Status: `RESEARCH / NON-NORMATIVE`
Date: `2026-07-26`

## 1. Research scope

Product: **AXIGNAL**, a premium Global Opportunity Intelligence platform.

Primary audience:

- active multi-asset wealth operators;
- entrepreneurs with investible liquidity;
- independent professional investors;
- small family offices;
- advisers, holdings and research boutiques.

Hero workflow under investigation:

```text
Globe
→ opportunity
→ claims
→ evidence
```

Time horizon: current product patterns and public documentation available in July 2026.

This is a fast public-source benchmark. It is not a substitute for observed sessions with qualified AXIGNAL users.

## 2. Executive read

The strongest comparable products each solve only part of AXIGNAL's desired experience.

- Bloomberg proves that breadth, speed, persistent workspaces and shortcuts can sustain mission-critical use, but its density and function memorisation create a steep learning burden.
- AlphaSense proves that natural-language research, citations, monitoring and project workspaces reduce fragmentation, but its experience remains search- and document-centric rather than spatial.
- Koyfin proves the value of cross-asset dashboards, watchlists, graphing and command navigation, but user-created dashboards can shift too much interface design work onto the user.
- TradingView proves that heatmaps can compress a market into an immediately readable overview when size, colour, grouping and metric are explicit.
- Windy provides the clearest interaction analogue: a map as the primary surface, a persistent time control, selectable layers and progressive inspection from global conditions to a precise point.
- Google Earth proves that spatial immersion, saved places and historical replay can make exploration intrinsically satisfying.
- Palantir provides the closest architectural analogue: maps, graphs, objects and workflows operating over one ontology rather than disconnected screens.

The best AXIGNAL model is therefore **not** a Bloomberg clone, configurable dashboard builder or chat-first research assistant. It is a **map-first investigation shell with a persistent evidence rail, a shared context stack and graph/history as reversible lenses over the same canonical object state**.

## 3. Product benchmark

### 3.1 Bloomberg Terminal

#### Observed evidence

Bloomberg positions Launchpad as a configurable workspace combining multi-asset monitors, alerting, charts and news. Its Terminal increasingly adds ASKB as a conversational interface that complements existing workflows.

Official source:

- https://professional.bloomberg.com/products/bloomberg-terminal/

Public user and industry commentary repeatedly describes two simultaneous truths:

- the platform is comprehensive, reliable and deeply embedded;
- the interface can be overwhelming, difficult to navigate and dependent on learned function paths.

Supporting public sources:

- https://www.g2.com/products/bloomberg-terminal/reviews
- https://www.wired.com/story/the-bloomberg-terminal-is-getting-an-ai-makeover-like-it-or-not/

#### Product lesson

Adopt:

- command palette and keyboard acceleration;
- persistent workspaces;
- linked components that react to one selected object;
- professional information density;
- strong defaults for recurring monitoring.

Reject:

- memorised function codes as the primary navigation model;
- independently configured windows with inconsistent state;
- density without an explicit investigation path;
- AI that abstracts users away from sources.

### 3.2 AlphaSense

#### Observed evidence

AlphaSense combines generative search, deep research, monitoring, workspaces, financial data and scheduled workflow agents. Its current Generative Search supports source and entity selection, different output modes, citations, follow-up questions and workspace persistence.

Official sources:

- https://www.alpha-sense.com/platform/
- https://help.alpha-sense.com/hc/en-us/articles/41665816407699-Accessing-Configuring-Generative-Search
- https://help.alpha-sense.com/hc/en-us/articles/41666587181203-Interacting-with-Generative-Search
- https://help.alpha-sense.com/hc/en-us/articles/51087728136979-Getting-Started-with-Workspaces

#### Product lesson

Adopt:

- research projects that preserve context;
- monitoring as a push workflow;
- citations adjacent to generated synthesis;
- explicit query scope;
- outputs that can become reports or structured grids.

Reject:

- chat as the only entry point;
- a linear answer stream as the representation of a complex opportunity;
- generated narrative that hides contradictory evidence;
- separate workspace state that does not remain synchronised with map and graph state.

### 3.3 Koyfin

#### Observed evidence

Koyfin provides configurable dashboards, watchlists, cross-asset views, advanced graphs, screeners and a command bar activated through `/`. Dashboard widgets can be resized and arranged by users.

Official sources:

- https://www.koyfin.com/features/custom-dashboards/
- https://www.koyfin.com/help/topic/functionality/
- https://www.koyfin.com/help/getting-started-with-koyfin/

#### Product lesson

Adopt:

- cross-asset continuity;
- reusable watchlist views;
- rapid command navigation;
- comparison and graph templates;
- user-saved research configurations.

Reject:

- blank-canvas dashboard configuration during onboarding;
- requiring users to build the product's information hierarchy themselves;
- a proliferation of widgets without a canonical investigation flow.

AXIGNAL SHOULD provide curated role- and universe-specific defaults before allowing advanced customisation.

### 3.4 TradingView heatmaps

#### Observed evidence

TradingView heatmaps explicitly encode two separate values: cell size represents relative importance and colour represents the selected analytical condition. Users can switch markets, groupings, labels and display values and move from global patterns to individual assets.

Official sources:

- https://www.tradingview.com/support/solutions/43000766446-tradingview-heatmaps-from-global-trends-to-details/
- https://www.tradingview.com/support/solutions/43000707156-how-to-set-up-the-display-of-the-heatmap/

#### Product lesson

Adopt:

- explicit dual encodings;
- visible legends;
- grouping by sector, geography or universe;
- overview-to-detail interaction;
- fast fullscreen exploration.

Reject:

- colour-only meaning;
- undefined heat intensity;
- universal red/green semantics;
- comparing incomparable opportunities through one aggregate colour.

### 3.5 Windy

#### Observed evidence

Windy uses the map as the product's primary surface. Users select layers, inspect points, move through time, compare models and preserve the spatial context while changing what is visualised.

Official and product sources:

- https://www.windy.com/
- https://www.windy.com/articles/38548
- https://windy.app/features

#### Product lesson

Adopt:

- map-first entry;
- persistent timeline;
- one active primary layer with optional overlays;
- immediate legend and model metadata;
- progressive global-to-local inspection;
- animated change only when it communicates direction or time.

Reject:

- unrestricted simultaneous layers;
- important controls hidden behind multiple menus;
- animation used as decoration;
- map colours without a readable non-map alternative.

### 3.6 Google Earth

#### Observed evidence

Google Earth supports global exploration, saved projects and places, rich contextual details and historical imagery through a timeline.

Official sources:

- https://earth.google.com/
- https://support.google.com/earth/answer/148094
- https://developers.google.com/maps/documentation/earth/add-features-to-projects

#### Product lesson

Adopt:

- a sense of continuous space;
- saved viewpoints and investigation trails;
- historical replay without leaving the map;
- contextual details attached to geographic objects;
- shareable narratives assembled from selected places.

Reject:

- decorative 3D that weakens metric reading;
- camera movement that loses analytical orientation;
- geographic spectacle without a clear data question.

### 3.7 Palantir Foundry

#### Observed evidence

Palantir describes its Ontology as the shared semantic system connecting objects, logic, actions and workflows. Foundry applications include map-based and graph-like exploration over ontology objects rather than isolated datasets.

Official sources:

- https://www.palantir.com/docs/foundry/architecture-center/ontology-system
- https://www.palantir.com/docs/foundry/platform-overview/overview/
- https://palantirfoundation.org/docs/foundry/ontology/applications

#### Product lesson

Adopt:

- one selected object shared across map, graph and detail;
- explicit object and relation types;
- provenance-aware user actions;
- context-preserving transitions;
- feedback loops attached to canonical objects.

Reject:

- operational actions that exceed AXIGNAL's information-only boundary;
- enterprise-builder complexity exposed to ordinary users;
- custom ontology configuration as a prerequisite for first value.

## 4. Cross-product UX problems

### Problem 1 — Breadth becomes navigation debt

Users value comprehensive coverage, but more functions and data increase the chance that relevant information is missed or takes too long to find.

Severity: `CRITICAL`
Frequency signal: `HIGH`
Confidence: `HIGH`

AXIGNAL response:

- one canonical investigation flow;
- semantic zoom;
- a persistent context stack;
- an explainable command palette;
- curated starting lenses;
- no blank dashboard during first use.

### Problem 2 — Fragmented research loses context

Users frequently move between charts, filings, news, searches and private notes. Each transition risks losing filters, time, entity scope and the reason an item mattered.

Severity: `CRITICAL`
Frequency signal: `HIGH`
Confidence: `HIGH`

AXIGNAL response:

- all surfaces bind to one `InvestigationContext`;
- map, graph, opportunity, claim and evidence are views of the same state;
- every saved research trail preserves filters, time and selected objects;
- browser-style back/forward semantics are mandatory.

### Problem 3 — Chat compresses but can conceal

Natural language lowers the entry barrier and accelerates synthesis, but a generated answer can obscure contradictions, coverage gaps and the distinction between retrieved and inferred material.

Severity: `HIGH`
Frequency signal: `RISING`
Confidence: `HIGH`

AXIGNAL response:

- AI explains the current canonical view;
- AI never replaces the view;
- generated statements link to claim IDs;
- contradictions and unknowns remain structurally visible;
- the home screen is not an empty chat box.

### Problem 4 — Customisation becomes setup work

Professional users value custom dashboards, but unrestricted configuration shifts information architecture work onto the customer.

Severity: `MEDIUM-HIGH`
Frequency signal: `MEDIUM`
Confidence: `MEDIUM-HIGH`

AXIGNAL response:

- curated default workspace;
- progressive customisation after value is demonstrated;
- saved lenses, trails and watchlists instead of arbitrary widget canvases;
- advanced professional layouts may be introduced later.

### Problem 5 — Beautiful maps can become decorative

Maps create orientation and discovery, but they become misleading when metric, coverage, time window or aggregation level are unclear.

Severity: `HIGH`
Frequency signal: `MEDIUM`
Confidence: `HIGH`

AXIGNAL response:

- every layer declares metric, unit, time, source coverage and aggregation;
- only one primary heat layer is active;
- overlays use lines, symbols or patterns rather than competing heat palettes;
- textual and tabular equivalents are always available.

## 5. Evaluated interaction directions

### Direction A — Configurable terminal

Primary surface: multi-panel dashboard with charts, tables, map and news.

Strengths:

- high density;
- familiar to finance professionals;
- supports simultaneous monitoring.

Weaknesses:

- resembles existing terminals;
- high setup and learning cost;
- weakens AXIGNAL's discovery proposition;
- easily becomes card and widget accumulation.

Decision: `REJECT AS PRIMARY MODEL`

### Direction B — Conversational research workspace

Primary surface: natural-language question, cited response and saved research threads.

Strengths:

- low initial friction;
- easy synthesis;
- familiar 2026 interaction pattern.

Weaknesses:

- highly exposed to absorption by general AI platforms;
- linear representation of nonlinear evidence;
- contradictions and temporal state can disappear inside prose;
- weak spatial discovery.

Decision: `REJECT AS PRIMARY MODEL / RETAIN AS SECONDARY LENS`

### Direction C — Map-first investigation shell

Primary surface: global map with layer controls, persistent time axis, contextual evidence rail and reversible graph lens.

Strengths:

- embodies AXIGNAL's climate metaphor;
- differentiates from chat-first research tools;
- supports discovery before query;
- preserves space, time and evidence together;
- can reveal cross-market transmission paths.

Weaknesses:

- requires strict visual grammar;
- not all claims are geographic;
- dense graphs and layers can overwhelm;
- technically demanding.

Mitigations:

- non-geographic objects anchor to market, jurisdiction or related entity when appropriate;
- a list/table alternative accompanies every map;
- one primary lens and one overlay at a time;
- semantic zoom and bounded graph expansion.

Decision: `SELECT`

## 6. Recommended AXIGNAL interaction model

Canonical shell:

```text
┌───────────────────────────────────────────────────────────────────┐
│ Brand | Context breadcrumbs | Command/Search | Saved trail | User │
├──────────┬─────────────────────────────────────────┬──────────────┤
│ Universes│                                         │ Evidence rail │
│ & lenses │             Globe / Map                 │ Opportunity   │
│          │                                         │ Claims        │
│          │                                         │ Evidence      │
├──────────┴─────────────────────────────────────────┴──────────────┤
│ Persistent time machine | change markers | play/scrub | as-of     │
└───────────────────────────────────────────────────────────────────┘
```

The graph does not open as a disconnected application. It replaces or overlays the central map while retaining:

- selected opportunity;
- filters;
- time;
- geography;
- evidence rail;
- investigation trail.

## 7. Differentiating interaction primitives

- **Context stack:** preserves the investigation path and allows reversible movement.
- **Lens switch:** changes between Opportunity, Evidence, Contradiction, Transmission and History without changing the selected subject.
- **Evidence rail:** remains visible from opportunity to source.
- **Semantic zoom:** changes aggregation and object type rather than only enlarging geometry.
- **Claim pulse:** shows material claim-state change without casino-like urgency.
- **Uncertainty veil:** visually communicates incomplete coverage or model uncertainty without implying missing geography is neutral.
- **Investigation trail:** saves selected objects, time, filters and reasoning path as one reusable research object.
- **Explain current view:** AI describes only the visible canonical state and cites claim IDs.

## 8. Source map and limitations

Strong evidence:

- official product documentation for interaction features;
- current AlphaSense help documentation;
- current Bloomberg and Palantir product descriptions;
- explicit heatmap and map interaction documentation.

Weaker evidence:

- public review and Reddit commentary is anecdotal and self-selected;
- no authenticated product sessions were observed directly;
- no AXIGNAL target users have yet been tested;
- no latency or task-completion benchmark has yet been conducted.

## 9. Research decision

The benchmark supports adopting **Map-first Investigation Shell** as the prototype direction.

It does not yet justify freezing final UI composition, visual identity, exact controls or information density. Those require prototype testing with qualified users.
