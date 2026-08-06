# AXIGNAL Development Contracts

Status: `v1.5-global-e2e-candidate / HUMAN APPROVAL REQUIRED / NO PUBLIC LAUNCH`
Goal ID: `AXIGNAL-GOAL-001`
Canonical baseline: `main@b9a08a2a07d04d635164e161d1b27a7a53df8575`
Engineering-stack candidate: `e1e4999ecd1a7140d9b18ea4b5ad6f0a20e32073`

These documents are normative specifications for AXIGNAL.

Contract 31 is the candidate active programme authority. It extends the finished-global-product decision through P27, separates engineering evidence from canonical acceptance, makes P24 an acceptance framework, requires P25 and P26, and assigns final public-launch authority only to P27.

Contract 30 and ADR-015 remain preserved as audit history. Contracts 00–30 remain applicable capability contracts where they do not weaken or contradict Contract 31.

## Contract set

| Contract | Purpose |
|---|---|
| [00 — Product Constitution](00-product-constitution.md) | Mission, product identity, B2G shell and invariants |
| [01 — Business Model and Pricing](01-business-model-and-pricing.md) | Buyer, value, pricing and commercial evidence |
| [02 — Epistemic Claims System](02-epistemic-claims-system.md) | Claims, provenance, admission and contradiction |
| [03 — Data Sources and APIs](03-data-sources-and-apis.md) | Source admission and rights |
| [04 — System Architecture](04-system-architecture.md) | Components, storage and deployment |
| [05 — UI and UX Exploration](05-ui-ux-exploration.md) | Core experience |
| [06 — Security, Privacy and Regulatory Boundary](06-security-privacy-regulatory.md) | Threat, privacy and regulatory controls |
| [07 — Product API](07-product-api.md) | API resources and entitlements |
| [08 — Quality, Observability and Gates](08-quality-observability-gates.md) | Quality and release evidence |
| [09 — Delivery and Acceptance](09-delivery-and-acceptance.md) | Delivery and definition of done |
| [10 — Documentation and Operations](10-documentation-and-operations.md) | Runbooks, incidents and change control |
| [11 — Product Hypothesis Register](11-hypothesis-register.md) | Falsifiable hypotheses |
| [12 — Interaction Model](12-interaction-model.md) | InvestigationContext and lenses |
| [13 — Visualisation Grammar](13-visualisation-grammar.md) | Globe, Graph, Timeline and evidence semantics |
| [14 — Conversational Navigation](14-conversational-navigation.md) | Navigator |
| [15 — Intent Intelligence](15-intent-intelligence.md) | Knowledge Tides |
| [16 — Multilingual Semantic System](16-multilingual-semantic-system.md) | Multilingual evidence and UX |
| [17 — Research Candidate Queue](17-research-candidate-queue.md) | Research prioritisation |
| [18 — Development Agent Governance](18-development-agent-governance.md) | Goal, task, skill and gate discipline |
| [19 — Technology Stack and CI](19-technology-stack-and-ci.md) | Stack and secure CI |
| [20 — Design System and Motion](20-design-system-and-motion.md) | Product and landing system |
| [21 — Marketing Site and Conversion](21-marketing-site-and-conversion.md) | B2G landing, public surfaces and conversion |
| [22 — Packaging, Pricing and Entitlements](22-packaging-pricing-and-entitlements.md) | Candidate plans, seats, trial and economics |
| [23 — Acquisition Analytics and Experimentation](23-acquisition-analytics-and-experimentation.md) | Funnel and experiments |
| [24 — Trust Center and Public Methodology](24-trust-center-and-public-methodology.md) | Public trust surfaces |
| [25 — Navigator Research and Retrieval](25-navigator-research-and-retrieval.md) | ResearchRun and dossiers |
| [26 — Private Knowledge and Tenant Memory](26-private-knowledge-and-tenant-memory.md) | Private knowledge |
| [27 — Local Research Worker and Candidate Claim Pipeline](27-local-research-worker-candidate-claim-pipeline.md) | Proposal and admission handoff |
| [28 — B2G Procurement Commercial and Global Source Program](28-b2g-procurement-commercial-and-global-source-program.md) | Procurement-specific commercial and source rules retained where compatible |
| [29 — Bounded AI Assistance and Token Entitlements](29-bounded-ai-assistance-and-token-entitlements.md) | AI scope and token semantics |
| [30 — Global E2E Development Contract v1.4](30-global-e2e-development-contract-v1.4.md) | Preserved P00–P24 historical programme authority |
| [31 — Global E2E Development Contract v1.5](31-global-e2e-development-contract-v1.5.md) | Candidate P00–P27 authority, P25/P26 integration and P27 final launch gate |

## Authority order

```text
explicit human decision
→ Goal Lock
→ AGENTS.md
→ Contract 18
→ Contract 31
→ applicable capability contracts
→ accepted ADRs
→ typed task
→ implementation
```

A lower layer may not silently weaken a higher layer.

## Active candidate programme

- [`docs/roadmap/15-global-e2e-development-program-v1.5.md`](../roadmap/15-global-e2e-development-program-v1.5.md)
- [`ADR-016`](../adr/ADR-016-v1-5-canonical-programme-and-final-launch-gate.md)
- [`data/programmes/global-e2e-canonical-state.v1.5.json`](../../data/programmes/global-e2e-canonical-state.v1.5.json)
- [`data/programmes/global-e2e-task-registry.v1.5.json`](../../data/programmes/global-e2e-task-registry.v1.5.json)
- [`data/growth/google-search-console-integration.v0.1.json`](../../data/growth/google-search-console-integration.v0.1.json)

## Current truth

```text
main                           P00 accepted / P01 in progress
engineering stack              P02–P26 evidence present in stacked drafts
P25-T01                        engineering E2E pass / public signup blocked
P26-T01                        engineering E2E pass / phase still in progress
P27                            not started
public launch                  NO_GO
```

## Supersession

Contract 31 supersedes conflicting programme order, P24 final-launch authority, bounded-public-launch interpretations, stale pricing authority and any statement that engineering code alone constitutes accepted product state.

It does not erase:

- Contract 30;
- ADR-015;
- accepted technical evidence;
- source-specific safety rules;
- phase PRs and CI records;
- rollback history;
- negative market evidence;
- financial, security or audit ledgers.

## Machine-readable policy

- [`config/ai-assistance-policy.v0.1.json`](../../config/ai-assistance-policy.v0.1.json) — disabled-by-default AXIGNAL-only AI policy governed by Contract 29 and ADR-014.
- [`schemas/global-e2e-v1.5-task.schema.json`](../../schemas/global-e2e-v1.5-task.schema.json) — dual engineering/canonical state for P25–P27 tasks.

## Canonical identity

- AXIGNAL
- axignal.com
- `LowToHi/axignal`
- `AXIGNAL-GOAL-001`
- Parent category: `Global Opportunity Intelligence & Operations`
- First commercial shell: `Business-to-Government Opportunity Intelligence`
