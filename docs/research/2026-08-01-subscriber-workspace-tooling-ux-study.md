# AXIGNAL Subscriber Workspace — Product, Tooling and UX/UI Study

Status: `RESEARCH_COMPLETE / IMPLEMENTATION_CONTRACT_READY / HUMAN_USABILITY_EVIDENCE_PENDING`  
Observed repository head: `abd37a5844c79288858e94ec308e85abe26822fe`  
Date: `2026-08-01`  
Goal: `AXIGNAL-GOAL-001`

## 1. Executive decision

AXIGNAL already contains a strong engineering spine, an evidence-governed Investigation Shell, authenticated ResearchRuns, human review, seat governance and billing surfaces. It does **not** yet contain a coherent subscriber product shell in which all operative capabilities are discoverable, consistently navigable and assembled around the complete tender lifecycle.

The correct target is a **dual-context product architecture**:

```text
Global Opportunity Intelligence
→ discover, monitor, compare and investigate

Contextual Tender Workspace
→ qualify, prepare, coordinate, review, hand off, follow and learn
```

Globe, Graph and Timeline remain first-class intelligence lenses. They do not become the permanent navigation model for bid execution. Once a subscriber opens a tender workspace, the dominant mental model changes from spatial discovery to a task-and-readiness workflow.

The UX is not accepted merely because it is visually polished or because browser tests pass. It is accepted only when all visible controls are functional, the complete subscriber journey works against real typed APIs, WCAG 2.2 AA is demonstrated, and qualified B2G users complete the core tasks with the declared thresholds.

## 2. Repository evidence reviewed

### Existing product surfaces

- `apps/web/app/page.tsx` composes authentication, ResearchRun progress, human review, billing, seat governance and the Investigation Shell.
- `apps/web/components/investigation-shell.tsx` is a monolithic client component with Navigator, synthetic Globe/Graph, Timeline, opportunities, claims and evidence.
- `apps/web/components/research-progress-bridge.tsx` exposes persistent ResearchRun state.
- `apps/web/components/human-review-bridge.tsx` exposes bounded human-review decisions.
- `apps/web/components/billing-bridge.tsx` exposes plan selection, checkout, upgrade, cancellation and ledger state.
- `apps/web/components/seat-governance-bridge.tsx` exposes seat capacity, invitations, members and role changes.
- `apps/api/src/axignal_api/procurement_domain.py` defines tender workspaces, contact channels, clarifications, source provenance and subscriber-controlled external handoff.
- `packages/design-tokens/src/tokens.css` defines the current dark/light Signal Teal token foundation.
- `apps/landing/components/landing-experience.tsx` and `apps/landing/app/globals.css` define the strongest current AXIGNAL brand expression.

### Existing structural strengths

- server-resolved tenant and role authority;
- persistent, typed InvestigationContext;
- proposal/admission separation;
- source and evidence provenance;
- explicit contradictions and unknowns;
- persistent ResearchRun progress;
- bounded human-review workflow;
- trial, billing and seat governance;
- dark/light token foundation;
- keyboard focus and reduced-motion foundations;
- Playwright browser coverage for selected paths.

### Structural UX problems

1. Subscriber capabilities are rendered as bridges, floating panels or sections inside one shell instead of one coherent information architecture.
2. The global shell is fixed to a dense four-column layout and does not establish a scalable navigation model.
3. The visible demo state remains coupled to a synthetic Moscow real-estate context rather than the B2G product shell.
4. The product has no integrated tender execution navigation for requirements, evidence, documents, tasks, clarifications, changes, commercial review, approvals, handoff and outcomes.
5. Billing, seats and human review are operational islands rather than destinations inside one product shell.
6. Design tokens are too small for a production design system: typography, density, status, elevation, focus, data visualisation, layering and component-state tokens remain incomplete.
7. Several visible actions are prototype controls. The finished product must prohibit dead or decorative controls.

## 3. External research synthesis

The benchmark was used to identify durable workflow patterns, not to copy a competitor's visual design.

### Public-procurement and RFP platforms

- Mercell positions tendering as an end-to-end, audit-ready connected workflow.
- Responsive combines intake, requirements analysis, collaboration, response projects, content, progress and go/no-go assessment.
- Loopio combines project context, deadlines, Q&A, approved knowledge, review workflows and reporting.
- GovWin IQ foregrounds opportunity intelligence, buyer context, documents and strategic pursuit planning.

The consistent market pattern is:

```text
opportunity intake
→ qualification / go-no-go
→ requirements analysis
→ assignments and collaboration
→ approved knowledge and documents
→ review and readiness
→ external submission handoff
→ outcome and reporting
```

AXIGNAL must retain its differentiator: every recommendation, requirement, response and decision remains linked to source provenance, epistemic state, time and authority.

### Navigation and workflow patterns

