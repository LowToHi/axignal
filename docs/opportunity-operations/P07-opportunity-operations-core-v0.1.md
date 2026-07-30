# P07 — Opportunity Operations Core v0.1

Task: `AX-GE2E-P07-T01`  
Programme: `AXIGNAL-GOAL-001 / v1.4.0`  
Status: `DRAFT_ENGINEERING_FOUNDATION`  
Canonical activation: `false`

## 1. Purpose

P07 defines the domain-neutral operating core used by all AXIGNAL opportunity libraries.
It turns evidence-backed opportunity candidates into controlled pursuits, decisions, work,
approvals, submissions or activations, outcomes, learning and portable workspace records.

P07 does not activate any opportunity product, submit any bid or application, accept legal
terms, commit spend, publish externally or infer a commercial outcome.

## 2. Dependency and truth boundary

P07 is stacked on the exact engineering head:

```text
AX-GE2E-P06-T01@d6317f32caad4f916f1871c23753bacd36b4d9d6
```

Engineering may proceed because P06 has exact-head evidence. Canonical activation remains
blocked because P06, P05, P04, P03 and P02 are not canonically accepted and P01 remains
incomplete.

```text
P01 canonical state                  IN_PROGRESS
P02 canonical activation            false
P03 canonical activation            false
P04 canonical activation            false
P05 canonical activation            false
P06 engineering evidence ready       true
P06 canonical activation            false
P07 engineering branch authorised    true
P07 canonical activation            false
merge to main                        false
external actions executed              0
commercial/public activation         none
```

## 3. Core separation

The following concepts are independent records and may not be silently collapsed:

```text
Opportunity
Qualification
Pursuit
Decision
Work
Approval
Submission or activation
Outcome
Learning
Portable bundle
Audit event
```

A high score is not a decision. A decision is not an approval. An approval is not a submission.
A submission is not a win. A workflow closure is not an observed external outcome.

## 4. Seven modules

### 4.1 Opportunity Registry

Service: `opportunity_registry`

Records:

- `Opportunity`
- `QualificationAssessment`
- `OpportunitySignal`

Responsibilities:

- register evidence-backed candidates;
- preserve source, rights, jurisdiction, language, temporal and document lineage;
- record incomplete and contradictory qualification inputs;
- link possible duplicates without silent merge;
- separate detection, qualification and pursuit.

### 4.2 Pursuit Service

Service: `pursuit_service`

Records:

- `Pursuit`
- `PursuitMember`
- `PursuitStrategy`

A pursuit references one exact opportunity version. It opens only after an approved pursue
decision. Membership grants collaboration access, not budget, approval or submission authority.
Strategies are immutable versions and are superseded rather than overwritten.

### 4.3 Decision Service

Service: `decision_service`

Records:

- `DecisionRecord`
- `DecisionOption`
- `DecisionEvidenceLink`

Every consequential transition records options, criteria, evidence, unknowns, risks, dissent,
proposer, decider, policy version and rationale. Model recommendations remain proposals.
A decision cannot imply a separate legal, budget, rights, document, export or submission approval.

### 4.4 Work Execution Service

Service: `work_execution_service`

Records:

- `WorkItem`
- `WorkDependency`
- `Deliverable`
- `WorkEvidence`

Work becomes ready only when all mandatory dependencies are satisfied or explicitly waived by a
human authority. Worker state mutation is idempotent and bounded to assigned work. `IN_PROGRESS`
never grants authority to submit, activate, spend, sign or publish.

### 4.5 Approval Service

Service: `approval_service`

Records:

- `ApprovalRequest`
- `ApprovalDecision`
- `ApprovalPolicySnapshot`

Approvals are typed, scoped, version-pinned, expiring and revocable. Unknown, conflicting,
expired, superseded or revoked approval states deny the dependent action.

### 4.6 Outcome Registry

Service: `outcome_registry`

Records:

- `Outcome`
- `OutcomeEvidence`
- `RealisationMeasurement`

