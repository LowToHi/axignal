# P08 — Global Procurement Library + Bid Workspace v0.1

Task: `AX-GE2E-P08-T01`

Status: `DRAFT_ENGINEERING_FOUNDATION`

Canonical activation: `false`

## 1. Purpose

P08 specialises the domain-neutral Opportunity Operations Core for global public procurement.

It implements the engineering contract for:

- procurement notices and versions;
- buyers and contracting authorities;
- procedures and governing rules;
- lots and lot constraints;
- requirements, eligibility and exclusion grounds;
- Bid Workspaces;
- bid documents and evidence packs;
- commercial and pricing models;
- submission records;
- award and contract observations.

P08 does not authorise production-source admission, legal compliance conclusions, autonomous bidding, external submission, signature, price commitment, acceptance of terms or public claims of global coverage.

## 2. Dependency boundary

P08 is stacked on the frozen P07 engineering head:

```text
AX-GE2E-P07-T01@e30f800cb284f1381c28c4ccbc116a8da4a9fe92
```

P07 engineering evidence is available, but P07 canonical activation remains false.

The transitive P01–P06 canonical dependencies also remain unresolved.

Therefore:

```text
P08 engineering work allowed       true
P08 canonical activation           false
merge to main                      false
external procurement submission      0
production source admission           0
public global coverage claim          0
```

## 3. Ontology binding

P08 binds exactly to:

```text
AX-LIB-O01 — Global Public Procurement
Workspace type — Bid Workspace
```

Core entities:

```text
ProcurementOpportunity
Notice
Procedure
Buyer
Lot
Award
```

Core predicates:

```text
PUBLISHED_BY
HAS_LOT
HAS_REQUIREMENT
AWARDED_TO
CONTRACTS_WITH
CLASSIFIED_AS
```

Core events:

```text
NOTICE_PUBLISHED
NOTICE_CORRECTED
DEADLINE_CHANGED
AWARD_PUBLISHED
CONTRACT_SIGNED
```

Taxonomy references:

```text
CPV
NUTS
PSC
NAICS
```

Source-native classifications remain immutable. Mappings are versioned assertions and may be one-to-many or many-to-many.

## 4. Trust boundary

The system distinguishes:

```text
reachability            != admissibility
publication             != currentness
notice                  != procedure
procedure               != lot
lot                     != eligibility
eligibility score       != eligibility decision
qualification           != pursue approval
bid readiness           != submission authority
submission package      != external submission
submission              != receipt
receipt                 != award
award                   != signed contract
contract value          != realised value
```

Unknown, stale, conflicting, superseded, withdrawn, revoked or incomplete inputs remain explicit and fail closed.

## 5. Eight domain modules

### 5.1 NOTICE_REGISTRY

Service: `procurement_notice_registry`

Records:

- `Notice`
- `NoticeVersion`
- `Amendment`
- `SourcePublication`

Responsibilities:

- preserve source-native notice identity;
- maintain immutable notice versions;
- distinguish correction, amendment, cancellation and withdrawal;
- reconcile duplicate publications;
- calculate currentness deterministically;
- invalidate downstream state when affected fields change.

### 5.2 BUYER_PROCEDURE

Service: `buyer_procedure_service`

Records:

- `Buyer`
- `ContractingAuthority`
- `Procedure`
- `ProcedureRule`

Responsibilities:

- resolve buyer candidates without silent merge;
- preserve contracting-authority and payer distinctions;
- bind procedure type to source and jurisdiction;
- version governing rules;
- represent contested identity and authority relationships.

### 5.3 LOT_STRUCTURE

Service: `lot_structure_service`

Records:

- `Lot`
- `LotGroup`
- `PlaceOfPerformance`
- `ClassificationAssignment`

Responsibilities:

- model each lot independently;
- preserve lot-specific value, deadline and requirements;
- represent exclusivity and aggregate constraints;
- preserve native taxonomy codes;
- evaluate selected-lot compatibility;
- invalidate readiness after relevant amendments.

### 5.4 REQUIREMENT_ELIGIBILITY

Service: `requirement_eligibility_service`

Records:

- `Requirement`
- `EligibilityCriterion`
- `ExclusionGround`
- `EvidenceRequirement`

Responsibilities:

- atomise and anchor requirements;
- distinguish mandatory, optional and scored requirements;
- evaluate eligibility for exact bidder, lot, jurisdiction and time;
- represent exclusion grounds separately;
- identify evidence gaps;
- preserve human-reviewed interpretation separately from extracted text.

### 5.5 BID_WORKSPACE

Service: `bid_workspace_service`

Records:

- `BidWorkspace`
- `BidStrategy`
- `BidTeam`
- `WorkPackage`

Responsibilities:

- bind one tenant to one exact opportunity and notice version;
- bind selected lots;
- require an approved P07 pursue decision;
- manage bounded work without granting approval authority;
- calculate readiness;
- prevent cross-tenant access;
- close or block workspaces after withdrawal or cancellation.

