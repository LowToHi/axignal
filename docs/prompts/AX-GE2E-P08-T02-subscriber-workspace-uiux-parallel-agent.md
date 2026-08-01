# Parallel Agent Prompt — AXIGNAL Subscriber Workspace UI/UX

Act as a **Staff Product Engineer, Principal UX Architect, Design Systems Lead, Procurement Workflow Expert, Accessibility Lead and QA Lead**.

## Mission

Implement the complete subscriber-facing AXIGNAL product shell and Tender Workspace on branch:

```text
agent/ax-subscriber-workspace-uiux-v1
```

Base exclusively on the latest accepted UX architecture branch containing:

```text
docs/research/2026-08-01-subscriber-workspace-tooling-ux-study.md
docs/experience/subscriber-workspace-information-architecture-v1.md
data/experience/subscriber-workspace-ux-contract.v1.json
skills/subscriber-workspace-ux.registry.yaml
skills/subscriber-workspace-ux/README.md
```

Do not reinterpret AXIGNAL as a chatbot, tender list or dossier generator. Preserve:

```text
Global Opportunity Intelligence
+ Evidence-Governed Investigation
+ Opportunity Operations
```

AXIGNAL finds, evaluates and helps prepare tenders. The subscriber decides, approves, signs, communicates and submits.

## Required method

1. Audit the current exact head before modifying code.
2. Activate and record every skill in `skills/subscriber-workspace-ux.registry.yaml`.
3. Produce a capability-to-route matrix marking each capability `OPERATIONAL`, `PARTIAL`, `CONTRACT_ONLY` or `MISSING`.
4. Define shared route, permission, state, component and token contracts before parallel implementation.
5. Implement against real typed API routes and persistent state. Never silently replace failure with fixtures.
6. Preserve all server-side tenant, role, entitlement, rights, approval and external-action boundaries.
7. Keep the current DeepSeek transport alias `deepseek-v4-flash` and governed checkpoint label `deepseek-v4-flash-0731`; do not expand model authority.
8. Run complete component, API, browser, accessibility, visual and regression validation on one exact head.

## Product architecture to implement

### Global shell

Persistent branded sidebar:

```text
Command Center
Opportunities
Investigations
Workspaces
Libraries
Alerts
Reports
Team
More
  Plan & Billing
  Settings
  Methodology
  Help
```

Header:

```text
organisation switcher
global search / command palette
primary create or investigate action
entitlement state
notifications
help
user menu
```

Maximum two navigation levels. Expanded navigation uses text labels. Visibility comes from server-resolved capabilities.

### Tender workspace

Contextual navigation:

```text
Overview
Qualification
Requirements
Evidence
Documents
Workplan
Clarifications
Changes
Commercial
Team & Approvals
Submission
Outcome & Learning
Audit
```

Implement every destination as a route-addressable, reload-safe surface. Preserve filters, selection, drawer state, browser history and return location.

### Required first-class tools

- actionable Command Center;
- searchable/filterable opportunity inventory and comparison;
- Investigation workspace retaining Navigator, Globe, Graph, Timeline, claims and evidence;
- active/archived tender workspace inventory;
- tender overview with source, notice version, lots, deadline, readiness, blockers, amendments and next action;
- bid/no-bid qualification and immutable decision record;
- accessible requirement-to-evidence-to-response matrix;
- evidence and approved reusable knowledge;
- source/subscriber document pack with versions, anchors, extraction/OCR, translations and approvals;
- tasks, owners, dependencies, milestones and critical path;
- official contact channels and clarification approval/handoff workflow;
- amendment diff and impact centre;
- commercial model and approval state;
- team, seats, invitations, roles and review workflow;
- final readiness preflight, package manifest and official submission handoff;
- outcome/debrief/learning;
- audit and provenance;
- integrated reports, billing, settings and help.

## UX/UI standard

Use the landing as the visual source of truth:

