# AXIGNAL End-to-End Development Map

Version: `0.8.0`
Status: `CANDIDATE / F8 PROCUREMENT EVIDENCE READY / TED PRODUCT ADMISSION NEXT`
Goal ID: `AXIGNAL-GOAL-001`
Canonical baseline: `main@9484c4ecce8ebe31484ef4f1f5e602f6c9cdfac9`

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
| [13 — B2G Pricing, Trial and Global Procurement Sources](13-b2g-pricing-trial-and-global-procurement-source-program.md) | TED E2E priority, B2G price validation, safe seven-day trial and federated source-expansion gates |

## Normative execution contracts

- [`docs/contracts/18-development-agent-governance.md`](../contracts/18-development-agent-governance.md)
- [`docs/contracts/28-b2g-procurement-commercial-and-global-source-program.md`](../contracts/28-b2g-procurement-commercial-and-global-source-program.md)
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

The canonical `main` branch contains a governed alpha vertical slice and the first bounded procurement-lifecycle evidence:

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

For European procurement, `main` additionally contains:

```text
TED bounded Search API probe
→ eForms SDK 1.14.2 parser
→ CN16 correction and notice-cancellation lineage
→ CAN29 result lineage
→ 50 immutable provisional Evidence Objects
→ deterministic sandbox admission
→ traceable procurement dossier
```

Current authority boundary:

- TED remains `TECHNICAL_PROBE`;
- production procurement policy and runtime remain disabled;
- product admission remains incomplete;
- no public procurement-support or global-coverage claim is authorised;
- no billing or seven-day trial is active;
- non-TED global sources are catalogue-only.

## Integrated baseline rule

The latest canonical procurement evidence baseline is:

```text
PR #40 → first lawful European procurement wedge
PR #41 → version-pinned TED eForms XML parser
PR #42 → deterministic procurement admission rehearsal
PR #44 → procurement lifecycle Evidence Objects and dossier
main    → 9484c4ecce8ebe31484ef4f1f5e602f6c9cdfac9
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

## Authorised development order

The highest-value next task is `AX-F8-T14`:

> Complete TED source-specific product admission and wire authenticated identity → server-resolved tenant → persistent ResearchRun → polling/SSE progress → worker → Evidence Objects and Candidate Claims → deterministic admission → dossier and claims returned to InvestigationContext → progressive fixture removal.

After that gate:

1. execute `AX-F9-T15` as a paid B2G Design Partner, pricing and private seven-day trial validation task;
2. keep `AX-F12-T10` blocked until European paid-value and source-admission evidence exists;
3. use the global source catalogue for research prioritisation only.

This order does not authorise production trial activation, public prices, Stripe billing, API redistribution, private customer documents, predictive procurement claims, broad source expansion or model-written canonical truth.
