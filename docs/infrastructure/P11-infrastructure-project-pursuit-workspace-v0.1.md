# P11 — Infrastructure Library + Project Pursuit Workspace v0.1

## Status

```text
Task                         AX-GE2E-P11-T01
Engineering base             P10@563acd353ba3a90d253d582b7c19f1554fd011b1
Normative dependency         P07@e30f800cb284f1381c28c4ccbc116a8da4a9fe92
Canonical activation         false
Merge to main                false
External actions executed    0
Production sources enabled   0
```

P11 implements `AX-LIB-O04 — Infrastructure and Capital Projects` and the tenant-scoped **Project Pursuit Workspace**. It does not activate sources, commit capital, sign agreements, submit expressions of interest or bids, or create observed project outcomes.

## Truth boundary

```text
project announcement       != project approval
project approval           != financing commitment
financing commitment       != financial close
permit application         != permit grant
land identified            != land secured
tender expected            != procurement notice published
package forecast           != contract opportunity
pursuit readiness          != authority to engage or submit
award announcement         != signed contract
signed contract            != construction start
construction start         != completion
project cost               != contract value
```

A source being reachable or listed proves neither admission, currentness, completeness nor permission to process it.

## Ontology binding

```text
Library ID       AX-LIB-O04
Canonical name   Infrastructure and Capital Projects
Workspace type   Project Pursuit Workspace
```

Entities: `InfrastructureOpportunity`, `Project`, `Asset`, `Sponsor`, `Contractor`, `FinancingPackage`.

Predicates: `SPONSORED_BY`, `DELIVERED_BY`, `FINANCED_BY`, `REQUIRES_PERMIT`, `HAS_MILESTONE`, `LOCATED_IN`.

Events: `PROJECT_ANNOUNCED`, `FINANCING_APPROVED`, `PERMIT_GRANTED`, `TENDER_EXPECTED`, `CONSTRUCTION_STARTED`.

Taxonomies: `NUTS`, `CPV`, `CPC`.

## Eight modules

### PROJECT_REGISTRY

Maintains immutable project versions, announcements, corrections, supersessions, withdrawals and cancellations. An announcement creates at most a candidate signal.

### SPONSOR_STAKEHOLDER

Separates sponsor, owner, client, authority, operator, contractor and financier. A named sponsor proves neither funding nor procurement authority.

### ASSET_SCOPE_LOCATION

Models assets, sites, corridors and delivery packages with geographic, jurisdictional, taxonomy and temporal lineage. Project, asset, package, lot and contract remain distinct.

### PERMIT_LAND_ENVIRONMENT

Tracks environmental approval, planning permission, construction permit, operating licence, title, lease, easement, right of way, utility connection and community or indigenous consent. Application is not grant; identification is not security.

### FINANCING_COMMERCIAL

Separates project cost, approved budget, financing request, committed debt, committed equity, grant support, guarantees, viability-gap support, contract value and realised spend. Approval is not commitment; commitment is not financial close.

### PROJECT_PURSUIT_WORKSPACE

Binds one tenant, one exact project version and one approved P07 pursuit to target assets/packages, capture team, work, stakeholders, finance, permits, land, milestones, risks, documents, rights, approvals and readiness.

### DELIVERY_MILESTONE_RISK

Preserves forecast, target, announced and observed milestones. Risk classes cover sponsor, financing, permits, land, environmental/social, technical, procurement, schedule, cost and demand/revenue. Risk acceptance is human-only.

### EXTERNAL_ACTION_OUTCOME

Controls sponsor engagement, NDA, partnering MOU, EOI, prequalification, bid, investment commitment and contract signature. Preparation never implies execution. Receipts, awards, contracts and outcomes require observed evidence.

## Lifecycle

```text
DISCOVERED
ANNOUNCED
CONCEPT
FEASIBILITY
APPRAISAL
FINANCING_PENDING
FINANCING_COMMITTED
PERMITTING_AND_LAND
PROCUREMENT_EXPECTED
PURSUIT_ACTIVE
CONTRACTED_OR_IN_DELIVERY
CLOSED
```

Unlisted transitions are denied. An announced project cannot jump directly to financing committed or contracted. Cancellation, suspension or withdrawal closes the current version without deleting evidence.

## Pipeline

