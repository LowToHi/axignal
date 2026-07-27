# ADR-010 — Local AI has proposal authority, never admission authority

Status: `ACCEPTED / IMPLEMENTATION REQUIRED`
Date: `2026-07-27`
Goal ID: `AXIGNAL-GOAL-001`

## Context

AXIGNAL intends to operate research workers continuously over authorised APIs, documents and emerging external information. Local models can reduce marginal cost, preserve sensitive processing boundaries and perform high-volume extraction, classification, entity resolution and contradiction discovery.

A generative model, whether local or external, remains probabilistic. Allowing it to write canonical claims would contradict the epistemic core of AXIGNAL and make source rights, provenance, reproducibility and correction dependent on unverified model output.

## Decision

Every local or external model has **proposal authority only**.

A model MAY create:

- extraction candidates;
- entity and relation proposals;
- Evidence Object drafts bound to real source material;
- Candidate Claims;
- contradiction candidates;
- explicit unknowns;
- research plans;
- dossiers;
- admission-handoff packages.

A model MUST NOT:

- create or update canonical Claim Ledger records directly;
- assign `ADMISSIBLE`, `CORROBORATED` or `ACTIONABLE` state;
- override source or rights policy;
- treat its own confidence as evidence;
- publish opportunities;
- merge private tenant knowledge into global state;
- alter deterministic gate outcomes;
- erase rejected, contested or superseded history.

The canonical authority chain is:

```text
source and raw object
→ Evidence Object
→ model or parser proposal
→ Candidate Claim
→ deterministic gates
→ optional human adjudication
→ canonical Claim Ledger transition
```

## Permission model

Research workers MUST receive only the minimum permissions required to:

- read authorised source queues;
- read bounded source objects;
- write proposal or quarantine records;
- append job and cost telemetry;
- enqueue admission-review packages.

They MUST NOT hold:

- canonical claim-write credentials;
- database-owner or migration permissions;
- deployment credentials;
- unrestricted tenant access;
- source-policy administration rights;
- secrets unrelated to the active task.

## Local and external model parity

The authority boundary applies equally to:

- self-hosted models;
- third-party APIs;
- vision or OCR models;
- embedding models;
- rerankers;
- agentic workflows;
- human-authored model prompts.

Running a model locally does not increase its epistemic authority.

## Structured outputs

Model outputs MUST be validated against versioned Pydantic models or JSON Schemas. Invalid, incomplete or ambiguous output MUST be retried within budget, repaired deterministically where safe or quarantined.

Schema validity does not imply epistemic validity.

## Admission independence

The admission runtime MUST independently verify:

- structure;
- source existence and addressability;
- source rights;
- temporal scope;
- units, currencies and denominators;
- entity identity;
- independent-source lineage;
- contradiction pressure;
- claim-type policy;
- freshness and expiry;
- tenant and publication scope.

The producing model identity or benchmark score MUST NOT waive a gate.

## Human review

Human review MAY resolve ambiguity or approve high-impact transitions, but it MUST preserve:

- the original model proposal;
- deterministic gate results;
- evidence lineage;
- reviewer identity and reason;
- reversible transition history.

Human review does not convert unsupported model text into evidence.

## Consequences

### Positive

- preserves AXIGNAL's epistemic differentiation;
- allows inexpensive continuous research without granting truth authority;
- supports model replacement and benchmarking;
- limits the impact of hallucination, compromise and prompt injection;
- makes local and API models interchangeable behind a gateway;
- enables safe use of lower-cost models for volume.

### Negative

- requires a separate admission runtime and schemas;
- increases pipeline stages and latency;
- some high-value claims require human review;
- more artifacts and audit events must be stored;
- model output cannot be displayed as canonical immediately.

## Acceptance

This decision is implemented when:

1. worker credentials cannot write canonical claim tables;
2. every model output is stored as proposal, evidence draft, dossier or Candidate Claim;
3. admission revalidates source, rights, structure, time and epistemic status independently;
4. tests prove direct canonical writes are rejected;
5. prompt-injection fixtures cannot change permissions or admission state;
6. local and external model metadata are preserved;
7. replacing a model does not alter the authority model;
8. rejected and contested proposals remain auditable;
9. no user-facing surface labels a proposal as admitted truth.

## Rollback

If a worker or model route is compromised, disable its queue consumer and credentials, quarantine outputs since the last trusted checkpoint, preserve audit evidence, replay affected admission packages from source objects with a trusted parser or model and leave existing canonical claims unchanged unless an independent correction or retraction process requires action.
