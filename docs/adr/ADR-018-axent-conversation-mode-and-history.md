# ADR-018 — AXENT conversation mode and local chat history

Status: `PROPOSED / IMPLEMENTED IN ENGINEERING FIXTURE`
Date: `2026-08-03`
Goal ID: `AXIGNAL-GOAL-001`
Decision owner: Product authority

## Context

The AXENT entry surface currently keeps its welcome hero, starter cards and next-step panel visible after the first message. That makes the interaction feel like a form with an appended reply instead of a conversation. It also offers no way to return to an earlier AXENT thread or start a clean one.

## Decision

AXENT enters a focused chat mode as soon as a message is submitted. In chat mode the welcome hero, starter prompts, next-step card and trust footer are removed from the main content area. The main surface becomes a scrollable message log with a persistent composer and source-grounding detail attached to assistant replies.

The right rail becomes Chat history in both welcome and chat states. It provides a New chat action, selectable saved conversations and an empty state. Conversations are stored in browser local storage under a tenant-scoped key; the assistant endpoint receives the prior bounded message window so the DeepSeek transport can preserve conversational context without moving tenant history into an unbounded server memory.

The server remains authoritative for retrieval, scope checks and model access. Local history is a presentation convenience, not a source of truth or evidence ledger.

## Alternatives considered

### Keep the RAG rail as the permanent right rail

Rejected for the primary chat flow because it leaves no navigation surface for returning to a conversation. RAG evidence remains available through the server response and assistant grounding detail.

### Store all chat history server-side immediately

Deferred. It would require a durable conversation contract, retention policy, tenant export/deletion semantics and additional observability before enabling it for subscribers.

### Open a separate route for every chat

Deferred. The current fixture needs fast, reversible local switching; URL-addressable conversation resources can follow the durable server contract.

## Consequences

Positive:

- the first message produces a clear, calm chat surface;
- users can start over without losing prior local threads;
- bounded prior messages are available to the assistant provider;
- no browser secret or authoritative evidence is stored in the chat layer.

Negative:

- local history is device and browser scoped until a durable conversation service exists;
- local storage requires a clear retention and deletion UX before production rollout;
- six-locale copy and accessibility states must remain aligned.

## Rollback

Remove the chat-mode branch and restore the RAG rail rendering while retaining the endpoint contract. The local history key is versioned and can be ignored without migration.

## Acceptance

- first submit removes welcome-only content;
- New chat returns to the welcome state without deleting saved threads;
- a saved thread can be reopened;
- assistant requests include a bounded prior message window;
- no non-AXIGNAL question bypasses the existing server scope guard;
- TypeScript, production build and focused E2E tests pass.
