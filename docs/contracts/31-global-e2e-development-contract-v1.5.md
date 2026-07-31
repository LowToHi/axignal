# 31 — AXIGNAL Global E2E Development Contract v1.5

Version: `1.5.0`
Status: `NORMATIVE CANDIDATE / HUMAN APPROVAL REQUIRED / NO PUBLIC LAUNCH`
Goal ID: `AXIGNAL-GOAL-001`
Date: `2026-07-31`
Canonical repository baseline: `main@b9a08a2a07d04d635164e161d1b27a7a53df8575`
Engineering-stack candidate: `e1e4999ecd1a7140d9b18ea4b5ad6f0a20e32073`
Human authority: `Rafael López`
Decision record: `ADR-016`
Supersedes: Contract `30` as active programme authority and conflicting portions of Contracts `00`, `01`, `21`, `22`, `23`, `24`, ADR-015 and P24 launch-mode interpretations.
Preserves: accepted evidence, immutable ledgers, rollback records, source-specific safety rules and historical contracts as audit history.

---

## 0. Authority and interpretation

### 0.1 Binding decision

AXIGNAL MUST NOT be represented as a finished, generally available or publicly launched commercial product until the exact final repository head passes `P27` and the human authority approves the resulting acceptance-manifest digest.

Before P27, AXIGNAL MAY conduct:

- internal development and CI;
- synthetic, fixture, sandbox and disposable-environment tests;
- private demonstrations labelled with their actual maturity;
- controlled buyer research;
- contractually bounded Design Partner or private paid-acceptance work;
- source-specific technical probes;
- private security, operational and product acceptance.

Before P27, AXIGNAL MUST NOT conduct:

- unrestricted public signup;
- open public paid availability;
- paid media representing AXIGNAL as launched;
- unsupported global-coverage claims;
- publication of a library that has not reached its commercial gate;
- silent conversion from trial to paid;
- general live Stripe charging;
- a public launch under a reduced product definition;
- use of `end-to-end` for workflows that materially terminate outside AXIGNAL;
- presentation of engineering evidence as canonical product acceptance.

### 0.2 No silent scope reduction

AXIGNAL is governed as a finished global product programme. A narrower product may be researched or privately demonstrated, but it cannot replace the contracted finished product without:

1. an explicit human decision;
2. a superseding contract;
3. a new ADR;
4. migration and rollback analysis;
5. preservation of prior evidence and negative findings.

### 0.3 No partial public launch

The only commercial dispositions are:

```text
NO_GO
PRIVATE_ACCEPTANCE
ACCEPTED_FOR_PUBLIC_LAUNCH
```

`PRIVATE_ACCEPTANCE` means explicitly admitted organisations operating under controlled terms. It is not a public launch, public beta, open signup or general availability.

The following prior P24 label is superseded and prohibited as a launch authority:

```text
BOUNDED_PUBLIC_LAUNCH
```

---

## 1. Canonical definition of AXIGNAL

> **AXIGNAL is a global opportunity-intelligence and opportunity-operations platform. It detects signals, connects governed evidence, helps professional teams decide which opportunities deserve attention, and provides the workspace in which those teams manage each pursuit through its outcome and learning.**

The product requires three inseparable layers:

```text
GLOBAL OPPORTUNITY INTELLIGENCE
+ EVIDENCE-GOVERNED INVESTIGATION
+ OPPORTUNITY OPERATIONS
```

A product that stops at search results, alerts, Candidate Claims, dossiers, model recommendations or a conversational answer is incomplete.

### 1.1 Value chain

```text
GLOBAL SIGNALS
→ SOURCE-ADMITTED EVIDENCE
→ CANDIDATE CLAIMS
→ DETERMINISTIC ADMISSION
→ INVESTIGATION CONTEXT
→ OPPORTUNITY
→ PURSUIT
→ OPERATIONAL WORKSPACE
→ OUTCOME
→ LEARNING
```

### 1.2 Public product identity and first commercial shell

Parent product identity:

> **AXIGNAL — Global Opportunity Intelligence & Operations**

First commercial shell:

> **Business-to-Government (B2G) Opportunity Intelligence**

First acquisition universe:

> **Public contracts and global tenders**

The relationship is:

