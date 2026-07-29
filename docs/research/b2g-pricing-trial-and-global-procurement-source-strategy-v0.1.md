# B2G Pricing, Seven-Day Trial and Global Procurement Source Strategy v0.1

Date: `2026-07-29`
Status: `RESEARCH EVIDENCE / NOT PRODUCT OR PRICE ADMISSION`
Goal ID: `AXIGNAL-GOAL-001`
Governing decision: `ADR-013`
Governing contract: `28-b2g-procurement-commercial-and-global-source-program.md`

## 1. Research question

Can AXIGNAL enter public-procurement intelligence at a price that is commercially reachable for qualified SMEs and bid professionals while preserving premium B2G positioning, and can a seven-day free trial and global official-source programme be introduced without weakening source rights, epistemic authority or operating economics?

## 2. Current evidence and limitations

Public-procurement intelligence is an established commercial category. Current providers demonstrate several viable motions:

- low-friction or free opportunity discovery used as acquisition;
- paid professional intelligence for teams;
- bid qualification and preparation workflows;
- custom enterprise contracts, data, integration and support;
- time-limited free access in at least one comparable platform.

This evidence supports testing AXIGNAL's packaging. It does **not** prove:

- AXIGNAL's exact willingness to pay;
- conversion at any proposed price;
- retention;
- the value of AXIGNAL's visual interface alone;
- the accuracy or economic value of future predictions;
- demand for every jurisdiction;
- a right to ingest, store, transform, display or redistribute every official source.

## 3. Comparable commercial signals

### Stotles

Official product and pricing surfaces position Stotles as a B2G platform for public-sector sales and bidding. Current public packaging includes a free discovery layer, individual or basic access, team sales intelligence, bid qualification/preparation and custom expert plans.

Observed signal:

- public procurement users accept a ladder from free discovery to several hundred pounds per month for team intelligence;
- combined sales and bid workflows can approach the high hundreds of pounds per month;
- premium value is attached to qualification, buyer intelligence, collaboration and bid workflow rather than notice access alone.

Official references:

- `https://www.stotles.com/`
- `https://www.stotles.com/pricing`

### TenderAlpha

TenderAlpha publicly offers a seven-day free plan and paid procurement-data products, including broader data access and enterprise-oriented capabilities.

Observed signal:

- a seven-day procurement-intelligence trial is commercially plausible;
- trial existence does not establish which limits, qualification controls or conversion mechanism are optimal for AXIGNAL;
- broad international data can be sold, but coverage count is not proof of source fidelity or equal lifecycle depth.

Official references:

- `https://tenderalpha.com/platform/`
- `https://tenderalpha.com/`

### Deltek GovWin IQ

GovWin IQ demonstrates the upper end of the government-market-intelligence category through specialised federal, state, local and Canadian opportunity intelligence, analyst support and enterprise sales.

Observed signal:

- procurement intelligence can sustain a premium, sales-led category;
- enterprise value includes analyst interpretation, forecasts, market context and workflow support;
- a premium incumbent does not validate an early-stage AXIGNAL Enterprise price without buyer and delivery evidence.

Official reference:

- `https://www.deltek.com/en/products/business-development/govwin`

## 4. Pricing interpretation

The relevant market does not force a choice between `€20/month commodity SaaS` and `€50,000/year enterprise only`.

A plausible initial price ladder is:

| Commercial state | Candidate price | Purpose |
|---|---:|---|
| Design Partner | €300–€600/month per organisation | Paid validation with feedback and bounded support |
| Professional | €349–€499/month | One professional, admitted European scope, bounded ResearchRuns and dossiers |
| Team / Growth | €899–€1,499/month | Shared bid or advisory workflow, larger capacity and history |
| Enterprise | €18,000–€45,000/year starting band | Governance, API, private sources, security and contractual support |

These are hypothesis bands, not public prices.

### Why the entry band should not begin at €99

A €99 plan could increase top-of-funnel conversion but creates four risks:

1. anchors AXIGNAL against commodity alert products;
2. may not cover document processing, support and data operations;
3. attracts users without a recurring professional procurement workflow;
4. makes later premium repositioning harder.

The hypothesis can still be tested through a deliberately constrained discovery product, but not as the default full AXIGNAL workflow.

### Why Professional should not begin at €1,000

An entry price near €1,000 per month could preserve premium perception but may force a sales-led purchase for SMEs and independent advisers before product-market evidence exists.

The `€349–€499` band is therefore a candidate sweet spot because it:

- remains materially above commodity alert pricing;
- can be purchased by a professional team without full enterprise procurement in many cases;
- creates room for a strong team expansion tier;
- can support meaningful included capacity if processing is bounded;
- is testable through paid Design Partners.

## 5. Pricing experiment design

AXIGNAL SHOULD test offers, not abstract survey numbers alone.

### Experiment P1 — Paid Design Partner

Offer A:

- €350/month;
- one organisation;
- two users;
- bounded European ResearchRuns;
- direct onboarding;
- structured feedback commitment.

Offer B:

- €550/month;
- larger ResearchRun allowance;
- priority support;
- monthly workflow review;
- same core product authority and source coverage.

Measure:

- acceptance;
- time to first dossier;
- repeated use;
- operator support time;
- requests that indicate missing entitlement versus missing product value;
- renewal or conversion to annual plan.

### Experiment P2 — Professional annual commitment

Compare:

- monthly flexibility at the upper end of the band;
- annual commitment with a real, plainly disclosed saving or added capacity.

Do not use fabricated crossed-out pricing.

### Experiment P3 — Team value metric

Compare packaging based on:

- seats plus ResearchRuns;
- shared monitored opportunities plus dossiers;
- jurisdiction packs plus collaboration.

Do not expose provider token accounting as the customer value metric.

## 6. Seven-day trial viability

### 6.1 Why seven days can work

Seven days is sufficient when the product can immediately route a verified user to a relevant live opportunity and complete a ResearchRun without waiting for a rare publication event.

The period is too short when:

- onboarding requires extensive private-data integration;
- the user must wait for a new notice;
- dossier generation is not reliable;
- value depends on long-term alerts or historical outcome analysis;
- the user cannot identify a relevant category quickly.

AXIGNAL must therefore preload a relevant admitted search scope or allow the user to begin from an existing official notice.

### 6.2 Recommended controlled trial

| Dimension | Initial candidate |
|---|---|
| Duration | 7 consecutive days |
| Identity | Verified business email / organisation |
| Tenant | One server-resolved tenant |
| Users | Maximum 2 |
| Geography | European TED only, after product admission |
| ResearchRuns | 3 |
| Full dossiers | 2 |
| Documents/pages | Hard capped and displayed before processing |
| Saved opportunities | Bounded |
| Alerts | Standard cadence, bounded |
| Export | One trial-labelled export where rights permit |
| API | None |
| Bulk data | None |
| Private connectors | None |
| Predictions | None |
| Card | Prefer no card for first validation cohort |
| Expiry | Execution stops; short read-only period |
| Retention | Maximum 30-day candidate for tenant-private trial state |
| Conversion | Explicit plan selection only |

### 6.3 Trial risk register

| Risk | Failure mode | Required control |
|---|---|---|
| Compute abuse | Automated users process many documents | Hard ResearchRun, page, concurrency and cost ceilings |
| Source redistribution | User extracts bulk official data | No API, no bulk export, rate and behaviour controls |
| Multi-account abuse | Repeated free trials | Domain and organisation deduplication, cooling-off period |
| Privacy | Uploaded or annotated tenant data persists | Isolation, declared retention, deletion and backup expiry |
| Misleading authority | Trial outputs appear legally definitive | Evidence states, uncertainty, review boundary and prohibited copy |
| Silent billing | User is charged unexpectedly | No auto-conversion; affirmative plan selection |
| Poor activation | User sees no relevant opportunity | Guided CPV/geography onboarding and a relevant initial investigation |
| Support burden | Every trial requires manual research | Trial cannot scale until full value loop works without operator repair |
| Premium erosion | Free access appears equivalent to paid product | Severe capacity, collaboration, API, history and governance boundaries |

