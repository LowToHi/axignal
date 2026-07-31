# P18 — Intent Intelligence & Knowledge Tides

**Task:** `AX-GE2E-P18-T01`  
**Engineering base:** `4f2d52bcff78bba020ede336f34e494b442fa898`  
**State:** `DRAFT_ENGINEERING_FOUNDATION`  
**Canonical activation:** blocked

## Objective

Implement privacy-safe intent intelligence and research-candidate generation.
P18 converts eligible interaction evidence into bounded private preference
proposals and privacy-suppressed aggregate Knowledge Tides. It does not turn
behaviour into consent, attention into market demand, or a research candidate
into an authorised ResearchRun.

## Frozen inputs

P18 binds byte-exactly to the P17 cross-library runtime and to the existing
`UserIntentEvent`, `AggregateIntentSignal`, `PreferenceProfile`, and
`ResearchCandidate` schemas. It adds no external source and no source
catalogue.

## Truth boundary

```text
one interaction             != preference
repeated interaction        != consent
pseudonymous                != anonymous
private intent              != aggregate tide
aggregate attention         != market demand
intent velocity             != causality
inferred preference         != confirmed preference
coverage gap                != external-world fact gap
Knowledge Tide              != admitted evidence
research candidate          != authorised ResearchRun
```

Knowledge Tides are internal analytical candidates. They describe eligible,
aggregated attention under a declared method and window. They cannot establish
commercial demand, user identity, legal applicability, truth, or product
priority by themselves.

## Architecture

P18 contains eight modules:

1. `INTENT_EVENT_GATE`
2. `PURPOSE_CONSENT_LEDGER`
3. `PRIVATE_PREFERENCE_MEMORY`
4. `COHORT_PRIVACY_AGGREGATOR`
5. `KNOWLEDGE_TIDE_ENGINE`
6. `MANIPULATION_BIAS_DEFENCE`
7. `RESEARCH_CANDIDATE_FACTORY`
8. `RETENTION_DELETION_AUDIT`

The materialised contract contains 32 record types and 48 invariants.

## Purpose separation

The five purposes are evaluated independently:

- execute investigation;
- private memory;
- product improvement;
- aggregate tides;
- model evaluation.

Permission for one purpose grants no authority for another. Continued use,
repeated use, silence, suggested prompts and campaign responses are not
consent. Revocation applies before the next materialisation.

## Private preference memory

Private memory is user-scoped and opt-in. One event creates only an observed
interest. Repeated evidence may create an inferred preference proposal.
Only an explicit user action can establish a confirmed preference.

Deletion creates a tombstone, removes the preference from future use and
invalidates open downstream materialisations. A model or worker cannot confirm,
restore or export a preference.

## Aggregate privacy

P18 makes no differential-privacy claim. It applies deterministic suppression:

- at least 20 unique eligible users;
- at least 5 unique organisations;
- no organisation above 25% of the cohort;
- at least 3 active days;
- reidentification risk must be `LOW`;
- sparse dimensions require at least 10 observations;
- no row-level, user-level or organisation-level output.

Pseudonymous identifiers never appear in Knowledge Tide or global research
candidate outputs. Cross-tenant row joins are prohibited. The global aggregate
path is a one-way privacy gate, not a product query over tenant rows.

## Influence and manipulation

Bot, internal-test, campaign, suggested-prompt and API-automation origins remain
explicit. They cannot be silently counted as spontaneous organic attention.
Dominant-organisation concentration, burst behaviour and coordinated influence
produce `COORDINATION_SUSPECTED` or quarantine rather than a growth signal.

## Knowledge Tide states

```text
EMERGING_ATTENTION
ACCELERATING_ATTENTION
PERSISTENT_ATTENTION
BROAD_ATTENTION
DECLINING_ATTENTION
COORDINATION_SUSPECTED
INSUFFICIENT_COHORT
PRIVACY_SUPPRESSED
```

The state is method-versioned and window-specific. It preserves campaign
influence, cohort eligibility, organisation diversity, coverage gaps,
contradiction pressure and manipulation risk.

## Research-candidate boundary

A candidate generated from a Knowledge Tide:

- has `PROPOSAL_ONLY` authority;
- contains no user, organisation-member or raw-message identifiers;
- includes aggregate scope and falsification conditions;
- may be prioritised only through current human review;
- cannot start, approve or fund a ResearchRun;
- cannot admit a source, evidence item or claim.

## Lifecycle

```text
CAPTURED
→ PURPOSE_CHECKING
→ ELIGIBLE_PRIVATE | ELIGIBLE_AGGREGATE
→ AGGREGATING
→ PRIVACY_REVIEW
→ TIDE_PROPOSED
→ CANDIDATE_PROPOSED
→ HUMAN_REVIEW
→ PRIORITISED
```

`SUPPRESSED` and `EXPIRED` are explicit terminal states for the affected
evidence version.

## Pipeline

```text
I01_RESOLVE_SCOPE
I02_VALIDATE_EVENT_SCHEMA
I03_ENFORCE_PURPOSE_PERMISSIONS
I04_CLASSIFY_ORIGIN
I05_UPDATE_PRIVATE_MEMORY
I06_BUILD_ELIGIBLE_COHORT
I07_APPLY_PRIVACY_SUPPRESSION
I08_COMPUTE_TIDE_DIMENSIONS
I09_DETECT_MANIPULATION
I10_PROPOSE_RESEARCH_CANDIDATE
I11_HUMAN_PRIORITISATION
```

## Authority

Models may propose canonical intent labels, preference hypotheses, tide
interpretations and research questions. They cannot grant consent, lower a
privacy threshold, recover a suppressed cohort, confirm a preference, create
an admitted fact, prioritise themselves or start research.

Workers may perform bounded aggregation and invalidation. They cannot mix
tenants, retain deleted input, widen purpose permissions or expose cohort
members.

## Verification

The P18 verifier checks:

- five frozen input bindings;
- eight modules, 32 records and 48 invariants;
- twelve lifecycle states and eleven pipeline stages;
- privacy thresholds and purpose separation;
- 40 deterministic conformance fixtures;
- 72 adversarial cases with zero canonical, ResearchRun, privacy-disclosure
  and authority-elevation deltas;
- byte-exact rollback to the frozen P17 head.

## Activation gate

Engineering evidence does not authorise canonical activation. P18 remains
blocked until P17 and transitive dependencies are accepted or normatively
superseded, privacy and deletion controls are validated, and typed human
Privacy, Research and Product authorities approve.
