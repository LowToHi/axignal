# P02 — Individual Library Contracts and Adversarial Semantics

Version: `0.1.0`  
Task: `AX-GE2E-P02-T01`  
Status: `DRAFT INDIVIDUAL CONTRACTS / CANONICAL ACTIVATION BLOCKED`

## Purpose

This increment turns the P02 registry foundation into an explicit contract catalog for every declared library:

- `AX-LIB-F01` through `AX-LIB-F07`;
- `AX-LIB-O01` through `AX-LIB-O09`.

Each contract freezes its entity surface, predicates, events, lifecycle, temporal axes, jurisdiction rules, taxonomy references, exclusions, workspace type and acceptance-test identifiers. Shared invariants remain centralised so individual libraries cannot weaken rights, evidence, admission, rollback or canonical-ledger boundaries.

## Shared non-negotiable invariants

```text
ambiguous rights                    → RESTRICTED
generative direct admission         → false
evidence mutability                 → false
source-native values preserved      → true
unknown / unavailable / zero        → distinct
workspace canonical-ledger mutation → false
public product availability         → false
rollback preserves lineage          → true
```

Every opportunity library depends on all seven foundational libraries and references the same opportunity lifecycle and graph-role profile. No opportunity library may privately redefine identity, rights, evidence, time, taxonomy or canonical admission.

## Individual contract surface

The machine-readable catalog is:

```text
data/ontology/library-contracts.v0.1.json
schemas/library-contract-catalog.schema.json
```

The catalog contains exactly:

```text
7 foundational contracts
9 opportunity contracts
16 contracts total
```

Opportunity contracts declare the canonical workspace types already registered by P02, including Bid, Application, Compliance, Project Pursuit, Account, Country and Market Strategy, Supply, Transition and Innovation workspaces.

## Adversarial semantic cases

`data/ontology/p02-adversarial-cases.v0.1.json` freezes twelve fail-closed cases:

1. missing publication time remains unknown and is not replaced by retrieval time;
2. publication, retrieval and observation axes remain distinct;
3. candidate entity matches cannot silently merge identities;
4. entity splits preserve predecessor and successor lineage;
5. taxonomy crosswalks remain reversible many-to-many mappings;
6. source-native taxonomy codes and labels remain immutable;
7. generative output cannot directly request `ADMISSIBLE` state;
8. technically accessible sources with ambiguous rights become `RESTRICTED`;
9. missing values remain unknown rather than zero;
10. tenant-private workspaces cannot mutate the canonical Claim Ledger;
11. suspended or revoked sources contribute zero new admitted claims;
12. trend-only evidence cannot make an opportunity actionable.

## Deterministic verification

`scripts/verify_p02_library_contracts.py` validates:

- the Draft 2020-12 catalog schema;
- exact contract identity and cardinality;
- registry/catalog name, version, state and workspace agreement;
- dependency closure across F01–F07 and O01–O09;
- shared rights, evidence, AI-admission and rollback invariants;
- entity-resolution and taxonomy reversibility;
- complete temporal-axis semantics;
- execution of all twelve adversarial cases;
- continued P01 dependency and canonical activation fail-closed state.

The verifier is part of the existing `Contract Validation` workflow.

## Truth boundary

This increment does not:

- accept or supersede P01;
- authorize merge to canonical `main`;
- admit a source or library;
- implement database, API, parser, runtime or UI resources;
- create global coverage, legal, eligibility or commercial claims;
- permit a model or workspace to mutate canonical evidence or claims.

P02 remains engineering evidence on an isolated branch until P01 is accepted or a normative ADR explicitly supersedes that dependency, rollback evidence exists and Human Product Authority approves activation.
