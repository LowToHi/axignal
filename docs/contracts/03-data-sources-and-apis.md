# 03 — Data Sources and APIs Contract

Version: `0.1.0`
Status: `NORMATIVE`

## 1. Principle

ASIGNAL MUST treat data rights, provenance, latency and transformation quality as product capabilities.

A source is not admissible merely because it is technically accessible or publicly visible.

## 2. Source admission record

Every source MUST have a versioned record containing:

- `source_id` and canonical name;
- owner and jurisdiction;
- access mechanism;
- authentication method;
- official documentation URL;
- licence or contractual basis;
- commercial-use status;
- storage permission;
- transformation permission;
- display and redistribution permission;
- derived-claim permission;
- attribution requirements;
- retention restrictions;
- personal-data classification;
- market-data classification;
- latency and expected update schedule;
- rate limits and fair-use rules;
- reliability tier;
- lineage group;
- parser version;
- operational owner;
- legal-review date;
- status and kill switch.

## 3. Rights dimensions

Rights MUST be evaluated separately for:

1. collection;
2. transient processing;
3. persistent storage;
4. model input;
5. derived calculations;
6. internal display;
7. customer display;
8. export;
9. API redistribution;
10. model training or evaluation.

Permission in one dimension MUST NOT be inferred for another.

## 4. Source states

- `DISCOVERED`
- `LEGAL_REVIEW`
- `TECHNICAL_PROBE`
- `SANDBOX`
- `INTERNAL_ONLY`
- `PRODUCT_ADMITTED`
- `RESTRICTED`
- `SUSPENDED`
- `REVOKED`

A source MUST default to `RESTRICTED` when rights are ambiguous.

## 5. Initial public and institutional sources

The following sources are candidates for the foundation programme. Inclusion does not equal automatic product admission.

### European Central Bank Data Portal

Use cases:

- exchange rates;
- interest rates;
- monetary and financial statistics;
- selected market and banking indicators.

Official API documentation: `https://data.ecb.europa.eu/help/api/overview`

### Eurostat and European Commission statistical services

Use cases:

- demographic, economic, industrial and regional indicators;
- NUTS geography;
- labour, housing, trade and sector context;
- AMECO macroeconomic series.

Official entry points:

- `https://ec.europa.eu/eurostat/`
- `https://economy-finance.ec.europa.eu/economic-research-and-databases/economic-databases/ameco-database/bulk-downloads-and-api-access_en`

### TED Open Data and Search API

Use cases:

- procurement notices;
- buyers, awards, classifications and dates;
- contract renewal and pre-procurement research.

Official documentation:

- `https://docs.ted.europa.eu/api/latest/`
- `https://docs.ted.europa.eu/ODS/latest/`

### SEC EDGAR

Use cases:

- company submissions;
- XBRL facts;
- filings and event disclosures;
- public-company entity and event claims.

Official resources:

- `https://www.sec.gov/about/developer-resources`
- `https://data.sec.gov/`

ASIGNAL MUST implement the SEC identification and fair-access requirements, including an appropriate `User-Agent`.

### World Bank Data and Data360

Use cases:

- global development and sovereign indicators;
- market, population, infrastructure and sector context;
- trade and tariff information where available.

Official resources:

- `https://datahelpdesk.worldbank.org/knowledgebase/articles/889392-about-the-indicators-api-documentation`
- `https://data360.worldbank.org/en/api`
- `https://wits.worldbank.org/witsapiintro.aspx`

### Additional public-source candidates

Subject to source admission:

- IMF data services;
- OECD data services;
- national statistics offices;
- government open-data portals;
- regulatory registers;
- company registers where lawful;
- patents, scientific publications and standards metadata;
- central-bank and ministry publications;
- geospatial and cadastral open data;
- public grant and subsidy registers.

## 6. Commercial-data candidates

Commercial sources MAY be added only after a clear unit-economic case.

Candidate categories:

- delayed and real-time market data;
- private-company and transaction databases;
- property listings and valuation data;
- shipping, trade and supply-chain data;
- on-chain data;
- crowdfunding and marketplace intelligence;
- news and event feeds;
- company, people and ownership datasets.

A commercial source contract MUST record whether derived claims may be displayed independently from raw data.

## 7. Prohibited assumptions

ASIGNAL MUST NOT assume that it can scrape or redistribute:

- banking portals;
- Alibaba or other commercial marketplaces;
- property portals;
- Kickstarter or crowdfunding platforms;
- broker platforms;
- exchange websites;
- paywalled research;
- social networks;
- private databases;
- customer dashboards.

Each requires an official API, licence, partnership, user-authorised connector or documented legal basis.

## 8. Connector architecture

Every connector MUST implement a common interface:

```text
probe()
authenticate()
fetch(cursor, window)
normalise(raw_object)
checkpoint()
report_quality()
report_rights()
revoke()
```

Each fetch MUST produce:

- raw object reference;
- source timestamp;
- retrieval timestamp;
- checksum;
- cursor or request identity;
- response metadata;
- parser version;
- licence snapshot reference.

## 9. Raw-data storage

Raw responses SHOULD be stored immutably in object storage when permitted.

The canonical database MUST store only references and metadata necessary to reproduce lineage. Raw retention MUST follow source-specific rights and privacy rules.

## 10. Normalisation

The platform MUST canonicalise:

- entities;
- identifiers;
- currencies;
- units;
- dates and time zones;
- geographies;
- classifications;
- source language;
- corporate and instrument identifiers;
- asset and opportunity types.

Original values MUST be preserved alongside canonical values.

## 11. Entity resolution

Entity resolution MUST be confidence-scored and reversible.

No low-confidence merge may silently combine:

- companies;
- funds;
- issuers;
- public bodies;
- properties;
- people;
- instruments;
- projects.

The system MUST support aliases, mergers, renamings, parent-child relationships and identifier changes over time.

## 12. Freshness

Freshness MUST be source-relative.

Each source MUST declare:

- publication cadence;
- collection cadence;
- expected delay;
- next expected update;
- stale threshold;
- expired threshold;
- outage behaviour.

The UI MUST NOT label monthly or quarterly data as real-time.

## 13. Data quality

Each ingestion batch MUST record:

- completeness;
- schema conformance;
- duplicate rate;
- missing-key rate;
- parse failures;
- unexpected value distribution;
- timeliness;
- entity-resolution confidence;
- source drift;
- rights status.

Material degradation MUST quarantine affected claims and downstream opportunities.

## 14. API-key and credential handling

- Secrets MUST be stored in a dedicated secret manager or encrypted deployment secret mechanism.
- Secrets MUST NOT be committed, logged or embedded in client bundles.
- Connector credentials MUST use least privilege.
- Rotation procedures and expiry alerts MUST exist.
- User-authorised connections MUST be tenant-scoped and revocable.

## 15. Source attribution

The UI and API MUST preserve required attribution. Attribution MUST travel with derived products where contractually required.

## 16. Kill switch

Every source MUST support immediate disabling without requiring a full deployment.

Disabling a source MUST trigger evaluation of:

- claims dependent on it;
- corroboration status;
- opportunity status;
- cached API output;
- exports;
- user alerts.

## 17. Source admission gate

A source reaches `PRODUCT_ADMITTED` only when:

- access is stable;
- rights are documented;
- parser and normalisation tests pass;
- provenance is complete;
- quality metrics meet universe thresholds;
- operational cost is acceptable;
- outage and revocation behaviour is tested;
- user-facing attribution is implemented.