Outcomes require observed evidence and source time. `UNKNOWN` remains distinct from `LOST`.
Forecast, target, award and realised value remain separate. Corrections create superseding
versions and preserve history.

### 4.7 Learning and Portability Service

Service: `learning_portability_service`

Records:

- `LearningRecord`
- `HypothesisUpdate`
- `PortableWorkspaceBundle`
- `ImportReport`

Learning separates observation, interpretation, hypothesis and recommendation. Model-generated
learning remains proposed and cannot modify policy, prompts, models, thresholds or permissions.
Exports are rights-aware and secret-free. Imports create tenant-scoped candidates only.

## 5. Opportunity lifecycle

P07 inherits the exact P02 lifecycle:

```text
DETECTED
QUALIFYING
QUALIFIED
REJECTED
PURSUIT_OPEN
DECISION_PENDING
APPROVED
DECLINED
IN_EXECUTION
SUBMITTED_OR_ACTIVATED
WON_OR_REALIZED
LOST_OR_CLOSED
LEARNING_CAPTURED
```

Only declared transitions are valid. Each transition records the prior state, target state,
decision reference, actor, time and reason. Terminal states cannot silently re-enter execution.

A lifecycle label does not establish legal eligibility, probability of success or outcome certainty.

## 6. Ten-stage operating pipeline

```text
O01_DETECT
→ O02_QUALIFY
→ O03_OPEN_PURSUIT
→ O04_DECIDE
→ O05_PLAN_WORK
→ O06_EXECUTE
→ O07_APPROVE
→ O08_SUBMIT_ACTIVATE
→ O09_RECORD_OUTCOME
→ O10_LEARN_PORT
```

Authority by stage:

| Stage | Maximum authority |
|---|---|
| Detect | candidate only |
| Qualify | proposal only |
| Open pursuit | human |
| Decide | human |
| Plan work | proposal only |
| Execute work | candidate only |
| Approve | human |
| Submit or activate | human |
| Record outcome | human |
| Learn and package | proposal only |

The default decision is `DENY`. `INDETERMINATE` is executed as `DENY`.

## 7. Decision contract

Decision states:

```text
DRAFT
PROPOSED
PENDING_APPROVAL
APPROVED
REJECTED
SUPERSEDED
REVOKED
```

Decision types:

```text
QUALIFY
PURSUE
CONTINUE
SUBMIT_OR_ACTIVATE
WITHDRAW
CLOSE
```

Consequential decisions require a capable human decider distinct from the proposer. Missing,
stale or revoked required evidence cannot yield `APPROVED`. Scores and probabilities remain
inputs and never become decisions automatically.

## 8. Work contract

Work states:

```text
BACKLOG
READY
IN_PROGRESS
BLOCKED
REVIEW
DONE
CANCELLED
```

Dependency states:

```text
UNSATISFIED
SATISFIED
WAIVED_BY_HUMAN
INVALIDATED
```

An invalidated dependency returns downstream work to `BLOCKED`. Completion requires evidence or
an explicit not-applicable decision. Cancelled work remains in the audit trail.

## 9. Typed approvals

P07 defines eight approval types:

```text
PURSUE
BUDGET
RIGHTS
LEGAL
DOCUMENT
SUBMISSION_OR_ACTIVATION
EXPORT
OUTCOME_CLOSE
```

Separation of duties:

- requester cannot approve the same consequential request;
- models, browsers, connectors and workers cannot approve;
- rights and legal approvals require distinct qualified authorities;
- document and submission approvals are separate;
- budget and pursue approvals are separate;
- break-glass cannot bypass rights, submission, export or legal controls.

Every action re-evaluates rights, privacy, classification, current document versions and kill
switches after approval. Approval never manufactures evidence or document authority.

## 10. External-action preflight

Submission or activation requires all configured approvals for the exact subject version and
purpose, plus:

```text
server-resolved tenant and workspace
active source and action rights
current document versions and anchors
valid audit chain
no active kill switch
human submission or activation authority
```

Any missing, unknown, expired, conflicting, stale or revoked input produces `DENY`.

## 11. Outcomes

Outcome states:

```text
WON
LOST
NO_BID
WITHDRAWN
EXPIRED
REALIZED
NOT_REALIZED
UNKNOWN
```

An unobserved result is `UNKNOWN`, not `LOST`. A submission cannot be stored as `WON`. A model
cannot create an observed outcome. Realisation measurements require method, interval, currency or
unit, and uncertainty.

## 12. Learning

Learning states:

```text
PROPOSED
REVIEWED
ADMITTED
CONTESTED
SUPERSEDED
```

Causal claims require an explicit method. Unknown outcomes constrain the claim. Contested
learning remains visible but creates no automatic rule. Cross-opportunity aggregation preserves
tenant, rights and confidentiality boundaries.

## 13. Portability

Portable bundle version: `0.1.0`

Required sections include:

```text
manifest
schema_versions
opportunity
qualification
pursuit
decisions
work
approvals
documents
evidence_refs
outcomes
learning
audit
rights_manifest
hash_manifest
```

Export controls include rights, classification, secret exclusion, personal-data minimisation,
document currentness, destination policy, a content hash manifest and human export approval.

Imports are always `CANDIDATE_ONLY`. Imported decisions, approvals and outcomes are historical
records and carry no live authority. Unknown schemas or broken hashes quarantine the bundle.

## 14. Audit contract

Every consequential command creates an append-only event containing actor, server-resolved tenant
and workspace, subject and version, before and after hashes, policy, decision, reason, correlation,
time, previous-event hash and event hash.

Integrity controls:

```text
append_only
hash_chain
canonical_serialization
monotonic_sequence
tamper_detection
tenant_partition
```

A broken chain blocks export and canonical operations. Rollback produces an audit event and does
not erase history.

## 15. Authority ceiling

```text
browser                         request only
connector                       candidate only
model                           proposal only
worker                          bounded work mutation
opportunity operator            tenant-scoped operation
human approver                  typed approval only
human outcome authority         outcome recording only
human export authority          export approval only
independent admission runtime   deterministic write after approval
```

Prohibited operations include model approval, model submission, model spend, model acceptance of
terms, worker approval, worker submission, client-selected tenant authority, connector-created
outcomes, live imported approvals and learning-driven self-modification.

## 16. Evidence matrix

P07 contains:

```text
7   operational modules
23  record types
42  domain invariants
9   opportunity-library bindings
13  lifecycle states
10  pipeline stages
8   approval types
10  rights dimensions
35  conformance fixtures
63  adversarial cases
```

Each module has five fixtures:

- happy path candidate;
- incomplete context;
- revoked dependency;
- cross-tenant attempt;
- authority escalation attempt.

Each module has eight adversarial cases, plus seven cross-module cases. Every adversarial case has
canonical delta `0` and external-action delta `0`.

## 17. Rollback

P07 rollback removes the eleven P07-only artifacts, restores the P06 workflow and verifies the
complete repository tree byte-for-byte against:

```text
P06@d6317f32caad4f916f1871c23753bacd36b4d9d6
```

Seven P06 authority artifacts are hashed before and after the rehearsal to prevent dependency
drift.

## 18. Canonical gates

Canonical activation remains blocked until:

- P06 is canonically accepted or superseded by a normative ADR;
- P05, P04, P03, P02 and P01 transitive dependencies are resolved;
- lifecycle, decisions, work, approvals, outcomes, learning, portability and audit tests pass;
- all 35 fixtures and 63 adversarial cases pass;
- byte-exact rollback passes;
- Human Opportunity Authority approves;
- Human Approval Authority approves;
- Human Rights Authority approves;
- Human Product Authority approves.

Until those gates are satisfied, P07 is engineering evidence only and must not merge to `main`.
