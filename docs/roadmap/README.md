# AXIGNAL End-to-End Development Map

Version: `0.5.0`
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
| [04 — Dynamic Skill Map](04-dynamic-skill-map.md) | Core skill lifecycle, routing and activation rules |
| [05 — Dependency and Gate Graph](05-dependency-and-gates.md) | Authorisation order, evidence and fail-closed transitions |
| [07 — Visual System Validation](07-visual-system-validation.md) | Candidate brand/UI directions, automated checks, user tests and non-freeze gate |
| [08 — Marketing, Pricing and Conversion](08-marketing-pricing-and-conversion-work-package.md) | Product fidelity, landing, pricing, FAQ, Trust Center, analytics and commercial validation |
| [09 — Commercial Dynamic Skills](09-commercial-dynamic-skill-map.md) | Candidate skills and task routing for fidelity, conversion, pricing, acquisition, CRM, SEO and trust |
| [10 — Research, Retrieval and Candidate Claims](10-research-retrieval-and-candidate-claims-work-package.md) | ResearchRun, authorised retrieval, tenant memory, Candidate Claims, dossier and admission handoff |

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

All registry files are validated as one ID set. A duplicate skill ID, identity mismatch or missing required specialist skill fails closed.

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
- The selected Investigation Shell composition is accepted as the prototype fidelity target through ADR-007.
- The executable shell now has a typed, persistent and CI-green InvestigationContext vertical slice.
- Exact production colours, typography, dimensions and motion remain unfrozen under Contract 20.
- The current visual implementation must preserve:
  - persistent Navigator chat;
  - `AUTO / GLOBE / GRAPH / DUAL` in the primary context bar;
  - dominant Globe or Graph canvas;
  - opportunities and Claim/Evidence Rail;
  - persistent Timeline;
  - dark Signal Teal and first-class light counterpart;
  - shared InvestigationContext and epistemic semantics.
- The public acquisition system is governed by Contracts 21–24 and Issue #6.
- Navigator Research Mode is now governed by Contracts 25–27 and ADR-009–010.
- The research architecture requires:
  - a visible and budgeted ResearchRun;
  - official APIs before Browser where available;
  - authorised Browser retrieval with provenance and prompt-injection controls;
  - three isolated logical knowledge domains on one PostgreSQL/pgvector platform initially;
  - tenant-private memory with explicit purpose and deletion controls;
  - Evidence Objects and Candidate Claims before admission;
  - local and external AI with proposal authority only;
  - contradiction and unknown discovery;
  - a traceable dossier and admission-queue handoff.
- The first research vertical slice must remain synthetic and bounded before real sources, live Browser, customer data or continuous production workers are authorised.
- Buyer, public copy, plan names, prices, acquisition channels, model routes and initial source licences remain hypotheses until their gates pass.

## Canonical identity

- Brand: **AXIGNAL**
- Domain: `axignal.com`
- Repository: `LowToHi/axignal`
- Goal ID: `AXIGNAL-GOAL-001`

Any occurrence of `ASIGNAL`, `asignal.com` or `ASIGNAL-GOAL-001` is a naming defect and blocks the relevant gate.

## Authorised operational priority

The authorised priority is:

> Preserve the faithful AXIGNAL Investigation Shell and conversion system while implementing the bounded synthetic ResearchRun vertical slice: user research request → official-API and authorised-Browser fixtures → Evidence Objects → Candidate Claims → contradictions and unknowns → dossier → admission queue → InvestigationContext update.

This priority does not authorise production-scale source ingestion, unrestricted Browser access, customer private data, a second vector database or model-written canonical claims.
