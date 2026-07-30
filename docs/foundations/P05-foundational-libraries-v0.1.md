# P05 — Foundational Libraries v0.1

**Task:** `AX-GE2E-P05-T01`  
**State:** `DRAFT_ENGINEERING_FOUNDATION`  
**Canonical activation:** `false`  
**Stacked baseline:** `AX-GE2E-P04-T01@2977a6cd4056969313cf7356070eedf6f7d85ed0`

## Purpose

P05 converts the seven foundational contracts frozen in P02 into reusable,
machine-verifiable reference services. It does not admit real data, expose a
commercial product, create database migrations, or give canonical authority to a
connector, worker, model, browser or tenant workspace.

The implemented foundation consists of:

1. a strict common record envelope;
2. candidate and admitted authority separation;
3. bitemporal append-only history;
4. explicit cross-library references;
5. seven deterministic reference services;
6. conformance fixtures;
7. adversarial semantic tests;
8. exact rollback to the frozen P04 head.

## Dependency boundary

P05 depends on P04. P04 has exact-head engineering evidence, so preparatory
engineering can proceed on a stacked branch. Canonical activation remains
blocked because P04, P03 and P02 are not canonically accepted and P01 remains
incomplete.

```text
P04 engineering evidence ready       true
P04 canonical activation             false
P05 engineering branch authorised    true
P05 canonical activation             false
merge to main                        false
```

## Authority model

```text
browser                              zero canonical authority
model                                proposal only
connector                            candidate only
worker                               bounded candidate mutation
human data authority                 admission decision
independent admission runtime        deterministic admitted write
```

No proposal-store operation can address the admitted ledger directly. The
admitted ledger is append-only, bitemporal and protected by independent policy.

## Common record envelope

Every object carries:

- immutable object and library identifiers;
- object and schema type;
- authority state;
- exact source and rights snapshots;
- observed, recorded and validity times;
- jurisdiction and language context;
- classification;
- canonical payload hash;
- supersession reference.

Candidate and admitted records cannot share mutable storage. History is
represented through supersession and tombstones, never destructive updates.

## F01 — Jurisdiction and geography

The jurisdiction resolver treats codes as versioned assertions, not timeless
identifiers. It preserves disputed and overlapping scopes, historical
predecessors, geometry hashes, publisher versions and validity intervals.

Key fail-closed rules:

- no locale-to-jurisdiction inference;
- no label-to-geometry inference;
- no silent collapse of disputed boundaries;
- no code interpretation without scheme and time;
- no reversal of predecessor or successor direction.

## F02 — Entities, organisations and ownership

Entity resolution produces candidate matches only. Similar names or high model
confidence cannot merge records. Admitted merges are evidence-backed,
reviewable and reversible.

Ownership records preserve:

- direct versus indirect interest;
- observed ownership versus inferred control;
- percentage and class;
- jurisdiction;
- validity interval;
- evidence and reviewer.

Person objects default to restricted processing.

## F03 — Taxonomies and classifications

Taxonomy concepts are immutable within a version. Source-native codes and labels
are retained beside normalized forms. Crosswalks support all cardinalities and
distinguish equivalence, broader, narrower and related mappings.

Retired concepts remain available for historical records. Confidence is
metadata, not admission authority.

## F04 — Time, currency, value and units

The service maintains separate axes for publication, retrieval, observation,
event, validity, effectiveness, revision, vintage and recording.

It explicitly distinguishes:

```text
unknown
unavailable
not applicable
zero
```

Currency conversion requires a rate, provider, timestamp and method. Unit
comparison fails when dimensions are incompatible. Restatements append new
versions instead of overwriting earlier values.

## F05 — Languages, terminology and translation

Source-native text is immutable. Language, script, region and locale remain
separate. Translation and transliteration are different operations.

Machine translation is always proposed until reviewed and cannot establish
legal equivalence. Terminology remains scoped by domain, jurisdiction and
validity interval.

## F06 — Source rights and provenance

The service evaluates the ten rights dimensions independently:

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

Accessibility is never treated as permission. Ambiguous, expired, suspended or
revoked rights deny the affected action. Kill switches invalidate cached
decisions and in-flight convenience.

## F07 — Documents and content

Document versions and extracted content are immutable and content-addressed.
Every extraction references exact source bytes, parser version and deterministic
anchors.

Withdrawal, amendment, correction, supersession and attachment remain distinct
relations. Extraction confidence cannot substitute document authority or
signature verification.

## Cross-library joins

Every cross-library reference includes the target library, object, schema
version, resolution time and authority state.

A join:

- cannot raise the least-authoritative input;
- preserves contested entities and mappings;
- excludes revoked contributions;
- retains source-native text;
- requires temporal context for value normalization;
- keeps anchors bound to exact document versions;
- preserves all rights and lineage.

## Reference implementation

`scripts/p05_foundation_reference.py` provides deterministic functions for:

- value-state preservation;
- interval resolution;
- currency conversion;
- rights evaluation;
- document-anchor validation;
- least-authority propagation;
- canonical-write eligibility;
- entity candidate classification;
- crosswalk cardinality.

These functions are conformance references, not public runtime authority.

## Evidence

The P05 verifier validates:

- three Draft 2020-12 schemas;
- seven library implementations;
- exact compatibility with P02 contracts;
- exact rights compatibility with P03 and P04;
- 21 conformance fixtures;
- 49 adversarial cases;
- deterministic reference functions;
- dependency and authority ceilings.

## Rollback

The rollback removes the eleven P05-only artifacts, restores the P04 workflow,
preserves seven P04 authority artifacts and compares the complete tracked tree
with the frozen P04 head.

## Explicit exclusions

P05 does not:

- admit a real source;
- ingest production data;
- create production tables or APIs;
- migrate existing tenant data;
- claim global coverage;
- activate opportunity libraries;
- grant canonical authority to AI;
- authorize exports, billing or launch.

## Canonical acceptance path

Canonical activation requires dependency resolution, all conformance and
adversarial tests, exact rollback, and explicit approval from Human Data,
Rights and Product Authorities.
