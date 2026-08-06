# AX-GE2E-P08-T02 — Subscriber workspace E2E

Goal ID: `AXIGNAL-GOAL-001`
Phase: `P08`
Status: `AX_SUBSCRIBER_WORKSPACE_ENGINEERING_IN_PROGRESS`
Typed specification: `2026-08-02_subscriber-workspace-e2e.task.json`

## Objective

Implement the authenticated Intelligence Shell and contextual Tender Workspace from the exact PR #128 architecture head while preserving evidence, rights, tenant and subscriber-authority boundaries.

## Exact starting point

- architecture PR: `#128` (`agent/ax-subscriber-workspace-ux-architecture-skills-v1`);
- head: `3d2085026232504bff13966dfdde64acabdc54e1`;
- head tree: `2ec917abcc137b7a39eefc609234d4ea8aa66614`;
- working branch: `codex/subscriber-workspace-e2e`;
- isolated worktree: `.worktrees/subscriber-workspace-e2e`.

## Implementation order

- [x] resolve exact authority branch and preserve the dirty landing worktree;
- [x] read governing contracts, UX research, architecture contract and mandatory skill registry;
- [x] audit current subscriber capabilities;
- [x] freeze shared route, state, permission, API, event, token, fixture and acceptance-test contracts;
- [x] implement shared shell and design system;
- [x] implement Intelligence Shell and global destinations as an engineering candidate;
- [x] implement all Tender Workspace routes and bounded core mutations;
- [ ] validate browser, API, persistence, permission, accessibility, visual and performance gates;
- [ ] package evidence, rollback and independent gate request.

## Non-negotiable boundaries

- No autonomous submission, external communication or signature.
- No silent fixture fallback.
- No client-authoritative tenant, role, entitlement or approval.
- No live Stripe activation, public launch, source admission or canonical UX acceptance.
- Globe, Graph and Timeline remain functional, traceable and nonvisual-first-class lenses.
- Qualified-user UX evidence remains external and cannot be self-issued by implementation.

## Rollback

Set `AXIGNAL_SUBSCRIBER_WORKSPACE_ENABLED=false` to retain the current bounded InvestigationShell, then revert the branch. Persistent canonical and audit ledgers are not deleted by UI rollback.
