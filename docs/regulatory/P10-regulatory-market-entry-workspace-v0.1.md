# P10 — Regulatory Library and Market Entry Workspace v0.1

## Status

```text
Task                              AX-GE2E-P10-T01
Engineering state                 DRAFT_ENGINEERING_FOUNDATION
Canonical state                   BLOCKED
Canonical activation authorised   false
Merge to main allowed             false
Normative dependency              AX-GE2E-P07-T01
Engineering base                  P09@841e068f0a8e86e6d89733d3958ecd43f0d7eca7
```

## Objective

Implement regulation intelligence and the **Market Entry and Compliance Opportunity Workspace** without creating unsupported source, product, legal, commercial or launch claims.

P10 specialises `AX-LIB-O03 — Regulatory and Policy Demand`. It does not authorise production source activation, personalised legal advice, automatic compliance conclusions, market-entry approval, signature, regulatory filing, authorisation, enforcement outcomes or canonical authority.

## Dependency truth

The canonical programme declares P07 as the normative dependency. P09 is only the cumulative engineering base:

```text
P07 Opportunity Operations Core
→ P08 Procurement engineering
→ P09 Grants engineering
→ P10 Regulatory engineering
```

Engineering readiness does not imply canonical acceptance.

## Core semantic boundary

P10 preserves these distinctions:

```text
policy announcement  ≠ draft instrument
draft instrument     ≠ adopted instrument
adopted instrument   ≠ published instrument
published instrument ≠ instrument in force
instrument in force  ≠ instrument applicable to a subject
applicability        ≠ compliance
control mapped       ≠ control implemented
control implemented  ≠ control effective
registration         ≠ authorisation
notification         ≠ approval
filing               ≠ receipt
receipt              ≠ acceptance
inspection           ≠ finding
finding              ≠ sanction
sanction             ≠ remediation
workspace READY      ≠ legal advice
workspace READY      ≠ compliance guarantee
workspace READY      ≠ filing authority
```

Unknown, contested, stale, revoked, repealed or insufficiently anchored legal material fails closed.

## Library binding

```text
Library ID       AX-LIB-O03
Canonical name   Regulatory and Policy Demand
Workspace        Market Entry and Compliance Opportunity Workspace
```

Entities:

- `RegulatoryOpportunity`
- `RegulatoryInstrument`
- `Obligation`
- `Consultation`
- `EnforcementAction`
- `AffectedSector`

Predicates:

- `ISSUED_BY`
- `APPLIES_TO`
- `CREATES_OBLIGATION`
- `AMENDS`
- `REPEALS`
- `ENFORCED_BY`

Events:

- `INSTRUMENT_PUBLISHED`
- `CONSULTATION_OPENED`
- `RULE_EFFECTIVE`
- `RULE_AMENDED`
- `RULE_REPEALED`

Taxonomies: NACE, NAICS and CPC.

## Eight domain modules

### Instrument Registry

Service: `regulatory_instrument_registry`

Preserves immutable instrument versions, amendments, repeal lineage and source-native identifiers. Proposal, adoption, publication, effect and application remain separate. Consolidated text is a derived view and never erases authoritative versions.

### Authority and Jurisdiction

Service: `regulatory_authority_scope_service`

Separates issuer, competent authority, enforcement authority and filing recipient. Jurisdiction, territorial scope, personal scope, market scope and extraterritorial reach remain explicit. Probabilistic resolution remains candidate-only.

### Applicability and Obligations

Service: `regulatory_applicability_service`

Binds applicability to entity, product, activity, jurisdiction, time and exact instrument version. Separates obligations, prohibitions, permissions, exemptions and thresholds. Hierarchy conflicts and unresolved definitions require human legal review.

### Consultation and Transition

Service: `regulatory_change_service`

Separates consultation, draft, policy announcement, adopted instrument, guidance and transition period. Publication, entry into force, application and enforcement dates remain independent. A consultation or draft is never automatically binding law.

### Market Entry Workspace

Service: `market_entry_workspace_service`

Binds one server-resolved tenant, P07 pursuit, target jurisdiction, market, product/service scope, activity scope and instrument version set. Opening requires approved `PURSUE`. Membership grants no legal, signature, filing or activation authority.

### Compliance Controls

Service: `compliance_control_service`

Maps controls to exact obligations and anchors. Design, implementation, testing and operating evidence remain separate. Stale or revoked evidence contributes zero readiness. Model-generated remediation remains proposal-only.

