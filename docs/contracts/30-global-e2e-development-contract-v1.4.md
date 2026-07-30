# 30 — AXIGNAL Global E2E Development Contract v1.4

Version: `1.4.0`
Status: `NORMATIVE CANDIDATE / NO PUBLIC LAUNCH`
Goal ID: `AXIGNAL-GOAL-001`
Baseline: `main@9ee3e12620f137208c1943a05501f2671a1f4817`
Decision record: `ADR-015`

## 1. Purpose

This contract governs the completion of AXIGNAL as a finished global product before public commercial launch.

AXIGNAL is:

> **A global opportunity-intelligence and opportunity-operations platform. It detects signals, connects governed evidence, helps professional teams decide which opportunities deserve attention and provides the workspace in which those teams manage each pursuit through its outcome and learning.**

The required product architecture is:

```text
GLOBAL OPPORTUNITY INTELLIGENCE
+ EVIDENCE-GOVERNED INVESTIGATION
+ OPPORTUNITY OPERATIONS
```

A product that stops at filtered information, Candidate Claims, dossiers or recommendations is incomplete.

## 2. No-partial-launch rule

AXIGNAL MUST NOT enter public commercial launch, general availability or unrestricted live billing while any critical P00–P24 gate is missing.

Permitted before the launch gate:

- internal development and CI;
- synthetic and sandbox tests;
- private demos labelled as incomplete;
- controlled research sessions;
- contractually bounded Design Partners;
- source-specific technical probes;
- private acceptance environments.

Not permitted before `P24 = ACCEPTED_FOR_PUBLIC_LAUNCH`:

- public availability represented as a finished product;
- unsupported global-coverage claims;
- public self-service live charging;
- marketing of a library that has not reached its commercial gate;
- claims that a workflow is end-to-end when execution leaves AXIGNAL;
- silent reduction of this contract's library or workspace scope.

A scope reduction requires an approved superseding contract and ADR.

## 3. Product layers

### 3.1 AXIGNAL Core

- authenticated identity and organisations;
- server-resolved tenant;
- Navigator;
- persistent ResearchRun;
- InvestigationContext;
- Evidence Objects;
- Candidate Claims;
- independent deterministic admission;
- Claim Ledger;
- human review;
- Globe;
- Graph;
- Timeline;
- dossiers;
- alerts;
- entitlements;
- audit.

### 3.2 Foundational libraries

AXIGNAL MUST implement:

| ID | Library |
|---|---|
| `AX-LIB-F01` | Jurisdiction and geography |
| `AX-LIB-F02` | Entities, organisations and ownership |
| `AX-LIB-F03` | Taxonomies and classifications |
| `AX-LIB-F04` | Time, currency, value and units |
| `AX-LIB-F05` | Languages, terminology and translation |
| `AX-LIB-F06` | Source rights and provenance |
| `AX-LIB-F07` | Documents and content |

These libraries MUST be versioned, source-aware, reversible and shared across all opportunity libraries.

### 3.3 Opportunity libraries

AXIGNAL MUST implement:

| ID | Library | Operational workspace |
|---|---|---|
| `AX-LIB-O01` | Global Public Procurement | Bid Workspace |
| `AX-LIB-O02` | Grants and Non-Dilutive Funding | Application Workspace |
| `AX-LIB-O03` | Regulatory and Policy Demand | Market Entry and Compliance Opportunity Workspace |
| `AX-LIB-O04` | Infrastructure and Capital Projects | Project Pursuit Workspace |
| `AX-LIB-O05` | Corporate, Filings and Ownership Signals | Account Opportunity Workspace |
| `AX-LIB-O06` | Sovereign, Macro and Public Investment | Country and Market Strategy Workspace |
| `AX-LIB-O07` | Trade, Supply Chain and Market Flows | Supply Opportunity Workspace |
| `AX-LIB-O08` | Energy and Climate Transition | Transition Opportunity Workspace |
| `AX-LIB-O09` | Innovation, Research and Intellectual Property | Innovation Opportunity Workspace |

Every library MUST have independent rights, quality, lifecycle, privacy, entitlement, observability, disclosure and rollback gates.

## 4. Library and source states

```text
DISCOVERED
→ LEGAL_REVIEW
→ TECHNICAL_PROBE
→ EVIDENCE_READY
→ PRODUCT_ADMITTED
→ PRIVATE_ACCEPTANCE
→ COMMERCIAL
```

Terminal or protective states:

```text
RESTRICTED
SUSPENDED
REVOKED
REJECTED
```

A catalogue entry is research evidence, not product availability.

By P24, every source family in an active catalogue MUST have a recorded disposition:

- `COMMERCIAL`;
- `RESTRICTED` with an approved user-visible limitation;
- `REJECTED` with evidence and an approved coverage consequence;
- `REVOKED` or `SUSPENDED` with the affected product claims quarantined.