```text
AXIGNAL parent product
→ B2G commercial shell
→ public-contract and tender wedge
→ admitted procurement libraries
```

No individual source, including TED, defines the product identity.

### 1.3 B2G message boundary

The initial B2G shell MUST communicate:

- public contracts and tenders;
- Business-to-Government teams and workflows;
- qualification rather than raw-alert volume;
- buyer, award, supplier, company and ownership context;
- traceable evidence and visible uncertainty;
- human bid/no-bid authority;
- source and coverage limitations.

It MUST NOT claim:

- guaranteed eligibility;
- guaranteed awards or win rate;
- complete global coverage;
- legal advice;
- autonomous bid decisions;
- public availability before P27.

---

## 2. Two-dimensional programme state

AXIGNAL MUST distinguish engineering progress from canonical acceptance.

### 2.1 Engineering states

```text
NOT_STARTED
ENGINEERING_IN_PROGRESS
ENGINEERING_EVIDENCE_READY
ENGINEERING_E2E_PASS
ENGINEERING_REJECTED
SUPERSEDED
```

### 2.2 Canonical states

```text
CANONICAL_NOT_STARTED
CANONICAL_ACCEPTANCE_BLOCKED
CANONICALLY_ACCEPTED
PRODUCT_ADMITTED
COMMERCIAL
SUSPENDED
REVOKED
REJECTED
```

### 2.3 Governing rule

```text
code exists
≠ engineering evidence ready
≠ canonical acceptance
≠ product admission
≠ commercial availability
≠ public launch
```

A later phase MAY be developed as bounded engineering when its structural contracts are frozen. It MUST NOT be canonically accepted, product-admitted, commercially activated or represented as available while critical dependencies remain unresolved.

### 2.4 Repository truth

The repository currently has two legitimate reference points:

```text
canonical main
= main@b9a08a2a07d04d635164e161d1b27a7a53df8575

engineering stack candidate
= e1e4999ecd1a7140d9b18ea4b5ad6f0a20e32073
```

`main` remains the canonical source until an approved merge changes it. The engineering stack is evidence, not canonical product authority.

---

## 3. Required product architecture

### 3.1 AXIGNAL Core

AXIGNAL Core includes:

- persistent global identity;
- organisations and server-resolved tenants;
- memberships, roles and seat governance;
- Navigator;
- persistent ResearchRun;
- InvestigationContext;
- Evidence Objects;
- Candidate Claims;
- independent deterministic admission;
- append-only Claim Ledger;
- bounded human review;
- Globe;
- Graph;
- Timeline;
- dossiers;
- alerts;
- entitlements;
- audit;
- deletion and retention;
- export and portability.

### 3.2 Foundational libraries

AXIGNAL MUST implement and accept:

| ID | Library |
|---|---|
| `AX-LIB-F01` | Jurisdiction and Geography |
| `AX-LIB-F02` | Entities, Organisations and Ownership |
| `AX-LIB-F03` | Taxonomies and Classifications |
| `AX-LIB-F04` | Time, Currency, Value and Units |
| `AX-LIB-F05` | Languages, Terminology and Translation |
| `AX-LIB-F06` | Source Rights and Provenance |
| `AX-LIB-F07` | Documents and Content |

These libraries MUST be versioned, source-aware, reversible and shared across opportunity libraries.

### 3.3 Opportunity libraries

AXIGNAL MUST implement and accept:

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

Every library MUST have independent rights, quality, lifecycle, privacy, entitlement, observability, disclosure, kill-switch and rollback gates.

### 3.4 Source and library states

```text
DISCOVERED
→ LEGAL_REVIEW
→ TECHNICAL_PROBE
→ EVIDENCE_READY
→ PRODUCT_ADMITTED
→ PRIVATE_ACCEPTANCE
→ COMMERCIAL
```

Protective or terminal states:

```text
RESTRICTED
SUSPENDED
REVOKED
REJECTED
```

Catalogue inclusion is never source admission.

### 3.5 Opportunity Operations Core

The shared operational model MUST include:

```text
Opportunity
Pursuit
Workspace
Decision
Requirement
WorkItem
Milestone
Document
Comment
Approval
SubmissionOrActivationRecord
Outcome
Learning
Template
ActivityEvent
```

