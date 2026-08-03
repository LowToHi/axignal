# Contract 31 — Axent Customer Support E2E v1.0

Status: `CLOSED / PASS`

Contract ID: `AX-CONTRACT-AXENT-SUPPORT-E2E-v1.0`

Axent is implemented as a canonical support domain rather than an isolated chatbot. The implementation combines tenant-scoped persistence, governed versioned knowledge, server-authoritative context, fail-closed policy, typed tools, cryptographically bound consent, append-only evidence, human escalation, customer notification, telemetry and exact-head E2E verification.

## Permanent authority boundary

Axent MAY discover, retrieve, summarise, explain, classify, propose, execute explicitly authorised tools, create support cases and escalate.

Axent MUST NOT admit canonical truth, alter canonical evidence, approve customer operational decisions, mutate billing entitlements, approve Legal or Privacy/Data Rights decisions, admit sources, authorise public claims, issue discretionary refunds, declare a breach or close a critical incident.

Effective authority is always the intersection of authenticated user authority, Axent policy and the server-authoritative tool contract.

## Closed implementation phases

```text
AXENT-0 contract and boundaries                    CLOSED / PASS
AXENT-1 persistence and tenant isolation           CLOSED / PASS
AXENT-2 governed knowledge                         CLOSED / PASS
AXENT-3 server-authority context                   CLOSED / PASS
AXENT-4 read-only support chat                     CLOSED / PASS
AXENT-5 bounded tool execution                     CLOSED / PASS
AXENT-6 consented customer actions                 CLOSED / PASS
AXENT-7 human escalation round trip                CLOSED / PASS
AXENT-8 security and reliability                   CLOSED / PASS
AXENT-9 final E2E                                  CLOSED / PASS
```

## Implemented authority and evidence

The closed implementation includes:

- canonical support conversations, messages, citations and verified facts;
- support cases, immutable case events, assignment, resolution, reopen and close;
- tenant-scoped tool invocations and action ledger;
- forced PostgreSQL RLS and composite tenant foreign keys;
- approved, effective and versioned help knowledge;
- server-authoritative identity, entitlement, seat, ResearchRun and workspace context;
- typed read tools with no free-form SQL execution;
- low-risk reversible writes with idempotency and reconciled effects;
- HMAC confirmation tokens bound to tenant, subject, conversation, action, parameters and prior state;
- passkey-backed step-up authentication for material actions;
- reversible workspace archive and restore without retrospective ledger mutation;
- human support console and customer notification round trip;
- feedback, evaluation, incident linkage and tenant-safe metrics;
- prompt/tool-injection, cross-tenant replay, token substitution, expiry and assurance tests;
- clean PostgreSQL installation, restart persistence and fresh-process verification;
- backup, deliberate mutation, restore into a clean database and restricted-role verification;
- pinned workflow Actions and repository-wide supply-chain verification.

## Required closure markers

```text
AXENT_SUPPORT_CONTRACT_PASS
AXENT_PERSISTENCE_AND_TENANT_ISOLATION_PASS
AXENT_GROUNDED_KNOWLEDGE_PASS
AXENT_SERVER_AUTHORITY_CONTEXT_PASS
AXENT_READ_ONLY_SUPPORT_E2E_PASS
AXENT_BOUNDED_TOOL_EXECUTION_PASS
AXENT_CONSENTED_CUSTOMER_ACTIONS_PASS
AXENT_HUMAN_ESCALATION_ROUND_TRIP_PASS
AXENT_SUPPORT_SECURITY_AND_RELIABILITY_PASS
AXENT_CUSTOMER_SUPPORT_E2E_PASS
```

`AXENT_CUSTOMER_SUPPORT_E2E_PASS` is emitted only by the dedicated exact-head workflow after static contract verification, compilation, lint, focused tests, web typecheck, clean database bootstrap, live support round trip, restart, fresh-process verification, backup, mutation and clean restore have all succeeded.

## Closed invariants

```text
cross_tenant_leakage                = 0
unauthorised_material_actions       = 0
critical_policy_bypass              = 0
billing_authority_mutation          = 0
unknown_tool_default                = DENY
human_only_authority                = ESCALATE
exact_head_matrix                   = PASS
fresh_process_verification          = PASS
backup_mutation_restore             = PASS
supply_chain_reproducibility        = PASS
```

## Operational boundary

This contract closes the Axent customer-support implementation. It does not expand Axent authority beyond the permanent boundary and does not independently authorise production deployment, source admission, commercial entitlement mutation or public claims outside their respective authorities.
