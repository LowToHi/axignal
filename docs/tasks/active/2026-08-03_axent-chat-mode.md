# AXENT chat mode and conversation history

## Objective

Make AXENT a functional conversation surface after the first submitted message and provide tenant-scoped local chat history with a New chat control.

## Context

Goal: `AXIGNAL-GOAL-001`.

The existing entry screen was a welcome composition with a composer, starter cards and a static RAG rail. It did not transition to a true chat or preserve conversations for later return.

## Affected systems

- `apps/web/components/subscriber/axent-home.tsx`
- `apps/web/components/subscriber/axent-home.module.css`
- `apps/web/app/api/subscriber-workspace/assistant/route.ts`
- `tests/e2e/subscriber-axent-chat.spec.ts`

## Implementation

- switch the main surface to a message log after the first submit;
- persist and restore tenant-scoped local conversation history;
- add New chat and saved conversation selection;
- pass a bounded prior message window to the assistant route;
- keep assistant grounding detail visible without restoring welcome cards;
- retain server scope, fixture fallback and proposal-only authority.

## Validation checklist

- [x] first message hides welcome-only UI;
- [x] assistant reply renders in the active thread;
- [x] New chat returns to welcome state;
- [x] saved conversation can be reopened;
- [x] TypeScript passes;
- [x] production build passes;
- [x] AXENT E2E tests pass;
- [x] Globe regression E2E tests pass.

## Risks and rollback

Local storage is not a durable conversation system and must not be treated as evidence or canonical memory. Versioned keys allow the feature to be disabled or replaced without migration. Disable the chat-mode branch and return to the prior entry composition if rollout evidence fails.