It MUST support tenant isolation, collaboration, assignments, approvals, exports, retention, deletion, audit, mobile and accessibility.

---

## 4. Active programme P00–P27

| Phase | Contracted outcome |
|---|---|
| `P00` | Canonical integration and governance synchronisation |
| `P01` | Global buyer, workflow, budget and market evidence |
| `P02` | Global ontology and library contracts |
| `P03` | Security, identity and rights by design |
| `P04` | Source Admission Factory and Connector SDK |
| `P05` | Foundational libraries |
| `P06` | Multilingual and Document Intelligence |
| `P07` | Opportunity Operations Core |
| `P08` | Global Procurement and Bid Workspace |
| `P09` | Grants and Application Workspace |
| `P10` | Regulatory and Market Entry Workspace |
| `P11` | Infrastructure and Project Pursuit Workspace |
| `P12` | Corporate and Account Opportunity Workspace |
| `P13` | Sovereign/Macro and Strategy Workspace |
| `P14` | Trade/Supply and Supply Opportunity Workspace |
| `P15` | Energy/Climate and Transition Workspace |
| `P16` | Innovation/IP and Innovation Workspace |
| `P17` | Cross-library intelligence |
| `P18` | Intent Intelligence and Knowledge Tides |
| `P19` | Scenarios, calibration and outcomes |
| `P20` | Enterprise, API, private data and integrations |
| `P21` | Commercial runtime, pricing, Stripe and seat governance |
| `P22` | Production, SLO, disaster recovery, security, privacy and legal acceptance framework |
| `P23` | Final product UX, B2G landing, copy and market shell |
| `P24` | Exact-evidence acceptance framework and manifest; no longer the final launch authority |
| `P25` | Persistent identity, passwordless authentication and trial-abuse governance |
| `P26` | Organic discovery, programmatic SEO, AI-citation governance and Founder Operations |
| `P27` | Final exact-head re-acceptance and public-launch gate |

### 4.1 Current programme disposition

```text
P00     CANONICALLY_ACCEPTED
P01     IN_PROGRESS
P02–P24 ENGINEERING STACK PRESENT / CANONICAL ACCEPTANCE BLOCKED
P25-T01 ENGINEERING_E2E_PASS / PUBLIC SIGNUP BLOCKED
P26-T01 ENGINEERING_E2E_PASS / PUBLIC INDEXING BLOCKED
P26     IN_PROGRESS
P27     NOT_STARTED
PUBLIC LAUNCH NO_GO
```

### 4.2 P24 role after v1.5

P24 remains the reusable acceptance engine for:

- evidence binding;
- payment-evidence levels;
- integrated journeys;
- typed approvals;
- stop conditions;
- evidence-preserving rollback.

P24 MUST NOT itself authorise public launch after P25 and P26 introduced material new surfaces.

### 4.3 P26 task decomposition

```text
AX-GE2E-P26-T01
Organic Discovery and Founder Admin Foundation
ENGINEERING_E2E_PASS

AX-GE2E-P26-T02
Customers, Trials and Billing Administration
NOT_STARTED

AX-GE2E-P26-T03
Risk, Abuse, Sources and Coverage Administration
NOT_STARTED

AX-GE2E-P26-T04
Operations, SLO, Incidents, DR, Settings and Audit Administration
NOT_STARTED
```

A complete sidebar is not evidence that every module is operationally mutable.

### 4.4 P27 final gate

P27 is the only phase permitted to return:

```text
ACCEPTED_FOR_PUBLIC_LAUNCH
IN_PROGRESS
REJECTED
```

P27 MUST bind the exact heads and evidence of P00–P26 and re-evaluate every production, security, privacy, legal, billing, UX, identity, abuse, SEO, consent and operations boundary added after P22–P24.

---

## 5. Identity and authentication contract

### 5.1 Public authentication target

AXIGNAL public authentication is passkey-first:

```text
verified email bootstrap
→ WebAuthn passkey with user verification
→ opaque revocable server session
→ short-lived signed API assertion
→ server-resolved tenant and membership
```

Passwords MAY exist only as a bounded compatibility mechanism. They are not the preferred public signup path.

### 5.2 Session controls

Production session requirements:

```text
cookie: __Host-axignal_session
Secure: true
HttpOnly: true
SameSite: Lax
Path: /
Domain attribute: absent
idle timeout: 1 hour
absolute timeout: 24 hours
API assertion lifetime: 60 seconds
```

Sessions MUST be revocable and rotate after material authentication or privilege changes.

### 5.3 Recovery

Recovery MUST use stronger evidence than email possession alone and MUST:

- revoke existing sessions;
- revoke or contain affected authenticators;
- require a new passkey;
- issue new recovery codes;
- create append-only security events;
- impose temporary restrictions on critical actions when appropriate.

### 5.4 Identity authority

```text
email verified
≠ durable authenticator
account created
≠ tenant authority
membership active
≠ unrestricted authority
tenant seat
≠ Founder Admin authority
```

The browser cannot select or widen tenant authority.

---

## 6. Seven-day trial and abuse governance

### 6.1 Trial owner

A trial belongs to a tenant or resolved economic identity, not to a browser account.

```text
one governed tenant
→ one trial grant
→ one seven-day clock
→ one shared token and cost budget
→ two governed seats
```

### 6.2 Trial start

The clock starts only on the first admitted AI operation:

```text
email verified
→ passkey registered
→ trial READY
→ first admitted AI request
→ trial ACTIVE
→ expires_at = started_at + 7 days
```

Signup, email verification, login, alert subscription or opening the workspace MUST NOT start the clock.

### 6.3 Candidate trial limits

```text
duration: 7 consecutive 24-hour periods
seats: 2
token ceiling: 1,000,000
internal cost ceiling: server-side
ResearchRun concurrency: 1
bulk export: restricted
private connectors: restricted
public API: disabled unless separately admitted
```

### 6.4 Multiple-account controls

Strong identity claims MAY reuse or deny another trial. Weak signals MAY require step-up or review but MUST NOT independently prove abuse.

Risk decisions:

```text
ALLOW
ALLOW_RESTRICTED
REUSE_EXISTING_TRIAL
STEP_UP_REQUIRED
MANUAL_REVIEW
BLOCK_ABUSE
```

The following boundaries are mandatory:

```text
account created ≠ trial granted
risk score ≠ proof of fraud
shared IP ≠ abuse
new email alias ≠ new economic identity
alert subscriber ≠ trial user
```

### 6.5 Economic governance

Token, internal cost and concurrency reservations MUST be transactional. Exhaustion stops new expensive operations while preserving already-created customer work according to retention policy.

---

## 7. Plans, seats and pricing

### 7.1 Candidate price-book authority

The server-side commercial runtime is the current technical source of candidate package definitions.

Current candidate implementation:

| Package | Candidate amount | Flat-tier seat capacity |
|---|---:|---:|
| `CONTROLLED_TRIAL_7D` | `0 EUR` | `2` |
| `PROFESSIONAL_MONTHLY` | `149 EUR/month` | `3` |
| `TEAM_MONTHLY` | `399 EUR/month` | `15` |
| `ENTERPRISE_CONTRACT` | Quote only | Contracted |

These amounts are:

```text
CANDIDATE_ONLY
```

They are not validated public prices, market evidence or revenue forecasts.

Historical ranges such as `349–499 EUR/month` and `899–1,499 EUR/month` remain hypothesis history and MUST NOT override the active candidate price book.

Final pricing requires P01, P21 and P27 evidence for:

- buyer budget;
- willingness to pay;
- completed customer value;
- retention;
- margin;
- support burden;
- acquisition payback;
- packaging comprehension.

### 7.2 Flat-tier seat model

Stripe bills one package unit. AXIGNAL governs seats internally.

```text
verified trial or subscription
→ tenant seat entitlement
→ RESERVED or ACTIVE allocation
→ membership
→ role binding
→ server-resolved access
→ RLS
→ append-only audit
```

Professional cannot allocate a fourth seat. Team cannot allocate a sixteenth seat. A Team tenant MAY operate with fewer than four users.

### 7.3 Trial and paid boundaries

```text
Stripe customer ≠ tenant authority
subscription event ≠ membership
candidate price ≠ public-current price
paid invoice ≠ completed customer value
technical quota ≠ commercial entitlement
```

### 7.4 Live billing

