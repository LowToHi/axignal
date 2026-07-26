# 01 — ASIGNAL Phase Map

Version: `0.3.0`
Status: `NORMATIVE CANDIDATE`

## Phase sequence

```text
F0  Goal and contracts
F1  UX architecture and validation
F2  Reproducible repository spine
F3  Epistemic kernel
F4  Navigator and shared InvestigationContext
F5  Globe, Graph and Timeline parity
F6  Multilingual semantic system
F7  Intent Intelligence and Knowledge Tides
F8  First lawful opportunity universe
F9  Paid design-partner product
F10 Scenarios, calibration and outcomes
F11 Enterprise, API and private data
F12 General availability and universe expansion
```

A later phase MAY be explored, but it MUST NOT be represented as accepted or production-ready before its dependencies pass.

---

## F0 — Goal and contractual foundation

State: `IN_PROGRESS`

### Objective

Freeze the product purpose, epistemic rules, business hypotheses, data boundaries and agent governance without pretending that unvalidated assumptions are facts.

### Deliverables

- Goal Lock;
- product constitution;
- business and pricing hypotheses;
- claim and evidence system;
- source admission;
- architecture;
- security and regulatory boundary;
- API and quality gates;
- roadmap, tasks, contracts and skill registry.

### Contracts

`00–04`, `06–11`, `18` and roadmap documents.

### Gate F0

Pass when:

- every subsystem maps to contracts;
- every phase maps to tasks and skills;
- no material iteration remains only in chat history;
- Goal Lock tests are executable in PR review;
- the next phase can be implemented without inventing product scope.

---

## F1 — UX architecture and validation

State: `IN_PROGRESS`

### Objective

Determine and validate the best investigation experience before production UI implementation.

### Required capabilities

- conversational Navigator;
- visible command interpretation;
- `AUTO / GLOBE / GRAPH / DUAL` routing;
- Globe–Graph functional parity;
- persistent Timeline;
- persistent Claim and Evidence Rail;
- investigation trails;
- multilingual interaction architecture;
- privacy-visible intent memory;
- sober, professional and meaningful WOW design.

### Deliverables

- competitive benchmark;
- buyer workflows;
- three materially different interaction directions;
- prototype v0.2 or later;
- control variant for comparative testing;
- interaction contract;
- visualisation grammar;
- conversational navigation contract;
- multilingual UX contract;
- user-testing evidence.

### Skills

`goal-keeper`, `ux-researcher`, `interaction-architect`, `visualisation-designer`, `accessibility-auditor`, `multilingual-localiser`, `gate-evaluator`.

### Gate F1

Pass only when qualified users demonstrate:

- ≥85% opportunity-to-evidence completion;
- ≥90% correct command interpretation;
- ≥95% context retention across Globe and Graph;
- ≥80% understanding of heat metric and coverage;
- ≥75% unaided contradiction discovery;
- equivalent core-task success across launch languages within an approved tolerance;
- no repeated interpretation of evidence strength as expected return;
- preference for the selected architecture over the control.

---

## F2 — Reproducible repository spine

State: `LOCKED`
Dependency: `F0` and sufficient `F1` interaction contracts.

### Objective

Create a reproducible monorepo, local environment, CI and observability baseline before production source ingestion.

### Deliverables

- Next.js application;
- FastAPI service;
- PostgreSQL with PostGIS and pgvector;
- worker and scheduler;
- object-storage interface;
- migrations;
- synthetic fixtures;
- contract, schema and OpenAPI validation;
- unit, integration, end-to-end and accessibility test harnesses;
- OpenTelemetry baseline;
- one-command local startup.

### Gate F2

A clean clone MUST reproduce the environment and run all synthetic checks without production credentials.

---

## F3 — Epistemic kernel

State: `LOCKED`
Dependency: `F2`.

### Objective

Implement the authoritative path from evidence to admitted claim and opportunity.

### Deliverables

- Source Registry;
- immutable raw-object references;
- Evidence Registry;
- Entity Registry;
- claim proposal;
- structural, rights, temporal, quantitative and epistemic gates;
- Claim Ledger;
- contradiction relations;
- expiry and correction propagation;
- opportunity subgraph assembly;
- transactional outbox and audit events.

### Gate F3

Synthetic valid, rejected, contradictory, corrected and expired claims MUST replay deterministically. Model output MUST be unable to bypass admission.

---

## F4 — Navigator and shared InvestigationContext

State: `LOCKED`
Dependencies: `F1`, `F2`, `F3`.

### Objective

Turn natural language into typed, reversible navigation and research operations.

### Deliverables

- multilingual intent parser;
- explicit command preview;
- typed command plan;
- `InvestigationContext` state machine;
- permissions and entitlement checks;
- command execution and undo;
- explanation mode grounded in canonical resources;
- clarification only when materially necessary;
- conversation and UI state synchronisation;
- saved investigation trails.

### Gate F4

The same command MUST produce equivalent canonical context across supported languages and MUST never write directly to the Claim Ledger.

---

## F5 — Globe, Graph and Timeline parity

State: `LOCKED`
Dependencies: `F1–F4`.

