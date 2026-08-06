# P09 — Grants Library + Application Workspace

**Task:** `AX-GE2E-P09-T01`  
**Programme:** `1.4.0`  
**Engineering base:** `AX-GE2E-P08-T01@3e28e08a12d02701d4ab312edfbedc56fcd8bb59`  
**Normative dependency:** `AX-GE2E-P07-T01@e30f800cb284f1381c28c4ccbc116a8da4a9fe92`  
**Status:** `DRAFT_ENGINEERING_FOUNDATION`  
**Canonical activation:** `false`

## 1. Purpose

P09 specialises the domain-neutral Opportunity Operations Core for
`AX-LIB-O02 — Grants and Non-Dilutive Funding` and its tenant-scoped
`Application Workspace`.

It implements contracts and deterministic reference behaviour for:

- funding opportunities and calls;
- funders, programmes and instruments;
- applicant and consortium eligibility;
- application workspaces;
- narrative, evidence and ethics content;
- budgets, funding rates and co-financing;
- human-controlled application submission;
- observed awards and grant agreements.

It does not activate any source, submit any application, promise eligibility,
estimate win probability without an admitted method, or create canonical
funding facts.

## 2. Dependency truth

The programme defines P07 as P09's normative dependency. P08 is only the
cumulative engineering base used by this stacked branch.

```text
normative dependency    P07@e30f800cb284f1381c28c4ccbc116a8da4a9fe92
engineering base        P08@3e28e08a12d02701d4ab312edfbedc56fcd8bb59
P07 canonical           false
P08 canonical           false
P09 canonical           false
merge to main           false
```

If the P08 stack is not canonically accepted, P09 must be rebased onto an
accepted P07-derived chain before activation.

## 3. Library binding

```text
library      AX-LIB-O02
name         Grants and Non-Dilutive Funding
workspace    Application Workspace
```

### Entities

- `FundingOpportunity`
- `FundingCall`
- `Programme`
- `Funder`
- `Applicant`
- `Grant`

### Predicates

- `FUNDED_BY`
- `ELIGIBLE_FOR`
- `HAS_BUDGET`
- `HAS_DEADLINE`
- `TARGETS`
- `REQUIRES`

### Events

- `CALL_OPENED`
- `CALL_AMENDED`
- `DEADLINE_CHANGED`
- `AWARD_ANNOUNCED`
- `CALL_CLOSED`

### Taxonomies

- `NACE`
- `NAICS`
- `TRL`

## 4. Domain boundaries

P09 preserves the following distinctions:

```text
funding opportunity != funding call
call != programme
programme != funding instrument
funder != managing authority != payer
applicant != consortium != partner
eligibility assessment != eligibility guarantee
application readiness != submission authority
submitted application != verified receipt
verified receipt != award
award != signed grant agreement
signed agreement != payment
payment != realised impact
```

"Non-dilutive" does not imply absence of obligations, repayment risk,
state-aid constraints, audit duties, reporting, clawback or co-financing.

## 5. Eight modules

### 5.1 CALL_REGISTRY

Service: `funding_call_registry`

Records: `FundingCall`, `CallVersion`, `CallAmendment`, `FundingTopic`.

The module preserves amendments, suspension, closure, withdrawal, source-native
identifiers and content-addressed versions. A source that is withdrawn or
revoked contributes zero readiness.

### 5.2 FUNDER_PROGRAMME

Service: `funder_programme_service`

Records: `Funder`, `Programme`, `FundingInstrument`, `ManagingAuthority`.

Funder, programme owner, managing authority, intermediary and payer remain
separately resolvable. A programme budget is never silently represented as a
call budget.

### 5.3 ELIGIBILITY_SCOPE

Service: `grant_eligibility_service`

Records: `EligibilityCriterion`, `ExclusionCriterion`, `TargetScope`,
`EvidenceRequirement`.

Eligibility is scoped to the exact applicant or consortium, call version,
topic, jurisdiction, cut-off and evidence set. Unknown mandatory criteria never
pass.

### 5.4 CONSORTIUM_PARTNERS

Service: `grant_consortium_service`

Records: `Applicant`, `Consortium`, `PartnerRole`, `ParticipationConstraint`.

Coordinator, beneficiary, affiliated entity, associated partner,
subcontractor and third party remain distinct. Membership never grants
signature or submission authority.

### 5.5 APPLICATION_WORKSPACE

Service: `application_workspace_service`

Records: `ApplicationWorkspace`, `ApplicationStrategy`, `ApplicationTeam`,
`WorkPackage`.

The workspace is tenant-scoped and binds one applicant or consortium to one
funding opportunity, call version and topic. Opening requires approved P07
qualification and pursuit decisions.

### 5.6 NARRATIVE_EVIDENCE

Service: `application_content_service`

Records: `ApplicationSection`, `EvidenceAttachment`, `ImpactPathway`,
`EthicsRequirement`.

Model-generated text remains proposal content. Applicant attestations,
evidence, source documents and forecasts remain distinguishable. Ethics,
safeguarding, conflicts and state-aid declarations require human review.