Stripe live remains blocked until P27 and separate Finance, Tax, Security and Commercial authority approve the exact manifest.

---

## 8. Organic discovery and programmatic SEO

### 8.1 Organic acquisition chain

```text
admitted source data
→ normalisation and enrichment
→ SEO page candidate
→ deterministic IndexabilityGate
→ founder review
→ versioned expiring snapshot
→ public page, sitemap and structured data
→ Tender Alert
→ CRM lead
→ independent passwordless signup
→ governed trial
```

### 8.2 Indexability boundary

```text
dataset ≠ indexable page
generated page ≠ published page
crawlable ≠ indexed
indexed ≠ ranked
traffic ≠ qualified buyer
```

Arbitrary search facets MUST remain product search state unless independently admitted as public pages.

### 8.3 Public page classes

```text
TENDER_HUB
MARKET_INTELLIGENCE
TENDER_DETAIL
```

Publication requires:

- sufficient inventory;
- buyer diversity;
- search-demand evidence;
- data quality;
- content uniqueness;
- source coverage;
- content depth;
- freshness;
- non-synthetic evidence;
- a versioned snapshot;
- source and methodology disclosure.

### 8.4 AI citation governance

Observed AI citations are evidence events, not endorsements, rankings or conversion proof.

```text
AI citation ≠ recommendation
AI citation ≠ acquisition
AI citation ≠ factual authority
```

Citation events MUST preserve provider, surface, cited URL, protected query evidence, observation source and time.

### 8.5 Tender Alerts

Tender Alerts use independent double opt-in:

```text
request
→ bot verification
→ PENDING_CONFIRMATION
→ email delivery
→ explicit POST confirmation
→ ACTIVE
```

Opening a confirmation URL MUST NOT activate consent. An alert MUST NOT create an identity, tenant, seat, trial or paid package.

---

## 9. Google Search Console governance

### 9.1 Current evidence

A DNS TXT Search Console verification record has been provided for `axignal.com` and is registered in:

```text
data/growth/google-search-console-integration.v0.1.json
```

The verification token is public DNS verification material, not an application secret.

The current truthful state is:

```text
DNS verification evidence: USER_ATTESTED_PRESENT
Search Console property candidate: sc-domain:axignal.com
Search Console API access: NOT_YET_PROVEN
live performance import: BLOCKED
Founder OS mutation authority: BLOCKED
```

### 9.2 Acceptance evidence

Search Console becomes an admitted integration only after evidence proves:

- the verified property returned by the official API;
- least-privilege credentials;
- successful read-only `sites.list` or equivalent capability discovery;
- successful Search Analytics query;
- no credential material in the repository;
- tenant and founder scope separation;
- rate limits and error handling;
- audit events;
- revocation and kill switch;
- data retention and privacy disposition.

### 9.3 Search Console data authority

Search Console data MAY inform:

- crawl and indexing diagnostics;
- query, page, country and device performance;
- click, impression, CTR and position trends;
- indexability investigations;
- organic funnel analysis.

It MUST NOT by itself:

- publish or unpublish pages;
- change the IndexabilityGate;
- prove buyer quality;
- prove revenue attribution;
- grant Founder Admin access;
- authorise a launch.

---

## 10. MCP connector governance

### 10.1 Candidate Google Search Console MCP

The following user-provided MCP catalogue entry is recorded as a candidate:

```text
https://mcpservers.org/es/servers/ahonn/mcp-server-gsc
```

Its current state is:

```text
DISCOVERED
/ USER-PROVIDED CATALOGUE ENTRY
/ IMPLEMENTATION AND MAINTAINER NOT INDEPENDENTLY VERIFIED
/ NOT SECURITY-REVIEWED
/ NOT PRODUCT-ADMITTED
/ NOT CONNECTED TO PRODUCTION
```

### 10.2 MCP admission

No MCP server may be connected merely because it exists or is listed in a registry.

Admission requires:

- exact repository and release identity;
- maintainer and licence review;
- dependency and supply-chain review;
- tool inventory;
- read/write/destructive classification;
- credential flow review;
- network and egress limits;
- prompt-injection and tool-poisoning review;
- secret isolation;
- explicit tool allowlist;
- test environment evidence;
- kill switch;
- audit;
- human approval.

