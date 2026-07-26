# AXIGNAL End-to-End Development Map

Version: `0.3.2`
Status: `CANDIDATE / EVOLVING UNTIL FINAL MAP FREEZE`
Goal ID: `AXIGNAL-GOAL-001`

This directory is the execution map that connects the AXIGNAL product goal to phases, tasks, contracts, dynamic skills, evidence and gates.

## Execution chain

```text
Goal Lock
→ Phase
→ Task
→ Required contracts
→ Activated skills
→ Implementation
→ Acceptance evidence
→ Gate decision
→ Next authorised phase
```

No development agent may skip a layer or infer a different product goal from an isolated task.

## Documents

| Document | Purpose |
|---|---|
| [00 — Goal Lock](00-goal-lock.md) | Immutable product purpose, invariants and anti-goals |
| [01 — Phase Map](01-phase-map.md) | End-to-end phases, deliverables, gates and dependencies |
| [02 — Task Catalogue](02-task-catalogue.md) | Typed executable tasks with stable IDs |
| [03 — Contract Map](03-contract-map.md) | Which contracts govern each capability and phase |
| [04 — Dynamic Skill Map](04-dynamic-skill-map.md) | Skill lifecycle, routing and activation rules |
| [05 — Dependency and Gate Graph](05-dependency-and-gates.md) | Authorisation order, evidence and fail-closed transitions |
| [07 — Visual System Validation](07-visual-system-validation.md) | Candidate brand/UI directions, automated checks, user tests and non-freeze gate |

## Normative execution contracts

- [`docs/contracts/18-development-agent-governance.md`](../contracts/18-development-agent-governance.md)
- [`AGENTS.md`](../../AGENTS.md)
- [`skills/registry.yaml`](../../skills/registry.yaml)
- [`schemas/task.schema.json`](../../schemas/task.schema.json)
- [`schemas/skill.schema.json`](../../schemas/skill.schema.json)

## Status hierarchy

Roadmap state:

- `DRAFT`
- `CANDIDATE`
- `FROZEN`
- `SUPERSEDED`

Phase state:

- `LOCKED`
- `AUTHORISED`
- `IN_PROGRESS`
- `GATE_REVIEW`
- `PASSED`
- `FAILED`
- `PAUSED`

Task state:

- `PROPOSED`
- `READY`
- `IN_PROGRESS`
- `BLOCKED`
- `EVIDENCE_READY`
- `ACCEPTED`
- `REJECTED`
- `SUPERSEDED`

## Current position

- Foundation contracts: created in PR #1 and consolidated into the active roadmap PR.
- UX research and map-first prototype: created in PR #4 and consolidated into the active roadmap PR.
- Final UX and final visual identity remain unfrozen.
- The current visual work is governed by Contract 20, ADR-006 and the visual-system validation work package.
- New material requirements integrated into the active map include:
  - conversational navigation and claim explanation;
  - `AUTO / GLOBE / GRAPH / DUAL` lens routing;
  - functional parity between Globe and Graph;
  - English, Spanish, French, German, Portuguese and Simplified Chinese;
  - user-intent memory;
  - aggregate Knowledge Tides;
  - research candidate queue;
  - privacy, manipulation and epistemic separation controls;
  - layered brand, UI, epistemic and data-visualisation systems;
  - comparison of materially different visual directions before freeze.

## Canonical identity

- Brand: **AXIGNAL**
- Domain: **axignal.com**
- Repository: `LowToHi/axignal`
- Goal ID: `AXIGNAL-GOAL-001`

Any occurrence of `ASIGNAL`, `asignal.com` or `ASIGNAL-GOAL-001` is a naming defect and blocks the relevant gate.

## Only authorised operational priority

Until this map is frozen, the only authorised priority is:

> Complete and validate the AXIGNAL Investigation Shell map, including Navigator, Globe/Graph parity, multilingual architecture, Intent Intelligence and the candidate visual-system comparison, before production UI implementation.
