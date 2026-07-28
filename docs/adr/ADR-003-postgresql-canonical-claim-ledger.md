# ADR-003 — PostgreSQL as Canonical Claim Ledger

- Status: `ACCEPTED`
- Date: `2026-07-26`

## Context

AXIGNAL requires relational integrity, temporal history, graph relationships, geospatial queries, vector retrieval, tenant controls and transactional state transitions. Starting with separate relational, graph, vector, geospatial and analytical databases would increase operational complexity before workload evidence exists.

## Decision

PostgreSQL is the canonical source of truth for:

- entities;
- evidence metadata;
- claims and versions;
- state transitions;
- source registry;
- graph nodes and edges;
- opportunities;
- scenarios and outcomes;
- tenant entitlements;
- audit events.

PostGIS provides geospatial capability and pgvector provides semantic indexes.

Specialised graph, search or analytical systems MAY be added as rebuildable projections. They MUST NOT become the sole canonical store without a superseding ADR.

## Consequences

- Foundation development remains operationally manageable.
- Transactions can atomically connect claim admission, event outbox and audit state.
- Graph queries may require typed edge tables and recursive SQL.
- Performance gates, not architectural fashion, determine later extraction.
- Every projection must be rebuildable from the ledger.

## Alternatives considered

- Neo4j as the primary graph database.
- A vector database as the knowledge store.
- Event sourcing with a dedicated log from day one.
- Immediate polyglot persistence with ClickHouse and OpenSearch.
