# 04 — System Architecture Contract

Version: `0.1.0`
Status: `NORMATIVE`

## 1. Architecture objective

AXIGNAL MUST begin as a modular, observable and contract-first system that can run on a controlled VPS without pretending to have hyperscale requirements.

The initial architecture MUST optimise for:

- epistemic correctness;
- data provenance;
- reversible decisions;
- low operational cost;
- source isolation;
- fast product iteration;
- clear future extraction boundaries.

It MUST NOT begin as an unnecessary fleet of microservices.

## 2. Baseline architecture

```text
Browser
  ↓
Next.js Web Application
  ↓
AXIGNAL API / BFF
  ↓
Application Core
  ├── Identity and entitlements
  ├── Claims query service
  ├── Opportunity service
  ├── Scenario service
  ├── Search service
  └── Export service
  ↓
Canonical PostgreSQL
  ├── relational ledger
  ├── graph edges
  ├── PostGIS geography
  └── pgvector indexes

Workers
  ├── connectors
  ├── raw normalisation
  ├── entity resolution
  ├── claim extraction
  ├── deterministic admission
  ├── contradiction discovery
  ├── aggregation
  └── scenario evaluation

Object storage
  └── immutable raw evidence where rights permit
```

## 3. Repository architecture

Recommended monorepo:

```text
apps/
  web/                     Next.js product and public site
  admin/                   Internal operations and adjudication
services/
  api/                     FastAPI public/internal API
  worker/                  Background jobs and connectors
  scheduler/               Scheduled and event-triggered orchestration
packages/
  contracts/               Shared schemas and generated clients
  epistemic-core/          Claim rules, gates and transitions
  ontology/                Canonical predicates and universe extensions
  source-sdk/              Connector interface and testing harness
  ui/                      Design system and visual primitives
  observability/           Logging, metrics and tracing helpers
infra/
  compose/                  Local and single-node deployments
  terraform/               Cloud and provider resources
  ansible/                 VPS provisioning and hardening
docs/
  contracts/
  adr/
  research/
  runbooks/
schemas/
openapi/
```

## 4. Technology baseline

The baseline is dated July 2026 and MUST be pinned by lockfiles and container digests.

### Web

- Next.js `16.2.x` Active LTS or later approved security-patched LTS;
- TypeScript in strict mode;
- React Server Components where appropriate;
- Tailwind CSS and shadcn/ui primitives;
- MapLibre GL JS for open, GPU-accelerated map and globe rendering;
- deck.gl for dense geospatial and large-layer visualisation;
- a graph renderer selected by benchmark, initially Sigma.js or Cytoscape.js;
- Apache ECharts or D3 for specialised analytical views;
- Playwright for end-to-end testing;
- Vitest for unit and component tests.

The web application MUST be server-first for data loading and permissions. Authoritative entitlement checks MUST occur on the server.

### Backend and data processing

- Python `3.13+`;
- FastAPI;
- Pydantic v2;
- SQLAlchemy 2 or equivalent explicit repository layer;
- Alembic migrations;
- Polars and PyArrow for analytical transforms;
- JSON Schema 2020-12 for portable contracts;
- Celery-compatible jobs over Valkey/Redis for the initial worker system;
- idempotent job keys and a transactional outbox.

### Canonical storage

- PostgreSQL `18.x` stable release line;
- PostGIS for geography;
- pgvector for semantic indexes;
- native recursive queries and typed edge tables for the initial graph;
- row-level security where tenant isolation requires it.

PostgreSQL is the canonical source of truth. A dedicated graph database or analytical database MAY be added only after a recorded scale or query-performance gate.

### Object storage

S3-compatible object storage MUST be used for raw evidence and exports where source rights permit. Cloudflare R2, MinIO or another approved provider MAY satisfy the interface.

### Cache and queues

Valkey or Redis MAY provide:

- task queue transport;
- ephemeral cache;
- rate-limit counters;
- distributed locks where unavoidable.

No canonical claim state may exist only in the cache.

### Authentication and billing

- OIDC-compatible authentication abstraction;
- organisation, workspace, role and entitlement model owned by AXIGNAL;
- Stripe for subscriptions, invoicing and metered entitlements;
- webhook verification, replay protection and idempotency are mandatory.

The identity provider MUST be replaceable through an adapter and an ADR.

### Observability

- OpenTelemetry instrumentation;
- Prometheus-compatible metrics;
- Grafana dashboards;
- Loki-compatible structured logs;
- Tempo-compatible distributed traces;
- Sentry or equivalent client/server exception tracking as an optional managed layer.

### Infrastructure

- Docker for reproducible services;
- Docker Compose for development and controlled single-node alpha;
- Caddy or Traefik as edge proxy;
- GitHub Actions for CI;
- OpenTofu/Terraform plus Ansible for reproducible infrastructure;
- encrypted backups and tested restore procedures.

Kubernetes MUST NOT be introduced before a documented operational or scaling gate.

## 5. Domain modules

### Source Registry

Owns source contracts, rights, credentials, health, lineage groups and kill switches.

### Ingestion

Owns source-specific retrieval and immutable raw-object metadata.

### Entity Registry

Owns canonical entities, identifiers, aliases and temporal relationships.

### Evidence Registry

Owns evidence hashes, extracts, storage references and provenance.

### Claim Ledger

Owns immutable claim identity, versions, statuses and transitions.

### Admissibility Runtime