GOV.UK distinguishes between:
- navigation for repeated services with multiple non-linear tasks; and
- task lists for transactions with a clear completion path.

Carbon recommends a persistent side navigation when users frequently switch among more than five secondary destinations, with no more than two navigation tiers; deeper structure belongs inside the page.

Therefore AXIGNAL needs:
- a persistent **global sidebar** for product destinations;
- a **contextual workspace navigation** for the active tender;
- a visible **readiness/task path** for completion;
- tabs or in-page sections below the second hierarchy level.

### Accessibility and data density

WCAG 2.2 adds requirements relevant to AXIGNAL including focus not obscured, target size, non-drag alternatives, consistent help, redundant-entry reduction and accessible authentication. WAI-ARIA APG distinguishes static tables from interactive grids and requires explicit keyboard behavior for grids, dialogs, tabs, toolbars and trees.

AXIGNAL must prefer semantic HTML and native tables until the workflow genuinely requires an interactive grid. Complex requirement matrices must have a documented keyboard model and an equivalent non-grid reading mode.

## 4. Subscriber jobs-to-be-done

The workspace must let a subscriber:

1. understand what requires attention now;
2. discover and save relevant tenders;
3. compare opportunities without losing provenance;
4. open a tender workspace from an explicit pursue decision;
5. understand the current notice version, deadlines, lots and changes;
6. make a defensible bid / no-bid decision;
7. determine eligibility and exclusion risks;
8. convert requirements into assigned work;
9. connect every response to current evidence;
10. manage documents, versions, anchors, translations and approvals;
11. contact the official channel or prepare a clarification with human approval;
12. track dependencies, tasks, blockers and the critical path;
13. build and review the commercial model;
14. prepare a complete submission package;
15. hand off to the official platform without AXIGNAL impersonating the subscriber;
16. record receipt, award, loss, cancellation or unknown outcome;
17. reuse approved knowledge without carrying stale or unauthorised content;
18. manage members, seats, roles, billing and security;
19. export an evidence-preserving dossier;
20. recover their exact context after interruption, error or reload.

## 5. Complete subscriber capability architecture

### A. Global product shell

| Destination | Purpose | Current evidence | Required disposition |
|---|---|---|---|
| Command Center | Work requiring attention, deadlines, blockers and recent changes | Missing as coherent destination | Build |
| Opportunities | Search, filters, saved views, ranking explanation and comparison | Partial inside Investigation Shell | Rebuild as functional destination |
| Investigations | Navigator, ResearchRuns, Globe, Graph, Timeline, claims and evidence | Operational bounded core | Refactor into destination |
| Tender Workspaces | Active, archived and closed pursuits | Domain contract exists | Build |
| Libraries | Governed evidence, documents, approved content and provenance | Partial/contractual | Build |
| Alerts | Saved searches and tender alerts | Backend/public-discovery evidence exists | Integrate |
| Reports | Dossiers, exports and decision records | Partial dossier capability | Build |
| Team | Members, invitations, roles and capacity | Operational bridge | Integrate |
| Plan & Billing | Entitlement, usage boundary, checkout, invoices and cancellation | Operational bridge/candidate billing | Integrate |
| Settings | Organisation, profile, capability, notifications, locale, privacy and security | Fragmented/missing | Build |
| Help | Contextual help, shortcuts, methodology and support | Missing | Build |

### B. Tender workspace

| Workspace section | Required capabilities |
|---|---|
| Overview | identity, source, notice version, buyer, lots, deadlines, status, next action, blockers, readiness and recent changes |
| Qualification | fit, strategic rationale, eligibility, exclusions, risk, bid/no-bid decision and dissent |
| Requirements | atomic requirement matrix, source anchor, mandatory/scored state, owner, status, due date, evidence and response |
| Evidence | supporting/adverse evidence, freshness, rights, provenance, approved reusable knowledge and gaps |
| Documents | source pack, subscriber documents, versions, translations, extraction/OCR state, response pack and signatures |
| Workplan | tasks, owners, dependencies, milestones, critical path, workload and overdue state |
| Clarifications | official contact channels, question drafts, internal review, subscriber approval, handoff and answer application |
| Changes | notice amendments, field-level diff, impacted requirements, invalidated approvals, rework and acknowledgement |
| Commercial | currency, price schedule, cost assumptions, tax boundary, margin proposal, approvals and risks |
| Team & Approvals | roles, assignments, comments, mentions, review stages, separation of duties and decision ledger |
| Submission | readiness preflight, package manifest, unresolved blockers, official-channel handoff and receipt record |
| Outcome & Learning | submitted/unknown/award/loss/cancelled state, evidence, debrief, reusable learning and policy-safe metrics |
| Audit | immutable activity, provenance, decisions, exports, external handoffs and authority changes |

## 6. Recommended information architecture

### Global sidebar

