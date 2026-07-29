# TED Search API v3 and official notice downloads

- Status: `TECHNICAL_PROBE / NOT_PRODUCT_ADMITTED`
- Goal ID: `AXIGNAL-GOAL-001`
- Source ID: `src_ted_search_api_v3`
- Universe: `eu_public_procurement`
- Review date: `2026-07-29`
- Operational owner: `source-admission`

## 1. Purpose

Provide the first official machine-access path for the European Public Procurement Intelligence universe:

```text
bounded expert query
→ JSON Search API result projection
→ official notice URLs by format and language
→ complete XML notice retrieval when required
→ immutable raw-evidence reference
→ deterministic eForms extraction
```

This source record authorises a technical probe only. It does not authorise production ingestion, customer display, export, API redistribution or model training.

## 2. Access contract

### Search API

- endpoint: `https://api.ted.europa.eu/v3/notices/search`;
- method: `POST`;
- authentication: none;
- transport: HTTPS only;
- redirects: prohibited by the AXIGNAL connector;
- credentials in URL: prohibited;
- non-standard ports: prohibited;
- response: JSON search envelope containing the requested fields and official URLs for notice formats and languages;
- pagination modes: `PAGE_NUMBER` and `ITERATION`;
- maximum notices per page: `250`;
- maximum fields per page: `10000`;
- page-number mode maximum retrievable notices: `15000`;
- iteration mode: no total-result limit documented, but still bounded per page;
- exact query length, clause and fair-use limits must be enforced from current official documentation rather than inferred.

Official references:

- `https://docs.ted.europa.eu/api/latest/search.html`
- `https://docs.ted.europa.eu/ODS/latest/reuse/search-api.html`
- `https://op.europa.eu/en/web/ted-reusers-workshops/questions_and_answers_2023_12_14`

### Complete notice

Search projections are discovery and index data. The complete notice should be retrieved from the official TED URL in XML when a canonical claim depends on a field not fully represented in the projection.

Official notices can also be downloaded in daily or monthly XML packages. Direct links support XML, HTML and PDF variants in official EU languages.

References:

- `https://docs.ted.europa.eu/ODS/latest/reuse/index.html`
- `https://ted.europa.eu/en/help/data-reuse`

## 3. Representation boundary

The API and eForms ecosystem contain three distinct JSON/XML roles:

1. **Search API envelope — JSON**
   - query result count;
   - fields explicitly requested;
   - official URLs for available formats and languages;
   - pagination or iteration token.

2. **Canonical notice — XML**
   - complete published eForms or legacy TED notice;
   - authoritative raw source for deterministic field extraction;
   - versioned according to notice and procedure lifecycle.

3. **eForms SDK field repository — JSON**
   - parser metadata;
   - business-term identifiers, field contexts, XML paths, types and code lists;
   - not procurement evidence by itself.

AXIGNAL must not silently treat a JSON search projection as equivalent to a complete XML notice.

## 4. Initial bounded query

The technical probe pins the exact query demonstrated by the Publications Office in its official TED reusers workshop. It deliberately uses Luxembourg as a transport-contract probe; it is not the commercial geography configuration.

```json
{
  "query": "place-of-performance IN (LUX)",
  "fields": [
    "publication-number",
    "notice-title",
    "buyer-name",
    "notice-type"
  ],
  "limit": 3,
  "scope": "ACTIVE",
  "checkQuerySyntax": false,
  "paginationMode": "PAGE_NUMBER",
  "page": 1
}
```

The connector may execute only this fixed, reviewed query profile during the initial probe. User-provided arbitrary expert-query strings and the later Spain/France/Germany commercial query are not admitted at this stage.

## 5. Rights decision

TED's legal notice states:

- procurement notices published in the Supplement to the Official Journal may generally be freely reused for commercial or non-commercial purposes unless otherwise stated;
- SIMAP metadata is dedicated to the public domain under CC0 1.0;
- editorial website content is licensed under CC BY 4.0;
- source credit and disclosure of changes are required where applicable;
- identifiable persons and third-party works may require additional rights;
- protected logos and industrial-property material are excluded.