Owns deterministic gates. It MUST be a pure or transactionally controlled module with replayable results.

### Graph

Owns typed edges between claims, evidence, entities, markets, scenarios and opportunities.

### Trend Engine

Owns time-windowed aggregates and trend metrics.

### Scenario Engine

Owns frozen model versions, inputs, forecasts, calibration and outcome comparison.

### Opportunity Engine

Owns opportunity subgraphs, maturity states, invalidation conditions and user-facing summaries.

### Product Delivery

Owns search, filters, maps, visualisations, watchlists, alerts, exports and API entitlements.

## 6. Data flow

Every source object MUST follow this sequence:

```text
retrieve
→ fingerprint
→ persist raw reference
→ normalise
→ resolve entities
→ extract candidate claims
→ validate schema
→ validate rights
→ run epistemic gates
→ commit admitted state
→ update graph
→ recalculate affected aggregates
→ invalidate caches
→ emit user-facing changes
```

Steps MAY be asynchronous. State transitions MUST remain idempotent and auditable.

## 7. Event model

The initial event system SHOULD use a PostgreSQL transactional outbox and worker queue.

Canonical event examples:

- `source.object.retrieved`
- `source.object.normalised`
- `entity.resolution.proposed`
- `claim.proposed`
- `claim.admitted`
- `claim.contested`
- `claim.expired`
- `opportunity.recomputed`
- `scenario.generated`
- `scenario.invalidated`
- `source.suspended`
- `entitlement.changed`

Events MUST include schema version, event ID, correlation ID, causation ID and occurred time.

NATS JetStream, Kafka-compatible infrastructure or a durable workflow engine MAY replace or augment the initial design only after an ADR.

## 8. Search architecture

Foundation search SHOULD combine:

- PostgreSQL full-text search;
- structured filters;
- graph traversal;
- pgvector semantic similarity;
- geographic filters;
- temporal filters.

OpenSearch or another search engine MAY be introduced when measured query or indexing requirements exceed the PostgreSQL design.

## 9. Graph architecture

The initial graph MUST use typed node and edge tables in PostgreSQL.

A graph-specialised replica MAY be introduced for exploration queries if:

- canonical writes remain in PostgreSQL;
- replication lag is visible;
- stale graph results are labelled;
- the replica can be rebuilt from the ledger;
- no product truth depends solely on the replica.

## 10. AI gateway

All model use MUST pass through an internal gateway recording:

- provider and model;
- model snapshot or version where available;
- prompt or template version;
- input provenance;
- token or compute cost;
- latency;
- output hash;
- safety and policy decisions;
- downstream disposition.

Model providers MUST be replaceable. No provider response may write directly to the canonical claim ledger.

Local models MAY be used for inexpensive extraction, classification and embeddings. Paid frontier models SHOULD be reserved for workflows where measured value justifies cost.

## 11. Tenant and entitlement model

Tenant isolation MUST be designed from the first schema.

Resources MUST distinguish:

- global public knowledge;
- globally licensed paid knowledge;
- organisation-private data;
- user-private annotations and watchlists;
- export-restricted data;
- source-specific entitlements.

Entitlement checks MUST be enforced at query and export boundaries.

## 12. Deployment stages

### Local development

Docker Compose, seeded fixtures and synthetic sources.

### Foundation alpha

Single hardened VPS MAY host stateless application services, workers and supporting services. PostgreSQL and object storage MAY be colocated only for non-critical alpha with verified backups.

### Paid beta

Database, object storage and backups SHOULD be separated from the application node. High-availability and disaster-recovery targets MUST be documented.

### Scale

Services are extracted only according to measured bottlenecks, source isolation, regulatory boundaries or team ownership.

## 13. Backup and recovery

The system MUST provide:

- encrypted daily backups;
- point-in-time recovery where supported;
- object-store versioning where permitted;
- quarterly restore tests before paid production;
- documented recovery-time and recovery-point objectives;
- immutable audit-event retention.

## 14. Performance objectives

Foundation targets:

- cached product page p95 under 1.5 seconds;
- interactive map response under 100 milliseconds for local UI state changes;
- common API query p95 under 500 milliseconds excluding cold analytical jobs;
- claim drill-down p95 under 800 milliseconds;
- no UI freeze for standard supported map or graph layers;
- background processing latency labelled by source class.

## 15. Accessibility and internationalisation

- WCAG 2.2 AA is mandatory for product surfaces;
- visual encodings MUST not depend on colour alone;
- keyboard and reduced-motion operation are mandatory;
- canonical content MUST preserve source language;
- UI copy and summaries MUST support internationalisation;
- currency, dates, units and time zones MUST remain explicit.

## 16. Extraction gates

A module MAY become a separate service when at least one condition is demonstrated:

- independent scaling requirement;
- security or regulatory isolation;
- materially different availability objective;
- connector dependency conflict;
- release cadence conflict;
- dedicated team ownership;
- database workload isolation;
- cost reduction supported by measurement.

## 17. Acceptance criteria

Architecture foundation is accepted when:

- the monorepo builds reproducibly;
- local deployment starts from one documented command;
- schema migrations are automated and reversible where possible;
- one synthetic connector completes the full claim lifecycle;
- observability links source object to visible opportunity;
- tenant and entitlement tests pass;
- a source can be disabled and downstream state updates correctly;
- backups can be restored;
- the web interface renders a map, graph and claim drill-down from contract fixtures.