### 10.3 Default permissions

A Search Console MCP MUST start read-only.

Default permitted classes MAY include:

- list verified properties;
- query Search Analytics;
- inspect URL/index status where supported;
- read sitemap state.

Default denied classes include:

- add or delete sites;
- submit or delete sitemaps;
- modify users or permissions;
- change DNS;
- expose OAuth or service-account secrets;
- execute arbitrary shell or browser automation;
- mutate Founder OS state without a typed operation.

MCP output is external tool evidence. It is not canonical product authority.

---

## 11. Founder Operations control plane

### 11.1 Route and identity

The private founder control plane is exposed under `/admin` only when enabled.

Founder authority is:

```text
valid passwordless session
∩ recent AAL2 passkey verification
∩ server-side founder allowlist
∩ active founder_admin_principal in PostgreSQL
∩ typed SECURITY DEFINER operation
∩ append-only audit event
```

Tenant ownership or a paid seat does not grant founder authority.

### 11.2 Required modules

The complete Founder Operations programme MUST govern:

#### Growth

- Overview;
- Organic SEO;
- Pages and Sitemaps;
- AI Citations;
- Tender Alerts;
- CRM.

#### Commercial

- Customers and Trials;
- Billing;
- invoices and credit notes;
- upgrades, downgrades and cancellations;
- refunds, disputes and dunning;
- entitlement reconciliation.

#### Trust and data

- Risk and Abuse;
- Sources and Coverage;
- source rights and admission;
- library state;
- claims and publication evidence;
- consent and deletion.

#### Platform

- Operations;
- queues and workers;
- SLO and error budgets;
- incidents;
- backup and restore;
- feature flags and kill switches;
- Settings;
- Audit.

### 11.3 Truthful controls

A module without server-side authority MUST be shown as read-only, blocked or not implemented. The UI MUST NOT simulate a control that has no durable effect.

---

## 12. Production, security and re-acceptance

P25 and P26 materially changed the attack surface after P22 and P24 by adding:

- public identity and recovery;
- WebAuthn credentials;
- sessions;
- trial-abuse decisions;
- email delivery;
- consent records;
- public SEO pages;
- crawlers and sitemaps;
- CRM contacts;
- Founder Admin authority;
- new PostgreSQL schemas;
- external Search Console and MCP candidates.

Therefore P27 MUST re-run or renew:

- threat model;
- security acceptance;
- privacy and data-protection review;
- legal and terms review;
- DR and restore evidence;
- SLO and capacity evidence;
- accessibility and browser acceptance;
- billing reconciliation;
- trial abuse and false-positive review;
- email and consent acceptance;
- SEO publication and crawler acceptance;
- Founder Admin privilege review;
- MCP and Search Console integration review;
- exact-head human approvals.

CI green is necessary but insufficient.

---

## 13. Global-coverage gate

AXIGNAL MAY use `global` publicly as a coverage claim only when:

1. O01–O09 are implemented and canonically accepted;
2. admitted coverage exists in Europe, North America, Latin America, Asia, Oceania and Africa;
3. coverage and gaps are visible;
4. source-native identifiers, taxonomies, currencies and languages are preserved;
5. every library has a multinational E2E;
6. cross-library queries preserve authority and provenance;
7. unavailable or revoked sources contribute no claims;
8. rights and revocation are independently enforceable;
9. P27 accepts the exact coverage manifest.

The parent category name may be used internally before this gate. Public copy MUST not imply coverage that has not been accepted.

---

## 14. Evidence and launch gate

### 14.1 Required evidence classes

P27 requires applicable:

- schema and migration evidence;
- exact-head deterministic tests;
- real-source bounded tests;
- source-right records;
- security review;
- privacy and legal review;
- multilingual evidence;
- accessibility evidence;
- SLO, capacity and cost evidence;
- restore and rollback evidence;
- complete Stripe sandbox round trip;
- controlled live technical payment when authorised;
- independent paid-customer evidence;
- completed customer-value workflows;
- retention and renewal evidence;
- margin and support evidence;
- buyer and pricing evidence;
- SEO and Search Console evidence;
- consent and email evidence;
- Founder Operations evidence;
- human approvals bound to one manifest digest.

