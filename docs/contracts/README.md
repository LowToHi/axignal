# AXIGNAL Development Contracts

Status: `v0.3-roadmap-candidate`
Goal ID: `AXIGNAL-GOAL-001`

These documents are normative specifications for the product, architecture and delivery of AXIGNAL. They define externally testable obligations between product surfaces, data pipelines, epistemic runtime, operators, agents and users. They are not a substitute for jurisdiction-specific legal advice or customer-facing legal terms.

## Contract set

| Contract | Purpose |
|---|---|
| [00 — Product Constitution](00-product-constitution.md) | Mission, boundaries, users, non-goals and product invariants |
| [01 — Business Model and Pricing](01-business-model-and-pricing.md) | Buyer, value, packaging, pricing hypotheses and commercial gates |
| [02 — Epistemic Claims System](02-epistemic-claims-system.md) | Claim ontology, provenance, admission, contradiction and scoring |
| [03 — Data Sources and APIs](03-data-sources-and-apis.md) | Source admission, licensing, ingestion and initial source universe |
| [04 — System Architecture](04-system-architecture.md) | Stack, components, storage, eventing, deployment and boundaries |
| [05 — UI and UX Exploration](05-ui-ux-exploration.md) | Globe, graph, time machine, claims, accessibility and navigation |
| [06 — Security, Privacy and Regulatory Boundary](06-security-privacy-regulatory.md) | Threat model, privacy, financial-information boundary and controls |
| [07 — Product API](07-product-api.md) | Resource model, endpoints, versioning, entitlements and errors |
| [08 — Quality, Observability and Gates](08-quality-observability-gates.md) | SLOs, data quality, model calibration, release and universe gates |
| [09 — Delivery and Acceptance](09-delivery-and-acceptance.md) | Build sequence, milestones, acceptance evidence and definition of done |
| [10 — Documentation and Operations](10-documentation-and-operations.md) | Required docs, runbooks, ADRs, incidents and change control |
| [11 — Product Hypothesis Register](11-hypothesis-register.md) | Buyer, pricing, wedge, regulatory and defensibility hypotheses with falsification rules |
| [12 — Interaction Model](12-interaction-model.md) | Investigation shell, shared context, lenses and time-machine behaviour |
| [13 — Visualisation Grammar](13-visualisation-grammar.md) | Shared semantics for heat, claims, contradiction, graph, time and missing coverage |
| [14 — Conversational Navigation](14-conversational-navigation.md) | Navigator commands, explanation, visible interpretation and lens routing |
| [15 — Intent Intelligence](15-intent-intelligence.md) | Private interest memory, Knowledge Tides and privacy-preserving aggregation |
| [16 — Multilingual Semantic System](16-multilingual-semantic-system.md) | Six-language semantics, translation provenance, aliases and locale behaviour |
| [17 — Research Candidate Queue](17-research-candidate-queue.md) | Coverage gaps, tide-driven research, prioritisation and admission handoff |
| [18 — Development Agent Governance](18-development-agent-governance.md) | Goal Lock, phases, tasks, dynamic skills, evidence and fail-closed gates |

Contracts 12–18 remain normative candidates until their applicable phase gates pass.

## Roadmap and execution

- [`docs/roadmap/README.md`](../roadmap/README.md)
- [`docs/roadmap/00-goal-lock.md`](../roadmap/00-goal-lock.md)
- [`docs/roadmap/01-phase-map.md`](../roadmap/01-phase-map.md)
- [`docs/roadmap/02-task-catalogue.md`](../roadmap/02-task-catalogue.md)
- [`docs/roadmap/03-contract-map.md`](../roadmap/03-contract-map.md)
- [`docs/roadmap/04-dynamic-skill-map.md`](../roadmap/04-dynamic-skill-map.md)
- [`docs/roadmap/05-dependency-and-gates.md`](../roadmap/05-dependency-and-gates.md)

## UX research and prototype

- [`docs/research/ux-competitive-benchmark.md`](../research/ux-competitive-benchmark.md)
- [`docs/research/buyer-workflows.md`](../research/buyer-workflows.md)
- [`docs/research/prototype-test-plan.md`](../research/prototype-test-plan.md)
- [`docs/flows/global-discovery-flow.md`](../flows/global-discovery-flow.md)
- [`docs/prototypes/globe-opportunity-claims-v0.1.html`](../prototypes/globe-opportunity-claims-v0.1.html)

## Machine-readable specifications

- [`schemas/claim.schema.json`](../../schemas/claim.schema.json)
- [`schemas/source.schema.json`](../../schemas/source.schema.json)
- [`schemas/opportunity.schema.json`](../../schemas/opportunity.schema.json)
- [`schemas/task.schema.json`](../../schemas/task.schema.json)
- [`schemas/skill.schema.json`](../../schemas/skill.schema.json)
- [`schemas/investigation-context.schema.json`](../../schemas/investigation-context.schema.json)
- [`schemas/command-plan.schema.json`](../../schemas/command-plan.schema.json)
- [`schemas/user-intent-event.schema.json`](../../schemas/user-intent-event.schema.json)
- [`schemas/preference-profile.schema.json`](../../schemas/preference-profile.schema.json)
- [`schemas/aggregate-intent-signal.schema.json`](../../schemas/aggregate-intent-signal.schema.json)
- [`schemas/research-candidate.schema.json`](../../schemas/research-candidate.schema.json)
- [`openapi/axignal-v1.yaml`](../../openapi/axignal-v1.yaml)
- [`skills/registry.yaml`](../../skills/registry.yaml)

## Canonical identity

- Brand: **AXIGNAL**
- Domain: **axignal.com**
- Repository: `LowToHi/axignal`
- Goal ID: `AXIGNAL-GOAL-001`

The strings `ASIGNAL`, `asignal.com` and `ASIGNAL-GOAL-001` are forbidden in active artifacts.

## Normative language

The terms **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT** and **MAY** express requirement strength.

## Change policy

A material change to scope, authority, data rights, claim semantics, pricing entitlement, user-intent use, multilingual semantics, agent governance or public API MUST:

1. update the affected contract;
2. add or amend an ADR;
3. update roadmap tasks, skills and gates;
4. include migration and rollback implications;
5. preserve an auditable version history.

## Foundation status

The foundation freezes the desired architecture and product rules. Buyer, pricing, predictive models, initial universe and final interaction architecture remain hypotheses until their commercial, empirical and usability gates pass.
