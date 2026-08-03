# Contract 31 — Axent Customer Support E2E v1.0

Status: `IMPLEMENTATION_IN_PROGRESS / FAIL_CLOSED`

Contract ID: `AX-CONTRACT-AXENT-SUPPORT-E2E-v1.0`

Axent SHALL be implemented as a canonical support domain, not as an isolated chatbot. The implementation SHALL combine tenant-scoped persistence, versioned knowledge, server-authoritative context, a governed policy engine, typed tools, consent, append-only audit, human escalation and exact-head E2E evidence.

## Permanent authority boundary

Axent MAY discover, retrieve, summarise, explain, classify, propose, execute explicitly authorised tools, create support cases and escalate.

Axent MUST NOT admit canonical truth, alter canonical evidence, approve customer operational decisions, mutate billing entitlements, approve Legal or Privacy/Data Rights decisions, admit sources, authorise public claims, issue discretionary refunds, declare a breach or close a critical incident.

## Required implementation phases

```text
AXENT-0 contract and boundaries
AXENT-1 persistence and tenant isolation
AXENT-2 governed knowledge
AXENT-3 server-authority context
AXENT-4 read-only support chat
AXENT-5 bounded tool execution
AXENT-6 consented customer actions
AXENT-7 human escalation round trip
AXENT-8 security and reliability
AXENT-9 final E2E
```

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

## Current bounded implementation

This branch introduces the canonical persistence schema, RLS, append-only citation/action ledgers, support conversations, messages, cases, tool invocation records, a server-authoritative Context Builder, a fail-closed policy engine, deterministic grounded read-only responses, typed read tools and human escalation case creation.

It does not claim final closure. Material actions remain denied or confirmation-gated and no billing authority mutation is implemented.

## Final closure conditions

```text
cross_tenant_leakage                = 0
unauthorised_material_actions       = 0
critical_policy_bypass              = 0
billing_authority_mutation          = 0
exact_head_matrix                   = PASS
fresh_process_verification          = PASS
backup_mutation_restore             = PASS
```
