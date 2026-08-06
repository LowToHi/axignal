# P02 — Global Ontology and Library Contracts

Version: `0.1.0`  
Task: `AX-GE2E-P02-T01`  
Status: `DRAFT IMPLEMENTATION FOUNDATION / CANONICAL ACTIVATION BLOCKED`

## 1. Purpose

P02 freezes the reusable semantic contracts that every foundational library, opportunity library, source connector, Evidence Object, Candidate Claim, Canonical Claim, entity-resolution decision, taxonomy mapping, temporal query and operational workspace must share.

The target is not a universal ontology. The target is a **small, versioned and reversible contract surface** that prevents each library from inventing incompatible meanings for identity, evidence, time, rights, classification and opportunity state.

## 2. Transition boundary

The implementation branch is authorised to begin. Canonical activation is not.

At branch creation, `main` still records:

```text
AX-GE2E-P01-T01  IN_PROGRESS
P02 authorised   false
```

Therefore this branch may add schemas, registries, tests and design evidence, but it must not:

- mark P01 accepted;
- claim buyer personas, budgets or pricing are validated;
- change any source to `PRODUCT_ADMITTED` or `COMMERCIAL`;
- represent any draft library as product availability;
- enable public global-coverage claims;
- merge P02 into canonical `main` without the P01 gate or a normative superseding ADR.

This distinction preserves historical truth while allowing engineering preparation to proceed.

## 3. Contract families

P02 defines nine reusable contract families:

| ID | Contract | Responsibility |
|---|---|---|
| `AX-ONT-U01` | `UniverseContract` | Bounded semantic, rights, jurisdiction and time scope |
| `AX-ONT-L01` | `LibraryContract` | Versioned foundational or opportunity-library surface |
| `AX-ONT-S01` | `SourceContract` | Access, rights, lineage, quality, parser and kill switch |
| `AX-ONT-EV01` | `EvidenceContract` | Immutable source-bound evidence and extraction lineage |
| `AX-ONT-C01` | `ClaimContract` | Atomic assertion and epistemic lifecycle |
| `AX-ONT-OP01` | `OpportunityContract` | Evidence-backed opportunity subgraph and pursuit linkage |
| `AX-ONT-EN01` | `EntityContract` | Identity, aliases, identifiers and reversible resolution |
| `AX-ONT-TX01` | `TaxonomyContract` | Source-native classifications and reversible crosswalks |
| `AX-ONT-TM01` | `TemporalContract` | Independent publication, retrieval, observation, event, validity, effective, revision and vintage time |

## 4. Foundational libraries

The seven foundational libraries are shared dependencies for every opportunity library:

1. `AX-LIB-F01` — Jurisdiction and geography
2. `AX-LIB-F02` — Entities, organisations and ownership
3. `AX-LIB-F03` — Taxonomies and classifications
4. `AX-LIB-F04` — Time, currency, value and units
5. `AX-LIB-F05` — Languages, terminology and translation
6. `AX-LIB-F06` — Source rights and provenance
7. `AX-LIB-F07` — Documents and content

No opportunity library may redefine these semantics privately.

## 5. Opportunity libraries

P02 registers the contract boundary for all nine opportunity libraries and their operational workspace type. Every opportunity library depends on all seven foundational libraries, but remains independently versioned, admitted and reversible.

The registry does not claim that any library is implemented, accepted, commercial or globally available.

## 6. Canonical semantic boundaries

### 6.1 Universe

A universe is a bounded set of admissible subjects, source versions, jurisdictions, temporal scope and explicit exclusions. It is not a marketing coverage claim.

Unknown scope remains unknown. An unavailable source contributes no claims.

### 6.2 Source

Technical accessibility never implies admissibility. Rights are evaluated independently for collection, processing, storage, model input, calculation, display, export, redistribution and training/evaluation.

Ambiguous rights default to `RESTRICTED`.

### 6.3 Evidence

Evidence is immutable and source-bound. Original source-native values and canonical values are both retained. Evidence without a rights snapshot cannot be admitted.

Evidence Objects, Candidate Claims and Canonical Claims are separate objects.

### 6.4 Claim

Claims are atomic, scoped, time-bounded and typed. Observed, calculated, inferred, predictive and legal/regulatory semantics remain distinct.

Generative output cannot directly enter the canonical Claim Ledger.

### 6.5 Entity

Entity resolution is confidence-bearing and reversible. Merges, splits, aliases, renamings, ownership changes and identifier changes are time-bounded.

Observed and inferred relationships are never collapsed into one undifferentiated edge.

### 6.6 Taxonomy

Source-native identifiers, versions and labels are preserved. Crosswalks are reversible many-to-many proposals until admitted.

### 6.7 Time

Publication, retrieval, observation, event, validity, effective, revision and vintage time are independent axes. Missing time is represented as unknown with a reason, never silently replaced by “now”.

### 6.8 Opportunity

An opportunity is a versioned evidence-backed subgraph connected to a tenant-private operational pursuit. It is not a generated paragraph.

Operational workspace state cannot mutate the canonical Claim Ledger.

## 7. Cross-library invariants

The machine-readable registry freezes ten initial invariants:

- immutable IDs with explicit replacements;
- original and canonical values preserved together;
- rights independent from accessibility;
- no generative bypass of admission;
- epistemic classes remain distinct;
- unknown, unavailable and zero remain distinct;
- cross-library joins preserve full lineage;
- tenant-private operations cannot mutate shared canonical evidence;
- entity resolution and taxonomy crosswalks are reversible;
- draft libraries and sources cannot appear commercial or globally available.

## 8. Machine-readable artifacts

```text
schemas/global-ontology-registry.schema.json
data/ontology/global-ontology-registry.v0.1.json
scripts/verify_p02_ontology_foundation.py
```

The verifier proves:

- schema validity;
- exactly seven foundational libraries;
- exactly nine opportunity libraries;
- all opportunity libraries depend on all foundational libraries;
- exactly nine contract families;
- required epistemic, source, rights and temporal semantics;
- no draft library is represented as product availability;
- canonical activation remains fail-closed while P01 is not accepted.

## 9. Acceptance path

Canonical P02 activation requires all of the following:

1. P01 accepted, or a normative ADR explicitly superseding the dependency.
2. Schema and registry validation.
3. Individual contracts for F01–F07 and O01–O09.
4. Temporal ambiguity tests.
5. Reversible entity-resolution tests.
6. Reversible taxonomy-crosswalk tests.
7. Tests proving AI cannot bypass admission.
8. Rollback rehearsal.
9. Human Product Authority approval.

Until then, this work remains a draft implementation foundation.

## 10. Explicit exclusions

This first P02 increment does not implement:

- database migrations;
- API resources;
- runtime entity resolution;
- taxonomy ingestion;
- source admission;
- Opportunity Operations persistence;
- UI;
- public coverage;
- commercial activation.

Those are later increments after the contract surface is reviewed and frozen.
