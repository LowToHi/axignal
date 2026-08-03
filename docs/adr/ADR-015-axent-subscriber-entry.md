# ADR-015 — AXENT as the subscriber entry surface

Status: `PROPOSED / IMPLEMENTATION IN PROGRESS`
Date: `2026-08-03`
Goal ID: `AXIGNAL-GOAL-001`
Decision owner: Product authority

## Context

The subscriber Shell currently opens on a command-centre dashboard. That forces a new subscriber to understand AXIGNAL's information architecture before expressing intent, and it separates onboarding, support and investigation guidance into different destinations.

AXIGNAL already has a bounded DeepSeek proposal transport and a server-resolved subscriber context containing tenant, opportunity, workspace, rights and capability state. A conversational entry surface can make that context useful without turning the product into a general-purpose assistant.

## Decision

Introduce `AXENT` as the first Shell destination and default home surface. Keep Command Center available as a separate destination at `/command-center`.

AXENT will:

1. accept natural-language questions about AXIGNAL onboarding, opportunities, evidence, workspaces, methodology and support;
2. retrieve only server-resolved AXIGNAL context and tenant-authorised evidence;
3. display source-backed, unknown and needs-review material separately in a RAG context rail;
4. use the existing DeepSeek transport only through an explicit server-side feature flag, with `proposal-only` authority;
5. suggest navigation or workspace preparation, but require an explicit subscriber confirmation before navigation and never approve, send, sign, submit or mutate external state;
6. retain a deterministic engineering-fixture response when the live assistant flag is disabled.

The visual entry state is intentionally conversation-first: a centered question, large composer, onboarding prompts, a reversible next step and a compact RAG source rail.

## Alternatives considered

### Keep Command Center as the default

Rejected for the subscriber entry point because it optimises for returning operators and hides the product's first-use path.

### General-purpose chatbot

Rejected because it would expand scope, data access, safety and support obligations beyond AXIGNAL's product boundary.

### DeepSeek direct access from the browser

Rejected because provider secrets, tenant scope and capability decisions must remain server-side.

## Consequences

Positive:

- lower onboarding friction and clearer first intent;
- one entry point for onboarding, support and investigation routing;
- visible provenance and uncertainty at the point of answer;
- no change to the existing DeepSeek alias or proposal-only authority;
- a feature flag and fixture mode provide a reversible rollout.

Negative:

- AXENT needs a typed server chat contract and adversarial scope tests before live enablement;
- source grouping and language parity must be maintained across six locales;
- the Shell now has a home route distinct from Command Center and must preserve stable deep links.

## Rollback

Disable `AXIGNAL_SUBSCRIBER_WORKSPACE_ENABLED` to return to the legacy Shell, or route the first destination back to `/command-center` without deleting the AXENT surface or its audit history.

## Acceptance

This ADR advances only after server-side scope checks, tenant isolation, prompt-injection handling, model identity, source provenance, accessibility, multilingual parity and explicit navigation confirmation have independent evidence.
