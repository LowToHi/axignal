# 26 — AXIGNAL Private Knowledge and Tenant Memory Contract

Version: `0.1.0`
Status: `NORMATIVE CANDIDATE`
Goal ID: `AXIGNAL-GOAL-001`

## 1. Purpose

AXIGNAL MAY remember user and organisation knowledge to continue investigations, retrieve private documents and personalise workflows. This capability MUST preserve tenant isolation, purpose limitation, reversibility and a strict separation from global economic truth.

Private memory exists to help a user investigate more effectively. It does not authorise AXIGNAL to convert confidential material, personal preference or user attention into public claims or opportunities.

## 2. Logical knowledge domains

AXIGNAL MUST maintain three logically isolated domains:

1. `axignal_global` — admitted public or licensed sources, evidence, claims, opportunities and graph state;
2. `tenant_private` — user- or organisation-authorised documents, notes, trails, private evidence, preferences and embeddings;
3. `intent_intelligence` — purpose-limited intent events, aggregate cohorts, Knowledge Tides and research-priority signals.

The domains MAY initially share one PostgreSQL and pgvector platform, but MUST use separate schemas, access policies, indexes, encryption contexts, retention rules and audit trails.

## 3. Tenant-private item types

Private knowledge MAY include:

- uploaded documents;
- user notes;
- organisation research reports;
- saved Investigation Trails;
- watchlists;
- authorised connector data;
- private Evidence Objects;
- private Candidate Claims;
- confirmed preferences;
- inferred preferences with visible basis and expiry;
- private entity aliases and mappings;
- prior research dossiers;
- monitoring configurations.

Raw chat text is not automatically durable memory.

## 4. Purpose separation

The system MUST distinguish at least:

- execute the current request;
- retain a private investigation;
- remember a confirmed preference;
- infer a temporary preference;
- improve product quality;
- contribute to privacy-protected aggregate Knowledge Tides;
- evaluate a model or workflow.

One purpose MUST NOT imply consent for another. Consent and authority surfaces MUST be specific, visible and reversible.

## 5. Memory levels

### Ephemeral context

Used only for the current session or ResearchRun and deleted or expired according to short retention.

### Saved investigation memory

Explicitly saved trails, dossiers, selections and notes.

### Inferred preference

A time-bounded inference based on repeated eligible behaviour. It MUST expose basis, confidence, expiry and correction controls.

### Confirmed preference

A user- or organisation-confirmed setting or interest.

### Organisation knowledge

Private material governed by organisation roles, policies, retention and contractual rights.

## 6. User controls

Users MUST be able to:

- see whether memory is enabled;
- inspect saved investigations;
- inspect inferred and confirmed preferences;
- correct or delete memory;
- disable future memory;
- remove a private source or connector;
- export eligible private data;
- exclude eligible activity from aggregate analysis where applicable;
- see when private knowledge influenced a response.

Deletion MUST propagate to retrieval indexes, embeddings, caches, derived private artifacts and future prompts within the documented service objective.

## 7. Tenant isolation

Every private object MUST carry:

- tenant ID;
- owner or organisation scope;
- access-control policy;
- purpose permissions;
- retention class;
- source and rights metadata;
- created and updated times;
- encryption and key context where applicable;
- audit references;
- deletion state.

Row-Level Security or an equivalently strong policy MUST enforce tenant isolation at the database boundary. Application filters alone are insufficient.

## 8. Retrieval policy

Private retrieval MUST require:

- an authenticated principal;
- a tenant scope;
- an authorised purpose;
- an allowed item class;
- a time and retention check;
- source-rights compatibility;
- an auditable query or ResearchRun.

Hybrid retrieval MAY use structured filters, lexical search, pgvector and private graph edges. Every result MUST retain tenant and item identifiers.

A model MUST NOT receive broader private context than required for the current operation.

## 9. Cross-domain bridges

Permitted bridges:

```text
private knowledge
→ private answer, private dossier or private Candidate Claim
```

```text
eligible pseudonymous intent events
→ privacy-protected cohort aggregate
→ Knowledge Tide
→ Research Candidate
```

