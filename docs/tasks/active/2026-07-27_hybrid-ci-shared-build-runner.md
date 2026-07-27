# AXIGNAL hybrid CI shared build runner

Goal ID: `AXIGNAL-GOAL-001`
Tasks: `AX-F2-T10`, `AX-F2-T11`, `AX-F2-T12`
Status: `ACTIVE / NON-BLOCKING / FAIL-CLOSED`

## Objective

Reduce GitHub-hosted Actions consumption by moving trusted non-privileged build workloads to an isolated AXIGNAL runner on `187.124.220.48`, without exposing existing application services, Docker, databases or secrets.

## Decision

Use a restricted shared-host runner named `axignal-build-01` with labels `self-hosted`, `linux`, `x64`, `axignal-build`.

It may execute frozen dependency installation, TypeScript, product and landing builds, Playwright, FastAPI lint/unit tests and non-privileged trusted benchmarks.

It may not execute Docker, Compose, migration/restore tests, deployment, external pull requests or workflows with product secrets.

Deleting `iamancha.com` is not required. Removal would free capacity but would not replace the isolation boundary because LowToHi, BioCultur, Traefik, persistent databases and rootful Docker would remain.

## Current CI allocation

```text
GitHub-hosted
→ contracts, schemas, OpenAPI, untrusted code, Docker/PostGIS/pgvector/Valkey and fallback

axignal-build-01
→ frozen install, typecheck, builds, Playwright and FastAPI on trusted revisions

future axignal-ci
→ optional dedicated/rootless Docker integration runner
```

## Repository work completed

- [x] reproducible pnpm lockfile;
- [x] frozen CI installation;
- [x] pinned GitHub Actions;
- [x] Contract Validation PASS;
- [x] Executable Spine PASS;
- [x] ADR-008 records the hybrid architecture;
- [x] Contract 19 permits the restricted shared-host tier;
- [x] `verify-shared-build-boundary.sh` added;
- [x] non-Docker cleanup hook added;
- [x] shared-build acceptance workflow added.

## Remote implementation gate

- [ ] inventory current CPU, RAM, disk, Docker networks, mounts and runner services;
- [ ] confirm capacity without deleting active projects;
- [ ] create isolated `axignal-runner` boundary;
- [ ] prove no sudo, Docker group or Docker socket access;
- [ ] prove no application networks, volumes, keys or `.env` mounts;
- [ ] register `axignal-build-01` with exact labels;
- [ ] install before/after cleanup hook;
- [ ] run shared-build acceptance from a trusted revision;
- [ ] disable the runner and prove GitHub-hosted fallback;
- [ ] update Issue #10 with immutable evidence.

## Failure policy

Any failed boundary check disables only the shared runner. GitHub-hosted CI remains canonical and AXIGNAL development continues.

## Rollback

Disable and unregister `axignal-build-01`, stop/remove only its isolated boundary and work directory, revoke short-lived registration material, preserve logs if compromise is suspected and re-run GitHub-hosted Contract Validation and Executable Spine. Existing application services must remain untouched.

## Activated skills

Registry `0.3.1`: `goal-keeper`, `contract-router`, `task-orchestrator`, `gate-evaluator`, `naming-guardian`, `security-reviewer`, `privacy-reviewer`, `observability-engineer`, `repository-architect`, `test-engineer`, `operations-engineer`, `operations-writer`.
