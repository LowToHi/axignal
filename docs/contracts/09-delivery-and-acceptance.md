# 09 — Delivery and Acceptance Contract

Version: `0.1.0`
Status: `NORMATIVE`

## 1. Delivery model

AXIGNAL MUST be developed through evidence gates, not arbitrary calendar phases.

A phase ends when its acceptance evidence exists. Time estimates MAY assist planning but MUST NOT substitute for proof.

The build sequence is intentionally narrow:

```text
contracts
→ synthetic end-to-end spine
→ first lawful source
→ canonical claim ledger
→ spatial and graph exploration
→ narrow paid product
→ validated retention
→ additional universes
```

## 2. Workstream order

### Phase F0 — Foundation contracts

Deliverables:

- repository constitution;
- product, business, epistemic, data, architecture, UX, security, API, quality and operations contracts;
- machine-readable schemas;
- initial OpenAPI specification;
- foundation ADRs.

Exit criteria:

- contracts cross-reference correctly;
- naming is canonical;
- product boundary is explicit;
- initial implementation backlog can be derived without inventing scope.

### Phase F1 — Reproducible repository

Deliverables:

- monorepo skeleton;
- lockfiles;
- containerised local environment;
- CI;
- migration framework;
- test fixtures;
- observability baseline;
- secret-management pattern.

Exit criteria:

- clean clone starts with one documented command;
- CI runs tests, lint, type checking, schema validation and security scanning;
- no production secret is required for synthetic execution.

### Phase F2 — Synthetic epistemic spine

Deliverables:

- synthetic source connector;
- raw evidence object;
- entity registry;
- claim proposal;
- deterministic admission;
- claim ledger;
- contradiction edge;
- opportunity assembly;
- API response;
- UI claim drill-down.

Exit criteria:

- one fixture travels from source object to visible opportunity with full lineage;
- rejected and expired claims prove fail-closed behaviour;
- model output cannot bypass the gate;
- replay produces equivalent canonical state.

### Phase F3 — First admitted source

Recommended first source family: official macroeconomic or public-institution data with clear technical access and usage conditions.

Deliverables:

- source admission record;
- rights review;
- production connector;
- incremental ingestion;
- quality dashboard;
- source kill switch;
- customer-visible attribution.

Exit criteria:

- source admission gate passes;
- parser drift and outage paths are tested;
- claims generated from the source are auditable;
- disabling the source correctly degrades downstream products.

### Phase F4 — Explorer vertical slice

Deliverables:

- AXIGNAL Globe with one meaningful layer;
- Explorer filters;
- Atlas graph;
- claim detail;
- opportunity detail;
- temporal state change;
- watchlist;
- textual accessibility alternative.

Exit criteria:

- qualified test users can move from global state to evidence without instruction;
- users understand observed, inferred and predicted distinctions;
- map, graph and detail views agree on canonical fixtures;
- performance and accessibility targets pass.

### Phase F5 — Narrow opportunity universe

The first commercial universe MUST be selected by data rights, buyer value, differentiation and manageable regulatory scope.

Candidate initial wedge:

- European public procurement and non-dilutive capital;
- global macro and sovereign context;
- public-company disclosure events;
- regulation-created business opportunities.

Deliverables:

- universe ontology;
- source set;
- admission rules;
- opportunity templates;
- coverage report;
- legal and licensing review;
- pricing entitlement;
- customer onboarding.

Exit criteria:

- universe admission gate passes;
- at least 100 historical opportunities or equivalent events are reconstructable with traceability;
- quality audit meets thresholds;
- at least one buyer workflow saves measurable research effort.

### Phase F6 — Paid design-partner release

Deliverables:

- Stripe subscriptions;
- account and organisation model;
- entitlements;
- billing webhooks;
- onboarding;
- terms and privacy surfaces;
- invite workflow;
- support and incident runbooks;
- paid product analytics.

Exit criteria:

- at least 10 independent qualified users pay;
- billing and entitlement tests pass;
- paid users receive no unlicensed data;
- support load remains within the operating model;
- critical security and restore gates pass.