### 5.6 DOCUMENT_PACK

Service: `bid_document_pack_service`

Records:

- `BidDocument`
- `ResponseSection`
- `EvidenceAttachment`
- `SignatureRequirement`

Responsibilities:

- map every response section to requirements;
- bind assertions to exact evidence anchors;
- preserve source-native and translated text;
- validate document currentness;
- identify mandatory response gaps;
- preserve signature and certification requirements;
- enforce rights, classification and secret exclusion.

### 5.7 COMMERCIAL_MODEL

Service: `procurement_commercial_service`

Records:

- `PriceSchedule`
- `CostAssumption`
- `CurrencyConversion`
- `CommercialRisk`

Responsibilities:

- distinguish price, cost, tax, discount and evaluated price;
- preserve currencies, units and temporal context;
- require rate provider, timestamp and method for conversion;
- preserve assumptions and uncertainty;
- block final validation when tax or currency context is unknown;
- prohibit models and workers from committing terms.

### 5.8 SUBMISSION_AWARD

Service: `submission_award_service`

Records:

- `SubmissionPackage`
- `SubmissionReceipt`
- `AwardNotice`
- `ContractAward`

Responsibilities:

- prepare immutable submission packages;
- run deterministic preflight;
- permit only typed human submission authority;
- record submitted bytes and hashes;
- require observed receipts;
- distinguish award notice, signed contract and realised outcome.

## 6. Notice and procedure lifecycle

```text
DISCOVERED
PUBLISHED
CORRECTED
AMENDED
LOTS_OPEN
QUALIFYING
BID_PREPARATION
CLARIFICATION
SUBMISSION_READY
SUBMITTED_EXTERNALLY
AWARD_PUBLISHED
CLOSED_OR_CANCELLED
```

Rules:

- unlisted transitions are denied;
- every transition references exact object versions;
- amendments invalidate affected projections;
- cancellation and withdrawal block submission;
- `SUBMITTED_EXTERNALLY` requires human authority and a recorded external event;
- `AWARD_PUBLISHED` requires observed award evidence;
- no state implies contract signature or realised value.

## 7. Procurement pipeline

```text
P01_DISCOVER
→ P02_NORMALIZE
→ P03_RESOLVE_BUYER
→ P04_MODEL_LOTS
→ P05_EXTRACT_REQUIREMENTS
→ P06_QUALIFY
→ P07_OPEN_BID_WORKSPACE
→ P08_PREPARE_RESPONSE
→ P09_VALIDATE_BID
→ P10_HUMAN_SUBMIT
→ P11_RECORD_AWARD
```

Authority by stage:

```text
Discovery and normalization     candidate only
Buyer resolution               proposal only
Lot and requirement modelling  candidate only
Qualification                  proposal only
Workspace opening              human
Response preparation           candidate only
Readiness validation           deterministic
External submission            human
Award recording                human with observed evidence
```

The default decision is `DENY`.

`INDETERMINATE` is executed as `DENY`.

## 8. Requirement classes

P08 defines nine classes:

```text
ELIGIBILITY
EXCLUSION
TECHNICAL
FINANCIAL
LEGAL
DOCUMENTARY
COMMERCIAL
DELIVERY
SUBMISSION
```

Every requirement preserves:

- source notice and lot;
- source-native text;
- exact document anchors;
- jurisdiction and effective interval;
- mandatory or optional status;
- evidence requirements;
- assessment and reviewer lineage;
- amendment and supersession history.

An active exclusion ground produces `FAIL`.

Unknown mandatory evidence never produces `PASS`.

## 9. Bid readiness

P08 defines ten independent gates:

```text
OPPORTUNITY_CURRENT
DEADLINE_VALID
LOT_SELECTION_VALID
ELIGIBILITY_PASSED
EXCLUSIONS_CLEARED
REQUIREMENTS_COVERED
DOCUMENTS_CURRENT
APPROVALS_CURRENT
PRICE_VALIDATED
SUBMISSION_CHANNEL_VERIFIED
```

Decision rules:

```text
all PASS                         READY
one DENY                         DENY
unknown or critical uncertainty REVIEW_REQUIRED
any other incomplete set         NOT_READY
```

Readiness is recalculated after:

- amendments;
- withdrawals;
- rights revocation;
- document supersession;
- approval expiry or revocation;
- lot-selection changes;
- commercial-model changes;
- deadline or channel changes.

Readiness never performs submission.

## 10. Bid Workspace

A Bid Workspace is tenant-scoped and server-resolved.

It binds:

- an opportunity version;
- a notice version;
- selected lots;
- a P07 pursuit;
- decisions;
- team and work records;
- approvals;
- document pack;
- commercial model;
- readiness report.

Workspace data cannot mutate global procurement records.

Membership grants no approval, signature, budget or submission authority.

## 11. Documents and multilingual parity

P08 inherits the six P06 languages:

```text
en
es
fr
de
pt
it
```

Critical dimensions:

