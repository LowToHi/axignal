# AX-F2-T16 — Shared Traefik private-pilot edge

Goal ID: `AXIGNAL-GOAL-001`
Phase: `F2`
Status: `IN_PROGRESS / DEPLOYMENT PROHIBITED`
Typed specification: `2026-07-29_shared-traefik-pilot-edge.task.json`

## Objective

Make the remote private-pilot automation compatible with the authorised shared application host while preserving Traefik ownership of `80/443`, binding AXIGNAL only to loopback, keeping credentials on the host and preventing deployment evidence from self-approving acceptance.

## Context

Read-only preflight found a running host-network Traefik instance on `187.124.220.48`. The original standalone Caddy port mapping would collide with it. The user authorised preparation of a compatibility PR but explicitly prohibited VPS mutation, deployment, Issue #31 closure and acceptance before review, merge, exact-SHA selection and confirmation of the ACME and operator emails.

## Affected systems

- pilot Compose edge boundary;
- Ansible bootstrap and exact-SHA deployment;
- Traefik dynamic routing;
- host-only secret generation, rotation and retirement;
- backup, rollback and watchdog Compose selection;
- deployment-state semantics;
- private-pilot CI and operational documentation.

## Implementation plan

- [x] register `AX-F2-T16` and ADR-011;
- [x] separate base, standalone and shared-Traefik Compose boundaries;
- [x] add an AXIGNAL-only Traefik dynamic route template;
- [x] generate UUID, password and service secrets only on the target host;
- [x] require `umask 077`, root ownership and mode `0600`;
- [x] add first-access rotation and plaintext-file retirement operations;
- [x] replace deployment self-acceptance with a blocked acceptance state;
- [x] extend static, unit, Compose and Ansible validation;
- [ ] obtain green GitHub Actions evidence;
- [ ] obtain independent review and merge.

## Blockers

- ACME contact email is not yet confirmed;
- initial operator email is not yet confirmed;
- physical deployment is prohibited before review, merge and exact-SHA selection;
- the implementing agent cannot issue the independent acceptance decision.

## Decisions

- Traefik remains the only public edge.
- Caddy binds `127.0.0.1:<configurable-port>:80` in shared mode.
- AXIGNAL owns one removable dynamic file and never restarts Traefik.
- Secret values never cross the controller or repository boundary.
- `DEPLOYED_AWAITING_ACCEPTANCE` is the strongest state deployment automation may write.

## Risks

- a divergent Traefik container name, entrypoint, resolver or file-provider directory blocks the playbook;
- a confirmed ACME contact that differs from the incumbent resolver requires a separate reviewed change;
- first-deployment failure can leave only the new pilot hostname returning `502`;
- a release without the shared overlay cannot safely serve as a shared-edge rollback target;
- secure handoff remains a human-controlled external operation.

## Validation checklist

- [x] Python unit tests pass locally;
- [x] remote operations contract verifier passes locally;
- [x] pilot candidate verifier passes locally;
- [x] no AXIGNAL public port exists in the shared Compose overlay;
- [x] deployment state remains acceptance-blocked;
- [x] no secret value is printed or committed;
- [ ] Ubuntu Ansible syntax gate passes in CI;
- [ ] both affected GitHub Actions workflows pass;
- [ ] independent reviewer accepts ADR-011 and the task evidence.

## Rollback considerations

Revert the PR before deployment. After a future deployment, stop only the AXIGNAL Compose project and remove only the AXIGNAL dynamic route. Preserve the incumbent Traefik process and all unrelated services. Rotate or revoke credentials independently of code rollback.

## Activated skills

Registry `0.3.1`: `goal-keeper`, `contract-router`, `task-orchestrator`, `gate-evaluator`, `naming-guardian`, `security-reviewer`, `privacy-reviewer`, `observability-engineer`, `repository-architect`, `test-engineer`, `operations-engineer`, `operations-writer`.

## Skill evidence ledger

- Inputs: `main@c2181f729f1500f7f59662d3b54710845977691e`, Issue #31 constraints, user-confirmed host and domain, and redacted read-only host preflight.
- Outputs: typed task, ADR-011, Contract 19 update, isolated Compose overlays, host-only credential lifecycle, blocked acceptance state, tests and runbooks.
- Warnings: ACME and operator emails remain unknown; physical topology, TLS, handoff and recovery evidence remain unavailable by explicit instruction.
- Conflicts resolved: availability and isolation override the original standalone Caddy port ownership; deployment evidence cannot override the independent acceptance gate.
- Tests: naming, task schema, YAML, Ruff, Python unit tests, pilot and remote contract verifiers, shell syntax and local Compose rendering.
- Disposition: `IN_PROGRESS`; GitHub-hosted CI and independent review are still required.
- Reviewer: unassigned; the implementing agent does not self-approve.
