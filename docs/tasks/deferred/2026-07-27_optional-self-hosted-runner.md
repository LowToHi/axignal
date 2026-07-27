# Optional AXIGNAL self-hosted runner

Goal ID: `AXIGNAL-GOAL-001`
Tasks: `AX-F2-T10`, `AX-F2-T11`, `AX-F2-T12`
Status: `DEFERRED / NON-BLOCKING`

## Decision

Repository hardening and GitHub-hosted CI are complete and passing. A persistent self-hosted runner is an optional optimisation, not a prerequisite for AXIGNAL development, review, deployment or operation.

The current VPS `187.124.220.48` remains eligible for AXIGNAL application hosting, staging, APIs, workers, PostgreSQL/PostGIS/pgvector and Valkey after normal deployment hardening. It is rejected only as a persistent Docker-capable CI runner in its present shared topology.

## Completed repository work

- `pnpm-lock.yaml` generated with pnpm `10.12.4`;
- frozen installs enforced;
- audited JavaScript dependencies patched;
- GitHub Actions pinned by immutable SHA;
- Contract Validation passing on GitHub-hosted runners;
- Executable Spine passing on GitHub-hosted runners;
- product and landing builds passing;
- Playwright, FastAPI, Ruff, PostGIS, pgvector and Valkey tests passing;
- manual runner acceptance and cleanup controls prepared for future use.

## Current canonical operating model

```text
GitHub-hosted runners
→ contracts, typecheck, builds, browser tests, API tests and disposable services

187.124.220.48
→ eligible AXIGNAL application/staging host after deployment hardening

Self-hosted runner
→ optional future optimisation in a dedicated host or strongly isolated VM
```

## Deferred acceptance criteria

When a compliant runner boundary is eventually assigned:

- [ ] runner identity is exactly `axignal-runner`, uid is nonzero;
- [ ] labels are `self-hosted`, `linux`, `x64`, `axignal-ci`;
- [ ] Docker reports rootless and rootful socket is inaccessible;
- [ ] disposable integration and cleanup pass;
- [ ] no product or production secrets are visible;
- [ ] Issue `#10` links immutable revision and workflow run.

## Non-blocking rule

Failure or absence of the optional self-hosted runner MUST NOT stop AXIGNAL work while GitHub-hosted CI remains green and sufficient. Heavy workloads may be reconsidered only when measurable queue time, cost or performance justifies the additional infrastructure.

## Next product priority

Prepare and validate a bounded AXIGNAL staging deployment on `187.124.220.48` without disturbing existing workloads. Deployment must use an inventory-first preflight, isolated networks and volumes, loopback-bound data services, explicit resource limits, health checks, backup/rollback and no production claim ingestion.

## Activated skills

Registry `0.3.1`: `goal-keeper`, `contract-router`, `task-orchestrator`, `gate-evaluator`, `naming-guardian`, `security-reviewer`, `privacy-reviewer`, `observability-engineer`, `repository-architect`, `test-engineer`, `operations-engineer`, `operations-writer`.
