# 28 — B2G Procurement Commercial and Global Source Program

Version: `0.2.0`
Status: `NORMATIVE CANDIDATE / CONTRACT 31 SUBORDINATE / NO PUBLIC ACTIVATION`
Goal ID: `AXIGNAL-GOAL-001`
Governing contract: `31`
Decision records: `ADR-013`, `ADR-015`, `ADR-016`

## 1. Purpose

This contract governs AXIGNAL's first commercial shell as **Business-to-Government (B2G) Opportunity Intelligence** and the source-specific expansion of the Global Public Procurement library.

It is subordinate to Contract 31.

Procurement is the first commercial and acquisition wedge. It does not define AXIGNAL's parent product identity and does not authorise a narrow public launch before the complete Contract 31 product passes P27.

## 2. Product and source boundary

```text
AXIGNAL parent product
= Global Opportunity Intelligence & Operations

first commercial shell
= Business-to-Government Opportunity Intelligence

first acquisition universe
= public contracts and global tenders

TED and other portals
= independently governed sources
```

AXIGNAL must not be described as a TED search tool, a raw tender database or a generic research assistant.

## 3. B2G value chain

```text
public procurement signals
→ source-admitted evidence
→ normalised notices, lots, buyers, awards and contracts
→ company-capability context
→ qualified opportunity
→ evidence and contradiction review
→ human bid/no-bid decision
→ Bid Workspace pursuit
→ requirements, tasks, documents and approvals
→ submission record
→ observed outcome
→ reusable win/loss learning
```

The product must preserve source, document, language, lifecycle, rights, uncertainty and human authority throughout the chain.

## 4. Procurement source catalogue

The global procurement programme must resolve at minimum:

1. EU TED;
2. UK Contracts Finder and Find a Tender;
3. US SAM.gov Contract Opportunities;
4. CanadaBuys;
5. Chile Mercado Público;
6. Colombia SECOP;
7. Brazil Compras.gov.br;
8. South Korea KONEPS;
9. India CPPP/eProcure;
10. Australia AusTender;
11. New Zealand GETS;
12. South Africa eTenders/OCDS;
13. Nigeria NOCOPO/OCDS.

At P27 each entry must be:

- `COMMERCIAL`;
- `RESTRICTED` with transparent approved limitation;
- or `REJECTED` with evidence and an approved coverage alternative.

No entry may remain merely catalogued and still contribute to a public coverage claim.

## 5. Source admission

Every source follows:

```text
DISCOVERED
→ LEGAL_REVIEW
→ TECHNICAL_PROBE
→ EVIDENCE_READY
→ PRODUCT_ADMITTED
→ PRIVATE_ACCEPTANCE
→ COMMERCIAL
```

Protective states:

- `RESTRICTED`;
- `SUSPENDED`;
- `REVOKED`;
- `REJECTED`.

Admission requires:

- official identity and endpoint;
- licence, terms and commercial-use disposition;
- authentication and rate limits;
- redistribution and document rights;
- source-native identifiers and lifecycle;
- update, correction, cancellation and outcome handling;
- schema-drift detection;
- quality and missingness;
- privacy and personal-data minimisation;
- cost and operational ownership;
- outage profile;
- attribution;
- kill switch;
- quarantine and rollback;
- user-visible coverage disclosure.

Public visibility never implies permission.

## 6. Procurement ontology

The library must preserve:

- notice and form type;
- procedure;
- lot;
- buyer and authority;
- supplier;
- award and contract;
- framework;
- classification;
- place of performance;
- publication, observation, deadline and validity time;
- corrections, cancellations and versions;
- values, currencies and unknowns;
- documents and anchors;
- source-native identifiers.

Crosswalks are many-to-many, versioned and reversible. A proposed crosswalk is not canonical equivalence.

## 7. B2G qualification

Qualification may use explicit dimensions such as:

- declared company capability;
- product or service taxonomy;
- geography and jurisdiction;
- buyer type;
- contract-value range;
- procedure;
- deadline;
- language;
- certifications observed or requiring verification;
- evidence quality;
- historical buyer and award context;
- partnership or ownership context.

Qualification must distinguish:

```text
company-declared capability
source-observed requirement
calculated match
inferred relevance
unknown verification
legal eligibility
```

A match is not win probability, eligibility certification or bid advice.

## 8. Bid Workspace

The Bid Workspace must support:

- opportunity and pursuit;
- bid/no-bid decision;
- owners and roles;
- requirements matrix;
- tasks and milestones;
- documents and source evidence;
- clarifications;
- approvals;
- submission record;
- award, loss, cancellation or withdrawal;
- win/loss learning;
- export and audit.

AXIGNAL cannot submit, sign or represent the organisation without a separately accepted typed authority.

## 9. Identity, seats and trial

B2G access uses the P25 and P21 authority chain.

Candidate trial:

- one per tenant or economic identity;
- seven days from first admitted AI use;
- two seats;
- 1,000,000-token ceiling;
- internal cost ceiling;
- one concurrent ResearchRun;
- no card;
- no silent conversion.

Candidate paid capacities:

- Professional: three seats;
- Team: fifteen seats.

A source or library entitlement remains constrained by rights and commercial state.

## 10. Candidate pricing

Current technical candidate price book:

| Package | Candidate price | Seats |
|---|---:|---:|
| Controlled trial | `0 EUR` | 2 |
| Professional | `149 EUR/month` | 3 |
| Team | `399 EUR/month` | 15 |
| Enterprise | Quote only | Contracted |

All are `CANDIDATE_ONLY`.

Historical bands remain research history. Final pricing requires P01, P21 and P27 evidence.

## 11. B2G landing and copy

Required public category language:

> **Business-to-Government (B2G) Opportunity Intelligence**

Required initial outcome framing:

> **Find the public contracts your business is built to pursue.**

The landing must:

- define B2G;
- lead with public contracts and tenders;
- explain qualification and evidence;
- show pursuit operations;
- disclose candidate trial and price status;
- exclude unsupported universal coverage and win claims;
- avoid making TED part of the product identity;
- remain non-public until its activation gate passes.

## 12. Organic procurement discovery

Admitted procurement data may support:

- country-sector Tender Hubs;
- Market Intelligence pages;
- selected enriched Tender Detail pages;
- Tender Alerts;
- source-grounded reports.

Every public page requires the P26 IndexabilityGate and a current versioned snapshot.

```text
source record ≠ SEO page
filter combination ≠ search demand
page generated ≠ page published
```

## 13. Search Console and MCP

Google Search Console may provide search-performance evidence after official API admission.

A DNS verification record does not prove API access or indexing authority.

The user-provided GSC MCP URL is a candidate connector only. It remains deny-by-default, read-only if probed and independently subject to connector and tool admission.

No MCP may admit a source, publish a page, submit or delete a sitemap, change Search Console permissions or expose credentials without explicit typed authority.

## 14. Buyer and commercial evidence

Procurement engineering evidence does not validate:

- buyer personas;
- budget;
- willingness to pay;
- package choice;
- trial conversion;
- customer value;
- retention;
- margin;
- repeatable acquisition.

P01 remains the canonical buyer-evidence gate. P27 is the final launch gate.

## 15. Private acceptance

Paid Design Partners or private acceptance may be used before launch only when:

- organisations are explicitly admitted;
- terms declare actual maturity;
- no open public signup exists;
- no public-launch claim exists;
- source scope and gaps are visible;
- access and billing are auditable;
- suspension and rollback exist;
- customer work and financial evidence are preserved.

Private acceptance is not a public procurement launch.

## 16. Global procurement gate

The procurement library is a candidate for canonical acceptance only when:

- source decisions are complete for the required catalogue;
- rights and attribution are current;
- multijurisdiction lifecycle E2E passes;
- source-native semantics and languages are preserved;
- Bid Workspace operation passes;
- identity, seats, trial and billing pass;
- coverage and gaps are visible;
- rollback and source kill switches pass;
- buyer and paid evidence are accepted;
- P27 binds the final exact head.

## 17. Current authority

```text
B2G SHELL                         SELECTED
PROCUREMENT ENGINEERING           PRESENT
TED AND OTHER SOURCES             INDEPENDENTLY GOVERNED
GLOBAL PROCUREMENT COMMERCIAL     NOT ACCEPTED
P25 IDENTITY/TRIAL ENGINEERING    PASS
P26 ORGANIC FOUNDATION            PASS
CANDIDATE PRICING                 0 / 149 / 399 / QUOTE
PUBLIC SIGNUP                     BLOCKED
PUBLIC INDEXING                   BLOCKED
STRIPE LIVE                       BLOCKED
PUBLIC LAUNCH                     NO_GO
```
