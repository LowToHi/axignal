# AXIGNAL runner hardening

Goal ID: `AXIGNAL-GOAL-001`
Tasks: `AX-F2-T10`, `AX-F2-T11`, `AX-F2-T12`
Status: `BLOCKED / FAIL-CLOSED`

## Objective

Freeze JavaScript dependencies, enforce reproducible CI and accept a non-root, isolated self-hosted runner for `LowToHi/axignal`.

## Context and affected systems

- PR `#9`, branch `agent/executable-spine-v0.1`;
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

The 2026-07-27 preflight found unrelated persistent web and database workloads on the candidate VPS, including PostgreSQL containers. This conflicts with the normative prohibition on colocating AXIGNAL CI with production databases or secrets. No AXIGNAL runner account or service was created.

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
- [ ] runner identity is exactly `axignal-runner`, uid is nonzero;
- [ ] labels are `self-hosted`, `linux`, `x64`, `axignal-ci`;
- [ ] Docker reports rootless and rootful socket is inaccessible;
- [ ] disposable integration and cleanup pass;
- [ ] no production-capable secret variables or forbidden key paths are visible;
- [ ] Issue `#10` links immutable revision and workflow run.

## Rollback considerations

Repository changes are additive or configuration-only and can be reverted as one hardening commit. Runner rollback must unregister the runner, stop its service, remove the dedicated user only after preserving incident evidence, and rebuild a compromised host rather than cleaning it in place.
