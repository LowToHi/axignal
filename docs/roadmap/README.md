# AXIGNAL End-to-End Development Map

Version: `1.5.0`
Status: `NORMATIVE CANDIDATE / HUMAN APPROVAL REQUIRED / NO PUBLIC LAUNCH`
Goal ID: `AXIGNAL-GOAL-001`
Canonical baseline: `main@b9a08a2a07d04d635164e161d1b27a7a53df8575`
Engineering-stack candidate: `e1e4999ecd1a7140d9b18ea4b5ad6f0a20e32073`
Active candidate programme: [`15-global-e2e-development-program-v1.5.md`](15-global-e2e-development-program-v1.5.md)

## Execution authority

```text
explicit human decision
→ Goal Lock
→ AGENTS.md
→ Contract 18
→ Contract 31
→ ADR-016
→ P00–P27 phase
→ typed task
→ activated skills
→ implementation
→ evidence
→ independent gate
```

No agent may skip a layer or represent code as an accepted phase without evidence and canonical authority.

## State model

```text
engineering progress
≠ canonical acceptance
≠ product admission
≠ commercial availability
≠ public launch
```

The active roadmap records both engineering and canonical state.

## Active documents

| Document | Purpose |
|---|---|
| [00 — Goal Lock](00-goal-lock.md) | Product purpose, identity, B2G shell and anti-goals |
| [01 — Phase Map](01-phase-map.md) | Active P00–P27 phases and dual state |
| [02 — Task Catalogue](02-task-catalogue.md) | Active and historical typed tasks |
| [03 — Contract Map](03-contract-map.md) | Contract-to-capability and phase mapping |
| [04 — Dynamic Skill Map](04-dynamic-skill-map.md) | Skill routing |
| [05 — Dependency and Gates](05-dependency-and-gates.md) | Fail-closed graph and P27 authority |
| [06 — Current Execution State](06-current-execution-state.md) | Canonical main and engineering-stack truth |
| [14 — Global E2E Programme v1.4](14-global-e2e-development-program-v1.4.md) | Preserved P00–P24 history |
| [15 — Global E2E Programme v1.5](15-global-e2e-development-program-v1.5.md) | Candidate P00–P27 programme |

Documents 07–13 remain capability work packages and historical evidence. Where their sequencing conflicts with Contract 31, Contract 31 and ADR-016 govern.

## Active candidate contracts

- [`31-global-e2e-development-contract-v1.5.md`](../contracts/31-global-e2e-development-contract-v1.5.md)
- [`18-development-agent-governance.md`](../contracts/18-development-agent-governance.md)
- Goal Lock and all applicable Contracts 00–30
- [`ADR-016`](../adr/ADR-016-v1-5-canonical-programme-and-final-launch-gate.md)
- [`AGENTS.md`](../../AGENTS.md)

Preserved historical authorities:

- [`30-global-e2e-development-contract-v1.4.md`](../contracts/30-global-e2e-development-contract-v1.4.md)
- [`ADR-015`](../adr/ADR-015-finished-global-product-before-public-launch.md)

## Current position

```text
canonical main
P00 accepted
P01 in progress
P02–P24 canonical acceptance blocked

engineering stack
P02–P24 bounded engineering evidence present
P25-T01 engineering E2E pass
P26-T01 engineering E2E pass
P26-T02–T04 not started
P27 not started

public launch
NO_GO
```

## Current authorised canonical task

```text
AX-GE2E-P01-T01
IN_PROGRESS
Validate global buyers, jobs, budgets and workflows
```

P02–P27 may hold bounded engineering evidence but remain canonically blocked until their dependencies pass.

## Public activation boundary

The following remain false:

- public launch;
- partial or bounded public launch;
- public signup;
- public indexing;
- public Tender Alerts;
- live self-service billing;
- unsupported global coverage;
- production MCP access.

Only `AX-GE2E-P27-T01` may produce the final public-launch disposition.
