# P12 — Corporate, Filings and Ownership Library + Account Opportunity Workspace

**Task:** `AX-GE2E-P12-T01`  
**Programme:** `P00–P24` v1.4  
**Library:** `AX-LIB-O05 — Corporate, Filings and Ownership Signals`  
**Workspace:** `Account Opportunity Workspace`  
**Engineering base:** `AX-GE2E-P11-T01@315d88731939c1904fcca7be4e5b58d4615ab423`  
**Normative dependency:** `AX-GE2E-P07-T01@e30f800cb284f1381c28c4ccbc116a8da4a9fe92`

## Status

`DRAFT_ENGINEERING_FOUNDATION / CANONICAL ACTIVATION FAIL-CLOSED`

P12 provides a reversible engineering specialisation for corporate registry identity, filings, ownership, control, governance, corporate actions and tenant-scoped account operations. It does not admit a corporate source, establish a beneficial owner, make a credit or legal conclusion, contact an external party, execute a transaction or authorise public product coverage.

P01 remains `IN_PROGRESS`. P02–P11 remain engineering evidence only and are not canonically activated. This phase is therefore stacked on the frozen P11 engineering head and must remain draft.

## Objective

Implement filings, ownership and the Account Opportunity Workspace while preserving:

- immutable filing and disclosure versions;
- reversible entity resolution;
- explicit separation of ownership, voting rights, economic interest and control;
- authorised, purpose-bound handling of director and beneficial-owner data;
- distinction between announced, agreed, approved, signed and completed corporate actions;
- tenant-scoped account thesis, pursuit, approval, work, outcome and learning;
- human-only external outreach, signatures, commitments and transactions;
- source-rights, privacy, multilingual and epistemic fail-closed behaviour.

## Exact `AX-LIB-O05` binding

```text
canonical name   Corporate, Filings and Ownership Signals
workspace        Account Opportunity Workspace
entities         CorporateOpportunity, Company, Filing,
                 OwnershipInterest, Director, BeneficialOwner
predicates       FILED_BY, OWNS, CONTROLLED_BY, DIRECTOR_OF,
                 SUBSIDIARY_OF, ANNOUNCES
events           FILING_PUBLISHED, OWNERSHIP_CHANGED,
                 DIRECTOR_APPOINTED, CAPITAL_RAISED,
                 ACQUISITION_ANNOUNCED
taxonomies       NACE, NAICS, LEI
```

The P12 runtime must match the P02 library contract exactly. It may specialise the domain but cannot widen the library contract, its source rights or its authority.

## Eight domain modules

| Module | Service | Purpose |
|---|---|---|
| `ENTITY_REGISTRY` | `corporate_entity_registry` | Registry identity, identifiers, names, status, predecessors and successors |
| `FILING_DISCLOSURE` | `corporate_filing_service` | Immutable filings, versions, restatements, withdrawals, disclosures and anchors |
| `OWNERSHIP_CONTROL` | `ownership_control_service` | Direct/indirect interests, voting rights, control bases and bounded beneficial ownership |
| `GOVERNANCE_OFFICER` | `corporate_governance_service` | Officers, board appointments, signing authority and privacy-bounded governance events |
| `CAPITAL_CORPORATE_ACTION` | `corporate_action_service` | Capital events, securities, acquisitions, disposals, restructurings and completion state |
| `ACCOUNT_OPPORTUNITY_WORKSPACE` | `account_opportunity_workspace_service` | Tenant-scoped account thesis, plan, decision, work and pursuit |
| `MONITORING_RELATIONSHIP_RISK` | `corporate_monitoring_risk_service` | Versioned signals, relationships, risks, contradictions and monitoring rules |
| `EXTERNAL_ACTION_OUTCOME` | `corporate_external_action_service` | Human-authorised outreach/transaction requests, observed outcomes and audit |

Each module defines four record types and six invariants: 32 record types and 48 domain invariants in total.

## Corporate truth boundary

```text
similar name or address          != same legal entity
registry record                  != current operating status
filing published                 != filing accepted or legally effective
filing amendment                 != deletion of the prior version
share ownership                  != voting control
voting control                   != beneficial ownership
director appointment announced  != appointment effective
director role                    != unrestricted signing authority
public officer data              != unrestricted personal-data enrichment
capital target                   != committed capital
committed capital                != received proceeds
acquisition announced            != transaction agreed
transaction agreed              != regulatory approval
transaction signed               != transaction completed
account readiness                != outreach or transaction authority
corporate signal                 != creditworthiness conclusion
```

Unknown, contested, incomplete, stale, withdrawn, superseded or rights-revoked evidence does not pass.

## Lifecycle

```text
DETECTED
→ ENTITY_RESOLVING
→ MONITORING
→ QUALIFYING
→ QUALIFIED
→ ACCOUNT_OPEN
→ DECISION_PENDING
→ APPROVED or DECLINED
→ IN_EXECUTION
→ CLOSED
```

`REJECTED` and `CLOSED` are terminal states for the current opportunity instance. A closed account can return to monitoring only through a new observed signal and a new versioned transition. Lifecycle state is not authority to contact, sign, spend, acquire, invest or transact.

## Operating pipeline

1. `DISCOVER_SIGNAL`
2. `RESOLVE_ENTITY`
3. `VALIDATE_FILING`
4. `MAP_OWNERSHIP_CONTROL`
5. `ASSESS_GOVERNANCE_PRIVACY`
6. `QUALIFY_ACCOUNT`
7. `BUILD_ACCOUNT_THESIS`
8. `REVIEW_RISKS_RIGHTS`
9. `DECIDE_PURSUE`
10. `AUTHORISE_EXTERNAL_ACTION`
11. `RECORD_OUTCOME_LEARNING`

