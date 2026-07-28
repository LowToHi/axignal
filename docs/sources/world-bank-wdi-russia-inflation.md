# World Bank WDI — Russian Federation consumer-price inflation

Status: `ADMITTED / BOUNDED DATASET`
Goal ID: `AXIGNAL-GOAL-001`
Source ID: `world-bank-wdi`
Review date: `2026-07-27`

## Purpose

Provide one reproducible country-level macroeconomic observation for the Moscow real-estate ResearchRun vertical slice:

- country: Russian Federation (`RUS`);
- indicator: `FP.CPI.TOTL.ZG`;
- label: Inflation, consumer prices (annual %);
- source collection: World Development Indicators;
- use: contextual observed fact, never local-property causality or personalised advice.

## Access contract

- API: World Bank Indicators API v2;
- authentication: none;
- scheme: HTTPS only;
- allowlisted host: `api.worldbank.org`;
- exact path: `/v2/country/RUS/indicator/FP.CPI.TOTL.ZG`;
- output: JSON;
- maximum request count per ResearchRun: `1`;
- maximum response size: `524288` bytes;
- timeout: `10` seconds;
- redirects: prohibited;
- credentials in URL: prohibited;
- non-standard ports: prohibited.

Canonical request shape:

```text
https://api.worldbank.org/v2/country/RUS/indicator/FP.CPI.TOTL.ZG
  ?format=json
  &mrnev=5
  &per_page=5
  &source=2
```

## Rights decision

The World Bank dataset terms state that datasets are CC BY 4.0 unless specifically labelled otherwise. The selected indicator page labels this indicator CC BY 4.0.

Allowed for this source record:

- commercial use: yes;
- transformation: yes;
- inclusion in AXIGNAL outputs: yes;
- redistribution of the data observation: yes, with attribution;
- model training: not authorised by this source record;
- removal of attribution: prohibited.

Required attribution:

> World Bank Open Data — World Development Indicators; changes and derived interpretation by AXIGNAL.

Terms and dataset references:

- `https://www.worldbank.org/ext/en/legal/terms-conditions/datasets`
- `https://datacatalog.worldbank.org/public-licenses`
- `https://data.worldbank.org/indicator/FP.CPI.TOTL.ZG?locations=RU`
- `https://datahelpdesk.worldbank.org/knowledgebase/articles/898581-api-basic-call-structures`

## Epistemic contract

The structured response is parsed deterministically. The parser may produce only an observed-fact Candidate Claim with:

- exact country;
- exact indicator code;
- exact period;
- exact numeric value;
- unit;
- raw-response hash;
- retrieval time;
- rights snapshot;
- method version.

A local or external language model is not needed for this source. If a model rewrites or proposes an interpretation, that proposal cannot pass automatic observed-fact admission.

The admitted fact may state the national annual inflation observation. It must not state or imply that inflation caused, guarantees or predicts a specific Moscow property outcome.

## Coverage and limitations

- annual, not monthly;
- country-level, not Moscow-level;
- latest period may lag the current date;
- underlying series includes third-party statistical inputs described by World Bank metadata;
- suitable as macro context only;
- insufficient on its own for an opportunity score or transaction recommendation.

## Kill switch

Set `axignal_global.sources.kill_switch = true` when:

- licence or dataset metadata changes;
- API response shape changes;
- attribution cannot be preserved;
- values conflict with the dataset metadata;
- request volume is challenged by the provider;
- the connector follows a redirect or leaves the allowlist;
- legal review revokes the admission decision.

The worker must fail closed and preserve the ResearchRun error state. It must not substitute another source silently.

## Bank of Russia quarantine note

The Bank of Russia Statistics API is registered separately as `QUARANTINED / RIGHTS_PENDING`. Its public API documentation is technically suitable, but the general website agreement does not provide sufficiently explicit commercial reuse and redistribution permission for AXIGNAL. Network access remains disabled until a source-specific rights review admits it.
