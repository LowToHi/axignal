# TED product admission — bounded non-personal profile v1.0

Status: `PRODUCT_ADMITTED / FEATURE-FLAGGED / DERIVED NON-PERSONAL ONLY`

## Decision

AXIGNAL admits `src_ted_search_api_v3` only through `ted-eforms-non-personal@1.0.0`. This is not an unrestricted admission of every value or asset carried by TED.

The profile permits transient retrieval of official eForms XML and persistence of deterministic procedure, code, geography, lifecycle, date, count and monetary facts. It prohibits raw XML persistence or redistribution, personal contact values, protected logos, third-party protected material, model training and ambiguous buyer or winner identity values.

## Official basis

The review uses the TED legal notice, TED privacy statement, Search API and direct XML documentation, Commission Decision 2011/833/EU and the OP-TED eForms SDK 1.14.2 examples. The Publications Office identifies SIMAP metadata as reusable under CC0, while reuse remains subject to personal-data, third-party-rights, industrial-property and attribution constraints.

## Rights dimensions

| Dimension | Decision |
|---|---|
| Collection | Permitted for the bounded official endpoints |
| Transient XML processing | Permitted |
| Raw XML persistence | Prohibited by AXIGNAL policy |
| Raw XML redistribution | Prohibited by AXIGNAL policy |
| Non-personal derived persistence | Permitted with lineage |
| Internal display | Permitted for admitted derived facts |
| Customer display/export/API | Conditional: admitted derived facts only, attribution required |
| Model training | Prohibited |

## Privacy boundary

TED notices can contain personal and professional contact data. The parser counts personal-field elements to prove the exclusion path executes, but values never enter:

- Source Objects;
- Evidence Objects;
- Candidate Claims;
- canonical claims;
- dossiers;
- logs, traces or CI artifacts;
- model prompts, analytics, exports or public APIs.

Buyer and winner names or identifiers are also excluded from automatic persistence because an organisation field may identify a natural person or individual entrepreneur. A future entity-resolution profile requires a separate legal and privacy gate.

## Exact admitted technical profile

- eForms SDK release `1.14.2`;
- `CustomizationID=eforms-sdk-1.14`;
- UBL `2.3`;
- CN subtype `16` and CAN subtype `29`;
- one to four explicit publication numbers per authenticated ResearchRun;
- direct XML URL derived server-side;
- maximum `2 MiB` per XML;
- no redirect, URL credential, query string or alternate host;
- double deterministic parse and complete lifecycle validation;
- independent redownload before canonical admission.

## Attribution

Customer-visible derived evidence must identify TED and the Publications Office of the European Union, disclose that AXIGNAL selected, normalised and contextualised the data, and retain publication-number and notice-version lineage.

## Kill switch

Any rights change, personal-value leakage, unknown parser profile, lineage/hash mismatch, attribution failure or anomalous admission-rate change moves the source to suspended/quarantined operation. Both retrieval and admission processes must stop accepting new work.

## Not authorised

This decision does not authorise bulk ingestion, national portal scraping, public procurement marketing, billing, bid preparation or submission, supplier win probability, legal eligibility, profitability analysis or personalised advice.