### Phase F7 — Retention and pricing validation

Deliverables:

- cohort analytics;
- value interviews;
- pricing tests;
- annual-plan offer;
- workflow improvements derived from usage;
- evidence of repeatable decision support.

Exit criteria:

- retention gate B2 passes;
- at least one pricing tier demonstrates sustainable gross margin;
- recurring use is driven by ongoing intelligence, not constant bespoke consulting.

### Phase F8 — Scenario and historical calibration

Deliverables:

- frozen historical dataset;
- temporal holdout;
- baseline models;
- calibration reports;
- scenario history;
- outcome reconciliation;
- user-facing uncertainty design.

Exit criteria:

- models outperform declared baselines or are honestly retained as descriptive only;
- calibration is acceptable by universe and horizon;
- old forecasts remain visible and immutable;
- failures and corrections display correctly.

### Phase F9 — Additional universes

A new universe MUST repeat the source, ontology, regulatory, UX and commercial gates. No universe receives automatic admission because the platform already exists.

### Phase F10 — Enterprise and API

Deliverables:

- organisation administration;
- SSO/SCIM where demanded;
- API keys and quotas;
- exports;
- private connectors;
- enterprise audit logs;
- contractual security documentation.

Exit criteria:

- one enterprise customer pays for a reproducible entitlement package;
- source redistribution rights match the package;
- tenant isolation and audit requirements pass.

## 3. Backlog derivation

Every implementation issue MUST reference:

- affected contract sections;
- acceptance criteria;
- dependencies;
- security and rights impact;
- observability requirement;
- rollback or kill switch.

Issues MUST NOT use vague completion language such as “implement intelligence engine” without contract-level decomposition.

## 4. Definition of done

A task is complete only when:

- code and configuration are committed;
- tests pass;
- docs and contracts are consistent;
- telemetry exists;
- migrations are handled;
- security and rights implications are addressed;
- acceptance evidence is attached;
- rollback or disabling is documented;
- no known critical issue is hidden.

## 5. Acceptance evidence

Acceptable evidence includes:

- automated test output;
- screenshots or recordings of product behaviour;
- schema validation;
- reproducible fixture replay;
- benchmark report;
- accessibility report;
- security scan;
- restore test;
- data-rights record;
- user-research notes;
- paid invoice or Stripe event for commercial gates.

Assertions without evidence do not close a gate.

## 6. Change control

Material changes require:

1. updated contract;
2. ADR;
3. migration impact;
4. test impact;
5. user and entitlement impact;
6. rollback plan.

Emergency security changes MAY precede documentation but MUST be reconciled immediately after containment.

## 7. Branch and PR policy

- Default implementation branch pattern: `agent/<scope>` or `feature/<scope>`.
- Foundation and material architecture work SHOULD use draft PRs until acceptance evidence is complete.
- PR descriptions MUST list contracts affected and checks run.
- Direct production changes to the default branch are prohibited except repository initialisation or authorised emergency repair.

## 8. Release policy

Release stages:

- `dev` — synthetic and local;
- `alpha` — internal or invited, may be incomplete;
- `design-partner` — paid narrow release with explicit limitations;
- `beta` — repeatable paid product with monitored SLOs;
- `general-availability` — supported entitlement with validated operations.

A release label MUST not overstate maturity.

## 9. Commercial stop-loss

Development of a universe MUST pause when:

- source rights remain unresolved;
- quality is insufficient;
- acquisition cost has no plausible payback;
- target users will not pay;
- retention is absent;
- regulatory scope requires a business model not approved by the constitution;
- source or AI cost destroys gross margin;
- the same user value is reproducible by a general AI without AXIGNAL’s graph and history.

## 10. Immediate implementation priority

After merge of foundation contracts, the only authorised priority is:

> **Build the synthetic end-to-end epistemic spine and render it through one map layer, one graph path, one opportunity and one claim-evidence drill-down.**

Do not begin broad source ingestion, production scraping or multi-universe development before that spine passes Phase F2.