### Authorisation and Filing

Service: `regulatory_authorisation_service`

Separates preparation, declaration, signature, external filing, receipt, acceptance, renewal, variation and withdrawal. Only typed human signatory and filing authority may execute consequential actions.

### Enforcement Outcomes

Service: `regulatory_enforcement_service`

Separates allegation, inspection, finding, enforcement action, sanction, remediation, appeal and closure. Every non-unknown external outcome requires observed evidence.

## Lifecycle

```text
DISCOVERED
PROPOSED
CONSULTATION_OPEN
ADOPTED
PUBLISHED
EFFECTIVE_PENDING
APPLICABLE
MARKET_ENTRY_ASSESSMENT
COMPLIANCE_PREPARATION
READINESS_REVIEW
AUTHORISED_OR_FILED
AMENDED_REPEALED_OR_CLOSED
```

Rules:

- unlisted transitions are denied;
- transitions bind exact instrument and workspace versions;
- drafts and consultations cannot transition directly to `APPLICABLE`;
- effective and application dates are independently verified;
- amendment or repeal invalidates dependent applicability and readiness;
- `AUTHORISED_OR_FILED` requires typed human filing authority and observed receipt evidence;
- terminal re-entry requires a superseding opportunity or decision;
- lifecycle state is not legal advice or a compliance guarantee.

## Operating pipeline

```text
R01_DISCOVER
→ R02_NORMALIZE_INSTRUMENT
→ R03_RESOLVE_AUTHORITY_SCOPE
→ R04_EXTRACT_APPLICABILITY
→ R05_ASSESS_OBLIGATIONS
→ R06_OPEN_MARKET_ENTRY_WORKSPACE
→ R07_MAP_CONTROLS_EVIDENCE
→ R08_VALIDATE_READINESS
→ R09_HUMAN_AUTHORISE_FILE
→ R10_RECORD_ENFORCEMENT_OUTCOME
→ R11_REASSESS_CHANGE
```

Discovery, extraction and control mapping produce candidates. Authority/scope and applicability assessments produce proposals. Workspace opening, filing and external outcome recording require humans. Readiness and change invalidation are deterministic. Default and indeterminate decisions are `DENY`.

## Applicability contract

Ten classes:

1. `LEGAL_STATUS`
2. `JURISDICTION`
3. `TERRITORIAL_SCOPE`
4. `PERSON_SCOPE`
5. `ENTITY_TYPE`
6. `SECTOR_OR_PRODUCT`
7. `ACTIVITY`
8. `THRESHOLD`
9. `EFFECTIVE_DATE`
10. `EXEMPTION_OR_TRANSITION`

States:

```text
UNKNOWN
NOT_APPLICABLE
PENDING_EVIDENCE
PASS
FAIL
CONTESTED
SUPERSEDED
```

Decision semantics:

```text
mandatory FAIL                         DOES_NOT_APPLY
UNKNOWN/PENDING_EVIDENCE/CONTESTED     REVIEW_REQUIRED
verified exemption                     EXEMPT
all required criteria PASS             APPLIES
missing criterion set                  NOT_READY
hierarchy conflict                     REVIEW_REQUIRED
```

These are governed operational decisions, not personalised legal advice.

## Obligation contract

Ten obligation types:

```text
OBLIGATION
PROHIBITION
PERMISSION
EXEMPTION
REPORTING
REGISTRATION
AUTHORISATION
NOTIFICATION
RECORDKEEPING
DISCLOSURE
```

Negation, modality, thresholds, dates, exceptions and filing instructions are critical dimensions. Repealed or superseded obligations contribute zero future readiness. Guidance-derived practices remain distinct from binding obligations.

## Regulatory time model

P10 never collapses announcement, consultation, adoption, publication, entry into force, application, transition, reporting, filing, inspection, decision and appeal dates. Every operative time preserves timezone, calendar, jurisdiction, source and uncertainty. Missing time is never replaced with `now`.

## Control and evidence model

Control states:

```text
NOT_MAPPED
PROPOSED
IMPLEMENTED
TESTED
EFFECTIVE
INEFFECTIVE
SUPERSEDED
```

Evidence types:

```text
DESIGN
IMPLEMENTATION
OPERATING
FILING
AUTHORISATION
TRAINING
MONITORING
AUDIT
REMEDIATION
EXCEPTION
```

A mapped control does not prove implementation, and implementation does not prove effectiveness.

## Twelve readiness gates

