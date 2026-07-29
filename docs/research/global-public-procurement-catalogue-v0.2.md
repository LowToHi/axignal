# Global Public Procurement Catalogue v0.2

Date: `2026-07-29`
Status: `RESEARCH CATALOGUE / PRIORITISED / NOT PRODUCT AVAILABILITY`
Goal ID: `AXIGNAL-GOAL-001`
Governing contract: `28`
Decision: `ADR-013`
Task: `AX-F12-T10`

## 1. Decision

AXIGNAL will pursue the broadest viable official public-procurement footprint while implementing sources in an economically rational order.

The catalogue therefore separates two goals:

```text
maximum worldwide discovery coverage
≠
implementation priority
```

A source may remain in the worldwide backlog even when a larger or more technically mature market is implemented first.

The canonical example is:

```text
SAM.gov → early implementation priority
NOCOPO → retained African long-tail source
```

NOCOPO is not removed. It remains available for later source admission when demand, rights, quality and economics justify implementation.

## 2. Catalogue breadth

Catalogue v0.2 contains:

- `146` source families;
- `140` distinct jurisdiction and government-level scopes;
- eight regional inventory files;
- national, federal, supranational, multilateral, state, provincial and municipal systems;
- a top-40 implementation queue;
- a long-tail worldwide backlog;
- a deterministic CI verifier.

Regional coverage includes:

- Europe;
- Eastern Europe and Central Asia;
- North America;
- Latin America and the Caribbean;
- Asia;
- the Middle East;
- Africa;
- Oceania;
- global and regional development institutions.

## 3. Discovery sources

The Open Contracting Partnership Data Registry is used as a discovery and comparability index. At the time of this research it exposed `134` datasets and extensive publisher metadata, coverage indicators and data-quality warnings.

Registry inclusion is not source admission. AXIGNAL must independently verify:

- the official publisher and endpoint;
- collection and commercial-use rights;
- storage, transformation, display, export and redistribution rights;
- completeness and update cadence;
- source-native identifiers and classifications;
- privacy exposure;
- attribution and revocation;
- operational cost.

Official national portals, government open-data catalogues and multilateral procurement sites are also used for continuous discovery.

## 4. Priority model

The priority score uses:

| Dimension | Weight |
|---|---:|
| Addressable market and procurement capacity | 35% |
| Official machine access and stability | 20% |
| Cross-border supplier accessibility | 15% |
| Lifecycle and document depth | 10% |
| Rights and attribution clarity | 10% |
| Taxonomy, language and maintenance fit | 10% |

The score is a queueing device, not a product-admission decision.

Paid customer demand, official API quality, rights clarity, lifecycle completeness, documents, measured source cost and reusable language or taxonomy infrastructure may alter the order.

## 5. Priority classes

### P0 — Current wedge

Only European TED may be P0.

P0 means current authorised implementation sequence, not product admission.

### P1 — Largest and most actionable

Large public-procurement markets or global platforms with sufficiently mature official access.

Examples:

- United States federal SAM.gov;
- UK Find a Tender and Contracts Finder;
- World Bank Procurement Notices;
- UN Global Marketplace;
- USAspending awards;
- CanadaBuys;
- Japan official procurement APIs;
- AusTender;
- France, Germany, Brazil, South Korea, Spain, Italy and the Netherlands.

### P2 — High-value second wave

Strategic national, regional and multilateral systems with strong market or cross-border value.

### P3 — Global long tail

Sources retained to achieve worldwide reach after higher-return implementation gates.

Nigeria NOCOPO is deliberately included here.

### P4 — Discovery and feasibility

Systems whose exact official endpoint, machine access or reuse basis still requires verification.

P4 entries cannot be implemented until their identity and access evidence are repaired.

## 6. First post-TED implementation queue

The first 15 candidates after TED are:

1. United States — SAM.gov Contract Opportunities;
2. United Kingdom — Find a Tender;
3. World Bank Procurement Notices;
4. United Nations Global Marketplace;
5. United Kingdom — Contracts Finder;
6. United States — USAspending contract awards;
7. Canada — CanadaBuys;
8. Japan — Government Procurement Information Portal API;
9. Australia — AusTender;
10. France — consolidated essential procurement data;
11. Germany — federal publication service;
12. Brazil — Compras.gov.br;
13. Brazil — PNCP;
14. Japan — GEPS data publication;
15. South Korea — KONEPS.

This order maximises market capacity and reusable connector value after the European TED E2E gate.

## 7. Multilateral leverage

Multilateral sources can provide global reach through fewer governed connectors.

Priority multilateral families include:

- World Bank Procurement Notices;
- United Nations Global Marketplace;
- Asian Development Bank opportunities;
- African Development Bank opportunities;
- Inter-American Development Bank procurement;
- European Bank for Reconstruction and Development ECEPP;
- European Investment Bank procurement;
- NATO Support and Procurement Organisation.

These sources do not replace national portals. They add cross-border projects and financed procurements across many countries.

## 8. Federal and subnational expansion

Country-level support cannot be inferred from one federal source.

The catalogue therefore preserves independent records for:

- US states and cities;
- Canadian provinces and municipalities;
- Australian states;
- UK devolved systems;
- Mexican states;
- Latin American provinces and cities;
- other subnational publishers where commercial demand justifies the maintenance burden.

A national or federal pack must disclose which government levels are actually covered.

## 9. Data and taxonomy boundary

Sources may use:

- CPV;
- NAICS;
- PSC;
- UNSPSC;
- national product and service catalogues;
- source-specific buyer, supplier and procedure identifiers.

AXIGNAL must preserve native values. Crosswalks must be:

- versioned;
- reversible;
- many-to-many;
- confidence-aware;
- temporally valid;
- reviewable.

A semantic model may propose a mapping but cannot admit authoritative equivalence.

## 10. Deterministic catalogue validation

The catalogue verifier fails closed when:

- breadth falls below 140 source families;
- source IDs are duplicated;
- summary counts drift from inventories;
- a URL is insecure without an explicit feasibility boundary;
- more than TED is assigned P0;
- any catalogue source is marked `PRODUCT_ADMITTED`;
- the implementation queue contains unknown or duplicate sources;
- SAM.gov is not the first post-TED implementation priority;
- NOCOPO is incorrectly promoted into the top implementation queue;
- global marketing, billing or trial authority is enabled.

## 11. Authority boundary

Catalogue v0.2 authorises:

- discovery;
- prioritisation;
- source-specific research;
- future bounded technical probes after dependencies pass.

It does not authorise:

- ingestion;
- scraping;
- product admission;
- redistribution;
- public global-coverage claims;
- billing or trial activation;
- simultaneous worldwide implementation.

Current maximum state:

```text
146 SOURCE FAMILIES CATALOGUED
/ 140 JURISDICTION SCOPES
/ SAM.GOV FIRST POST-TED PRIORITY
/ NOCOPO RETAINED IN GLOBAL BACKLOG
/ ZERO NEW SOURCES PRODUCT-ADMITTED
/ GLOBAL MARKETING DISABLED
```