### 5.7 BUDGET_CO_FINANCING

Service: `grant_budget_service`

Records: `ApplicationBudget`, `CostCategory`, `CoFinancingPlan`, `FundingRate`.

P09 distinguishes total project cost, eligible cost, requested grant,
co-financing, in-kind contributions, indirect cost, advances, reimbursements
and realised payments.

### 5.8 SUBMISSION_AWARD

Service: `grant_submission_award_service`

Records: `ApplicationPackage`, `ApplicationReceipt`, `GrantAward`,
`GrantAgreement`.

Package preparation and external submission are separate operations. Receipt,
award, agreement, payment and realised impact require distinct observed
evidence.

## 6. Lifecycle

```text
DISCOVERED
OPEN
AMENDED
QUALIFYING
CONSORTIUM_FORMING
APPLICATION_PREPARATION
REVIEW_READY
SUBMISSION_READY
SUBMITTED_EXTERNALLY
AWARD_ANNOUNCED
AGREEMENT_SIGNED
CLOSED_OR_WITHDRAWN
```

Unlisted transitions are denied. Every transition preserves the previous and
next state, exact call version, actor, decision and reason.

An amendment invalidates affected eligibility, consortium, budget, content and
readiness projections. A suspended, closed or withdrawn call blocks external
submission.

## 7. Operating pipeline

```text
G01_DISCOVER
→ G02_NORMALIZE
→ G03_RESOLVE_FUNDER
→ G04_EXTRACT_SCOPE
→ G05_ASSESS_ELIGIBILITY
→ G06_FORM_CONSORTIUM
→ G07_OPEN_APPLICATION_WORKSPACE
→ G08_PREPARE_APPLICATION
→ G09_VALIDATE_APPLICATION
→ G10_HUMAN_SUBMIT
→ G11_RECORD_AWARD
```

Authority by stage:

```text
discovery, normalization and extraction    candidate only
funder resolution and eligibility          proposal only
consortium and workspace opening            human
application preparation                     candidate only
readiness                                   deterministic
external submission                         human
award recording                             human + observed evidence
```

Default and indeterminate decisions are `DENY`.

## 8. Criterion classes

P09 evaluates ten independent classes:

1. `APPLICANT_TYPE`
2. `JURISDICTION`
3. `SECTOR`
4. `PROJECT_SCOPE`
5. `CONSORTIUM`
6. `TRL`
7. `FINANCIAL_CAPACITY`
8. `CO_FINANCING`
9. `STATE_AID_OR_COMPLIANCE`
10. `SUBMISSION`

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

A mandatory `UNKNOWN`, `PENDING_EVIDENCE` or `CONTESTED` state cannot become
`PASS`. Any mandatory `FAIL` produces `DENY`.

## 9. Consortium contract

Roles:

```text
COORDINATOR
BENEFICIARY
AFFILIATED_ENTITY
ASSOCIATED_PARTNER
SUBCONTRACTOR
THIRD_PARTY
```

Constraints include partner counts, jurisdiction counts, independence,
required roles, entity types, geography and conflicts of interest.

Partner withdrawal invalidates dependent work and readiness. Imported
membership has candidate authority only.

## 10. Application Workspace

The workspace requires:

- server-resolved tenant;
- funding opportunity and call version;
- topic;
- applicant and consortium versions;
- P07 pursuit and decision references;
- team and work references;
- approvals;
- application pack;
- budget;
- readiness report.

The browser cannot select authoritative tenant context. Team membership does
not confer approval, signature, declaration, financial or submission authority.

## 11. Application pack

Section types:

```text
EXCELLENCE
IMPACT
IMPLEMENTATION
WORK_PLAN
BUDGET_JUSTIFICATION
TEAM
ETHICS
RISK
ANNEX
DECLARATION
```

Each substantive assertion maps to an exact criterion, source anchor,
applicant statement or evidence object. Source-native legal and eligibility
text remains immutable.

Signatures and declarations cannot be automated without typed human authority.

## 12. Budget and co-financing

Validation preserves:

- amount and currency;
- exact call and topic version;
- eligible-cost rules;
- maximum rate and ceiling;
- cost categories;
- exchange-rate provider, value and timestamp;
- co-financing evidence;
- assumptions and reviewer;
- supersession history.

A request is denied when it exceeds eligible cost, the call ceiling or the
allowed funding rate. Unconfirmed co-financing yields review or denial and
never silently passes.

## 13. Application readiness

The twelve required gates are:

```text
CALL_CURRENT
DEADLINE_VALID
APPLICANT_ELIGIBLE
CONSORTIUM_VALID
SCOPE_ALIGNED
REQUIREMENTS_COVERED
ETHICS_COMPLIANCE_CLEARED
DOCUMENTS_CURRENT
BUDGET_VALIDATED
CO_FINANCING_CONFIRMED
APPROVALS_CURRENT
SUBMISSION_CHANNEL_VERIFIED
```

Decision:

```text
all PASS                         READY
any DENY                        DENY
UNKNOWN/INDETERMINATE/CONTESTED REVIEW_REQUIRED
missing gate                     NOT_READY
```

