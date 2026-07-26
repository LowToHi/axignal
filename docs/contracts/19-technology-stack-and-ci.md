# 19 — Technology Stack and CI Contract

Version: `0.1.0-candidate`
Status: `NORMATIVE CANDIDATE / STACK FREEZE REQUIRED`
Goal ID: `AXIGNAL-GOAL-001`

## 1. Purpose

This contract fixes the candidate implementation stack for AXIGNAL while preserving explicit replacement gates. A library is not adopted merely because it is fashionable; it must support epistemic correctness, Globe–Graph parity, multilingual operation, reproducibility and controlled operating cost.

## 2. Monorepo and package management

- `pnpm` workspaces MUST manage JavaScript and TypeScript packages.
- Turborepo SHOULD provide task orchestration and caching.
- Python dependencies MUST be locked reproducibly with `uv` or an equivalently auditable lock mechanism.
- Container images and GitHub Actions MUST be pinned to immutable versions or commit SHAs before production.

## 3. Web application

Foundation baseline:

- Next.js `16.2.x` Active LTS;
- App Router;
- React `19.2.x` compatible with the pinned Next.js release;
- TypeScript strict mode;
- Tailwind CSS v4;
- shadcn/ui CLI v4 using an AXIGNAL-owned internal component registry;
- Radix UI primitives as the initial accessibility foundation unless prototype evidence selects Base UI;
- `next-intl` or an equivalent ICU-compatible localisation layer;
- TanStack Query for remote server state;
- XState v5 for the typed `InvestigationContext`, Navigator command execution and reversible lens transitions;
- Zod at client boundaries generated or aligned with canonical JSON Schemas;
- Playwright, Vitest and axe-core for automated testing.

The frontend MUST NOT duplicate canonical business or epistemic rules.

## 4. Spatial, graph and analytical rendering

- MapLibre GL JS MUST provide the basemap, globe projection and camera model.
- deck.gl MUST provide dense WebGL analytical layers and large geospatial overlays.
- Sigma.js with Graphology is the preferred Graph candidate because AXIGNAL requires performant exploration rather than a node-editor canvas.
- Apache ECharts SHOULD provide standard analytical charts.
- D3 MAY provide custom scales, layouts and data transformations when an existing accessible component is insufficient.
- Tables and textual equivalents MUST remain first-class and synchronised.

Renderer selection remains subject to the F1 prototype benchmark and F5 performance gate.

## 5. Application motion

- CSS and the Web Animations API SHOULD handle simple state changes.
- Motion for React MAY handle coordinated interface transitions and shared-layout continuity.
- MapLibre and deck.gl native transition systems MUST control geographic camera and layer transitions.
- Graph transitions MUST preserve pinned positions and settle within the visualisation grammar budget.
- Remotion MUST NOT be loaded into the main interactive AXIGNAL shell.

## 6. Remotion boundary

Remotion SHOULD be provided as an isolated package or render worker for:

- Time Machine video exports;
- narrated investigation summaries;
- methodology and onboarding explainers;
- automated research brief videos;
- controlled public launch and social assets.

Remotion output MUST preserve claim IDs, as-of time, source attribution, coverage and uncertainty. It MUST NOT turn an unadmitted model narrative into canonical research.

## 7. Backend

- Python `3.13+`;
- FastAPI;
- Pydantic v2;
- SQLAlchemy 2;
- Alembic;
- Polars and PyArrow;
- generated TypeScript API clients from OpenAPI 3.1;
- structured outputs validated against Pydantic or JSON Schema;
- provider-independent AI gateway.

## 8. Canonical data platform

- PostgreSQL `18.x` is the canonical system of record.
- PostGIS provides spatial types and queries.
- pgvector provides semantic indexes.
- native full-text search, trigram indexes and structured filters provide initial lexical search.
- typed relational edge tables and recursive queries provide the initial canonical graph.
- S3-compatible object storage holds immutable source objects where rights permit.
- Valkey provides ephemeral cache, queue transport, rate limits and short-lived coordination.

A dedicated vector, graph, search or analytical database MUST NOT be introduced without a measured extraction gate and ADR.

## 9. Vector-search policy

AXIGNAL MUST use pgvector initially, not a separate vector database.

