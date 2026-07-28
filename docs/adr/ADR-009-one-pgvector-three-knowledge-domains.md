# ADR-009 — One pgvector platform, three isolated knowledge domains

Status: `ACCEPTED / IMPLEMENTATION REQUIRED`
Date: `2026-07-27`
Goal ID: `AXIGNAL-GOAL-001`

## Context

AXIGNAL requires semantic retrieval over global evidence and claims, tenant-private knowledge and aggregate intent signals. Treating these as one corpus would create privacy, provenance and truth-boundary failures. Creating multiple specialised vector databases immediately would add operational cost, replication complexity and premature infrastructure without measured need.

PostgreSQL is already the canonical system of record. PostGIS, pgvector, full-text search and typed relational tables provide the required foundation for the first lawful universe and early product scale.

## Decision

Use one PostgreSQL and pgvector platform initially, with three logically and operationally isolated knowledge domains:

### `axignal_global`

Contains admitted sources, raw-object references, Evidence Objects, Candidate Claims, canonical claims, contradictions, graph edges, opportunities and global embeddings.

### `tenant_private`

Contains tenant-authorised documents, notes, trails, private evidence, private Candidate Claims, preferences, watchlists and embeddings.

### `intent_intelligence`

Contains purpose-limited interpreted intent events, aggregate cohorts, Knowledge Tides, manipulation signals and research-priority artifacts.

Each domain MUST have:

- separate PostgreSQL schemas;
- separate tables and vector indexes;
- explicit service roles;
- Row-Level Security where tenant data exists;
- independent retention and deletion policy;
- separate encryption and secret contexts where applicable;
- domain-labelled retrieval results;
- bounded bridge services;
- audit logs and metrics.

A query MUST NOT perform unbounded similarity search across all three domains.

## Permitted bridges

```text
tenant_private
→ private ResearchRun response or dossier
```

```text
intent_intelligence aggregate
→ Research Candidate
→ external evidence collection
→ Candidate Claims
→ deterministic admission
```

```text
explicitly authorised tenant contribution
→ source-admission review
→ evidence and claim-admission pipeline
```

## Prohibited bridges

```text
private document
→ global Claim Ledger directly
```

```text
Knowledge Tide
→ admitted economic claim or opportunity directly
```

```text
vector similarity
→ truth, corroboration or causal relation
```

## Why not two physical vector databases

The relevant distinction is authority and tenancy, not the number of database products. Separate physical systems do not by themselves guarantee correct bridges, and they increase:

- deployment and backup complexity;
- data synchronisation risk;
- duplicate canonical state;
- operational cost;
- deletion-propagation complexity;
- disaster-recovery surface.

Logical isolation inside PostgreSQL is sufficient until measured scale or security evidence proves otherwise.

## Extraction gate for a dedicated vector service

A dedicated vector database MAY be introduced through a new ADR only when at least one condition is demonstrated:

- pgvector index size or concurrency cannot meet accepted SLOs;
- tenant isolation or metadata filtering cannot be enforced safely;
- vector ingestion materially disrupts canonical transactions;
- specialised retrieval capability is unavailable in pgvector;
- total cost, including replication, backup and operations, is lower;
- regulatory or contractual isolation requires physical separation.

The evaluation MUST include migration, deletion, backup, provenance and rollback evidence.

## Consequences

### Positive

- preserves PostgreSQL as canonical state;
- reduces early infrastructure cost;
- keeps vectors close to typed metadata and graph relationships;
- supports transactional deletion and audit;
- enables explicit tenant and authority boundaries;
- avoids premature platform fragmentation.

### Negative

- schema, role and Row-Level Security design must be rigorous;
- vector workloads may compete with canonical workloads;
- domain bridges require dedicated application services;
- future physical extraction may require reindexing and migration.

## Acceptance

This decision is implemented when:

1. all three schemas and service roles exist;
2. tenant-private tables enforce Row-Level Security;
3. vector queries require an explicit domain and tenant scope;
4. cross-domain bridge operations are typed and audited;
5. deletion removes or tombstones derived embeddings;
6. tests prove global, private and intent corpora cannot be queried as one unrestricted corpus;
7. backup and restore preserve domain boundaries;
8. a measured extraction gate exists before any dedicated vector service is adopted.

## Rollback

If a domain must be physically separated, freeze writes to its bridge, export canonical records and metadata, rebuild the target index from authoritative rows, verify counts and tenant isolation, switch reads behind a feature flag and retain the PostgreSQL source until rollback and deletion propagation are proven.
