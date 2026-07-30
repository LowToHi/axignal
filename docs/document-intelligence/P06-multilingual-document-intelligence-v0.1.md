# P06 — Multilingual and Document Intelligence v0.1

Task: `AX-GE2E-P06-T01`

Status:

```text
DRAFT_ENGINEERING_FOUNDATION
CANONICAL_ACTIVATION_AUTHORISED = false
```

## 1. Purpose

P06 materialises a bounded multilingual document-intelligence contract over the
P05 foundational libraries. It provides deterministic interfaces for:

- six-language semantic parity;
- native document extraction;
- OCR fallback;
- layout and reading-order reconstruction;
- mixed-language segmentation;
- version-pinned anchors;
- document-authority isolation;
- privacy, rights and revocation controls.

This increment does not admit real sources, ingest production documents, make
legal interpretations, or activate a public product.

## 2. Stacked dependency

P06 is engineered against the frozen P05 head:

```text
AX-GE2E-P05-T01@07de87e4ff79b19110394c8901db6a98e0be87b2
```

Canonical activation remains blocked by P05 and its transitive P04, P03, P02 and
P01 dependencies.

## 3. Language profile

The engineering profile freezes six BCP 47 languages:

| Tag | Script | Reference locale |
|---|---|---|
| `en` | `Latn` | `en-GB` |
| `es` | `Latn` | `es-ES` |
| `fr` | `Latn` | `fr-FR` |
| `de` | `Latn` | `de-DE` |
| `pt` | `Latn` | `pt-PT` |
| `it` | `Latn` | `it-IT` |

The profile is an executable engineering set. It does not claim universal
language coverage.

## 4. Semantic parity

Parity is tested independently across twelve dimensions:

1. source identity;
2. document version;
3. section structure;
4. obligations;
5. eligibility;
6. amounts;
7. dates;
8. negation;
9. modality;
10. named entities;
11. taxonomy codes;
12. citation anchors.

Critical mismatches in obligations, eligibility, amounts, dates, negation,
modality or citation anchors produce `DENY`. Unknown critical dimensions require
review. Aggregate embedding similarity cannot override a dimension-level
mismatch.

## 5. Source-native preservation

The source document remains authoritative as a version-pinned reference.

```text
source bytes
source text
source language
source layout
source identifiers
source taxonomy codes
```

Translations and semantic alignments are separate candidate objects. They
cannot overwrite source-native material or be presented as automated legal
equivalence.

## 6. Document pipeline

```text
D01_REFERENCE
→ D02_PREFLIGHT
→ D03_NATIVE_EXTRACTION
→ D04_OCR_FALLBACK
→ D05_LAYOUT_RECONSTRUCTION
→ D06_LANGUAGE_SEGMENTATION
→ D07_SEMANTIC_ALIGNMENT
→ D08_ANCHOR_VALIDATION
→ D09_HUMAN_ADMISSION
```

Every stage records immutable inputs, outputs, versions, rights snapshots,
classification and reason codes.

## 7. Native extraction and OCR

Native extraction is preferred for born-digital documents. OCR is a fallback
for scanned pages, image-only regions or declared document profiles.

Supported candidate modes:

- `NATIVE_TEXT`;
- `OCR_TEXT`;
- `TABLE_STRUCTURE`;
- `FORM_FIELDS`;
- `IMAGE_REGION_METADATA`.

OCR requires pinned engine, language-pack, preprocessing and layout versions.
Confidence is retained at token, line, block, page and document levels.

A high average confidence cannot hide a low-confidence critical span.

## 8. Layout and tables

Document intelligence preserves:

- page boundaries;
- bounding boxes;
- reading order;
- sections;
- table rows and columns;
- cell spans;
- headers;
- image regions;
- source-to-extraction lineage.

Row/column swaps, hidden-text disagreements and non-deterministic reading order
are quarantined.

## 9. Mixed-language documents

Language is assigned to segments rather than forced onto the whole document.

```text
DECLARED
DETECTED
MIXED
UNKNOWN
CONTESTED
```

Locale is not inferred from country alone. Script, language, region and locale
remain independent properties.

## 10. Anchors

Six anchor types are defined:

- `BYTE_RANGE`;
- `PAGE_BOX`;
- `TEXT_SPAN`;
- `SECTION_PATH`;
- `TABLE_CELL`;
- `IMAGE_REGION`.

An anchor binds:

```text
document_id
document_version
content_digest
anchor_type
page_index
geometry
quote_digest
extractor_version
created_at
```

Resolution fails closed when document version, content digest, geometry or quote
digest does not match. Stale or ambiguous anchors contribute zero canonical
evidence.

## 11. Document authority

Authority states are:

```text
RAW_REFERENCE
EXTRACTED_CANDIDATE
TRANSLATION_CANDIDATE
SEMANTIC_CANDIDATE
HUMAN_REVIEWED
ADMITTED
REVOKED
SUPERSEDED
```

Authority ceiling:

| Actor | Maximum authority |
|---|---|
| Browser | zero canonical authority |
| Connector | candidate only |
| OCR engine | candidate only |
| Parser | candidate only |
| Translation model | proposal only |
| Semantic model | proposal only |
| Worker | candidate only |
| Human Document Authority | approval only |
| Independent Admission Runtime | deterministic write after approval |

The least-authoritative input bounds all derived objects.

## 12. Rights and privacy

P06 inherits the ten rights dimensions from P03, P04 and P05. Missing,
ambiguous, expired, conflicting or revoked rights produce `DENY`.

Unknown classification defaults to `RESTRICTED`. Secrets are excluded from
ordinary extraction, logs, fixtures and exports. Personal-data detection can
propose a stricter classification but cannot lower one.

OCR and parser runtimes are isolated, non-root, bounded and network-denied by
default.

## 13. Quality contract

Quality is measured using:

- native-text coverage;
- OCR character accuracy;
- OCR word accuracy;
- layout fidelity;
- reading-order accuracy;
- table-cell accuracy;
- language-segment accuracy;
- anchor-resolution rate;
- critical parity match rate;
- unresolved-span rate.

Thresholds are specific to language, document class and extractor version.
Unknown metrics do not pass.

## 14. Evidence suite

The frozen suite contains:

```text
languages                6
parity dimensions       12
pipeline stages           9
extraction modes          5
anchor types              6
conformance fixtures     30
adversarial cases        54
```

Each language includes fixtures for born-digital extraction, scanned
low-confidence OCR, mixed-language segmentation, legal negation and stale
anchors.

Adversarial coverage includes:

- loss of negation;
- modality strengthening;
- locale-specific amount corruption;
- ambiguous date normalisation;
- entity merge through translation;
- taxonomy-code translation;
- anchor version mismatch;
- hidden text versus rendered-page mismatch;
- document prompt injection;
- personal-data leakage;
- rights revocation during OCR;
- withdrawn documents represented as current;
- table row/column swaps;
- reading-order corruption;
- low-confidence auto-admission;
- translation represented as legal original;
- OCR engine version drift;
- mixed-script confusables.

Every adversarial case has canonical delta zero.

## 15. Observability

P06 emits metrics for preflight, native extraction, OCR fallback, quarantine,
language segmentation, parity review, parity denial, anchor failures, rights
denials, revocation, candidates and admission.

Alerts cover unsupported formats, archive bounds, hidden-text disagreement,
prompt injection, low critical confidence, parity mismatch, anchor mismatch,
secret or personal-data leakage, revoked-document activity, authority
escalation and rollback residue.

## 16. Rollback

Rollback removes only the eleven P06 artifacts, restores the P05 workflow and
compares the complete tree byte-for-byte with the frozen P05 baseline.

P05 authority files are hashed before and after rollback.

## 17. Truth boundary

```text
P01 canonical state                  IN_PROGRESS
P02 canonical activation            false
P03 canonical activation            false
P04 canonical activation            false
P05 engineering evidence ready       true
P05 canonical activation            false
P06 engineering preparation          true
P06 canonical activation            false
merge to main                        false
production documents ingested         0
real OCR providers activated           0
public multilingual claim              0
```

## 18. Excluded scope

This increment does not include:

- production document upload;
- a live OCR provider;
- customer document persistence;
- legal advice;
- canonical translations;
- real-source admission;
- public language-coverage claims;
- billing;
- commercial activation;
- launch.
