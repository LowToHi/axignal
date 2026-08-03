# Goal Lock: AXIGNAL-GOAL-001

## Objective

Remove autonomous Globe rotation, focus the initial Globe on the current investigation area, and make AXENT saved conversations manageable, reusable and exportable.

## Affected systems

- `apps/web/components/subscriber/intelligence/SemanticGlobe.tsx`
- `apps/web/components/subscriber/axent-home.tsx`
- `apps/web/components/subscriber/axent-home.module.css`
- AXENT and Globe E2E coverage

## Validation checklist

- [x] Globe camera no longer auto-rotates.
- [x] Initial Globe orientation is derived from the current opportunity set.
- [x] Initial Globe focus preserves a north-up, zero-roll geographic frame.
- [x] Drag and zoom remain available.
- [x] Manual drag follows the geographic East-West/North-South frame without roll.
- [x] Globe selection changes do not trigger a fade transition.
- [x] Saved chats can be deleted after confirmation.
- [x] Saved chats can seed a new conversation as bounded context.
- [x] Saved chats can download as text and export as a local PDF.
- [x] TypeScript passes.
- [x] AXENT and Globe E2E suites pass.
- [ ] Validate server-backed history and cross-device sync when that contract exists.

## Rollback

Revert the Globe rotation derivation and remove the history action handlers and local PDF generator. No database migration or external service change is involved.
