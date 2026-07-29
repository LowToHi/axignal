# First Lawful and Commercial Universe Selection v0.1

- Goal ID: `AXIGNAL-GOAL-001`
- Decision ID: `AX-F8-UNIVERSE-001`
- Tasks: `AX-F8-T01`, `AX-F8-T02`
- Date: `2026-07-29`
- Status: `WEDGE SELECTED / IMPLEMENTATION NOT ADMITTED / PUBLIC SUPPORT CLAIM PROHIBITED`

## 1. Decision

AXIGNAL selects **European Public Procurement Intelligence** as its first commercial implementation wedge.

The first source family to enter legal and technical admission is **TED — Tenders Electronic Daily**, using its official Search API, Open Data reuse mechanisms and eProcurement Ontology.

This decision means only:

```text
candidate universes scored
→ one implementation wedge selected
→ ontology, source and policy work authorised
```

It does **not** mean:

```text
TED source PRODUCT_ADMITTED
European procurement universe supported
live ingestion authorised
commercial demand validated
billing authorised
```

## 2. Why this wedge

European public procurement combines the strongest current fit across AXIGNAL's commercial, legal, epistemic and product requirements:

- a recurring professional workflow with explicit deadlines and high failure cost;
- identifiable budget owners among SMEs, advisers, holdings and business-development teams;
- official machine-readable notices and bulk-reuse paths;
- geographic, relational and temporal structure for Globe, Graph and Timeline;
- structured observed facts such as buyer, lot, CPV, place, deadline, value and award;
- a credible public-data cost base before commercial data licences;
- no requirement for custody, transaction execution or personalised investment advice;
- a large addressable demand surface: the European Commission states that public procurement represents around 14% of EU GDP.

The wedge is not a tender-search clone. AXIGNAL's differentiation must come from:

- notice and award history as versioned claims;
- changes, corrections, cancellations and expiry;
- buyer, supplier, sector and geography graphs;
- supporting, contradicting and unknown evidence;
- market-demand and concentration context;
- persistent investigation trails;
- explicit coverage and rights boundaries.

## 3. Scoring method

Each candidate is scored from `0` to `5` against nine weighted criteria. The machine-readable source of truth is:

`data/universes/first-lawful-universe-scorecard.v0.1.json`

| Criterion | Weight |
|---|---:|
| Buyer value | 20 |
| Workflow frequency | 10 |
| Rights clarity | 15 |
| Official machine access | 15 |
| Epistemic fit | 10 |
| Globe/Graph/Timeline fit | 10 |
| Differentiation | 10 |
| Cost and margin fit | 5 |
| Regulatory simplicity | 5 |
| **Total** | **100** |

Selection requires:

- weighted total of at least `80`;
- buyer value of at least `4`;
- rights clarity of at least `4`;
- official machine access of at least `4`;
- regulatory simplicity of at least `3`;
- no dependence on unauthorised scraping, advice, execution or custody;
- a bounded official-source technical-probe path.

## 4. Results

| Rank | Candidate | Score | Gate | Decision |
|---:|---|---:|---|---|
| 1 | European public procurement intelligence | **96** | PASS | **SELECTED** |
| 2 | European trade and supply-chain shifts | 85 | PASS | Context-layer runner-up |
| 3 | European grants and non-dilutive capital | 82 | FAIL | Access fragmentation |
| 4 | Public-company strategic disclosures | 82 | PASS | Deferred: regulation and differentiation |
| 5 | EU regulation-created business demand | 80 | PASS | Deferred: inference policy |
| 6 | Macroeconomic and sovereign context | 80 | FAIL | Context only; buyer-value knockout |
| 7 | European real assets and property | 69 | FAIL | Rights and machine-access knockout |

A passing score does not force selection. The gate identifies viable candidates; the highest-scoring candidate is selected only when it also creates the strongest coherent first workflow.

## 5. Candidate analysis

### 5.1 European public procurement intelligence — selected

**Official evidence**

- TED Search API: `https://docs.ted.europa.eu/api/latest/search.html`
- TED Open Data Search API reuse: `https://docs.ted.europa.eu/ODS/latest/reuse/search-api.html`
- eProcurement Ontology: `https://docs.ted.europa.eu/EPO/latest/index.html`
- European Commission procurement overview: `https://single-market-economy.ec.europa.eu/single-market/public-procurement_en`
- Commission reuse decision: `https://eur-lex.europa.eu/eli/dec/2011/833/oj`

