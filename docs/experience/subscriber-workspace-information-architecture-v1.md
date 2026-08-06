# AXIGNAL Subscriber Workspace — Normative UX/UI Architecture

Version: `1.0.0-candidate`  
Status: `NORMATIVE CANDIDATE / IMPLEMENTATION REQUIRED / USER VALIDATION REQUIRED`  
Goal: `AXIGNAL-GOAL-001`

## 1. Product shell decision

AXIGNAL SHALL implement two coordinated shells over one server-authoritative context:

1. **Intelligence Shell** — discovery, search, Globe, Graph, Timeline, Navigator, claims and evidence.
2. **Operations Shell** — tender qualification, preparation, collaboration, readiness, handoff, outcome and learning.

The route, breadcrumb, selected organisation, opportunity, workspace, notice version, lot set and temporal state SHALL be reproducible.

## 2. Global navigation

Required destinations:

```text
Command Center
Opportunities
Investigations
Workspaces
Libraries
Alerts
Reports
Team
Plan & Billing
Settings
Methodology
Help
```

Rules:

- The expanded sidebar SHALL show text labels.
- Primary navigation SHALL NOT be icon-only.
- The global hierarchy SHALL NOT exceed two levels.
- A destination SHALL be omitted only when the server capability response denies visibility.
- A visible but unavailable destination SHALL expose its reason and recovery action.
- Counts SHALL represent actionable, typed states.
- The browser SHALL NOT infer permissions from plan names or UI state.

## 3. Tender workspace navigation

Required sections:

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

Each section SHALL be a route-addressable destination and SHALL preserve table filters, selected record, drawer state and return position.

## 4. Page anatomy

Every workspace page SHALL contain, as applicable:

```text
workspace identity header
source/version/freshness disclosure
deadline and timezone
readiness summary
next required action
section navigation
primary content
contextual evidence/detail rail
activity/provenance access
```

The page title SHALL name the subscriber task, not the implementation module.

## 5. Responsive behavior

- `>= 1440px`: expanded global sidebar, contextual workspace nav, primary canvas, optional detail rail.
- `1024–1439px`: collapsible global sidebar, contextual nav may become compact, detail rail overlays only on demand.
- `768–1023px`: drawer navigation, single primary work surface, persistent task/readiness header.
- `< 768px`: review and lightweight task completion; no silent removal of critical approvals, clarification, requirements or evidence reading.
- Complex editing MAY recommend desktop but SHALL retain read-only access and safe handoff on smaller screens.

## 6. State model

Every destination SHALL implement:

```text
loading
empty
ready
partial
stale
restricted
read_only
offline_or_source_unavailable
recoverable_error
terminal_error
```

State copy SHALL explain:
- what happened;
- whether user work is safe;
- what remains available;
- the next action;
- who owns recovery.

## 7. Data-dense interaction

- Native tables SHALL be preferred for read-only data.
- Interactive grids SHALL declare and test their keyboard model.
- Filters SHALL be reflected in the URL where safe.
- Saved views SHALL belong to the tenant/user according to explicit scope.
- Bulk actions SHALL show selected count, permission, consequence and partial-failure handling.
- Drawers SHALL preserve the underlying list state.
- Columns containing authority, deadline, blocker or status SHALL not be hidden by default.
- Unknown, unavailable, not applicable, zero and redacted SHALL be visually and semantically distinct.

## 8. Brand contract

The product SHALL use the shared AXIGNAL token package and extend it rather than duplicate landing-only variables.

Required identity:

```text
Signal Teal selection and primary action
mineral dark canvas
cool neutral text hierarchy
restrained borders and translucency
fine spatial/grid motifs where meaningful
institutional typography and density
```

Prohibited:

```text
generic template appearance
card mosaic dashboard
crypto-neon
decorative charts
continuous ambient motion
brand teal used as success
red/green as sole state encoding
unbounded glassmorphism
```

## 9. Accessibility contract

Target: `WCAG 2.2 AA`.

Mandatory:

- keyboard-complete core workflows;
- visible, unobscured focus;
- logical landmarks and headings;
- text alternatives for Globe, Graph, charts and status summaries;
- no drag-only operation;
- 24 CSS px minimum pointer target or compliant spacing exception;
- accessible authentication;
- consistent help;
- reduced motion;
- 200% zoom and reflow;
- screen-reader tested dialogs, tabs, menus, grids and live status;
- no information conveyed by colour alone;
- manual testing in addition to axe.

## 10. Functional truth

```text
visible control       => wired action or explicit unavailable state
success notification  => persisted and reconciled success
AI draft              != approved response
workspace ready       != submitted
handoff opened        != sent
sent confirmed        != accepted by buyer
award notice          != signed contract
```

## 11. Release gate

The subscriber workspace SHALL NOT be described as final until:

- all declared destinations are operational or intentionally excluded by the accepted contract;
- zero critical or high functional defects remain;
- zero critical accessibility defects remain;
- browser, API, persistence and permission E2E pass;
- visual regression is reviewed at supported breakpoints and themes;
- the qualified-user study meets the thresholds in the research document;
- Product, UX, Accessibility, Security and Privacy authorities approve the exact candidate.
