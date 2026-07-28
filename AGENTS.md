# AGENTS.md — AXIGNAL Repository Constitution

## 1. Authority

This file governs every human or automated contributor to `LowToHi/axignal`.

Order of authority:

1. explicit current user decision;
2. `docs/roadmap/00-goal-lock.md`;
3. `AGENTS.md`;
4. `docs/contracts/18-development-agent-governance.md`;
5. `docs/contracts/00-product-constitution.md`;
6. `docs/contracts/06-security-privacy-regulatory.md`;
7. `docs/contracts/02-epistemic-claims-system.md`;
8. other applicable contracts;
9. accepted ADRs;
10. typed task specification;
11. implementation details.

A lower layer may not silently weaken a higher layer.

## 2. Canonical naming

- Public brand: **AXIGNAL**
- Public domain: **axignal.com**
- Repository and technical slug: **axignal**
- Goal ID: `AXIGNAL-GOAL-001`
- Product category: **Global Opportunity Intelligence**

The legacy strings `ASIGNAL`, `asignal.com` and `ASIGNAL-GOAL-001` are active-document defects and MUST fail repository validation.

## 3. Goal Lock

Every material task MUST reference `AXIGNAL-GOAL-001` and resolve:

```text
Goal Lock
→ active phase
→ typed task
→ governing contracts
→ dynamic skills
→ implementation
→ evidence
→ independent gate decision
```

An agent MUST NOT infer a different product goal from an isolated issue, code module, provider limitation or implementation shortcut.

## 4. Product boundary

AXIGNAL is an information, research, observation and exploration platform. Initial releases MUST NOT:

- execute trades or transactions;
- custody client money or assets;
- manage or rebalance portfolios;
- provide a recommendation presented as personally suitable;
- guarantee returns, outcomes or opportunity materialisation;
- hide uncertainty, contradictions or expired evidence.

## 5. Canonical investigation experience

AXIGNAL combines:

- multilingual Navigator;
- Globe;
- Graph;
- Timeline;
- Claim and Evidence Rail;
- investigation trails;
- personal interest memory;
- Knowledge Tides;
- research candidate queue.

Globe and Graph are equal lenses over one shared `InvestigationContext`. Explicit user choice prevails over automatic routing.

## 6. Epistemic authority

AI output is never authoritative by itself.

- Agents may propose candidate claims.
- Deterministic validators decide structural validity.
- Admissibility policies decide whether a claim enters the canonical ledger.
- Scenario models expose version, horizon, assumptions and uncertainty.
- Every opportunity preserves supporting, contradicting and unknown claims.
- Historical failures and retractions remain auditable.

Canonical rule:

> The vector discovers; the graph contextualises; the runtime admits.

## 7. Intent Intelligence boundary

The following are separate bounded contexts:

```text
user message and intent
≠ private preference
≠ aggregate Knowledge Tide
≠ research candidate
≠ evidence
≠ admitted claim
≠ opportunity
≠ scenario
≠ outcome
```

User attention may determine what to investigate. It MUST NOT prove that an economic opportunity exists.

## 8. Architecture rules

- PostgreSQL is the canonical system of record.
- Embeddings are indexes, never the source of truth.
- Every external source requires a versioned source-admission record.
- Every material transformation is reproducible or explicitly labelled probabilistic.
- Ingestion, canonicalisation, claim admission, opportunity assembly and presentation remain separable.
- The frontend never manufactures authoritative scores.
- Public API contracts are versioned and backward compatibility is deliberate.
- Security, privacy, licensing, multilingual semantics and regulatory constraints are product requirements.

## 9. Dynamic skills

Every task MUST activate skills from `skills/registry.yaml`.

Always-on skills:

- `goal-keeper`;
- `contract-router`;
- `task-orchestrator`;
- `gate-evaluator`;
- `naming-guardian`;
- `security-reviewer`;
- `privacy-reviewer`;
- `observability-engineer`.

A missing required skill results in `BLOCKED`.

## 10. Delivery rules

- Work contract-first.
- Create an ADR for material architecture, product, source, regulatory, privacy or naming decisions.
- No feature is production-ready without acceptance evidence.
- No source is production-enabled without rights, rate-limit, provenance, retention and kill-switch fields.
- No universe is marketed as covered before its admission gate passes.
- No model score is shown without calibration evidence and uncertainty.
- No phase is presented as passed before an independent gate decision.

## 11. Repository structure

```text
apps/                 Product surfaces
services/             Backend services and workers
packages/             Shared libraries and schemas
infra/                Deployment and infrastructure definitions
docs/contracts/       Normative product and engineering contracts
docs/roadmap/         Goal, phases, tasks, contracts, skills and gates
docs/adr/             Architecture decision records
docs/research/        Non-normative research
docs/flows/           User and system flows
docs/prototypes/      Non-production validation artifacts
docs/runbooks/        Operational procedures
schemas/              Machine-readable contracts
skills/               Dynamic skill registry and contracts
openapi/              Public and internal API specifications
```

## 12. Quality gates

Every material PR MUST report:

- Goal ID, phase and task IDs;
- contracts affected;
- skills activated and versions;
- tests and evidence;
- data migrations;
- privacy and licensing impact;
- threat-model impact;
- multilingual impact;
- accessibility impact;
- observability added;
- rollback or kill switch;
- known limitations;
- only authorised next priority.

Fail closed when authoritative evidence is missing.

## 13. Documentation language

Normative documents may be written in Spanish or English while retaining canonical English identifiers for schemas, code and APIs. Ambiguous business language MUST be replaced by typed definitions.

Original-language source evidence MUST remain recoverable.

## 14. Prohibited shortcuts

Do not:

- scrape a source merely because it is publicly viewable;
- treat duplicated syndication as independent corroboration;
- present correlation as causation;
- merge observed, calculated, inferred and predicted claims;
- infer real-time freshness from a slow source;
- use one opaque opportunity score instead of dimensional evidence;
- ship a chatbot as a substitute for the structured product;
- let high user interest create an economic claim;
- implement Globe or Graph as a decorative reduced-function view;
- translate only at the end of development;
- claim legal or financial immunity through disclaimers;
- rename AXIGNAL or axignal.com.