### 6.4 Trial decision metrics

The trial decision SHOULD use:

- verified-signup to first ResearchRun;
- ResearchRun to completed dossier;
- evidence-source drill-down;
- saved or monitored opportunity;
- return visit during seven days;
- qualified paid conversion or signed Design Partner commitment;
- variable cost per activated trial;
- operator support minutes;
- abuse blocks;
- deletion and expiry correctness;
- qualitative understanding of AXIGNAL's evidence boundary.

A conversion rate without activation, cost and trust evidence is insufficient.

## 7. Global official procurement-source strategy

### 7.1 Principle

There is no single worldwide TED. There is a federation of supranational, national, federal, regional, state, provincial, municipal and agency systems with different formats, legal bases, identifiers and lifecycle depth.

AXIGNAL should build:

```text
official source registry
+ source-specific adapters
+ canonical procurement model
+ reversible taxonomy crosswalks
+ evidence and lifecycle lineage
+ jurisdiction entitlements
```

It should not build:

```text
one scraper
+ one flattened notice table
+ unsupported worldwide coverage claim
```

### 7.2 Initial official-source inventory

| Region | Jurisdiction/system | Verified official access signal | Initial AXIGNAL state |
|---|---|---|---|
| Europe | EU TED Search API / ODS / eForms | Official API, open-data and versioned eForms resources | `TECHNICAL_PROBE` |
| Europe | UK Find a Tender / Contracts Finder | Official service and Contracts Finder API documentation | `DISCOVERED` |
| North America | US SAM.gov Contract Opportunities | Official Opportunities API with API-key and pagination model | `DISCOVERED` |
| North America | CanadaBuys | Official tender notices and contract-history/open-data resources; exact adapter feasibility still required | `DISCOVERED` |
| Latin America | Chile Mercado Público / ChileCompra | Official public API and procurement datasets | `DISCOVERED` |
| Latin America | Colombia SECOP | Official open-data datasets with OData/Socrata access | `DISCOVERED` |
| Latin America | Brazil Compras.gov.br | Official open-data portal and REST/OpenAPI services; service stability must be profiled | `DISCOVERED` |
| Asia | South Korea KONEPS | Official public-data REST APIs in JSON/XML | `DISCOVERED` |
| Asia | India Central Public Procurement / eProcure | Official portal; machine-access and rights profile must be independently verified | `DISCOVERED` |
| Oceania | Australia AusTender | Official central procurement portal and published reporting/data resources; adapter method requires verification | `DISCOVERED` |
| Oceania | New Zealand GETS | Official tender service and available feed/open-data mechanisms require profiling | `DISCOVERED` |
| Africa | South Africa eTenders | Official OCDS API/bulk publication with stated open licence | `DISCOVERED` |
| Africa | Nigeria NOCOPO | Official OCDS publication and public-use policy/licence | `DISCOVERED` |

The inventory is a research queue, not a product availability table.

### 7.3 Official reference entry points

- EU TED developer portal: `https://developer.ted.europa.eu/`
- UK Contracts Finder API: `https://www.contractsfinder.service.gov.uk/apidocumentation/home`
- US SAM.gov Opportunities API: `https://open.gsa.gov/api/get-opportunities-public-api/`
- CanadaBuys: `https://canadabuys.canada.ca/`
- ChileCompra API: `https://api.mercadopublico.cl/`
- Colombia SECOP open data: `https://www.datos.gov.co/`
- Brazil Compras.gov.br open data: `https://www.gov.br/compras/pt-br/acesso-a-informacao/dados-abertos`
- South Korea public data portal: `https://www.data.go.kr/`
- India eProcure: `https://eprocure.gov.in/eprocure/app`
- Australia AusTender: `https://www.tenders.gov.au/`
- New Zealand GETS: `https://www.gets.govt.nz/`
- South Africa eTenders OCDS API: `https://ocds-api.etenders.gov.za/`
- Nigeria NOCOPO: `https://nocopo.bpp.gov.ng/`
- OCDS standard: `https://standard.open-contracting.org/`