```text
INSTRUMENT_CURRENT
LEGAL_STATUS_VERIFIED
JURISDICTION_SCOPE_RESOLVED
APPLICABILITY_ASSESSED
OBLIGATIONS_MAPPED
EXEMPTIONS_TRANSITIONS_RESOLVED
CONTROLS_MAPPED
EVIDENCE_CURRENT
AUTHORISATIONS_IDENTIFIED
REPORTING_FILING_READY
APPROVALS_CURRENT
CHANNEL_AND_AUTHORITY_VERIFIED
```

```text
all PASS                               READY
any DENY                              DENY
UNKNOWN/INDETERMINATE/CONTESTED/STALE REVIEW_REQUIRED
missing gate                          NOT_READY
instrument change                     INVALIDATED
```

`READY` grants no signature, filing or market-entry authority.

## Filing boundary

Action types include authorisation, registration, notification, filing, declaration, renewal, variation and withdrawal.

Required P07 approvals:

```text
PURSUE
BUDGET
RIGHTS
LEGAL
DOCUMENT
SUBMISSION_OR_ACTIVATION
```

External filing also requires current instruments, verified recipient authority, verified channel, active rights, valid audit chain, inactive kill switch and typed human filing authority.

## Enforcement outcomes

```text
UNKNOWN
AUTHORISED
CONDITIONALLY_AUTHORISED
REJECTED
INSPECTION_OPEN
NON_COMPLIANCE_FOUND
SANCTIONED
REMEDIATED
CLOSED
```

`UNKNOWN` is distinct from no enforcement. Inspection does not imply finding; finding does not imply sanction; remediation does not imply closure. Appeals and corrections supersede rather than erase history.

## Multilingual legal semantics

Engineering profile: English, Spanish, French, German, Portuguese and Italian.

Critical dimensions:

- legal status;
- applicability;
- obligations;
- prohibitions;
- exemptions;
- thresholds;
- dates;
- negation;
- modality;
- filing instructions.

Critical mismatch produces `DENY`. Critical unknown produces `REVIEW_REQUIRED`. Source-native legal text remains authoritative and translation is never automatic legal equivalence.

## Source catalogue boundary

The catalogue contains EUR-Lex, CELLAR, US Federal Register, Regulations.gov, legislation.gov.uk and Canada Gazette.

All remain:

```text
status                       RESEARCH_CATALOGUE_NOT_PRODUCT_AVAILABILITY
product_admitted             false
rights_status                UNREVIEWED
public_coverage_authorised   false
```

Catalogue listing is not source admission and scraping permission is not assumed.

## Rights and authority

P10 inherits the ten P03 rights dimensions: collection, transient processing, persistent storage, model input, derived calculations, internal display, customer display, export, API redistribution and model training/evaluation.

Authority ceiling:

```text
browser                     request only
connector/OCR/parser        candidate only
model                       proposal only
worker                      bounded work mutation
market-entry operator       tenant-scoped operation
human legal authority       legal interpretation approval only
human compliance approver   typed approval only
human signatory             declarations and signatures only
human filing authority      external filing only
human enforcement authority observed outcome recording only
admission runtime           deterministic write after approval
```

Models and workers cannot declare applicability, provide authoritative personalised legal advice, approve entry, sign, file or create enforcement outcomes.

## Evidence matrices

Conformance matrix:

```text
8 modules × 5 fixture classes = 40 fixtures
```

Adversarial matrix:

```text
9 scopes × 8 threats = 72 cases
```

Threats cover stale/repealed versions, non-binding material escalation, unsupported scope or threshold inference, missing or contested evidence, revoked rights, cross-tenant references, authority escalation and fabricated external outcomes.

Every case preserves:

```text
canonical_delta         0
external_filing_delta   0
```

## Rollback

P10 rollback verifies the exact diff against `P09@841e068f0a8e86e6d89733d3958ecd43f0d7eca7`, hashes seven P09 authority files, removes eleven P10 artefacts, restores the workflow and compares the complete tree byte-for-byte with P09.

## Truth boundary

```text
P01 canonical state                  IN_PROGRESS
P02-P09 canonical activation        false
P09 engineering evidence ready       true
P10 canonical state                  BLOCKED
P10 canonical activation            false
merge to main                        false
external regulatory filings            0
production regulatory sources          0
public legal/compliance claims          0
commercial activation                none
```

P10 remains engineering evidence until the dependency chain and Human Regulatory, Legal, Compliance, Filing, Rights and Product authorities approve it.