```text
eligibility
exclusion grounds
requirements
amounts
dates
negation
modality
lot scope
submission instructions
```

A critical mismatch produces `DENY`.

A critical unknown produces `REVIEW_REQUIRED`.

Translations never replace source-native text or anchors.

## 12. Commercial model

Validation requires:

```text
amount
currency
tax context
units
assumptions
rate provider when conversion applies
rate timestamp
conversion method
human validator
exact model version
```

The system distinguishes:

```text
estimated value
budget ceiling
cost
offered price
evaluated price
tax
discount
option
forecast margin
realised value
```

Modelled values are proposals and cannot commit commercial terms.

## 13. Submission boundary

External submission requires all of the following:

```text
HUMAN_SUBMISSION_AUTHORITY
READY readiness report
current typed approvals
current notice and lot versions
valid deadline and timezone
current documents and anchors
validated price model
verified external channel
inactive kill switch
valid audit chain
```

Models, connectors, parsers and workers cannot:

- submit a bid;
- sign a document;
- accept terms;
- commit price;
- declare eligibility;
- fabricate a receipt;
- create an award.

## 14. Award boundary

Observed states:

```text
AWARD_OBSERVED
CONTRACT_OBSERVED
CLOSED
UNKNOWN
```

The following implications are prohibited:

```text
submission completed  -> award
award notice          -> signed contract
signed contract       -> realised value
internal workflow     -> external result
```

Award and contract records require version-pinned external evidence.

## 15. Rights

P08 inherits the ten rights dimensions:

```text
collection
transient_processing
persistent_storage
model_input
derived_calculations
internal_display
customer_display
export
api_redistribution
model_training_or_evaluation
```

Missing, ambiguous, conflicting, expired, suspended or revoked rights deny the affected action.

## 16. Authority model

```text
Browser                        request only
Connector                      candidate only
OCR/parser                     candidate only
Model                          proposal only
Worker                         bounded work mutation
Bid operator                   tenant-scoped operation
Human approver                 typed approval only
Human submission authority     external submission only
Human award authority          observed outcome recording only
Independent admission runtime  deterministic write after approval
```

Least authority bounds every derived object.

Imported approvals, receipts and awards have no live authority.

## 17. Evidence suites

P08 includes:

```text
40 conformance fixtures
72 adversarial cases
```

Each of the eight modules has five fixtures:

- happy path;
- incomplete context;
- revoked or withdrawn dependency;
- cross-tenant attempt;
- authority escalation.

Each module has eight adversarial cases, plus eight cross-module cases.

All cases require:

```text
canonical_delta             0
external_submission_delta   0
```

## 18. Deterministic reference functions

The reference implementation covers:

- notice currentness;
- deadline validity with timezone;
- eligibility and exclusion decisions;
- lot compatibility;
- mandatory requirement coverage;
- ten-gate readiness;
- commercial validation;
- submission authority;
- award normalization;
- canonical hashing.

These functions do not perform network access, production ingestion or external submission.

## 19. Observability

Metrics include:

- notice candidates, amendments and withdrawals;
- contested buyer resolution;
- lot conflicts;
- eligibility reviews and exclusion failures;
- requirement gaps;
- workspace openings;
- readiness denials;
- stale document packs;
- commercial denials;
- submission preflight denials;
- observed submissions and awards;
- authority escalation attempts;
- rollback failures.

Alerts fail closed on stale versions, unreconciled amendments, cross-tenant access, fabricated receipts, missing currencies or tax, model submission attempts and award creation without evidence.

## 20. Rollback

P08 adds eleven artifacts and modifies one CI workflow.

Rollback:

1. verifies the exact diff from the frozen P07 head;
2. hashes seven P07 authority artifacts;
3. removes all eleven P08-only artifacts;
4. restores the original CI workflow from P07;
5. verifies P07 authority hashes are unchanged;
6. verifies the resulting tree equals the frozen P07 baseline.

Rollback does not erase audit or acceptance evidence outside the branch.

## 21. Canonical truth

```text
P01 canonical state                  IN_PROGRESS
P02 canonical activation            false
P03 canonical activation            false
P04 canonical activation            false
P05 canonical activation            false
P06 canonical activation            false
P07 engineering evidence ready       true
P07 canonical activation            false
P08 engineering branch authorised    true
P08 canonical activation            false
merge to main                        false
external bids submitted                0
production procurement sources         0
commercial/public activation         none
```

## 22. Remaining gates

Canonical activation requires:

- P07 acceptance or normative superseding ADR;
- transitive resolution of P01–P06;
- exact ontology binding;
- all notice, lot, eligibility, document, pricing and submission tests;
- 40 fixtures passing;
- 72 adversarial cases failing closed;
- byte-exact rollback;
- Human Procurement Authority approval;
- Human Bid Approval Authority approval;
- Human Submission Authority approval;
- Human Rights Authority approval;
- Human Product Authority approval.

Until then, P08 remains an engineering foundation with no authorised launch, source admission, external bid submission or canonical activation.
