# AXIGNAL End-to-End Development Map

Version: `0.7.0`
Status: `CANDIDATE / F2 INTEGRATED / F1 VALIDATION AUTHORISED`
Goal ID: `AXIGNAL-GOAL-001`
Canonical baseline: `main@15a232249736658dbe05a67d1f2541384848f5b3`

This directory connects the AXIGNAL product goal to phases, tasks, contracts, dynamic skills, implementation evidence and independent gates.

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

No development agent may skip a layer or represent implemented code as an accepted phase without its gate evidence.

## Documents

| Document | Purpose |
|---|---|
| [00 — Goal Lock](00-goal-lock.md) | Immutable product purpose, invariants and anti-goals |
| [01 — Phase Map](01-phase-map.md) | End-to-end phases, deliverables, gates and dependencies |
| [02 — Task Catalogue](02-task-catalogue.md) | Typed executable tasks with stable IDs |
| [03 — Contract Map](03-contract-map.md) | Contracts governing each capability and phase |
| [04 — Dynamic Skill Map](04-dynamic-skill-map.md) | Core skill lifecycle, routing and activation rules |
| [05 — Dependency and Gate Graph](05-dependency-and-gates.md) | Authorisation order, evidence and fail-closed transitions |
| [06 — Current Execution State](06-current-execution-state.md) | Evidence-backed phase status and authorised priority |
| [07 — Visual System Validation](07-visual-system-validation.md) | Candidate UI directions, automated checks and user-test gate |
| [08 — Marketing, Pricing and Conversion](08-marketing-pricing-and-conversion-work-package.md) | Commercial validation work package |
| [09 — Commercial Dynamic Skills](09-commercial-dynamic-skill-map.md) | Candidate commercial skills |
| [10 — Research, Retrieval and Candidate Claims](10-research-retrieval-and-candidate-claims-work-package.md) | Research and admission work package |
| [11 — Consolidated Executable Baseline](11-consolidated-baseline.md) | Integration, migration rehearsal, supersession and rollback evidence |
| [12 — F2 Deliverable-Gap Closure](12-f2-deliverable-gap-closure.md) | Scheduler, object storage, OpenTelemetry and runtime-topology evidence |

## Normative execution contracts

- [`docs/contracts/18-development-agent-governance.md`](../contracts/18-development-agent-governance.md)
- [`AGENTS.md`](../../AGENTS.md)
- [`skills/registry.yaml`](../../skills/registry.yaml)
- [`schemas/task.schema.json`](../../schemas/task.schema.json)
- [`schemas/skill.schema.json`](../../schemas/skill.schema.json)

All registry files are validated as one ID set. Duplicate IDs, identity mismatches or missing required specialist skills fail closed.

## Status hierarchy

Roadmap: `DRAFT`, `CANDIDATE`, `FROZEN`, `SUPERSEDED`.

Phase: `LOCKED`, `AUTHORISED`, `IN_PROGRESS`, `EVIDENCE_READY`, `GATE_REVIEW`, `PASSED`, `FAILED`, `PAUSED`.

Task: `PROPOSED`, `READY`, `IN_PROGRESS`, `BLOCKED`, `EVIDENCE_READY`, `ACCEPTED`, `REJECTED`, `SUPERSEDED`.

## Current position

The canonical `main` branch contains a governed alpha vertical slice:

```text
identity
→ Navigator
→ persistent ResearchRun
→ governed source/document processing
→ Evidence Objects
→ Candidate Claims
→ proposal-only AI
→ deterministic admission
→ bounded human review
→ append-only Claim Ledger
→ InvestigationContext
```

Its reproducible runtime foundation now includes a persistent scheduler, content-addressed object storage, OpenTelemetry context/redaction and an explicit non-production topology.

Current evidence supports:

- F0 remains in gate review pending final map freeze;
- F1 has an executable product but lacks qualified-user acceptance;
- F2 is integrated and in formal gate review;
- F3–F5 have bounded vertical slices but are not general implementations;
- F6–F12 remain locked.

The authoritative detailed status is [`06-current-execution-state.md`](06-current-execution-state.md).

## Integrated baseline rule

Canonical integrations:

```text
PR #21 → cf83781766f12ebc55eeb9829d68d41e77500aa7
PR #22 → cb2c966d36207e908a19dd5381f9179d3c6fa406
PR #23 → 76ca919fea0d5740e80729aa7f9332f6aa6c5857
PR #24 → 15a232249736658dbe05a67d1f2541384848f5b3
```

Every new development unit MUST:

- branch from current `main`;
- remain independently reviewable;
- declare contracts, authority boundary, exclusions and rollback;
- pass only the gates relevant to its scope;
- avoid reopening superseded branches.

## Canonical identity

- Brand: **AXIGNAL**
- Domain: `axignal.com`
- Repository: `LowToHi/axignal`
- Goal ID: `AXIGNAL-GOAL-001`

Any active occurrence of `ASIGNAL`, `asignal.com` or `ASIGNAL-GOAL-001` outside permitted correction history is a naming defect.

## Authorised operational priority

> Build and execute the F1 qualified-user validation harness: pseudonymised sessions, frozen tasks, deterministic AXIGNAL/control assignment, append-only interaction history and reproducible metrics.

This priority does not authorise production deployment, unrestricted Browser access, customer private documents, OCR, broad source expansion, billing or model-written canonical claims.
