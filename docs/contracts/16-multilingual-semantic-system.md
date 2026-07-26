# 16 — AXIGNAL Multilingual Semantic System Contract

Version: `0.3.1`
Status: `NORMATIVE CANDIDATE`
Goal ID: `AXIGNAL-GOAL-001`

## 1. Purpose

AXIGNAL MUST operate as a multilingual knowledge system, not as an English product translated at presentation time.

Launch locales:

- English `en` — default;
- Spanish `es`;
- French `fr`;
- German `de`;
- Portuguese `pt-BR`, with terminology compatibility for `pt-PT`;
- Simplified Chinese `zh-Hans`.

## 2. Canonical identifiers

Schemas, APIs, predicates, event types and code identifiers MUST remain canonical English identifiers.

Example:

```text
claim_type
evidence_strength
contradiction_pressure
valid_until
source_authority
```

User-facing labels MAY be localised. Their semantic identifier MUST not change by locale.

## 3. Evidence preservation

Every multilingual evidence object MUST preserve:

- original text or extract;
- original language;
- source and publication context;
- canonical entity references;
- translated rendering where available;
- translation provider or method;
- translation version;
- translation confidence;
- terminology warnings;
- human-review status.

The translated text MUST never replace the original.

## 4. Claim representation

A claim MAY include:

```text
original-language assertion
→ canonical structured claim
→ English canonical rendering
→ locale-specific user rendering
```

The structured subject, predicate, value, units, time and geography remain shared across languages.

## 5. User controls

Claim and evidence surfaces MUST support:

- translated view;
- original view;
- side-by-side view where useful;
- source-language indicator;
- translation-confidence indicator when material;
- terminology notes;
- report of a translation defect.

## 6. Entity resolution

The entity registry MUST support:

- local names;
- official names;
- historical names;
- aliases;
- transliterations;
- abbreviations;
- language-specific ordering;
- jurisdiction identifiers;
- ambiguous-name disambiguation.

Example aliases for the same geography may include:

```text
Moscow
Moscú
Moscou
Moskau
Moscou / Moscovo according to locale usage
Москва
莫斯科
```

Canonical entity identity MUST not depend on the user language.

## 7. Search

Multilingual search MUST combine:

- exact local-language matching;
- canonical entity matching;
- transliteration;
- synonyms and controlled terminology;
- multilingual semantic retrieval;
- language-aware ranking;
- typed filters;
- match explanation.

Equivalent queries SHOULD produce semantically equivalent result sets subject to source-language coverage.

## 8. Navigator

The Navigator MUST:

- detect supported language;
- preserve original input;
- map intent to canonical command types;
- use canonical entities;
- execute one shared InvestigationContext;
- respond in the active locale;
- cite evidence independently of response language;
- expose ambiguity and translation uncertainty.

## 9. Terminology registry

AXIGNAL MUST maintain versioned terminology for:

- epistemic states;
- claim types;
- opportunity states;
- financial and economic terms;
- legal and regulatory concepts;
- data-rights language;
- user-consent language;
- Globe, Graph and Timeline interactions.

Critical terms MUST receive human linguistic review before paid production.

## 10. Locale formats

The UI MUST localise:

- dates;
- time zones;
- numbers;
- decimal and grouping separators;
- currencies;
- measurement units;
- plural rules;
- address formats where applicable.

Canonical stored values MUST remain explicit and locale-neutral.

## 11. Portuguese policy

Initial Portuguese UI uses `pt-BR` as the primary locale because it offers the largest initial audience hypothesis.

The terminology registry MUST identify terms that differ materially in `pt-PT`. A later complete `pt-PT` locale requires its own QA gate.

## 12. Chinese policy

Initial Chinese UI uses Simplified Chinese `zh-Hans`.

The architecture MUST not assume that `zh-Hans` and Traditional Chinese `zh-Hant` are interchangeable. `zh-Hant` requires a later supported-locale decision and QA gate.

## 13. Translation authority

Machine translation MAY produce candidate renderings.

It MUST NOT:

- alter canonical numeric values;
- change units or currencies silently;
- convert an inference into an observation;
- remove uncertainty;
- expand legal permission;
- overwrite source language;
- create an admitted claim.

## 14. High-risk terminology

Terms affecting these areas require elevated review:

- recommendation or suitability;
- probability and certainty;
- legal obligation;
- sanctions;
- property rights;
- financial instrument classes;
- risk and return;
- contradiction and falsification;
- source rights and export permissions;
- user consent.

## 15. Multilingual analytics

Analytics MUST distinguish:

- interface locale;
- original query language;
- source language;
- translation path;
- language-specific success and failure;
- entity-resolution ambiguity;
- unsupported-language fallbacks.

A higher failure rate in one language MUST not be hidden by global averages.

## 16. Performance

Language support MUST not require serial translation on every page view when stable renderings can be versioned and cached.

The system SHOULD use:

- canonical structured data;
- precomputed critical UI strings;
- cached claim renderings;
- asynchronous translation candidates;
- explicit fallback to original or English when unavailable.

Fallback MUST be labelled.

## 17. Accessibility

- language changes MUST be declared semantically;
- fonts MUST support required scripts;
- line height and density MUST accommodate German and Chinese differences;
- truncation MUST not hide material qualifiers;
- screen-reader labels MUST be localised;
- bidirectional architecture SHOULD remain possible even though no RTL locale is in the launch set.

## 18. QA corpus

The regression corpus MUST include equivalent tasks in all launch languages:

- navigate to a geography;
- discover a universe;
- change Globe/Graph lens;
- inspect a claim;
- inspect evidence;
- identify contradiction;
- set historical time;
- save a trail;
- configure private memory;
- understand Knowledge Tide language.

## 19. Acceptance criteria

The multilingual system is accepted when:

- core commands map to equivalent canonical intent across six languages;
- original evidence is always recoverable;
- translation provenance is visible;
- critical terminology passes human QA;
- entities resolve across aliases and transliteration;
- locale formats are correct;
- no translation changes epistemic type or certainty;
- language-specific task success stays within approved parity tolerance;
- unsupported or uncertain translation is clearly labelled.
