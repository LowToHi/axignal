# Subscriber workspace engineering evidence — 2026-08-02

Goal: `AXIGNAL-GOAL-001`
Task: `AX-GE2E-P08-T02`
State: `AX_SUBSCRIBER_WORKSPACE_ENGINEERING_IN_PROGRESS`

## Authority and isolation

- Architecture PR: `#128`
- Exact head: `3d2085026232504bff13966dfdde64acabdc54e1`
- Exact tree: `2ec917abcc137b7a39eefc609234d4ea8aa66614`
- Implementation branch: `codex/subscriber-workspace-e2e`
- Original dirty landing worktree was not modified.

## Implemented evidence

- Persistent labelled global shell, command palette, notification surface, locale/theme controls and contextual workspace navigation.
- Intelligence Shell with Navigator, shared context, GLOBE/GRAPH/DUAL lenses, Timeline, opportunity rail, claim/evidence rail, metrics and accessible equivalents.
- Route-addressable Tender Workspace with overview, qualification, requirements, evidence, documents, workplan, clarifications, changes, commercial, team/approvals, submission, outcome and audit sections.
- Server-resolved tenant, identity, roles, capabilities and entitlement.
- Explicit fixture boundary, fail-closed real adapter, idempotent action IDs, revision checks, audit events, separation of duties and generic cross-tenant `404`.
- Responsive browser inspection at 1680×945, 1024×768 and 390×844 in the selected in-app browser. No browser console errors were observed.
- Dark and light theme rendering inspected; light WebGL transparency and initial server theme reconciliation corrected.

## Executed validation

```text
corepack pnpm@10.12.4 --filter @axignal/web typecheck  PASS
corepack pnpm@10.12.4 --filter @axignal/web test       PASS (25/25)
corepack pnpm@10.12.4 --filter @axignal/web build      PASS
browser route/navigation and responsive inspection    PASS (bounded manual evidence)
browser console errors                                 0 observed
```

Server tests cover explicit fixture admission, role/capability resolution, malformed action rejection, idempotent persistence, bounded audit events, cross-tenant denial, clarification self-approval denial and the non-executing external-confirmation boundary.

## Unresolved completion gates

- Full user-facing copy parity for `en`, `es`, `fr`, `de`, `pt`, `it` is incomplete; locale selection and persistence alone are not translation parity.
- Persistent document creation, generic approval recording and export generation still expose honest rejected/unavailable mutation states.
- The Globe is functional WebGL with a nonvisual equivalent, but admitted cartographic assets and a real upstream InvestigationContext are not wired; it must not be treated as canonical geography.
- Automated browser accessibility, visual-regression and performance budgets have not been executed in the selected in-app-browser workflow.
- Qualified-user validation, contradiction-heavy scenario study and independent Product/UX/Accessibility/Security/Privacy gate decisions do not exist.

These gaps prohibit `AX_SUBSCRIBER_WORKSPACE_ENGINEERING_COMPLETE`, `FINAL_UX`, `CANONICAL_ACCEPTANCE` and `PUBLIC_LAUNCH`.