**Evidence-backed advantages**

- TED's Search API is aimed at data reusers and does not require authentication.
- The API supports published-notice search and XML retrieval; the Open Data documentation provides pagination and iteration modes for large retrievals.
- The official eProcurement Ontology covers procurement concepts from notification through awarding, ordering, invoicing and payment.
- EU documents are generally reusable for commercial and non-commercial purposes under Commission Decision 2011/833/EU, subject to source attribution, non-distortion, personal-data rules and third-party-rights exceptions.
- The Commission describes procurement as around 14% of EU GDP and explicitly recognises its importance for business access, innovation and competitiveness.

**Unresolved before source admission**

- capture a source-specific licence and legal-notice snapshot;
- map exact API fields and formats to retained, displayed and exportable dimensions;
- exclude or minimise personal contact information;
- prove notice modification, cancellation and award lineage;
- establish API limits, fair use, checkpointing and outage behaviour;
- measure field completeness by country, notice form and period;
- verify multilingual preservation and attribution rendering.

### 5.2 European trade and supply-chain shifts — runner-up context layer

**Official evidence**

- Eurostat Comext API: `https://ec.europa.eu/eurostat/web/user-guides/data-browser/api-data-access/api-getting-started/comext-database`
- International trade data: `https://ec.europa.eu/eurostat/web/international-trade-in-goods/information-data`

Comext has excellent geographic and temporal structure and provides official, harmonised trade statistics. It is not selected as the standalone wedge because high-volume aggregation, product-code semantics and opportunity interpretation create more operational cost and inference pressure. It should later supply procurement context such as import dependence, supplier geography and sector momentum.

### 5.3 European grants and non-dilutive capital — first adjacent universe

**Official evidence**

- Commission funding eligibility: `https://commission.europa.eu/funding-tenders/how-apply/eligibility-who-can-get-funding_en`
- Commission reuse decision: `https://eur-lex.europa.eu/eli/dec/2011/833/oj`

The workflow is commercially strong but calls, programmes, awards and national schemes are fragmented across access mechanisms. It remains the first adjacent expansion after a source-by-source access and rights inventory.

### 5.4 Public-company strategic disclosures — deferred

**Official evidence**

- SEC EDGAR APIs: `https://www.sec.gov/search-filings/edgar-application-programming-interfaces`

EDGAR provides unauthenticated JSON APIs, real-time updates and nightly bulk archives. It is deferred because it competes more directly with established financial-data workflows, fits the Globe less strongly and requires tighter investment-information controls.

### 5.5 EU regulation-created demand — deferred

**Official evidence**

- EUR-Lex webservice: `https://eur-lex.europa.eu/content/help/data-reuse/webservice.html?locale=en`
- EUR-Lex and Cellar reuse access: `https://eur-lex.europa.eu/content/help/data-reuse/reuse-contents-eurlex-details.html?locale=en`

EUR-Lex and Cellar provide structured access, relationships and reusable legal content. The universe is differentiated but translating a legal obligation into market demand is usually an inference. It requires a dedicated ontology, jurisdictional review and strict separation between observed legal facts and proposed economic implications.

### 5.6 Macro and sovereign context — mandatory context, not wedge

**Official evidence**

- Eurostat API: `https://ec.europa.eu/eurostat/web/user-guides/data-browser/api-data-access/api-introduction`

Macro data have excellent rights, access and deterministic-claim properties. They remain necessary context but are insufficiently differentiated as a standalone commercial workflow.

### 5.7 European real assets and property — rejected for the initial wedge

The buyer value and Globe fit are strong, but cross-border listing rights, transaction comparability, official coverage and licensing are too fragmented. No implementation is authorised under this decision.

## 6. Initial buyer scope

The bounded design-partner cohort is:

1. European SMEs and growth operators evaluating public-sector demand;
2. bid, market-entry and business-development advisers;
3. holdings, venture studios and corporate-development teams mapping buyers, competitors and demand;
4. professional research users monitoring procurement-driven market change.

The wedge remains compatible with the Product Constitution because it serves professional decision preparation, entrepreneurs, executives, advisers, holdings and corporate-development teams. It does not reposition AXIGNAL as a consumer tender-alert product.

## 7. First high-value workflow

