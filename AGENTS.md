# AGENTS.md — AXIGNAL Repository Constitution

## 1. Authority

This file governs every human or automated contributor to `LowToHi/axignal`.

Order of authority:

1. explicit current human decision;
2. `docs/roadmap/00-goal-lock.md`;
3. `AGENTS.md`;
4. `docs/contracts/18-development-agent-governance.md`;
5. `docs/contracts/31-global-e2e-development-contract-v1.5.md` after approval and canonical merge;
6. `docs/contracts/00-product-constitution.md`;
7. `docs/contracts/06-security-privacy-regulatory.md`;
8. `docs/contracts/02-epistemic-claims-system.md`;
9. other applicable contracts;
10. accepted ADRs;
11. typed task specification;
12. implementation details.

Contract 30 and ADR-015 remain preserved history. Contract 31 and ADR-016 are normative candidates until approved and merged.

A lower layer may not silently weaken a higher layer.

## 2. Canonical naming and product identity

- Public brand: **AXIGNAL**
- Public domain: **axignal.com**
- Repository and technical slug: **axignal**
- Goal ID: `AXIGNAL-GOAL-001`
- Parent category: **Global Opportunity Intelligence & Operations**
- First commercial shell: **Business-to-Government (B2G) Opportunity Intelligence**
- First acquisition universe: **public contracts and global tenders**

The legacy strings `ASIGNAL`, `asignal.com` and `ASIGNAL-GOAL-001` are active-document defects and MUST fail repository validation.

No individual source, including TED, may define AXIGNAL's product identity.

## 3. Goal Lock and programme chain

Every material task MUST reference `AXIGNAL-GOAL-001` and resolve:

```text
Goal Lock
→ Contract 31
→ active P00–P27 phase
→ typed task
→ governing contracts
→ dynamic skills
→ implementation
→ engineering evidence
→ canonical evidence
→ independent gate decision
```

An agent MUST NOT infer a different product goal from an isolated issue, code module, provider limitation or implementation shortcut.

## 4. Engineering and canonical state

Every status report MUST separate:

```text
engineering progress
≠ canonical acceptance
≠ product admission
≠ commercial availability
≠ public launch
```

Allowed engineering states:

- `NOT_STARTED`;
- `ENGINEERING_IN_PROGRESS`;
- `ENGINEERING_EVIDENCE_READY`;
- `ENGINEERING_E2E_PASS`;
- `ENGINEERING_REJECTED`;
- `SUPERSEDED`.

Allowed canonical states:

- `CANONICAL_NOT_STARTED`;
- `CANONICAL_ACCEPTANCE_BLOCKED`;
- `CANONICALLY_ACCEPTED`;
- `PRODUCT_ADMITTED`;
- `COMMERCIAL`;
- `SUSPENDED`;
- `REVOKED`;
- `REJECTED`.

Code existence or green CI MUST NOT be described as canonical product acceptance.

## 5. Public-launch boundary

AXIGNAL has no partial public-launch state.

Permitted dispositions:

```text
NO_GO
PRIVATE_ACCEPTANCE
ACCEPTED_FOR_PUBLIC_LAUNCH
```

`PRIVATE_ACCEPTANCE` is bounded, contractually explicit and not publicly represented as launch.

The following are prohibited as substitutes for the finished product:

- open public beta;
- bounded public launch;
- unrestricted public signup;
- public paid availability before P27;
- paid media representing an incomplete product as launched.

Only `AX-GE2E-P27-T01` may produce the final public-launch disposition.

## 6. Product boundary

AXIGNAL combines:

```text
Global Opportunity Intelligence
+ Evidence-Governed Investigation
+ Opportunity Operations
```

It MUST support the path:

```text
signals
→ admitted evidence
→ Candidate Claims
→ deterministic admission
→ InvestigationContext
→ Opportunity
→ Pursuit
→ Operational Workspace
→ Outcome
→ Learning
```

AXIGNAL MUST NOT be reduced to:

- a chatbot;
- a tender-alert list;
- a public-data mirror;
- a static dashboard;
- a generic research copilot;
- a claim or dossier generator without operational workflow.

Initial releases MUST NOT:

- execute trades or unrelated transactions;
- custody client money or assets;
- manage or rebalance portfolios;
- guarantee awards, eligibility, returns or opportunity materialisation;
- submit bids or represent customers without a separately approved authority;
- hide uncertainty, contradictions or expired evidence.

## 7. Canonical investigation and operations experience

AXIGNAL combines:

- multilingual Navigator;
- Globe;
- Graph;
- Timeline;
- Claim and Evidence Rail;
- InvestigationContext and Trails;
- Opportunity Operations;
- specialised workspaces;
- private interest memory;
- Knowledge Tides;
- research candidate queue;
- identity, seats and entitlements;
- alerts and public discovery;
- Founder Operations.

Globe and Graph are equal lenses over one shared `InvestigationContext`. Explicit user choice prevails over automatic routing.

## 8. Epistemic authority

AI output is never authoritative by itself.

- Agents may propose Candidate Claims.
- Deterministic validators decide structural validity.
- Admissibility policies decide whether a claim enters the canonical ledger.
- Scenario models expose version, horizon, assumptions and uncertainty.
- Every opportunity preserves supporting, contradicting and unknown claims.
- Historical failures and retractions remain auditable.