The default and indeterminate decisions are `DENY`.

## Filing, ownership and action semantics

### Filing versions

A filing record binds the registry, issuer, filing type, filing/version identifiers, publication time, effective time where observed, source version and document anchors. Amendments, restatements and withdrawals create lineage. They never overwrite prior evidence.

### Ownership and control

P12 keeps separate:

- registered shareholding;
- economic interest;
- voting rights;
- direct ownership;
- indirect ownership;
- ultimate parent;
- beneficial ownership;
- control by agreement;
- control through governance rights;
- contested or unknown interests.

A percentage between 0 and 100 is not, by itself, proof of control or beneficial ownership. Beneficial-owner processing requires source authority, purpose limitation, legal basis, minimisation and a current rights snapshot.

### Corporate actions

P12 represents announcement, proposal, agreement, approval, signature, completion, cancellation and termination separately. A model or worker cannot promote an announced or rumoured event to a completed fact.

## Account readiness gates

```text
ENTITY_RESOLVED
REGISTRY_STATUS_CURRENT
FILING_SET_CURRENT
OWNERSHIP_CHAIN_RESOLVED
CONTROL_BASIS_VERIFIED
GOVERNANCE_DATA_AUTHORISED
CORPORATE_ACTION_STATUS_VERIFIED
ACCOUNT_THESIS_EVIDENCE_LINKED
RISKS_AND_CONTRADICTIONS_REVIEWED
RIGHTS_AND_PRIVACY_CURRENT
APPROVALS_CURRENT
CHANNEL_RECIPIENT_AUTHORITY_VERIFIED
```

All twelve gates must be `PASS` for `READY`. Any `DENY` produces `DENY`; any other non-pass result produces `REVIEW_REQUIRED`; missing gates produce `NOT_READY`.

`READY` means only that a typed human authority may consider the configured external action. It is not legal advice, a credit rating, due-diligence completion, contact authority, signing authority, investment approval or transaction approval.

## Authority ceiling

```text
browser                         request only
connector/parser/OCR            candidate only
model                           proposal only
worker                          bounded work mutation
account operator                tenant-scoped operation
human corporate authority       corporate-fact approval only
human privacy authority         personal-data approval only
human legal authority           legal approval only
human finance authority         capital approval only
human external-action authority outreach/transaction action only
human outcome authority         observed outcome only
independent admission runtime   deterministic write after approval
```

Models and workers cannot:

- silently merge entities;
- declare a beneficial owner or controller;
- make a creditworthiness or legal conclusion;
- enrich natural-person data without authority;
- contact, represent or bind the organisation;
- sign, invest, acquire, sell or transact;
- convert private workspace content into global canonical evidence;
- create observed corporate outcomes.

## Rights and privacy

P12 inherits the ten rights dimensions without reduction:

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

A public register or filing portal is not automatically admissible for every field, purpose or product surface. Natural-person records are separately constrained by purpose, legal basis, minimisation, retention, display and export rules.

## Multilingual boundary

Critical parity is required for `en`, `es`, `fr`, `de`, `pt` and `it`, especially for:

- entity status;
- filing type and version;
- effective and event dates;
- ownership percentages and voting rights;
- control basis;
- director/officer role;
- transaction state;
- currency and valuation basis;
- negation, modality and qualifiers;
- citation anchors.

Machine translation is proposal-only and cannot create legal equivalence or change source-native evidence.

## Source catalogue boundary

The existing research catalogue contains five official candidate families:

```text
SEC EDGAR
UK Companies House
GLEIF LEI Data
ESMA ESEF
EU Business Registers Interconnection System
```

Every entry remains:

```text
product_admitted           false
rights_status              UNREVIEWED
public_coverage_authorised false
```

No connector, scraping path, source admission, production ingestion or public coverage claim is activated by P12.

## Conformance and adversarial evidence

The phase materialises:

- eight modules × five conformance classes = **40 fixtures**;
- nine scopes × eight threats = **72 adversarial cases**;
- deterministic reference functions for filing currentness, ownership, control, personal-data authority, corporate actions, readiness, external action and outcomes;
- schema validation and exact P02/P05/P06/P07/P11 inheritance checks;
- source-catalogue non-admission checks;
- byte-exact rollback to the frozen P11 head.

The adversarial matrix covers silent entity merge, filing version/status confusion, ownership-as-control or beneficial-owner inference, personal-data expansion, announcement-as-completion, revoked rights, cross-tenant references and authority escalation. Every case permits zero canonical delta and zero external-action delta.

## Rollback

P12 adds eleven phase-only artifacts and modifies only Contract Validation. The rollback rehearsal:

1. verifies the exact changed-path set from the frozen P11 head;
2. hashes seven P11 authority artifacts;
3. removes every P12-only artifact;
4. restores Contract Validation byte-for-byte from P11;
5. confirms no P12 residue;
6. confirms P11 authority files did not change;
7. compares the complete rolled-back tree with the frozen P11 baseline.

## Canonical activation gate

Engineering evidence is not canonical activation. P12 remains blocked until all thirty declared gates pass, including transitive P01–P11 resolution, independent source admissions, entity-resolution and ownership/control review, beneficial-owner privacy/legal approval, filing and corporate-action lineage proof, tenant isolation, multilingual parity, deterministic tests, rollback and the required human authorities.

## Explicit exclusions

- no source activation or product admission;
- no corporate data ingestion;
- no beneficial-owner or control claim;
- no personal-data enrichment;
- no creditworthiness, sanctions, legal or investment conclusion;
- no automated outreach, messaging or CRM contact;
- no signature, acquisition, investment, purchase or sale;
- no billing, commercial activation or public launch;
- no merge to `main` while dependencies remain false.