### Objective

Deliver equal investigative power across geographical and relational lenses.

### Deliverables

- Globe layers, coverage and semantic zoom;
- Graph nodes, typed edges and bounded expansion;
- Timeline playback and `as_of` reconstruction;
- AUTO lens router;
- Dual professional mode;
- preserved selection, filters, time and rail across lens changes;
- map-to-graph and graph-to-map transitions;
- textual and tabular accessibility alternatives;
- performance budgets.

### Gate F5

No accepted core workflow may require abandoning context or switching to an unrelated page to reach claims or evidence.

---

## F6 — Multilingual semantic system

State: `LOCKED`
Dependencies: `F3–F5`.

### Objective

Make multilingual operation part of data and knowledge architecture, not a UI translation layer.

### Deliverables

- canonical English identifiers;
- original-language evidence preservation;
- translated claim renderings;
- translation provenance and confidence;
- multilingual aliases, transliteration and entity resolution;
- multilingual search and embeddings;
- locale-aware dates, currencies, units and formats;
- terminology glossaries;
- linguistic QA fixtures for six launch languages.

### Gate F6

Core intent, entity, claim and evidence workflows MUST be semantically equivalent across launch languages, with the original always recoverable.

---

## F7 — Intent Intelligence and Knowledge Tides

State: `LOCKED`
Dependencies: `F4`, `F6`, privacy and security controls.

### Objective

Learn from user research behaviour without confusing attention with economic truth.

### Deliverables

- `USER_INTENT_EVENT` ledger;
- private interest memory;
- observed, inferred and confirmed preference levels;
- purpose-specific privacy controls;
- aggregate Knowledge Tides;
- unique-user and organisation diversity metrics;
- temporal decay;
- manipulation and coordination detection;
- coverage-gap detection;
- research candidate queue;
- separation from Claim Ledger and Opportunity Engine;
- user controls for review, correction, deletion and exclusion.

### Gate F7

The system MUST prove:

- no single tenant or user can create a collective trend by repetition;
- minimum cohort thresholds prevent reidentification;
- raw prompts do not leak across organisations;
- Knowledge Tides create research candidates, not economic claims;
- deletion and opt-out propagate correctly.

---

## F8 — First lawful opportunity universe

State: `LOCKED`
Dependencies: `F2–F7` as relevant.

### Objective

Launch one narrow, valuable and lawful universe through the complete product loop.

### Candidate wedge

- European procurement and non-dilutive capital;
- official macro and sovereign context;
- regulation-created business demand;
- selected public-company disclosures.

The final wedge remains evidence-dependent.

### Deliverables

- universe ontology;
- admitted sources;
- coverage report;
- source rights and attribution;
- universe-specific claim gates;
- opportunity templates;
- Globe and Graph layers;
- multilingual terminology;
- historical reconstruction;
- buyer workflow validation.

### Gate F8

Pass only when data rights, product value, coverage, quality, cost, regulation and user demand all meet the universe admission contract.

---

## F9 — Paid design-partner product

State: `LOCKED`
Dependency: `F8`.

### Objective

Validate willingness to pay, repeated consultation and operating economics.

### Deliverables

- identity, organisations and roles;
- Stripe billing and entitlements;
- pricing experiments;
- onboarding;
- privacy, terms and acceptable-use surfaces;
- customer support and incident runbooks;
- product analytics;
- at least 10 independent paying design partners.

### Gate F9

Paid prototype gate `B1` plus security, restore and source-entitlement gates.

---

## F10 — Scenarios, calibration and outcomes

State: `LOCKED`
Dependency: sufficient historical data and `F8–F9`.

### Objective

Preserve forecasts, compare them with outcomes and calibrate uncertainty.

### Deliverables

- temporal holdouts;
- baselines;
- scenario model registry;
- calibration reports;
- historical forecast replay;
- outcome claims;
- demotion and retirement rules;
- user-facing uncertainty.

### Gate F10

Predictive surfaces remain descriptive or disabled unless they outperform declared baselines and meet calibration thresholds.

---

## F11 — Enterprise, API and private data

State: `LOCKED`
Dependencies: `F8–F10` as required.

### Objective

Support professional teams and private knowledge without contaminating global canonical products.

### Deliverables

- SSO and SCIM where demanded;
- enterprise API and quotas;
- private connectors;
- tenant-private claims and annotations;
- export controls;
- enterprise audit logs;
- data residency options;
- contractual security documentation.

### Gate F11

At least one paying enterprise entitlement package MUST operate with tested tenant isolation and lawful source redistribution.

---

## F12 — General availability and universe expansion

State: `LOCKED`
Dependency: validated operations and retention.

### Objective

Scale only what has demonstrated trust, retention and sustainable economics.

### Deliverables

- production SLOs and disaster recovery;
- repeatable acquisition channels;
- annual plans and expansion revenue;
- additional universes through independent admission gates;
- jurisdiction-selective commercial availability;
- mature security and compliance programme.

### Gate F12

General availability requires validated retention, gross margin, legal scope, operational reliability and no unresolved Goal Lock violation.