```text
I01_DISCOVER
→ I02_NORMALIZE_PROJECT
→ I03_RESOLVE_STAKEHOLDERS
→ I04_MODEL_ASSET_SCOPE
→ I05_ASSESS_STAGE_FINANCE
→ I06_ASSESS_PERMITS_LAND
→ I07_OPEN_PROJECT_PURSUIT
→ I08_PLAN_PURSUIT
→ I09_VALIDATE_READINESS
→ I10_HUMAN_EXTERNAL_ACTION
→ I11_RECORD_PROJECT_OUTCOME
```

Discovery and normalization are candidate-only. Stakeholder, finance and permit assessments are proposal-only. Readiness is deterministic. Workspace opening, external action and outcome recording require typed humans. Default and indeterminate decisions are `DENY`.

## Stage evidence

Ten independently versioned classes:

```text
ANNOUNCEMENT
STRATEGIC_ALIGNMENT
CONCEPT
FEASIBILITY
APPRAISAL
FINANCING
PERMITTING
LAND_AND_RIGHTS
PROCUREMENT
DELIVERY
```

Only verified evidence satisfies a mandatory stage requirement. Reported, evidenced, unknown and contested states require review. Superseded and withdrawn evidence contribute zero readiness.

## Readiness gates

```text
PROJECT_CURRENT
SPONSOR_AND_AUTHORITY_RESOLVED
STAGE_EVIDENCE_VERIFIED
ASSET_LOCATION_SCOPE_RESOLVED
FINANCING_STATUS_VERIFIED
PERMITS_AND_LAND_RESOLVED
PROCUREMENT_PATH_VERIFIED
DELIVERY_PACKAGES_DEFINED
RISKS_AND_DEPENDENCIES_REVIEWED
DOCUMENTS_AND_RIGHTS_CURRENT
APPROVALS_CURRENT
CHANNEL_AND_AUTHORITY_VERIFIED
```

```text
all PASS                         READY
any DENY or BLOCK               DENY
unknown/contested/stale          REVIEW_REQUIRED
missing gate                    NOT_READY
changed dependency              INVALIDATED
```

`READY` is not permission to spend, sign, submit, accept terms or commit capital.

## External-action preflight

Execution requires `HUMAN_EXTERNAL_ACTION_AUTHORITY`, `READY`, current approvals, active rights, current project version, verified channel, valid audit chain and inactive kill switch.

P07 approvals required: `PURSUE`, `BUDGET`, `RIGHTS`, `LEGAL`, `DOCUMENT`, `SUBMISSION_OR_ACTIVATION`.

## Authority ceiling

```text
Browser                         request only
Connector                       candidate only
OCR or parser                   candidate only
Model                           proposal only
Worker                          bounded work mutation
Project operator                tenant-scoped operation
Human project authority         project decision only
Human finance authority         capital approval only
Human legal authority           legal approval only
Human signatory                 signature only
Human external-action authority external action only
Human outcome authority         observed outcome only
Admission runtime               deterministic write after approval
```

Models and workers cannot declare approval, committed finance, granted permits, secured land or published tenders. They cannot commit capital, sign, submit, accept terms or create outcomes.

## Multilingual contract

Engineering languages: `en`, `es`, `fr`, `de`, `pt`, `it`.

Critical dimensions: project stage, financing status, permit status, land rights, package scope, amounts, currency, dates, negation and modality. Critical mismatch yields `DENY`; critical unknown yields `REVIEW_REQUIRED`.

## Source boundary

Research-only entries:

- World Bank Projects & Operations;
- European Investment Bank Projects;
- EBRD Projects;
- Asian Development Bank Projects;
- African Development Bank Projects;
- Inter-American Development Bank Projects.

```text
product_admitted           false
rights_status              UNREVIEWED
public_coverage_authorised false
```

No connector or global coverage claim is activated.

## Evidence matrices

```text
8 modules × 5 classes = 40 fixtures
9 scopes × 8 threats = 72 adversarial cases
```

Threats cover stale/cancelled projects, announcements represented as approval, finance/permit inference, missing evidence, revoked rights, cross-tenant references, authority escalation and fabricated outcomes.

Every adversarial case requires:

```text
canonical_delta       0
external_action_delta 0
```

## Rollback

Rollback verifies exactly twelve changed paths, removes eleven P11 artifacts, restores CI from `P10@563acd353ba3a90d253d582b7c19f1554fd011b1`, preserves seven P10 authority files and compares the resulting tree byte-for-byte with the baseline.

## Canonical state

```text
P11 canonical state       BLOCKED
canonical activation      false
merge to main             false
external actions          0
production sources        0
commercial activation     none
```

Activation additionally requires accepted dependencies and Human Infrastructure, Finance, Legal, Signatory/External Action, Rights and Product authorities.