```text
professional user asks for public-demand opportunities
→ visible interpretation of geography, CPV sector, value band and deadline
→ ResearchRun created
→ admitted TED notices retrieved or refreshed
→ immutable raw notice references
→ observed Candidate Claims proposed
→ deterministic source, rights, structure, date, value, currency and geography gates
→ canonical claims or bounded escalation
→ opportunities rendered in Globe, Graph and Timeline
→ user inspects notice, changes, awards, contradictions and unknowns
→ investigation trail saved and monitored
```

Example bounded query:

> Show newly published cybersecurity procurements above €500,000 in Spain, France and Germany, explain which buyers recur, identify changed or cancelled notices, and show the evidence and deadlines.

This is not a promise that every notice contains an estimated value or that AXIGNAL can determine supplier suitability.

## 8. Claim authority boundary

### Eligible observed claims

- notice published, modified, cancelled or corrected;
- buyer identity and public-body identifiers when available;
- procedure and notice type;
- lot identity;
- CPV classification;
- place of performance;
- stated publication and submission dates;
- stated estimated or award value and currency;
- award result and named winning organisation when officially published.

### Eligible calculated claims

Only through reproducible deterministic transforms:

- time remaining to a stated deadline;
- currency-normalised value with source rate and timestamp;
- notice and award counts by admitted dimensions;
- buyer recurrence;
- supplier concentration;
- median and distribution statistics;
- change frequency and cancellation rate.

### Proposal-only or prohibited claims

- probability of winning;
- supplier suitability;
- expected profitability;
- causal claim that procurement growth proves sector attractiveness;
- bid strategy or legal eligibility advice;
- personalised investment recommendation;
- transaction or bid submission;
- canonical claims built from personal contact fields.

## 9. Privacy boundary

Procurement notices may contain contact-person names, phone numbers or email addresses. The first universe must:

- avoid using contact-person data as an opportunity or canonical claim;
- exclude personal contact fields from public API, analytics and model prompts by default;
- retain them only when strictly necessary, legally justified and source-admitted;
- apply field-level minimisation and deletion rules;
- distinguish organisations and public offices from natural persons;
- prevent cross-source person profiling.

## 10. Commercial test

Selection does not validate willingness to pay. The first commercial test must use a manually supported but technically real workflow.

Predeclared evidence required before marketing the universe as supported:

- at least five qualified workflow interviews in the bounded cohort;
- at least three design partners provide their real search criteria and one recent missed or costly procurement-research case;
- at least one end-to-end workflow produces a traceable dossier from admitted sources;
- at least two independent users return to a saved investigation or alert after the initial session;
- at least one paid event or signed design-partner commitment;
- measured data and compute cost compatible with the target plan;
- no critical rights, privacy, attribution or regulatory defect.

These thresholds design the next experiment; they are not claimed as achieved.

## 11. Next authorised implementation tasks

Only the following F8 tasks are activated:

1. `AX-F8-T03` — define the procurement universe ontology;
2. `AX-F8-T04` — admit the minimum lawful source set, beginning with TED;
3. `AX-F8-T05` — implement the TED connector and quality monitoring after source admission;
4. `AX-F8-T06` — implement procurement-specific claim policies.

Globe and Graph layers (`AX-F8-T07`) remain blocked until T03–T06 produce admitted claims. Commercial buyer validation (`AX-F8-T10`) remains blocked until a real end-to-end workflow exists.

## 12. Kill conditions

The wedge must be rejected or materially revised when any of these becomes true:

- TED rights do not permit the required storage, transformation or customer display;
- notice completeness is too inconsistent for the selected workflow;
- qualified buyers want only generic alerts and will not pay for evidence, history or investigation state;
- value requires unauthorised national-portal scraping;
- privacy-safe field minimisation destroys essential workflow value;
- source and processing cost makes target gross margin structurally unattractive;
- the system cannot avoid bid advice, supplier-suitability representation or misleading certainty;
- a generic search product reproduces the paid value without AXIGNAL's governed history.

## 13. Decision state

```json
{
  "selected_universe": "eu_public_procurement",
  "commercial_name": "European Public Procurement Intelligence",
  "selection_task_state": "ACCEPTED",
  "source_admission_state": "NOT_PRODUCT_ADMITTED",
  "universe_admission_state": "NOT_SUPPORTED",
  "runtime_default": "DISABLED",
  "public_marketing_state": "PROHIBITED_UNTIL_UNIVERSE_GATE",
  "next_authorised_tasks": [
    "AX-F8-T03",
    "AX-F8-T04",
    "AX-F8-T05",
    "AX-F8-T06"
  ]
}
```
