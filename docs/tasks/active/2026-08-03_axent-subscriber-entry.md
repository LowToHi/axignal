# AXENT subscriber entry surface

## Objective

Make AXENT the first destination and default conversational entry point for the subscriber Shell, grounded in server-resolved AXIGNAL context and the existing proposal-only DeepSeek transport.

## Context

Goal `AXIGNAL-GOAL-001`; P08 subscriber workspace head. The selected visual direction is a centered onboarding composer with three starter paths, a suggested workspace step and a RAG context rail grouped by source state.

## Affected systems

- `apps/web/components/subscriber/product-shell.tsx`
- `apps/web/components/subscriber/subscriber-workspace-app.tsx`
- `apps/web/components/subscriber/axent-home.tsx`
- `apps/web/app/api/subscriber-workspace/assistant/route.ts`
- subscriber Shell CSS and environment contract

## Implementation plan

1. Add AXENT as the first Shell route and preserve Command Center at `/command-center`.
2. Render the selected visual entry state with accessible composer, starter prompts, RAG rail and reversible workspace navigation.
3. Keep the chat server-side and fail closed on disabled feature, invalid payload and out-of-scope request.
4. Use fixture responses by default; enable DeepSeek only with an explicit server feature flag.
5. Verify type safety, local render, starter interaction and confirmation boundary.

## Blockers

- The live subscriber assistant API contract and retrieval adapter are not yet independently accepted; live DeepSeek remains disabled.

## Risks

- Scope drift into a general assistant.
- RAG source summaries being mistaken for canonical claims.
- Navigation confirmation being mistaken for approval or external action.

## Validation checklist

- [x] AXENT is above Command Center in the navigation.
- [x] `favicon.svg` asset is reused for AXENT identity.
- [x] RAG source groups distinguish source-backed, unknown and needs-review items.
- [x] Out-of-scope assistant messages fail closed.
- [x] Workspace navigation requires explicit acknowledgement.
- [x] Typecheck passes.
- [ ] Live DeepSeek and retrieval contract independently gated.
- [ ] Six-locale copy parity and dedicated E2E evidence.

## Rollback considerations

Disable `AXIGNAL_SUBSCRIBER_WORKSPACE_ENABLED` or route `/` back to `/command-center`; preserve all existing workspace and investigation routes.