Canonical rule:

> The vector discovers; the graph contextualises; the runtime admits.

Models and workers cannot:

- admit sources;
- admit canonical claims;
- grant tenant authority;
- assign seats;
- grant trials;
- publish SEO pages;
- mutate Search Console;
- install MCP connectors;
- authorise public launch.

## 9. Identity, trials and seats

Public identity is passkey-first and server-authoritative.

```text
verified email bootstrap
→ WebAuthn passkey
→ opaque revocable session
→ server-resolved tenant and membership
```

The browser cannot select tenant, role, seat capacity or Founder Admin status.

A trial belongs to a tenant or economic identity, not a browser account.

```text
one tenant
→ one trial grant
→ one seven-day clock
→ two seats
→ one shared token and cost budget
```

The clock begins at first admitted AI use, not signup.

Weak fraud signals cannot independently prove abuse.

Seat capacity is enforced server-side and transactionally:

- trial: 2;
- Professional candidate: 3;
- Team candidate: 15.

## 10. Organic discovery and consent

Programmatic SEO MUST use an `IndexabilityGate`.

```text
dataset ≠ indexable page
generated page ≠ published page
crawlable ≠ indexed
indexed ≠ ranked
traffic ≠ qualified buyer
```

A founder cannot publish a page that has not reached the required governed state.

Tender Alerts require double opt-in and MUST NOT create an account, tenant, seat, trial or paid entitlement.

CRM contacts are not identity or billing authority.

AI-citation observations are not endorsements, rankings, claims or conversion evidence.

## 11. Search Console and MCP boundary

A DNS Search Console verification record is evidence of declared domain verification only.

```text
DNS verification
≠ API access
≠ Search Analytics import
≠ sitemap mutation authority
≠ public indexing approval
```

Every MCP server and tool is deny-by-default.

MCP catalogue presence does not establish:

- exact implementation identity;
- maintainer trust;
- licence;
- security review;
- credential safety;
- production admission.

Search Console MCP probes, if approved, MUST begin read-only. Destructive site, sitemap, user, DNS, credential, shell and arbitrary-browser operations remain denied by default.

## 12. Founder Operations

Founder authority is independent of tenant seats and browser claims.

```text
valid passwordless session
∩ recent AAL2 verification
∩ server allowlist
∩ active founder principal
∩ typed server operation
∩ append-only audit
```

A visible sidebar does not prove operational completeness. Modules without durable authority MUST display `READ_ONLY`, `BLOCKED` or `NOT_IMPLEMENTED`.

P26 is complete only when T01–T04 pass.

## 13. Intent Intelligence boundary

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

## 14. Architecture rules

- PostgreSQL is the canonical system of record.
- Embeddings are indexes, never the source of truth.
- Every external source requires a versioned source-admission record.
- Every external connector and MCP requires independent admission.
- Every material transformation is reproducible or explicitly labelled probabilistic.
- Ingestion, canonicalisation, claim admission, opportunity assembly and presentation remain separable.
- The frontend never manufactures authoritative scores, roles, entitlements, publication state or provider state.
- Public API contracts are versioned and backward compatibility is deliberate.
- Security, privacy, licensing, multilingual semantics, consent and regulatory constraints are product requirements.
- Secrets are referenced, never stored in documentation, code or browser state.

## 15. Dynamic skills

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

## 16. Delivery rules

- Work contract-first.
- Create an ADR for material architecture, product, source, regulatory, privacy, naming or launch decisions.
- No feature is production-ready without acceptance evidence.
- No source is product-enabled without rights, rate-limit, provenance, retention, audit and kill-switch fields.
- No connector or MCP is enabled by catalogue presence.
- No universe is marketed as covered before its admission gate passes.
- No model score is shown without calibration evidence and uncertainty.
- No phase is presented as passed before an independent gate decision.
- No public activation occurs from CI, model, browser or provider events.

## 17. Repository structure

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

## 18. Quality gates

Every material PR MUST report:

- Goal ID, phase and task IDs;
- engineering and canonical state;
- contracts affected;
- skills activated and versions;
- exact head;
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

## 19. Documentation language

Normative documents may be written in Spanish or English while retaining canonical English identifiers for schemas, code and APIs. Ambiguous business language MUST be replaced by typed definitions.

Original-language source evidence MUST remain recoverable.

## 20. Prohibited shortcuts

Do not:

- scrape a source merely because it is publicly viewable;
- treat duplicated syndication as independent corroboration;
- present correlation as causation;
- merge observed, calculated, inferred and predicted claims;
- infer real-time freshness from a slow source;
- use one opaque opportunity score instead of dimensional evidence;
- ship a chatbot as a substitute for the structured product;
- let high user interest create an economic claim;
- implement Globe or Graph as decorative reduced-function views;
- translate only at the end of development;
- claim legal or financial immunity through disclaimers;
- treat a DNS token as API integration;
- install an MCP without security admission;
- claim Founder Operations complete from a sidebar;
- claim launch from green CI;
- rename AXIGNAL or axignal.com.
