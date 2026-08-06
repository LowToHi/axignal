# P15 — Energy and Climate Transition Library

## Task

`AX-GE2E-P15-T01`

## Status

`DRAFT_ENGINEERING_FOUNDATION / CANONICAL ACTIVATION BLOCKED`

P15 binds `AX-LIB-O08` to the **Transition Opportunity Workspace** on the
frozen, exact-head P14 engineering base.

## Materialised architecture

Eight bounded modules cover:

1. energy assets and projects;
2. technology, capacity and performance;
3. grid connection and system constraints;
4. policy support and market mechanisms;
5. emissions and carbon-accounting evidence;
6. tenant-scoped transition opportunity operations;
7. offtake, financing, delivery dependencies and risk;
8. external actions, outcomes and append-only audit.

The contract materialises 32 record types, 48 invariants, a 12-state
transition lifecycle, an 11-stage pipeline, 12 readiness gates, 40
conformance fixtures and 72 adversarial cases.

## Truth boundary

```text
project announced                 != project permitted
project permitted                 != financed
financed                          != under construction
under construction                != commissioned
commissioned                      != commercial operation
nameplate capacity                != available capacity
available capacity                != generated energy
connection application            != connection agreement
connection agreement              != energisation
policy target                     != binding support
support scheme                    != awarded support
emission factor                   != measured emissions
avoided-emission estimate         != realised abatement
offset or certificate             != physical energy attribute
offtake memorandum                != signed agreement
signed agreement                  != financial close
scenario                          != forecast
forecast                          != observed outcome
taxonomy alignment                != legal compliance
transition readiness              != external-action authority
```

## Authority ceiling

Browsers request, connectors and parsers create candidates, models propose,
and workers perform bounded mutations. Only typed humans may approve legal,
budget, pursuit, document or external-action decisions. Models and workers
cannot submit support or grid applications, sign offtake, order equipment,
trade environmental attributes, publish transition claims or commit capital.

## Source boundary

The five catalogue sources remain research-only:

- U.S. EIA Open Data;
- Eurostat Energy;
- ENTSO-E Transparency Platform;
- IRENA Statistics;
- Copernicus Climate Data Store.

Catalogue presence does not mean admission. Every source retains
`product_admitted=false`, `rights_status=UNREVIEWED`, no assumed scraping
permission and no public-coverage authority.

## Rollback

The P15 rollback removes every P15-only artifact, restores Contract Validation
byte-for-byte from frozen P14 and verifies that the complete resulting tree
equals `P14@f0ae67f8d38afbdb36e1b2e3d56e955b173fbe8d`.

## Activation boundary

Canonical activation and merge to `main` remain denied until transitive
programme dependencies, source rights, legal, finance, energy, product and
external-action gates are explicitly approved.