Every URL must be reverified during source admission. A landing page is not proof of a stable API or commercial reuse right.

## 8. Canonical model and taxonomy strategy

The global model should distinguish:

- procurement object taxonomy;
- supplier-industry taxonomy;
- geography;
- buyer identity;
- procedure and notice lifecycle;
- lot and award structure;
- monetary semantics;
- language and translation provenance.

Examples:

- CPV describes European procurement objects;
- NAICS primarily describes industries and supplier activity in North America;
- PSC describes US products and services;
- UNSPSC and national catalogues may be used in other systems.

A user-facing concept such as “custom software development” should resolve through a versioned semantic category linked to multiple source-native codes. The crosswalk must preserve:

- source code;
- source label and language;
- mapping method;
- mapping confidence or ambiguity;
- valid-from and valid-to dates;
- many-to-many relations;
- human-review state;
- rollback to the native representation.

Embeddings may support discovery but must not silently establish an authoritative taxonomy equivalence.

## 9. Recommended implementation sequence

### Immediate

- finish TED product admission;
- wire authenticated tenant → persistent ResearchRun → worker → dossier → InvestigationContext;
- validate one real professional B2G workflow;
- keep all non-TED systems catalogue-only.

### After the European paid-design-partner signal

- run bounded official technical probes for UK, US and one high-quality OCDS source;
- compare adapter complexity, rights, lifecycle completeness, user demand and cost;
- admit only the source that passes the complete gate.

### Subsequent expansion

- use customer demand to select LATAM jurisdiction packs;
- add Asia and Oceania through verified machine access;
- add Africa through OCDS and other official services where quality and rights pass;
- treat subnational portals as separate products when their value justifies operational fragmentation.

## 10. Commercial implications of global coverage

Global coverage should become an entitlement and expansion path, not an unpriced promise.

Possible later packaging:

- Europe core pack;
- North America pack;
- LATAM pack;
- selected Asia-Pacific pack;
- Global Enterprise pack;
- private or customer-specific source connector.

A pack can be sold only when its included sources, lifecycle depth, languages, freshness and export rights are explicitly disclosed.

A high-quality single jurisdiction can create more value than nominal coverage of 100 countries. Coverage marketing must therefore distinguish:

- listed source;
- searchable notice metadata;
- document access;
- lifecycle reconstruction;
- award history;
- evidence-linked dossier;
- monitored updates;
- API/export entitlement.

## 11. Decision

The research supports:

- adopting B2G as the first commercial narrative;
- testing a Professional entry band of `€349–€499/month`;
- testing Team / Growth at `€899–€1,499/month`;
- keeping Enterprise annual and custom from an initial `€18,000–€45,000/year` band;
- using paid Design Partners before freezing public pricing;
- implementing a capped seven-day trial only after the full E2E entitlement and deletion boundary exists;
- cataloguing global official procurement systems now;
- delaying actual non-TED product integration until the European E2E loop and paid-value gate pass.

## 12. Falsification conditions

The strategy must be revised if:

- qualified B2G users value only commodity alerts;
- the `€349–€499` entry band produces interest but no paid commitment;
- seven days cannot demonstrate value despite correct activation;
- trial cost, abuse or support burden is structurally unattractive;
- the trial damages premium perception;
- source rights prevent the evidence or export workflow users require;
- cross-jurisdiction normalisation destroys essential semantics;
- global-source demand is too fragmented to justify adapter operations;
- a narrower jurisdiction-specific product produces materially better retention and margin.