### 14.2 Private acceptance

`PRIVATE_ACCEPTANCE` may admit bounded organisations only when:

- each organisation is explicitly approved;
- terms describe experimental or acceptance status;
- no public signup exists;
- no paid media represents launch;
- access, billing and revocation are auditable;
- support burden is declared;
- source and coverage limitations are visible;
- stop conditions remain active.

Private acceptance does not satisfy P27 by itself.

### 14.3 Final launch disposition

```text
ACCEPTED_FOR_PUBLIC_LAUNCH
```

requires:

- P00–P26 canonically accepted;
- seven foundational libraries accepted;
- nine opportunity libraries accepted;
- required operational workspaces accepted;
- P26-T01–T04 accepted;
- P24 evidence framework bound to the final head;
- P27 exact-head integrated journeys accepted;
- production, security, privacy, legal and DR accepted;
- passwordless identity and recovery accepted;
- trial abuse and economics accepted;
- pricing and paid evidence accepted;
- organic acquisition and consent accepted;
- Search Console integration either admitted or explicitly non-required for launch;
- every connected MCP independently admitted;
- zero critical security findings;
- truthful copy and coverage disclosure;
- typed human approvals.

---

## 15. Current factual state

At the time of this contract candidate:

```text
canonical main                       b9a08a2a07d04d635164e161d1b27a7a53df8575
engineering stack candidate          e1e4999ecd1a7140d9b18ea4b5ad6f0a20e32073
P00 canonical state                  ACCEPTED
P01 canonical state                  IN_PROGRESS
P02–P24 canonical acceptance         BLOCKED
P25-T01 engineering                  E2E PASS
P26-T01 engineering                  E2E PASS
P26 phase                            IN_PROGRESS
P27                                  NOT STARTED
public signup                        BLOCKED
public indexing                      BLOCKED
production SMTP                      NOT CONFIGURED
production bot provider              NOT CONFIGURED
OIDC Microsoft/Google                NOT IMPLEMENTED
SAML/SCIM production acceptance      NOT PROVEN
Stripe live                          BLOCKED
commercial activation                BLOCKED
foundational libraries accepted      0
opportunity libraries commercial     0
buyer personas validated             false
pricing validated                    false
independent paid evidence             missing
public launch                        NO_GO
```

Google Search Console DNS verification is recorded as user-attested evidence. API access and data import remain unproven.

---

## 16. Supersession and migration

### 16.1 Superseded authority

Contract 31 supersedes:

- Contract 30 as the active programme and final-launch authority;
- ADR-015's P00–P24 terminal sequence;
- P24 as a standalone final launch gate;
- any P24 `BOUNDED_PUBLIC_LAUNCH` authority;
- Contract 00 language making European TED procurement the sole mandatory pre-launch product;
- Contract 01 and Contract 22 price bands where they conflict with the versioned candidate price book;
- Contract 21 audiences and examples that conflict with the B2G shell;
- any statement that P26 is complete solely because P26-T01 passed.

### 16.2 Preserved history

The following remain preserved:

- Contract 30;
- ADR-015;
- v1.4 task registry and phase documents;
- every phase implementation PR;
- every accepted or failed CI run;
- rollback plans;
- source catalogues;
- negative user or market evidence;
- financial and payment ledgers;
- security and incident history.

Historical evidence MUST NOT be rewritten to appear v1.5-native.

### 16.3 Canonical merge rule

This contract becomes active only after:

1. human approval;
2. Contract 31 and ADR-016 validation;
3. v1.5 roadmap, task and state registries pass;
4. exact branch evidence is recorded;
5. the approved PR is merged into the canonical branch.

Until then, it remains a normative candidate.

---

## 17. Signature

```text
Document:
AXIGNAL-GLOBAL-E2E-DEVELOPMENT-CONTRACT-v1.5

Contract:
31

Goal:
AXIGNAL-GOAL-001

Canonical baseline:
main@b9a08a2a07d04d635164e161d1b27a7a53df8575

Engineering candidate:
e1e4999ecd1a7140d9b18ea4b5ad6f0a20e32073

Human authority:
Rafael López

Decision:
[ ] APPROVED
[ ] APPROVED WITH CHANGES
[ ] REJECTED

Date:
____________________
```