Embeddings MAY support discovery, deduplication, multilingual similarity, candidate contradiction retrieval and analogue search. They MUST NOT admit claims, determine truth or become the sole representation of an entity or relationship.

A dedicated vector database may be evaluated when at least one threshold is demonstrated:

- index size or query concurrency exceeds agreed PostgreSQL budgets;
- tenant isolation or payload filtering cannot meet SLOs;
- vector ingestion materially disrupts canonical transactions;
- operational cost is demonstrably lower after including replication and backup;
- required retrieval capabilities cannot be implemented safely in pgvector.

## 10. API and realtime transport

- REST JSON under OpenAPI 3.1 is the public and internal HTTP foundation.
- Server-Sent Events SHOULD stream Navigator progress, research execution and material state updates.
- WebSockets MAY be introduced only for truly bidirectional realtime collaboration.
- Async event schemas SHOULD be documented with AsyncAPI before external event integrations.
- Public graph access MUST remain bounded and typed; no unrestricted database query language may be exposed.

## 11. Workflow and automation layers

### Canonical workflows

Core source, claim, opportunity and research workflows MUST be code-defined, idempotent, observable and replayable.

Foundation:

- PostgreSQL transactional outbox;
- worker queue over Valkey;
- scheduler with persisted job identity;
- explicit retry, dead-letter and compensation policy.

A durable workflow engine such as Temporal MAY be introduced through an ADR when long-running research, human review, timers, signals or cross-service compensation exceed the foundation orchestration model.

### Peripheral business automation

A self-hosted tool such as n8n MAY automate CRM, support, notifications and publishing. It MUST NOT write directly to the Claim Ledger, Opportunity Engine or rights state.

## 12. Authentication, billing and entitlements

- OIDC-compatible identity abstraction;
- AXIGNAL-owned organisation, workspace, role and entitlement model;
- Stripe for subscriptions, invoicing and metered entitlements;
- replaceable identity-provider adapter;
- all webhook operations signed, replay-protected and idempotent.

The final identity provider remains an explicit pre-F2 decision.

## 13. Observability

- OpenTelemetry;
- Prometheus-compatible metrics;
- Grafana;
- Loki-compatible logs;
- Tempo-compatible tracing;
- Sentry or equivalent error tracking where justified.

Every command, source object, candidate claim, admitted claim, opportunity and user-facing update MUST share traceable correlation metadata.

## 14. Infrastructure

- Docker and Docker Compose for development and alpha;
- Caddy as the preferred initial edge proxy;
- OpenTofu/Terraform plus Ansible;
- Cloudflare R2 or another approved S3-compatible service for production objects;
- MinIO MAY emulate S3 locally;
- Kubernetes remains prohibited before a documented scale or isolation gate.

The CI runner VPS MUST NOT also host production databases or production secrets.

## 15. Self-hosted GitHub Actions runner

The VPS at `187.124.220.48` is designated as a candidate AXIGNAL CI and benchmark host.

Mandatory rules:

- the runner MUST NOT execute as `root`;
- create a dedicated unprivileged `axignal-runner` account;
- use labels such as `self-hosted`, `linux`, `x64`, `axignal-ci`;
- isolate each job in a disposable container or equivalent clean workspace;
- never mount production SSH keys, databases or secret directories;
- grant the workflow minimum `GITHUB_TOKEN` permissions;
- untrusted fork pull requests MUST NOT execute arbitrary code on the persistent runner;
- heavy trusted jobs MAY run on the VPS after branch or maintainer authorisation;
- runner and base images MUST be patched and monitored;
- disk, CPU, memory, queue duration and cleanup MUST be observable.

A hybrid CI design SHOULD retain lightweight GitHub-hosted validation for untrusted pull requests while assigning trusted container, Playwright, benchmark and integration workloads to the self-hosted runner.

## 16. Acceptance gate

The stack is frozen only when:

- prototype v0.2 proves the selected frontend libraries;
- Globe and Graph performance budgets pass representative fixtures;
- multilingual rendering passes six-language fixtures;
- the self-hosted runner completes a clean, isolated trusted workflow;
- dependency, licence and supply-chain review passes;
- backup and restore paths exist for stateful development services;
- every provisional choice has an owner, version and replacement gate.
