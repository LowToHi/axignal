# AXIGNAL End-to-End Development Map

Version: `0.6.1`
Status: `CANDIDATE / CONSOLIDATED BASELINE ACTIVE`
Goal ID: `AXIGNAL-GOAL-001`
Canonical baseline: `main@cf83781766f12ebc55eeb9829d68d41e77500aa7`

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

No development agent may skip a layer, infer a different product goal from an isolated task or represent implemented code as an accepted phase without its gate evidence.

## Documents

| Document | Purpose |
|---|---|
| [00 — Goal Lock](00-goal-lock.md) | Immutable product purpose, invariants and anti-goals |
| [01 — Phase Map](01-phase-map.md) | End-to-end phases, deliverables, gates and dependencies |
| [02 — Task Catalogue](02-task-catalogue.md) | Typed executable tasks with stable IDs |
| [03 — Contract Map](03-contract-map.md) | Which contracts govern each capability and phase |
| [04 — Dynamic Skill Map](04-dynamic-skill-map.md) | Core skill lifecycle, routing and activation rules |
| [05 — Dependency and Gate Graph](05-dependency-and-gates.md) | Authorisation order, evidence and fail-closed transitions |
| [06 — Current Execution State](06-current-execution-state.md) | Evidence-backed phase status and currently authorised priority |
| [07 — Visual System Validation](07-visual-system-validation.md) | Candidate UI directions, automated checks and user-test gate |
| [08 — Marketing, Pricing and Conversion](08-marketing-pricing-and-conversion-work-package.md) | Landing, pricing, FAQ, Trust Center, analytics and commercial validation |
| [09 — Commercial Dynamic Skills](09-commercial-dynamic-skill-map.md) | Candidate skills for conversion, pricing, acquisition, CRM, SEO and trust |
| [10 — Research, Retrieval and Candidate Claims](10-research-retrieval-and-candidate-claims-work-package.md) | ResearchRun, retrieval, tenant memory, proposals, dossier and admission handoff |
| [11 — Consolidated Executable Baseline](11-consolidated-baseline.md) | Completed integration, migration rehearsal, supersession and rollback evidence |

## Normative execution contracts

- [`docs/contracts/18-development-agent-governance.md`](../contracts/18-development-agent-governance.md)
- [`AGENTS.md`](../../AGENTS.md)
- [`skills/registry.yaml`](../../skills/registry.yaml)
- [`skills/commercial-extension.registry.yaml`](../../skills/commercial-extension.registry.yaml)
- [`skills/research-retrieval.registry.yaml`](../../skills/research-retrieval.registry.yaml)
- [`schemas/task.schema.json`](../../schemas/task.schema.json)
- [`schemas/skill.schema.json`](../../schemas/skill.schema.json)
- [`schemas/research-run.schema.json`](../../schemas/research-run.schema.json)
- [`schemas/candidate-claim.schema.json`](../../schemas/candidate-claim.schema.json)
- [`schemas/tenant-knowledge-item.schema.json`](../../schemas/tenant-knowledge-item.schema.json)

All registry files are validated as one ID set. Duplicate IDs, identity mismatches or missing required specialist skills fail closed.

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
- `EVIDENCE_READY`
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

The canonical `main` branch contains an executable, governed alpha vertical slice:

```text
identity
→ Navigator
→ persistent ResearchRun
→ governed source/document processing
→ Evidence Objects
→ Candidate Claims
→ proposal-only AI
→ independent deterministic admission
→ append-only Claim Ledger
→ InvestigationContext
```

The current evidence supports these statements:

- F0 remains in gate review pending final map and cross-contract freeze;
- F1 has an executable prototype but still lacks qualified-user acceptance;
- F2 is evidence-ready with the cumulative baseline integrated and migration/restore rehearsed;
- F3 and F4 have bounded vertical slices but are not general implementations;
- F5 has a product shell and browser workflow but not validated full parity;
- F6–F12 remain locked.

The authoritative detailed status is [`06-current-execution-state.md`](06-current-execution-state.md). Static state labels in older roadmap sections must be interpreted through that current evidence document until the next full phase-map revision.

## Consolidated baseline rule

PR #21 was squash-merged as `cf83781766f12ebc55eeb9829d68d41e77500aa7`. PRs #5, #9 and #11–#19 are superseded audit evidence.

Every new development unit MUST:

- branch from current `main`;
- remain independently reviewable;
- declare its contracts, authority boundary, exclusions and rollback;
- pass only the gates relevant to its scope;
- avoid reopening or extending the superseded stack.

## Canonical identity

- Brand: **AXIGNAL**
- Domain: `axignal.com`
- Repository: `LowToHi/axignal`
- Goal ID: `AXIGNAL-GOAL-001`

Any active occurrence of `ASIGNAL`, `asignal.com` or `ASIGNAL-GOAL-001` outside explicitly permitted correction history is a naming defect and blocks the relevant gate.

## Authorised operational priority

> Implement bounded human review for `HUMAN_REVIEW_REQUIRED` and `CONTESTED`, preserving reviewer identity, reason codes, append-only history and non-bypassable deterministic gates. Then execute F1 qualified-user validation.

This priority does not authorise production deployment, unrestricted Browser access, customer private documents, OCR, broad source expansion, billing or model-written canonical claims.
