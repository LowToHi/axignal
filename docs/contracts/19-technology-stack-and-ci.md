# 19 — Technology Stack and CI Contract

Version: `0.3.0-candidate`
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
- Caddy as the preferred initial AXIGNAL application proxy;
- OpenTofu/Terraform plus Ansible;
- Cloudflare R2 or another approved S3-compatible service for production objects;
- MinIO MAY emulate S3 locally;
- Kubernetes remains prohibited before a documented scale or isolation gate.

AXIGNAL application services MAY share the current VPS with other explicitly inventoried workloads during development and staging when networks, volumes, ports, resource limits, credentials, backups and rollback remain isolated.

A pre-existing host edge proxy MAY remain the exclusive owner of public `80/tcp` and `443/tcp`. In that topology:

- AXIGNAL Caddy MUST publish only an explicitly configured high port on `127.0.0.1`;
- the incumbent edge MUST route only the approved AXIGNAL hostname to that loopback endpoint;
- the AXIGNAL route MUST use a dedicated, removable dynamic configuration file;
- AXIGNAL automation MUST NOT replace, restart or rewrite unrelated edge configuration;
- no AXIGNAL service may publish another host address or public port;
- host-only credentials MUST be generated under `umask 077`, remain outside repository and controller workspaces, and use mode `0600`;
- plaintext operator credentials MUST be rotated after first access and removed after verified secure handoff;
- deployment health evidence MUST remain separate from the independent acceptance decision.

A CI execution boundary with Docker control, production-capable secrets or unrestricted host access MUST NOT share a trust boundary with production databases or unrelated stateful services.

A non-privileged build runner MAY share the physical VPS when all of the following are true:

- it runs as a dedicated non-root user or inside an isolated runner container/VM;
- it has no access to `/var/run/docker.sock`, rootful Docker groups, product volumes, product networks or product secrets;
- it executes only trusted repository revisions;
- it runs bounded build, typecheck, browser and API-test workloads that do not require host Docker;
- its workspace, processes and caches are cleaned and observable;
- GitHub-hosted CI remains available as fallback.

## 15. Hybrid GitHub Actions design

The VPS at `187.124.220.48` is an AXIGNAL application/staging host candidate and MAY also host a restricted AXIGNAL build runner under the boundary above. Its use as an application host is independent from runner acceptance.

### GitHub-hosted tier

GitHub-hosted runners MUST remain the default for:

- untrusted fork or external pull requests;
- canonical naming, schema, registry and OpenAPI validation;
- jobs requiring disposable Docker services while no isolated Docker-capable runner exists;
- PostgreSQL/PostGIS/pgvector and Valkey integration tests;
- fallback when the self-hosted runner is offline, saturated or under investigation.

### Shared-host build tier

A restricted runner labelled `self-hosted`, `linux`, `x64`, `axignal-build` MAY execute:

- `pnpm install --frozen-lockfile`;
- strict TypeScript;
- Next.js product and landing builds;
- Playwright browser suites;
- FastAPI lint and unit tests;
- dependency and contract checks that require no privileged service;
- trusted benchmark fixtures without product secrets.

Mandatory rules:

- runner process identity MUST be `axignal-runner` and MUST NOT be `root`;
- the runner MUST NOT mount or access the host Docker socket;
- no production SSH keys, `.env` files, databases, volumes or secret directories may be visible;
- the runner MUST NOT join application Docker networks;
- untrusted pull-request code MUST NOT execute on it;
- CPU, memory, disk, queue duration, workspace cleanup and process residue MUST be observable;
- failure of this optional tier MUST fall back to GitHub-hosted CI and MUST NOT stop AXIGNAL development.

### Dedicated integration tier

A future runner labelled `axignal-ci` MAY execute trusted Docker, database, migration, restore, Remotion and benchmark workloads only inside a dedicated host or strongly isolated VM with rootless Docker and independent acceptance.

Removing an application such as `iamancha.com` is not required to enable the shared-host build tier. It would free capacity but would not replace the required runner isolation.

## 16. Acceptance gates

The implementation stack may advance when:

- prototype v0.2 proves the selected frontend libraries;
- Globe and Graph performance budgets pass representative fixtures;
- multilingual rendering passes six-language fixtures;
- the canonical GitHub-hosted CI path passes reproducibly;
- dependency, licence and supply-chain review passes;
- backup and restore paths exist for stateful development services;
- every provisional choice has an owner, version and replacement gate.

Before enabling the optional shared-host build runner:

- it MUST complete a clean non-privileged build-runner acceptance workflow;
- it MUST prove no Docker socket, product secret, product network or persistent workspace access;
- failure MUST leave GitHub-hosted CI as the active fallback.

Before enabling a Docker-capable dedicated integration runner:

- it MUST complete the full rootless Docker and post-job isolation acceptance workflow;
- the runner boundary MUST contain no production or unrelated stateful workload.
