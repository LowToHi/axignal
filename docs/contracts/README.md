# ASIGNAL Development Contracts

Status: `v0.1-foundation`

These documents are normative specifications for the product, architecture and delivery of ASIGNAL. They are called “contracts” because they define externally testable obligations between product surfaces, data pipelines, epistemic runtime, operators and users. They are not a substitute for legal advice or customer-facing legal terms.

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

## Machine-readable specifications

- [`schemas/claim.schema.json`](../../schemas/claim.schema.json)
- [`schemas/source.schema.json`](../../schemas/source.schema.json)
- [`schemas/opportunity.schema.json`](../../schemas/opportunity.schema.json)
- [`openapi/asignal-v1.yaml`](../../openapi/asignal-v1.yaml)

## Normative language

The terms **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT** and **MAY** express requirement strength.

## Change policy

A material change to scope, authority, data rights, claim semantics, pricing entitlement or public API MUST:

1. update the affected contract;
2. add or amend an ADR;
3. include migration and rollback implications;
4. preserve an auditable version history.

## Foundation status

This version freezes the desired architecture and product rules. It does not claim that the market, pricing or predictive models are already validated. Those remain hypotheses until the corresponding commercial and empirical gates pass.