```text
private source with explicit lawful contribution authority
→ source-admission review
→ evidence and claim-admission pipeline
```

Prohibited bridges:

```text
private document
→ global Claim Ledger without explicit authority and gates
```

```text
one user's preference
→ public Knowledge Tide
```

```text
high user attention
→ economic opportunity admitted
```

## 10. Knowledge Tides

Knowledge Tides MUST remain in the `intent_intelligence` domain. They describe aggregate user attention under minimum-cohort, independence, manipulation and privacy gates.

They MAY:

- prioritise research;
- identify coverage gaps;
- surface divergence between attention and admitted evidence;
- suggest monitoring topics.

They MUST NOT:

- prove market demand, profitability or suitability;
- expose private prompts or organisation investigations;
- create public claims directly;
- bypass source and admission gates.

## 11. Private claims and evidence

A tenant MAY maintain private Evidence Objects and Candidate Claims. They MUST be labelled `TENANT_PRIVATE` and MUST not be confused with global admitted claims.

A private claim MAY be shown in a private dossier when:

- its evidence and provenance are visible;
- its provisional or admitted-private state is explicit;
- access rights are valid;
- the user understands that it is not part of the global Claim Ledger.

## 12. External model boundary

Before sending private content to an external model, AXIGNAL MUST verify:

- purpose and user or organisation authority;
- provider data-processing terms;
- jurisdiction and transfer constraints;
- retention and training settings;
- minimisation and redaction;
- model and provider identity;
- audit logging without content leakage.

Where authority is absent, processing MUST remain local or fail closed.

## 13. Embeddings

Private and global embeddings MUST use separate indexes or partitions with enforced metadata filters. A vector match MUST never cross tenant or domain boundaries without an explicit authorised bridge.

Embeddings MUST NOT be the sole persistence of private meaning. Deleting an item MUST delete or tombstone every derived embedding.

## 14. Security

- Private storage MUST be encrypted in transit and at rest.
- Secrets and connector credentials MUST be tenant-scoped and revocable.
- Downloads and uploads MUST be malware-, type- and size-bounded.
- Private data MUST not enter application logs, telemetry or test artifacts.
- Support access MUST be exceptional, time-bounded and audited.
- Backups MUST preserve deletion and tenant-restoration policy.
- Cross-tenant retrieval tests MUST be mandatory release gates.

## 15. Retention

Retention MUST be defined separately for:

- raw chat text;
- ephemeral context;
- uploaded source objects;
- extracted text;
- embeddings;
- private Evidence Objects;
- private Candidate Claims;
- saved trails and dossiers;
- inferred preferences;
- confirmed preferences;
- audit records;
- aggregate intent statistics.

Expired or deleted material MUST not remain retrievable through embeddings, caches or summaries.

## 16. Observability

Required metrics include:

- private retrieval requests by purpose;
- cross-tenant denial count;
- result-set tenant purity;
- deletion propagation time;
- memory opt-in and opt-out rates;
- inferred-preference correction rate;
- external-model private-content rate;
- private-to-global contribution requests and rejection rate;
- Knowledge Tide suppression rate;
- unauthorised bridge attempts.

Metrics MUST not contain private content.

## 17. Failure behaviour

The system MUST distinguish:

- memory disabled;
- item not found;
- access denied;
- purpose not authorised;
- retention expired;
- connector revoked;
- external model not authorised;
- tenant boundary conflict;
- deletion pending;
- insufficient privacy cohort.

A retrieval failure MUST NOT fall back to another tenant, global approximation presented as private knowledge or fabricated memory.

## 18. Acceptance criteria

The capability is accepted when:

1. tenant-private retrieval is enforced at the data boundary;
2. cross-tenant tests fail closed;
3. global, private and intent indexes cannot be queried as one unbounded corpus;
4. users can inspect, correct and delete memory;
5. deletion propagates to embeddings and caches;
6. private context sent to external models is purpose-authorised and minimised;
7. private dossiers remain private by default;
8. Knowledge Tides meet cohort and manipulation gates;
9. no private material reaches the global Claim Ledger without explicit authority and full source/claim admission;
10. the UI shows when private knowledge influenced a result.