Reference:

- `https://ted.europa.eu/en/legal-notice`

### Current dimension decision

| Dimension | State | Initial interpretation |
|---|---|---|
| Collection | `PERMITTED` | Fixed official Search API probe |
| Transient processing | `PERMITTED` | Parse and validate non-personal projected fields |
| Persistent storage | `CONDITIONAL` | Raw notice storage requires personal/third-party field controls |
| Derived calculations | `CONDITIONAL` | Only from admitted non-personal fields and reproducible methods |
| Internal display | `CONDITIONAL` | Attribution and personal-data minimisation required |
| Customer display | `CONDITIONAL` | Not authorised by this probe record |
| Export | `CONDITIONAL` | Not authorised by this probe record |
| API redistribution | `CONDITIONAL` | Not authorised by this probe record |
| Model training | `UNKNOWN` | Explicitly outside the technical probe |

## 6. Personal-data boundary

TED notices may contain:

- contact-person names;
- professional email addresses;
- professional telephone numbers;
- natural persons as tenderers or contractors in specific cases;
- addresses and other contact details.

The initial AXIGNAL profile must:

- request only non-personal Search API fields;
- avoid persisting contact-person fields;
- exclude personal fields from model prompts, analytics, exports and public APIs;
- never use personal contact data as evidence of opportunity quality;
- prevent cross-notice or cross-source person profiling;
- require a separate legal basis and retention rule before any personal field is used.

The Publications Office states that notice-related personal data may remain on TED for ten years before internal archival. That source retention practice is not automatically an AXIGNAL retention entitlement.

## 7. Epistemic contract

The Search API probe may establish only:

- that the official endpoint responds under the reviewed request contract;
- that returned publication numbers and projected fields conform structurally;
- that official notice-format URLs are supplied when present;
- that a response hash, retrieval timestamp and query identity can be recorded;
- that no personal fields were requested or persisted.

It may not establish:

- completeness of every notice;
- validity of every buyer identifier;
- existence of values, criteria, deadlines, winners or offer counts in every notice;
- a supplier's eligibility or suitability;
- probability of winning;
- profitability;
- commercial support for the universe.

## 8. Known source limitations

Official TED documentation records important limitations, including:

- some search fields apply differently to eForms and legacy TED XML notices;
- source-entered time zones can be wrong and must not be silently guessed;
- winner information and some relationships may be missing;
- large queries and some open-data paths have performance constraints;
- notice and procedure identifiers require explicit version and lineage handling;
- old notice formats may still appear in historical data.

Missing or inconsistent values must remain `UNKNOWN`, `UNCOVERED` or `CONTESTED`, never zero.

## 9. Quality gates for promotion

The source cannot move from `TECHNICAL_PROBE` toward `SANDBOX` or `PRODUCT_ADMITTED` until evidence proves:

1. stable fixed-query access and bounded retry behaviour;
2. exact request and response-size budgets;
3. schema validation for the Search API envelope;
4. official XML URL validation and immutable hashing;
5. eForms SDK version detection;
6. notice subtype and legacy-format classification;
7. personal-field exclusion;
8. attribution rendering;
9. version and correction lineage;
10. country/subtype field-completeness metrics;
11. outage and kill-switch behaviour;
12. source-specific legal and privacy review.

## 10. Kill switch

Disable `src_ted_search_api_v3` when:

- rights or the legal notice materially change;
- endpoint or response shape drifts;
- the connector leaves the allowlisted host or path;
- personal fields enter a probe artifact;
- attribution cannot be preserved;
- unknown eForms versions are parsed as known;
- notices are silently treated as complete despite absent fields;
- rate-limit or fair-use requirements cannot be met;
- source-specific review revokes the probe.

The connector must fail closed and must not substitute a national portal, scraper or commercial aggregator silently.
