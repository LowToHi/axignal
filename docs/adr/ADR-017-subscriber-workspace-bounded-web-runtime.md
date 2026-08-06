# ADR-017 — Bounded subscriber workspace web runtime

## Status

Accepted for engineering validation; canonical UX acceptance and public launch are not authorised.

## Context

`AXIGNAL-GOAL-001` requires the PR #128 subscriber architecture to become a route-addressable, tenant-scoped product while preserving epistemic separation and subscriber authority. The existing investigation surface did not provide a labelled product shell, contextual tender workspace, persistent bounded actions, or explicit fixture/real-data failure boundaries.

## Decision

- Keep the current Next.js application and shared `@axignal/design-tokens` package.
- Introduce one server-resolved bootstrap contract and a small BFF for idempotent, revision-checked actions and audit events.
- Keep fixtures explicit, non-production-only, tenant-isolated and visibly labelled.
- Use the existing React/Next runtime, Lucide for accessible iconography, and React Three Fiber/Three for the functional Globe lens.
- Keep external communication, signature and submission execution outside AXIGNAL. The runtime can prepare a handoff and record a subscriber-confirmed external action only.
- Preserve the former InvestigationShell behind `AXIGNAL_SUBSCRIBER_WORKSPACE_ENABLED=false` as the rollback path.

## Alternatives considered

1. Replace the frontend framework or add a second component system. Rejected because it increases bundle, migration and maintenance cost without solving the authority boundary.
2. Infer roles or entitlement from client state. Rejected because tenant and permission authority must remain server-side.
3. Fall back silently to fixture data when the real adapter fails. Rejected because it would misrepresent source and operational state.
4. Implement external submission directly. Rejected because it exceeds AXIGNAL's product and consent boundary.

## Tradeoffs

- The engineering fixture enables deterministic validation but is not evidence of live-source readiness.
- The functional WebGL Globe provides interaction and nonvisual parity, but admitted cartographic assets and real upstream investigation data remain a separate gate.
- Hand-built semantic tables reduce dependency risk, but advanced virtualisation is deferred until measured data volume requires it.

## Consequences

- All workspace mutations are tenant-scoped, auditable and fail closed on stale or unauthorised state.
- The subscriber workspace can be rolled back without deleting canonical or audit records.
- Six locale identifiers and preference persistence exist, but full translated copy parity remains required before engineering completion.
- Qualified-user research and independent accessibility, security, privacy and product gate decisions remain mandatory.