Readiness is invalidated by changes to the call, deadline, applicant,
consortium, topic, evidence, budget, co-financing, approvals or submission
channel.

Readiness never grants signature or submission authority.

## 14. Submission boundary

External submission requires:

- `HUMAN_SUBMISSION_AUTHORITY`;
- readiness `READY`;
- exact current call and package versions;
- active rights;
- valid audit chain;
- inactive kill switch;
- verified channel;
- typed P07 approvals:
  - `PURSUE`
  - `BUDGET`
  - `RIGHTS`
  - `LEGAL`
  - `DOCUMENT`
  - `SUBMISSION_OR_ACTIVATION`

Models, connectors, parsers and workers cannot declare eligibility, confirm
co-financing, sign, accept obligations, submit, fabricate receipts or create
awards.

## 15. Award and agreement truth

Award states:

```text
UNKNOWN
REJECTED
RESERVE_LIST
AWARDED
AGREEMENT_PENDING
AGREEMENT_SIGNED
PAYMENT_PENDING
PAID
TERMINATED
```

Internal workflow completion is not evidence of submission or award. An award
announcement is not a signed agreement. A signed agreement is not payment.
Payment is not realised impact.

## 16. Multilingual contract

Languages:

```text
en es fr de pt it
```

Critical dimensions:

- eligibility;
- exclusions;
- consortium constraints;
- funding rate;
- co-financing;
- amounts;
- dates;
- negation;
- modality;
- submission instructions.

Critical mismatch produces `DENY`. Critical unknown parity produces
`REVIEW_REQUIRED`.

## 17. Source catalogue boundary

The existing research catalogue contains six discovered systems:

- EU Funding & Tenders Portal;
- CORDIS;
- Grants.gov;
- UK Find a Grant;
- Australian GrantConnect;
- World Bank Projects & Operations.

For every entry:

```text
product_admitted = false
rights_status    = UNREVIEWED
```

Catalogue listing is not source admission. P04 source-specific rights and
technical admission remain mandatory. P09 activates no source and authorises
no public coverage claim.

## 18. Authority model

```text
BROWSER                       request only
CONNECTOR                     candidate only
OCR_OR_PARSER                 candidate only
MODEL                         proposal only
WORKER                        bounded work mutation
APPLICATION_OPERATOR          tenant-scoped operation
HUMAN_APPROVER                typed approval only
HUMAN_SIGNATORY               declaration and signature only
HUMAN_SUBMISSION_AUTHORITY    external submission only
HUMAN_AWARD_AUTHORITY         observed outcome recording only
INDEPENDENT_ADMISSION_RUNTIME deterministic canonical write after approval
```

The least-authoritative dependency bounds every derived record.

## 19. Rights and privacy

P09 inherits exactly ten rights dimensions:

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

Unknown, ambiguous, expired or revoked rights deny the affected action.

Applicant, partner, personnel, financial and ethics information remains
tenant-scoped. Secrets and inappropriate personal data are excluded from logs,
fixtures and exports.

## 20. Evidence matrices

The conformance matrix is the deterministic product of eight modules and five
classes: candidate happy path, incomplete context, revoked dependency,
cross-tenant access and authority escalation. It materialises **40 fixtures**.

The adversarial matrix is the deterministic product of nine scopes—eight
modules plus cross-module—and eight threat profiles. It materialises **72
cases** covering stale versions, missing evidence, revoked rights, cross-tenant
references, authority escalation, critical unknowns, fabricated evidence and
gate bypass.

All materialised fixtures and cases enforce:

```text
canonical_write / canonical_delta          false / 0
external_submission / submission_delta     false / 0
```

## 21. Deterministic reference functions

`scripts/p09_grants_reference.py` implements:

- canonical digest;
- call-currentness evaluation;
- timezone-aware deadline evaluation;
- eligibility decision;
- consortium constraint decision;
- funding-rate and ceiling validation;
- twelve-gate readiness;
- human-only submission preflight;
- observed award normalization;
- candidate-only import authority.

No function invokes a model or external source.

## 22. Rollback

P09 rollback removes eleven P09-only artifacts, restores the P08 workflow and
verifies the resulting tree byte-for-byte against:

```text
3e28e08a12d02701d4ab312edfbedc56fcd8bb59
```

Seven P08 authority artifacts are hashed before and after rollback. Any
unexpected path, residual file or P08 drift fails the rehearsal.

## 23. Excluded scope

P09 does not implement:

- production source ingestion;
- grants portal credentials;
- external portal automation;
- automated signatures or declarations;
- automatic application submission;
- legal, state-aid or eligibility guarantees;
- funding-probability claims;
- public or commercial activation;
- canonical source or product admission;
- merge to `main`.

## 24. Canonical gate

Engineering evidence is not canonical acceptance. Activation remains blocked
until the normative dependency chain is resolved, the engineering stack is
rebased or accepted, all deterministic and adversarial gates pass, and the
required human authorities approve Grants, Application, Submission, Rights and
Product.