```text
near-black mineral canvas
Signal Teal accent
cool neutral typography
restrained lines and translucency
fine grid/spatial motifs
cinematic identity
institutional restraint
```

The product must be calmer and denser than the landing. Extend `@axignal/design-tokens`; do not create a second token system. Deliver first-class dark and light themes.

Prohibited:

- generic dashboard/card mosaic;
- default component-library appearance;
- crypto-neon or casino visuals;
- decorative charts;
- continuous ambient animation;
- teal used as success;
- red/green as sole encoding;
- icon-only primary navigation;
- dead controls;
- fake success;
- hidden fixture fallback.

## Interaction requirements

Every route implements:

```text
loading
empty
ready
partial
stale
restricted
read_only
source_unavailable
recoverable_error
terminal_error
```

Every mutation must show pending, persisted success, partial failure and recovery. Destructive actions require explicit scoped confirmation. External communication and submission remain subscriber-controlled.

Use semantic HTML by default. Use an interactive grid only where editing or directional keyboard navigation justifies it. The requirements matrix must also provide an accessible non-grid reading mode.

## Accessibility

Target `WCAG 2.2 AA` with:

- complete keyboard operation;
- unobscured focus;
- correct landmarks, headings and accessible names;
- no drag-only actions;
- text equivalents for Globe, Graph, Timeline and charts;
- 200% zoom/reflow;
- reduced motion;
- screen-reader tested dialogs, menus, tabs, toolbars and grids;
- automated axe plus manual keyboard and screen-reader evidence;
- zero critical accessibility defects.

## Engineering

Refactor the monolithic `InvestigationShell` into typed route-level surfaces and reusable components. Integrate the existing ResearchProgress, HumanReview, Billing and SeatGovernance capabilities into the navigation; do not leave them as disconnected floating bridges.

Evaluate dependencies before adoption for React 19/Next 16 compatibility, accessibility, maintenance, licence, bundle and security. Headless primitives, TanStack Table, Storybook, axe and Playwright visual comparisons may be adopted only after that review.

No client-side authority. No unrelated backend redesign. No source admission, public launch, Stripe live activation or autonomous external action.

## Testing and evidence

Required:

- unit/component tests for every primitive and state;
- component workbench stories for all states, themes and densities;
- API contract and permission tests;
- Playwright desktop, tablet and mobile journeys;
- keyboard-only E2E;
- axe checks;
- deterministic visual snapshots in one fixed environment;
- no horizontal overflow at supported breakpoints;
- performance budgets;
- tenant and role isolation regression;
- billing, seat, ResearchRun and human-review regression;
- exact-head identity and artifact digests.

Core browser journey:

```text
authenticate
→ Command Center
→ find opportunity
→ investigate evidence
→ compare
→ open qualification
→ record pursue decision
→ open Tender Workspace
→ detect blocking requirement
→ attach evidence
→ assign task
→ prepare clarification
→ approve handoff
→ process amendment impact
→ run readiness preflight
→ open official submission channel
→ subscriber confirms external action
→ record outcome
```

## Acceptance

Do not claim final UX until qualified-user evidence exists. Engineering completion requires:

```text
all declared routes functional
zero dead controls
zero critical/high functional defects
zero critical accessibility defects
all exact-head CI green
visual review approved
rollback tested
no authority regression
```

Human UX acceptance uses the thresholds in the research document, including median SUS `>= 85`, external-authority comprehension `100%`, context retention `>= 95%`, and destructive-action mistakes `0`.

## Output

Return:

1. exact base/head/tree;
2. changed-file inventory;
3. implemented capability matrix;
4. activated skill versions;
5. architecture and dependency decisions;
6. test and artifact evidence;
7. screenshots for both themes and supported breakpoints;
8. remaining limitations;
9. rollback instructions;
10. explicit status separating engineering completion from canonical UX acceptance.

Advance decisively, but do not weaken truth, accessibility, security, privacy, rights or subscriber authority to make the interface appear complete.
