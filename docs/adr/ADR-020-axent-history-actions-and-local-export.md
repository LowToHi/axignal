# ADR-020 — AXENT chat history actions and local export

## Status

Accepted

## Context

AXENT stores subscriber conversations locally under the tenant-scoped history key. A saved conversation must remain useful after the initial exchange: subscribers need to remove it, carry its evidence-bounded context into a new conversation, and retain an offline copy without sending chat content to an external export service.

## Decision

- Add explicit per-conversation actions for reuse as context, text download, PDF export and deletion.
- Reuse creates a new conversation state with a visible context attachment; the assistant request receives a bounded representation of that prior conversation as background context.
- Store the reused context as conversation metadata so subsequent turns in the new conversation retain the same provenance.
- Generate `.txt` and PDF artifacts entirely in the browser with object URLs; no chat content is uploaded for export.
- Confirm deletion before removing a conversation and clear the active view when the active conversation is deleted.
- Keep exports and deletion bounded to the locally stored tenant scope.

## Alternatives considered

- Reopen the old conversation and append to it: rejected because reuse must preserve a clean new thread and an auditable context boundary.
- Send export data to a server PDF service: rejected because it adds privacy, retention and operational burden for a local artifact.
- Hide actions in an undiscoverable overflow menu: rejected because the actions are core history capabilities and must be keyboard discoverable.

## Tradeoffs

- The browser-generated PDF uses a compact Helvetica text layout rather than a server-rendered branded document.
- Context reuse is bounded to recent messages to protect request size and inference cost.
- Local history remains device/browser scoped until a future server-backed history contract is introduced.

## Consequences

Subscribers can manage and carry forward their AXENT work without leaving the shell. The assistant receives explicit, bounded prior context while AXIGNAL keeps authority, evidence and uncertainty rules unchanged.