```text
AXIGNAL
├─ Command Center
├─ Opportunities
├─ Investigations
├─ Workspaces
├─ Libraries
├─ Alerts
├─ Reports
├─ Team
└─ More
   ├─ Plan & Billing
   ├─ Settings
   ├─ Methodology
   └─ Help
```

Global header:

```text
organisation switcher
+ global search / command palette
+ create / investigate action
+ current entitlement state
+ notifications
+ help
+ user menu
```

### Contextual tender sidebar

```text
Back to Workspaces
Tender identity and current state
Readiness summary

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

Rules:

- maximum two sidebar levels;
- no icon-only primary navigation in expanded mode;
- stable labels and route-addressable destinations;
- section badges communicate actionable counts, not decoration;
- status badges are not links unless they perform an action;
- Globe, Graph and Timeline are lenses inside Investigations and relevant workspace pages, not competing top-level products;
- mobile becomes a drawer plus contextual task selector; capability is not silently removed;
- every route preserves tenant, workspace, selection, filters and return location.

## 7. Core screen contracts

### Command Center

Must answer, in this order:

1. What must I do now?
2. Which deadline or blocker is most dangerous?
3. What changed since my last visit?
4. Which workspaces are ready, blocked or waiting?
5. What can AXIGNAL safely do next?

### Opportunity detail

Must separate:

- official facts;
- normalised facts;
- AXIGNAL inference;
- subscriber-provided facts;
- recommendation;
- unknowns and contradictions.

Primary actions:

```text
Investigate
Compare
Save
Open qualification
Dismiss with reason
```

### Tender overview

Persistent header:

```text
title
buyer
procedure / notice ID
selected lots
source and current version
deadline with timezone
workspace state
readiness
next required action
```

The first viewport must show critical blockers, recent amendments and the next action without opening another panel.

### Requirement matrix

Minimum columns:

```text
ID
requirement
class
lot
mandatory/scored
source anchor
status
owner
due date
evidence coverage
response state
risk
last change
```

Required functions:

- search, filter, sort, group, pin and saved views;
- bulk assignment and status change with permission checks;
- row detail drawer preserving table state;
- exact source anchor and version;
- explicit unknown and not-applicable rationale;
- keyboard-complete interaction;
- CSV/export only when rights permit;
- non-grid accessible reading mode.

### Clarification workflow

```text
requirement gap
→ draft question
→ internal review
→ subscriber approval
→ official-channel handoff
→ subscriber confirms sent
→ answer received
→ affected requirements and documents invalidated/revalidated
```

AXIGNAL may prepare and organise; the subscriber retains communication and representation authority.

## 8. Visual system and brand continuity

The landing establishes:

- near-black mineral canvas;
- Signal Teal light and glow;
- cool grey typography;
- restrained borders and translucency;
- fine grids/noise;
- orbital and geospatial motifs;
- cinematic scale with institutional restraint.

The authenticated product must inherit the identity without copying landing-page motion into daily work.

### Product expression

- dark-first, first-class light mode;
- quieter backgrounds and less atmospheric motion than the landing;
- Signal Teal reserved for selection, active state and primary action;
- semantic support, contradiction, unknown, critical and inferred states remain independent from brand colour;
- dense professional layouts use typography, alignment and separators before cards or shadows;
- no generic dashboard card mosaic;
- no crypto-neon, casino or decorative telemetry;
- motion communicates continuity, state transition and causality only;
- no continuous animation in work surfaces;
- every state works at 200% zoom and with reduced motion.

### Token expansion required

- type scale and line heights;
- compact/comfortable density;
- page, panel and data-grid spacing;
- control heights and target sizes;
- elevation and overlay hierarchy;
- status backgrounds, borders and text;
- focus ring and selected state;
- chart and map categorical scales;
- skeleton/loading states;
- z-index layers;
- motion duration/easing;
- responsive breakpoints;
- content widths and grid columns.

## 9. Component and engineering system

The repository should converge on:

- semantic, headless accessible primitives for dialogs, menus, tabs, tooltips and popovers;
- typed route-level loaders and mutations;
- a reusable product shell;
- server-authoritative navigation capabilities derived from role and entitlement;
- a typed table abstraction for dense data;
- form schema validation shared across client and server;
- a component workbench with documented states;
- deterministic visual regression;
- automated axe checks plus manual keyboard and screen-reader review;
- Playwright E2E against actual APIs and persistence;
- no new dependency without compatibility, bundle, security, licence and maintenance review.

Candidate libraries may be evaluated, not blindly adopted:

- Radix Primitives or equivalent accessible headless primitives;
- TanStack Table for headless typed table state;
- Storybook with interaction and accessibility tests;
- `@axe-core/playwright`;
- Playwright screenshot comparison;
- an icon set with stable accessible naming.

The visual result must remain AXIGNAL-owned. Installing a component library does not authorise its default appearance.

## 10. Functional integrity rules

A finished AXIGNAL workspace has:

- zero dead controls;
- zero fake success states;
- zero client-authoritative tenant, role, approval or entitlement decisions;
- no silent fallback from real data to fixtures;
- no missing value displayed as zero or low opportunity;
- no AI draft displayed as approved content;
- no external action without explicit subscriber authority;
- no destructive action without scoped confirmation and consequence text;
- no visible capability that is unavailable without an explanation;
- complete loading, empty, stale, restricted, read-only, offline, error and recovery states;
- optimistic UI only when rollback and reconciliation are explicit;
- stable deep links and browser back/forward behavior;
- all mutations idempotent where replay is possible.

## 11. Required usability research

### Cohort

Minimum 8 qualified participants:

- at least 3 bid/proposal managers;
- at least 2 business-development or B2G managers;
- at least 1 subject-matter reviewer;
- at least 1 organisation administrator;
- at least 1 accessibility participant or specialist;
- at least 2 sessions in a non-English primary locale.

### Tasks

1. find a relevant tender and explain why it matches;
2. compare two opportunities;
3. make and record a bid/no-bid recommendation;
4. find a blocking requirement;
5. attach or identify evidence for a requirement;
6. assign work and identify the critical path;
7. prepare and approve a clarification;
8. identify the impact of an amendment;
9. complete final readiness review;
10. hand off to the official submission channel and explain AXIGNAL's authority boundary.

### Acceptance thresholds

- first-session navigation success: `>= 90%`;
- opportunity-to-evidence completion: `>= 90%`;
- blocking-requirement detection: `>= 90%`;
- source/inference distinction: `>= 95%`;
- context retention across surfaces: `>= 95%`;
- correct next-action identification: `>= 90%`;
- external-authority comprehension: `100%`;
- destructive-action mistakes: `0`;
- critical accessibility defects: `0`;
- preference over the current shell: `>= 75%`;
- median SUS: `>= 85`;
- no repeated finding that the Globe obstructs bid execution.

## 12. Implementation sequencing

Parallel work is permitted only behind shared contracts.

```text
Track A — product shell and navigation
Track B — design system and component workbench
Track C — global destinations
Track D — tender workspace
Track E — requirements/evidence/document tools
Track F — collaboration, clarifications and approvals
Track G — accessibility, performance and visual regression
Track H — usability evidence and corrective iteration
```

Shared prerequisites:

- route and state contracts;
- capability/permission contract;
- design tokens;
- component APIs;
- event and analytics schema;
- fixture/real-data boundary;
- acceptance test IDs.

No track may independently invent navigation labels, status semantics, permissions, colours or persistence models.

## 13. Sources reviewed

Observed `2026-08-01`:

- Mercell public procurement platform: https://info.mercell.com/
- Responsive Response Projects: https://www.responsive.io/product/response-projects
- Responsive RFP software: https://www.responsive.io/solutions/rfp-software-new
- Loopio RFP response software: https://loopio.com/rfp-response-software/
- GOV.UK navigate a service: https://design-system.service.gov.uk/patterns/navigate-a-service/
- GOV.UK task list: https://design-system.service.gov.uk/components/task-list/
- Carbon UI shell left panel: https://carbondesignsystem.com/components/UI-shell-left-panel/usage/
- W3C WCAG 2.2: https://www.w3.org/TR/WCAG22/
- W3C WAI forms tutorial: https://www.w3.org/WAI/tutorials/forms/
- WAI-ARIA APG patterns: https://www.w3.org/WAI/ARIA/apg/patterns/
- WAI-ARIA grid pattern: https://www.w3.org/WAI/ARIA/apg/patterns/grid/
- W3C tables tutorial: https://www.w3.org/WAI/tutorials/tables/
- Radix accessibility: https://www.radix-ui.com/primitives/docs/overview/accessibility
- TanStack Table overview: https://tanstack.com/table/latest/docs/overview
- Storybook accessibility testing: https://storybook.js.org/docs/writing-tests/accessibility-testing
- Storybook interaction testing: https://storybook.js.org/docs/9/writing-tests/interaction-testing
- Playwright visual comparisons: https://playwright.dev/docs/test-snapshots
- Playwright accessibility testing: https://playwright.dev/docs/next/accessibility-testing

## 14. Decision

```text
SUBSCRIBER_TOOL_INVENTORY          COMPLETE
TARGET_INFORMATION_ARCHITECTURE    DEFINED
BRAND_CONTINUITY_CONTRACT          DEFINED
UX SKILL ROUTING                   DEFINED
IMPLEMENTATION                     NOT EXECUTED BY THIS STUDY
HUMAN USABILITY ACCEPTANCE         MISSING
PERFECT UX CLAIM                    PROHIBITED UNTIL EVIDENCE
```