It is not necessary to ingest every discovered source, but no source may remain ambiguously represented as supported.

## 5. Foundational-library requirements

### F01 — Jurisdiction and geography

MUST support countries, territories, administrative levels, places of performance, coordinates, versioned geometries, historical changes, multilingual names and source-native regional identifiers.

### F02 — Entities and ownership

MUST preserve legal identifiers, buyers, suppliers, public bodies, companies, aliases, historical names, parent/subsidiary relationships and time-bounded ownership. Observed and inferred relationships MUST remain distinct.

### F03 — Taxonomies

MUST support source-native and versioned classifications including CPV, NUTS, NAICS, PSC, NACE, ISIC, HS, SITC, CPC and admitted national catalogues. Crosswalks are reversible many-to-many proposals until admitted.

### F04 — Time, currency, value and units

MUST separate publication, observation, validity and effective dates; preserve currency and tax semantics; version FX conversions; preserve intervals and uncertainty; and never convert unknown into zero.

### F05 — Languages and terminology

MUST preserve original-language evidence and provide provenance-bearing translation, transliteration, aliases and terminology. Initial launch languages are English, Spanish, French, German, Portuguese and Italian.

### F06 — Rights and provenance

MUST record owner, endpoint, licence, terms, authentication, rate limits, commercial use, redistribution, personal-data scope, attribution, retention, revocation and review date. Scraping is never presumed lawful.

### F07 — Documents and content

MUST govern HTML, XML, JSON, CSV, PDF, scanned PDF, DOCX, XLSX, images, archives, XBRL, SDMX, OCDS and eForms through acquisition, hash, malware/type checks, rights, extraction/OCR, anchors, evidence references and admission.

## 6. Opportunity Operations

The horizontal operating model is:

```text
Opportunity
→ Pursuit
→ Decision
→ Workspace
→ Requirements
→ Tasks and Milestones
→ Documents
→ Review and Approval
→ Submission or Activation Record
→ Outcome
→ Learning
```

Required shared entities:

- `Opportunity`;
- `Pursuit`;
- `Decision`;
- `Requirement`;
- `WorkItem`;
- `Milestone`;
- `Document`;
- `Comment`;
- `Approval`;
- `Submission`;
- `Outcome`;
- `Learning`;
- `ActivityEvent`;
- `Template`.

All operational state is tenant-private and MUST NOT mutate the canonical Claim Ledger.

The platform MUST create retention through useful accumulated work, collaboration, evidence and learning—not by blocking export or cancellation.

## 7. Opportunity-library minimums

### O01 — Global Public Procurement

MUST resolve the worldwide procurement catalogue, beginning with the existing v0.2 inventory of 146 source families across 140 jurisdiction/government scopes. It MUST support notices, lots, buyers, suppliers, documents, corrections, cancellations, awards, contracts, frameworks, values, deadlines, classifications, lifecycle and explainable relevance.

The Bid Workspace MUST support pipeline, bid/no-bid, requirements matrix, tasks, documents, approvals, submission record, clarifications, award and win/loss learning.

### O02 — Grants and Non-Dilutive Funding

MUST support calls, programmes, topics, eligibility evidence, beneficiaries, budgets, co-financing, deadlines, consortium requirements, previous awards, project results and amendments.

The Application Workspace MUST support eligibility review, consortium, work packages, budget, tasks, evidence, approvals, submission and outcome.

### O03 — Regulatory and Policy Demand

MUST support proposal-to-effective lineage, consultations, amendments, obligations, affected sectors, effective dates, repeals and official guidance. AXIGNAL MUST NOT provide legal advice or declare compliance.

### O04 — Infrastructure and Capital Projects

MUST support project pipelines, sponsors, financiers, geography, procurement packages, milestones, environmental documents, contractors, status and delays.

### O05 — Corporate, Filings and Ownership Signals

MUST support official filings, XBRL facts, corporate events, capex, segments, acquisitions, ownership, subsidiaries, contracts and strategy signals with filing-level traceability.

### O06 — Sovereign, Macro and Public Investment

MUST preserve dataset vintages and revisions and separate observations, estimates and forecasts across macroeconomic, fiscal, demographic, credit, trade and public-investment data.

### O07 — Trade, Supply Chain and Market Flows

MUST support bilateral flows, products, tariffs, services, origin/destination, classifications, dependencies, concentration, trade measures and revisions.

### O08 — Energy and Climate Transition

MUST support generation, demand, capacity, projects, grids, fuels, prices, flows, emissions, policy targets, climate hazards and uncertainty without investment-performance claims.

### O09 — Innovation, Research and Intellectual Property

MUST support patents, families, legal status, applicants/assignees, classifications, citations, research projects, organisations, collaborations and results without patentability or freedom-to-operate legal conclusions.

## 8. Global-coverage gate

AXIGNAL MAY use “global” publicly only when:

1. O01–O09 are implemented and accepted;
2. admitted coverage exists in Europe, North America, Latin America, Asia, Oceania and Africa;
3. coverage and gaps are visible;
4. source-native identifiers, taxonomies, currencies and languages are preserved;
5. every library has a multinational E2E;
6. cross-library queries preserve authority and provenance;
7. unavailable sources contribute no claims;
8. rights and revocation are independently enforceable.

## 9. Development programme

The active programme is P00–P24:

| Phase | Outcome |
|---|---|
| P00 | Contract integration and canonical synchronisation |
| P01 | Global buyer, workflow and market evidence |
| P02 | Global ontology and library contracts |
| P03 | Security, identity and rights by design |
| P04 | Source Admission Factory and Connector SDK |
| P05 | Foundational libraries |
| P06 | Multilingual and Document Intelligence |
| P07 | Opportunity Operations Core |
| P08 | Global Procurement and Bid Workspace |
| P09 | Grants and Application Workspace |
| P10 | Regulatory and Market Entry Workspace |
| P11 | Infrastructure and Project Pursuit Workspace |
| P12 | Corporate and Account Opportunity Workspace |
| P13 | Sovereign/Macro and Strategy Workspace |
| P14 | Trade/Supply and Supply Opportunity Workspace |
| P15 | Energy/Climate and Transition Workspace |
| P16 | Innovation/IP and Innovation Workspace |
| P17 | Cross-library intelligence |
| P18 | Intent Intelligence and Knowledge Tides |
| P19 | Scenarios, calibration and outcomes |
| P20 | Enterprise, API, private data and integrations |
| P21 | Commercial runtime, pricing and Stripe |
| P22 | Production, SLO, disaster recovery, security and legal |
| P23 | Final UX, landing, copy and marketing |
| P24 | Global acceptance and public-launch gate |

P08–P16 MAY execute in parallel only after P02–P07 provide the required contracts and shared runtime.

## 10. Commercial architecture

Candidate packaging remains evidence-dependent:

- Professional: `€349–€499/month`;
- Team: `€899–€1,499/month`;
- Enterprise: from `€18,000/year`;
- additional-library packaging to be validated.

Paid plans MUST NOT impose a monthly AI-token quota or token-overage billing. Capacity is governed through users, workspaces, documents, concurrency, source rights, exports and operational limits.

The operating target is a reproducible route to:

```text
floor   20,000 EUR MRR
goal    25,000 EUR MRR
safety  30,000 EUR MRR
```

No price becomes public-current before paid, retention and margin evidence.

## 11. Evidence requirements

Every phase and library MUST provide applicable:

- schema evidence;
- deterministic tests;
- live-source bounded tests;
- rights records;
- security review;
- privacy review;
- multilingual evidence;
- performance and cost metrics;
- user research;
- paid evidence;
- restore and rollback evidence;
- user-visible coverage disclosure.

A task is not accepted because code exists.

## 12. Launch gate

P24 may return only:

```text
ACCEPTED_FOR_PUBLIC_LAUNCH
IN_PROGRESS
REJECTED
```

There is no `PARTIAL_LAUNCH`.

Public launch requires:

- P00–P24 accepted;
- seven foundational libraries accepted;
- nine opportunity libraries accepted;
- all operational workspaces accepted;
- cross-library E2E accepted;
- multilingual and accessibility accepted;
- Stripe external sandbox and live-boundary review accepted;
- global rollback accepted;
- paid use, retention and gross margin accepted;
- disaster recovery accepted;
- zero critical security findings;
- truthful copy and coverage disclosure.

## 13. Supersession

This contract supersedes:

- the active development ordering in roadmap F0–F12;
- ADR-013's requirement to postpone global source implementation until after a narrow procurement commercial launch;
- Contract 28 where it treats global procurement expansion as a post-launch programme;
- any v1.0–v1.3 chat or document sequence that permits a partial product launch.

It preserves as evidence and subordinate capability contracts:

- the Goal Lock;
- Contracts 00–29;
- ADR-012's evidence that procurement is the first implementation wedge;
- ADR-013's procurement pricing, trial and source-specific admission rules;
- ADR-014's bounded-AI and token-entitlement rules;
- all accepted technical evidence.

## 14. Migration

P00 changes governance artifacts, schemas and registries only. It MUST NOT:

- enable a new source;
- change a source to `PRODUCT_ADMITTED`;
- enable public billing;
- change live entitlements;
- activate global marketing claims;
- mutate customer or canonical claim data.

## 15. Rollback

If v1.4 is rejected or superseded:

- retain the contract and ADR as audit history;
- restore the prior active roadmap through a new recorded decision;
- leave all candidate libraries and sources disabled;
- preserve existing accepted technical evidence;
- do not delete task, source or gate history;
- keep public launch and unsupported global claims blocked.
