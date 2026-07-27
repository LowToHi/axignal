# AXIGNAL runner hardening

Goal ID: `AXIGNAL-GOAL-001`
Tasks: `AX-F2-T10`, `AX-F2-T11`, `AX-F2-T12`
Status: `BLOCKED / FAIL-CLOSED`

## Objective

Freeze JavaScript dependencies, enforce reproducible CI and accept a non-root, isolated self-hosted runner for `LowToHi/axignal`.

## Context and affected systems

- PR `#9`, branch `agent/executable-spine-v0.1`, as the executable base;
- hardening branch `agent/runner-hardening-v0.1`, stacked on that base;
- Issue `#10`;
- JavaScript dependency graph and executable-spine CI;
- VPS `187.124.220.48`;
- self-hosted runner lifecycle, rootless Docker and cleanup hooks.

## Implementation plan

1. generate `pnpm-lock.yaml` with pnpm `10.12.4`;
2. patch direct and transitive dependencies identified by the production audit;
3. enforce `pnpm install --frozen-lockfile`;
4. add trusted-only runner acceptance and cleanup controls;
5. preflight the candidate VPS;
6. register and execute only after the host boundary passes;
7. record GitHub Actions and host evidence in Issue `#10`.

## Blocker

The repeated 2026-07-27 read-only preflight found eight running containers, including four persistent database containers, one existing non-AXIGNAL Actions runner service, a rootful Docker socket and an inactive host firewall. This conflicts with the normative prohibition on colocating AXIGNAL CI with production databases or secrets. The required `axignal-runner` account is absent; no account, service, firewall rule or workload was changed.

The acceptance workflow remains intentionally undispatched because the required runner does not exist and `workflow_dispatch` is not exposed from an unmerged workflow on the default branch. Neither condition may be bypassed by adding an untrusted automatic trigger.

## Decisions

- fail closed instead of granting the runner rootful Docker access;
- preserve all unrelated services unchanged;
- keep acceptance manual-only and unavailable to pull-request events;
- bind disposable PostgreSQL and Valkey ports to loopback.

## Risks

- shared-host compromise could cross product boundaries;
- rootful Docker access would be equivalent to host root;
- a persistent runner could retain workspaces or credentials without hooks;
- acceptance cannot be claimed until a clean host and successful run exist.

## Validation checklist

- [x] PR `#9` head and existing checks verified;
- [x] lockfile generated with pnpm `10.12.4`;
- [x] direct and transitive production advisories patched;
- [x] frozen install, typecheck, build and E2E pass locally;
- [x] acceptance workflow covers exact toolchains, contract validation, full suites, rootless disposable services, bounded metrics and an independent post-job cleanup proof;
- [ ] runner identity is exactly `axignal-runner`, uid is nonzero;
- [ ] labels are `self-hosted`, `linux`, `x64`, `axignal-ci`;
- [ ] Docker reports rootless and rootful socket is inaccessible;
- [ ] disposable integration and cleanup pass;
- [ ] no production-capable secret variables or forbidden key paths are visible;
- [ ] Issue `#10` links immutable revision and workflow run.

## Rollback considerations

Repository changes are additive or configuration-only and can be reverted as one hardening commit. Runner rollback must unregister the runner, stop its service, remove the dedicated user only after preserving incident evidence, and rebuild a compromised host rather than cleaning it in place.

## Activated skills

Registry `0.3.1`: `goal-keeper`, `contract-router`, `task-orchestrator`, `gate-evaluator`, `naming-guardian`, `security-reviewer`, `privacy-reviewer`, `observability-engineer`, `repository-architect`, `test-engineer`, `operations-engineer`, `operations-writer`.
