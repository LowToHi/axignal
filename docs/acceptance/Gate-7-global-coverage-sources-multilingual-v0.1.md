# Gate 7 — Global coverage, sources and multilingual acceptance

## Status

```text
CONTRACT IMPLEMENTED
LIBRARY EVIDENCE FILES 0/16
GATE DECISION IN_PROGRESS
GLOBAL COVERAGE CLAIM DENIED
MULTILINGUAL CLAIM DENIED
PUBLIC LAUNCH NO_GO
```

## Purpose

Gate 7 creates one evidence-backed coverage report for every AXIGNAL library before
P27. It does not admit sources, approve rights, accept a library or authorise a
public claim. It makes missing evidence explicit and prevents engineering runtime
presence from being represented as production coverage.

The report covers exactly:

```text
AX-LIB-F01–AX-LIB-F07
AX-LIB-O01–AX-LIB-O09
```

## Binding definitions

```text
"global" = evidence of actual coverage + disclosure of material limitations
"multilingual" = ingestion + normalisation + search + presentation verified
"source admitted" = legal + technical + quality + rights + human authority
```

A source catalogue, accessible API, successful parser, CI fixture or candidate
connector is not an admitted source.

## Evidence architecture

The gate is split into three immutable layers:

1. `global-coverage-source-language-index.v0.1.json` defines the complete library
   set, runtime bindings, required languages and required authorities.
2. `data/acceptance/library-coverage/AX-LIB-*.json` contains one independent
   evidence file per library. Missing files are materialised as `MISSING` rather
   than inferred from source catalogues or engineering tests.
3. `verify_gate7_global_coverage.py` generates and validates the consolidated JSON
   and Markdown reports.

The generated report records, for every library:

- countries covered;
- languages and all four multilingual journey stages;
- sectors;
- historical depth;
- declared and observed update frequency;
- active, suspended and candidate sources;
- rights evidence and expiry;
- quality metrics;
- ingestion/publication lag;
- typed reviews and expiry;
- limitations;
- synthetic-data disclosure;
- kill-switch implementation and rehearsal;
- rollback implementation and rehearsal;
- bounded claim decision.

## Source admission

An active source is invalid unless all five gates are `PASS`:

```text
LEGAL
TECHNICAL
QUALITY
RIGHTS
HUMAN_AUTHORITY
```

The source must also:

- be in state `PRODUCT_ADMITTED`;
- have current, content-addressed evidence;
- have current rights or an explicit non-expiring rights decision;
- never be present simultaneously in another source bucket.

Candidate, suspended, revoked and rejected sources have zero public-claim
contribution. A suspended or revoked source may remain in the report for audit and
coverage-loss disclosure, but it cannot contribute to claims or current quality
metrics.

## Multilingual acceptance

The required initial language profile is:

```text
en  English
es  Spanish
fr  French
de  German
pt  Portuguese
it  Italian
```

Each language must have current evidence for:

```text
INGESTION
NORMALISATION
SEARCH
PRESENTATION
```

Translation fixtures or semantic-parity unit tests alone do not satisfy this gate.
The evidence must exercise the real source, normalisation, index/query and user
presentation path for the accepted head.

## Typed reviews

Every library must carry current approvals from:

- Product;
- Security;
- Privacy/Data Rights;
- Legal;
- Source Quality;
- UX/Accessibility;
- Human Coverage Authority.

Reviews are expiring, signed and bound to a manifest reference. A rejection or an
expired approval cannot be hidden by aggregate metrics.

## PASS contract

A library passes only when all of the following are true:

```text
canonical_state = ACCEPTED
countries_covered != empty
sectors != empty
active admitted sources != empty
historical_depth = PASS with current evidence
update_frequency = PASS with observed evidence
rights = PASS with current evidence
quality = PASS with current evidence
lag = PASS with current evidence
all required language journeys = PASS
all required typed reviews = APPROVE and current
limitations != empty
synthetic data disclosed and excluded from public claims
kill switch implemented, tested and evidenced
rollback implemented, tested and evidenced
claim_decision = APPROVED
```

Gate 7 returns `PASS` only if all sixteen libraries pass. Until then, all public
claim flags remain false and public claim text is forbidden.

## Adversarial guarantees

The verifier rejects at least these conditions:

- a global claim while the gate is `IN_PROGRESS` or `REJECTED`;
- an active source without complete admission;
- a suspended source contributing to a claim;
- undisclosed synthetic data contributing to a claim;
- duplicate source, language, library or review-authority identifiers;
- expired source evidence, rights or human reviews;
- Gate 7 `PASS` without tested kill switch and rollback;
- a library evidence file that changes its indexed identity or runtime binding.

## Current truthful state

All sixteen future evidence files are absent by design at the start of this gate.
The verifier therefore emits a complete report in which every missing field is
explicit, every library claim is `DENIED` and the aggregate decision is
`IN_PROGRESS`.

Existing P02–P16 engineering evidence remains useful input, but it does not become
canonical source, coverage, rights or multilingual acceptance automatically.

## Closure and P27 boundary

The ordinary pull-request workflow validates truthfulness and may pass while the
gate decision remains `IN_PROGRESS`. Final acceptance must execute the workflow
with `require_gate_pass=true`; that mode fails unless the consolidated report is
`PASS`.

Even `Gate 7 = PASS` does not authorise public launch. P27 must bind the accepted
Gate 7 artifact and its expiry to the final exact-head
`acceptance_manifest_digest` and receive all required launch-authority approvals.
