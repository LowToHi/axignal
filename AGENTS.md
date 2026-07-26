# AGENTS.md — ASIGNAL Repository Constitution

## 1. Authority

This file governs every human or automated contributor to `LowToHi/axignal`.

Order of authority:

1. `AGENTS.md`
2. `docs/contracts/00-product-constitution.md`
3. Other normative contracts under `docs/contracts/`
4. Accepted ADRs under `docs/adr/`
5. Task-specific instructions
6. Implementation details

A lower layer may not silently weaken a higher layer.

## 2. Canonical naming

- Public brand: **ASIGNAL**
- Public domain: **asignal.com**
- Repository and technical slug: **axignal**
- Product category: **Global Opportunity Intelligence**

Do not rename the repository slug merely to match the public brand. The distinction is intentional and documented in ADR-001.

## 3. Product boundary

ASIGNAL is an information, research, observation and exploration platform. Initial releases must not:

- execute trades or transactions;
- custody client money or assets;
- manage or rebalance portfolios;
- provide a recommendation presented as personally suitable;
- guarantee returns, outcomes or opportunity materialisation;
- hide uncertainty, contradictions or expired evidence.

## 4. Epistemic authority

AI output is never authoritative by itself.

- Agents may propose candidate claims.
- Deterministic validators decide structural validity.
- Admissibility policies decide whether a claim may enter the canonical ledger.
- Scenario models must expose version, horizon, assumptions and uncertainty.
- Every opportunity must preserve supporting, contradicting and unknown claims.
- Historical failures and retractions must remain auditable.

The canonical rule is:

> The vector discovers; the graph contextualises; the runtime admits.

## 5. Architecture rules

- PostgreSQL is the canonical system of record.
- Embeddings are indexes, never the source of truth.
- Every external source requires a versioned source-admission record.
- Every material transformation must be reproducible or explicitly labelled probabilistic.
- Ingestion, canonicalisation, claim admission, opportunity assembly and presentation must remain separable.
- The frontend must never manufacture authoritative scores.
- Public API contracts are versioned and backward compatibility is deliberate.
- Security, privacy, licensing and regulatory constraints are product requirements, not post-launch checks.

## 6. Delivery rules

- Work contract-first: update the normative contract before implementing a material behavioural change.
- Create an ADR for material architecture, scope, provider, regulatory or data-licensing decisions.
- No feature is production-ready without acceptance evidence.
- No source is production-enabled without rights, rate-limit, provenance and retention fields.
- No universe is marketed as covered before its admission gate passes.
- No model score is shown without calibration evidence and an uncertainty representation.

## 7. Repository structure

```text
apps/                 Product surfaces
services/             Backend services and workers
packages/             Shared libraries and schemas
infra/                Deployment and infrastructure definitions
docs/contracts/       Normative product and engineering contracts
docs/adr/             Architecture decision records
docs/research/        Non-normative research
docs/runbooks/        Operational procedures
schemas/               Machine-readable contracts
openapi/              Public and internal API specifications
```

## 8. Quality gates

At minimum, every implementation PR must report:

- contracts affected;
- tests executed;
- data migrations;
- privacy and licensing impact;
- threat-model impact;
- accessibility impact;
- observability added;
- rollback strategy.

Fail closed when authoritative evidence is missing.

## 9. Documentation language

Normative documents may be written in Spanish while retaining canonical English identifiers for schemas, code and APIs. Ambiguous business language must be replaced by typed definitions.

## 10. Prohibited shortcuts

Do not:

- scrape a source merely because it is publicly viewable;
- treat duplicated syndication as independent corroboration;
- present correlation as causation;
- merge observed, calculated, inferred and predicted claims;
- infer exact real-time freshness from a slow source;
- use a single opaque opportunity score as a substitute for dimensional evidence;
- ship a chatbot as a substitute for the structured product;
- claim legal or financial immunity through disclaimers.
