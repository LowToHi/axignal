# 00 — AXIGNAL Goal Lock

Version: `0.3.1`
Status: `NORMATIVE CANDIDATE`
Goal ID: `AXIGNAL-GOAL-001`

## 1. Locked goal

AXIGNAL MUST become a premium, global and multilingual **Opportunity Intelligence environment** in which professional users can discover, investigate, compare and monitor economic opportunities through a governed world model built from traceable claims, evidence, contradictions, time and outcomes.

The product MUST combine:

- natural-language navigation and explanation;
- a geographic Globe;
- a relational Graph;
- a persistent Timeline;
- claims and evidence;
- opportunity and scenario state;
- personal investigation memory;
- aggregate Knowledge Tides;
- a research candidate queue;
- auditable multilingual rendering.

## 2. Canonical user journey

```text
intent expressed in natural language or direct interaction
→ visible interpretation
→ InvestigationContext created or updated
→ AUTO chooses Globe or Graph, unless user overrides
→ opportunity discovered or research gap identified
→ supporting, contradicting and unknown claims inspected
→ evidence and source reached
→ time and transmission paths explored
→ investigation trail saved
→ optional private preference updated
→ privacy-protected aggregate intent signal updated
→ research candidate prioritised when justified
```

## 3. Product identity

- Public brand: **AXIGNAL**
- Domain: **axignal.com**
- Technical repository: `LowToHi/axignal`
- Category: **Global Opportunity Intelligence**
- Default language: English
- Supported launch languages:
  - English `en`
  - Spanish `es`
  - French `fr`
  - German `de`
  - Portuguese `pt-BR` initially, with terminology compatibility for `pt-PT`
  - Simplified Chinese `zh-Hans`

## 4. Product invariants

### 4.1 Claims, not generated prose, are authoritative

Generated explanations may navigate and explain canonical state. They MUST NOT silently create canonical facts, opportunities or scores.

### 4.2 Intention guides research, not truth

User interest can form an observed behavioural claim and a Knowledge Tide. It may prioritise investigation. It MUST NOT serve as direct evidence that an economic opportunity exists.

### 4.3 Globe and Graph are equal lenses

Globe and Graph MUST operate on the same `InvestigationContext`, claims, timeline, entitlements and evidence rail.

Neither may become a decorative or reduced-function view.

### 4.4 Explicit user choice prevails

Lens priority:

1. explicit user choice;
2. geographical intent → Globe;
3. relational, ownership, transmission or causal intent → Graph;
4. temporal intent → current lens plus Timeline;
5. evidence question → current lens plus claim/evidence rail;
6. hybrid query → AUTO may select Globe, Graph or Dual and MUST explain the choice.

### 4.5 Coverage absence is not negative evidence

Unavailable, unlicensed or missing data MUST be represented as unknown or uncovered, never as low opportunity.

### 4.6 Contradiction is first-class

Supporting evidence, contradictions, uncertainty, expiry and missing knowledge MUST remain visible.

### 4.7 Multilingual does not mean lossy translation

The system MUST preserve original source, language, canonical semantics, translation method and localised rendering separately.

### 4.8 Premium WOW through meaning

The interface MUST be cinematic in scale and institutional in detail. Motion, depth and visual transformation MUST communicate geography, relationships, time or epistemic state rather than decoration.

### 4.9 Observation, not personal investment advice

Foundation AXIGNAL MUST NOT execute transactions, hold assets, allocate portfolios or present opportunities as personally suitable investments.

### 4.10 Lawful data only

Public visibility does not imply permission to collect, persist, transform or redistribute.

## 5. Core product subsystems

```text
AXIGNAL
├── Navigator
│   ├── command interpretation
│   ├── claim and view explanation
│   └── multilingual conversation
├── Investigation Context
├── Lens Router
│   ├── AUTO
│   ├── GLOBE
│   ├── GRAPH
│   └── DUAL
├── Globe
├── Graph
├── Timeline
├── Claim and Evidence Rail
├── Opportunity and Scenario Engine
├── Investigation Trails
├── Personal Interest Memory
├── Knowledge Tides Engine
├── Research Candidate Queue
├── Claim Ledger
├── Source Registry
├── Multilingual Semantic Layer
└── Entitlements, Security and Audit
```

## 6. Anti-goals

An implementation MUST be rejected if it turns AXIGNAL into primarily:

- a chatbot that returns unstructured financial prose;
- a static dashboard collection;
- a map with decorative markers;
- a graph visualisation without operational workflows;
- a market-news aggregator;
- a trading or copy-trading interface;
- a single opaque opportunity score;
- a system where user popularity proves economic truth;
- a mass scraper without rights governance;
- a monolingual English product translated at the end;
- a platform whose core value can be replaced by a generic model prompt.

## 7. Goal-loss tests

Before any phase gate, the agent MUST answer:

1. Does this change strengthen the path from global discovery to evidence?
2. Does it preserve canonical claims and provenance?
3. Does it keep Globe, Graph, Timeline and Navigator contextually aligned?
4. Does it separate interest signals from economic evidence?
5. Does it work across the six launch languages by architecture?
6. Does it strengthen, rather than weaken, differentiation from general AI?
7. Does it preserve the observation-not-advice boundary?
8. Does it have a lawful data and privacy path?
9. Can it be disabled, rolled back or corrected?
10. Is there evidence that it advances the current authorised gate?

Any `NO` or `UNKNOWN` blocks acceptance unless the relevant contract explicitly permits the exception.

## 8. Naming guard

Canonical naming is exact:

- `AXIGNAL`
- `axignal.com`
- `LowToHi/axignal`
- `AXIGNAL-GOAL-001`

The legacy strings `ASIGNAL`, `asignal.com` and `ASIGNAL-GOAL-001` MUST fail documentation and repository validation.

## 9. Change rule

The Goal Lock may be changed only by:

1. explicit user decision;
2. an ADR describing the material change;
3. updates to affected contracts and roadmap;
4. migration analysis;
5. preservation of the previous Goal Lock version.

An agent MUST NOT reinterpret the Goal Lock from implementation convenience, provider limitations or current code structure.
