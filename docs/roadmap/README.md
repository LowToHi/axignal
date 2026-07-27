# AXIGNAL End-to-End Development Map

Version: `0.4.0`
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
| [08 — Marketing, Pricing and Conversion](08-marketing-pricing-and-conversion-work-package.md) | Product fidelity, landing, pricing, FAQ, Trust Center, analytics and commercial validation |

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
- The selected Investigation Shell composition is now accepted as the prototype fidelity target through ADR-007.
- Exact production colours, typography, dimensions and motion remain unfrozen under Contract 20.
- The current visual implementation must reproduce:
  - persistent Navigator chat;
  - `AUTO / GLOBE / GRAPH / DUAL` in the primary context bar;
  - dominant Globe or Graph canvas;
  - opportunities and Claim/Evidence Rail;
  - persistent Timeline;
  - dark Signal Teal and first-class light counterpart;
  - shared InvestigationContext and epistemic semantics.
- The public acquisition system is now governed by Contracts 21–24 and Issue #6.
- The landing is a complete conversion system including:
  - faithful product proof;
  - use cases and differentiation;
  - Pricing and plan comparison;
  - FAQ and objection handling;
  - Trust Center and public methodology;
  - conversion forms, CRM and onboarding handoff;
  - acquisition analytics and experiments;
  - six-language architecture;
  - SEO, accessibility and performance;
  - evidence-gated channel reinvestment.
- Buyer, public copy, plan names, prices and acquisition channels remain hypotheses until their gates pass.

## Canonical identity

- Brand: **AXIGNAL**
- Domain: **axignal.com**
- Repository: `LowToHi/axignal`
- Goal ID: `AXIGNAL-GOAL-001`

Any occurrence of `ASIGNAL`, `asignal.com` or `ASIGNAL-GOAL-001` is a naming defect and blocks the relevant gate.

## Authorised operational priority

Until the product and conversion map is frozen, the authorised priority is:

> Build and validate the faithful AXIGNAL Investigation Shell prototype and the complete conversion landing system—product proof, Pricing, FAQ, Trust Center and acquisition instrumentation—without starting unauthorised production-scale data or market expansion.

The product UI and landing MAY advance in parallel because they share the same visual system and because conversion testing requires faithful product proof. Phase-specific production capabilities remain locked until their gates authorise them.