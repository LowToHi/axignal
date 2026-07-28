# ADR-008 — Hybrid CI with a restricted shared-host build runner

Status: `ACCEPTED / IMPLEMENTATION REQUIRED`
Date: `2026-07-27`
Goal ID: `AXIGNAL-GOAL-001`

## Context

AXIGNAL requires reproducible CI without exhausting the finite GitHub-hosted Actions budget. The current VPS at `187.124.220.48` already hosts LowToHi, BioCultur, `iamancha.com`, Traefik, persistent databases and an existing runner. A read-only preflight correctly rejected installing a second Docker-capable persistent runner with host-level control.

That rejection was too broad when interpreted as preventing all AXIGNAL use of the VPS or requiring a new server before development could continue. The existing topology supports a safer middle path: move only non-privileged, trusted build workloads to a separately isolated runner and keep Docker-backed integration plus untrusted validation on GitHub-hosted infrastructure.

Deleting `iamancha.com` would free compute and storage but would not remove the shared-host trust boundary, rootful Docker daemon, other persistent databases or existing services. It is therefore not required for this decision.

## Decision

Adopt a three-tier hybrid CI model.

### Tier 1 — GitHub-hosted canonical validation

Use GitHub-hosted runners for:

- untrusted or external pull requests;
- naming, JSON Schema, skill registry and OpenAPI checks;
- Docker-backed PostgreSQL/PostGIS/pgvector and Valkey integration;
- fallback when a self-hosted runner is unavailable;
- any workflow whose isolation cannot be demonstrated locally.

### Tier 2 — Restricted shared-host build runner

Permit a runner named `axignal-build-01`, labelled `self-hosted`, `linux`, `x64`, `axignal-build`, on the current VPS only when:

- the process runs as `axignal-runner`, never `root`;
- it runs inside an isolated container, VM or equivalent boundary;
- `/var/run/docker.sock` is absent and inaccessible;
- no application Docker network, persistent volume, SSH key, `.env`, database credential or product secret is mounted or reachable;
- it executes only trusted internal revisions;
- workloads are limited to frozen dependency installation, TypeScript, Next.js builds, Playwright, FastAPI lint/unit tests and non-privileged benchmarks;
- CPU, memory, disk, queue time, workspace cleanup and process residue are bounded and observable;
- GitHub-hosted CI remains the automatic fallback.

### Tier 3 — Dedicated Docker-capable integration runner

Defer Docker, migration, restore and heavy integration jobs to a future dedicated host or strongly isolated VM labelled `axignal-ci`. This tier requires rootless Docker and full post-job isolation acceptance.

## Consequences

### Positive

- reduces GitHub-hosted Actions consumption;
- reuses existing infrastructure without deleting active projects;
- avoids exposing product services to CI-controlled Docker;
- preserves a trusted fallback path;
- prevents a secondary infrastructure optimisation from blocking product delivery.

### Negative

- two runner policies and workflow paths must be maintained;
- the shared runner cannot execute Docker-backed integration;
- host-level network isolation requires explicit verification;
- CI evidence must distinguish hosted, shared-build and dedicated-integration tiers.

## Acceptance

Before enabling `axignal-build-01`, evidence MUST show:

1. exact runner name, labels and non-root identity;
2. no Docker socket or rootful Docker group access;
3. no application networks, volumes or secret paths;
4. frozen install, typecheck, web/landing builds, Playwright and FastAPI tests passing;
5. bounded resource use;
6. completed-job workspace and process cleanup;
7. successful fallback to GitHub-hosted CI when the runner is disabled.

## Rollback

Disable the runner in GitHub, stop and remove its isolated execution boundary, revoke any short-lived registration material, preserve logs if compromise is suspected and run the canonical GitHub-hosted workflows. No application service or database must be modified during rollback.
