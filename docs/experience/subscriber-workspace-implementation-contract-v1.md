# AXIGNAL Subscriber Workspace — frozen implementation contract

Version: `1.0.0-engineering-candidate`
Goal: `AXIGNAL-GOAL-001`
Task: `AX-GE2E-P08-T02`
Status: `FROZEN_FOR_IMPLEMENTATION / CANONICAL_ACCEPTANCE_NOT_AUTHORISED`

## Capability audit at `3d208502`

| Capability | Status | Evidence / disposition |
|---|---|---|
| Authentication and server identity | OPERATIONAL | `AuthGate`, passwordless identity proxy and server session resolution; integrate unchanged. |
| Tenant and seat governance | OPERATIONAL_BOUNDED | Typed server proxy and UI bridge; route under Team. |
| Billing and entitlement | OPERATIONAL_CANDIDATE | Typed server proxy and UI bridge; route under Plan & Billing, no live activation. |
| InvestigationContext | OPERATIONAL_BOUNDED | Versioned shared context; refactor without weakening. |
| ResearchRun and human review | OPERATIONAL_BOUNDED | Persistent API bridges; integrate into Investigations and approvals. |
| Global product navigation | PARTIAL | Icon rail only; replace with persistent labelled sidebar. |
| Globe | PARTIAL_SYNTHETIC | Existing workspace uses CSS art; replace with the existing WebGL semantic globe foundation plus accessible tabular equivalent. |
| Graph and Timeline | PARTIAL_SYNTHETIC | Preserve typed selection and temporal state; add explicit accessible equivalents. |
| Opportunity inventory and comparison | PARTIAL_SYNTHETIC | Rebuild as route-addressable, filterable and provenance-aware inventory. |
| Tender domain and authority model | CONTRACT_IMPLEMENTED | P08 Pydantic contracts exist; expose via bounded server API. |
| Tender Workspace UI | MISSING | Build thirteen contextual routes. |
| Requirements, evidence and documents | CONTRACT_ONLY / BACKEND_PARTIAL | Build persistent workflow UI and API mutations. |
| Workplan, changes and commercial | CONTRACT_ONLY | Build persistent candidate workflow surfaces. |
| Clarifications and official handoff | DOMAIN_CONTRACT_ONLY | Build human approval and confirmation flow; never send autonomously. |
| Submission and outcome | DOMAIN_CONTRACT_ONLY / UI_MISSING | Build readiness preflight, official link handoff, subscriber confirmation and observed outcome record. |
| Reports, libraries, alerts, settings, methodology and help | PARTIAL_OR_MISSING | Integrate existing evidence where present; implement bounded destinations and honest unavailable states. |

## Frozen route contract

Global routes:

```text
/
/opportunities
/investigations
/workspaces
/libraries
/alerts
/reports
/team
/billing
/settings
/methodology
/help
```

Tender routes use `/workspaces/:workspaceId/:section` where `section` is:

```text
overview qualification requirements evidence documents workplan clarifications
changes commercial team submission outcome audit
```

Every route preserves safe URL state (`q`, `view`, `status`, `owner`, `selected`, `drawer`, `lens`, `as_of`) and restores focus after navigation.

## Frozen role and capability contract

Roles are server resolved: `OWNER`, `ADMIN`, `BID_MANAGER`, `CONTRIBUTOR`, `REVIEWER`, `FINANCE`, `VIEWER`.

Capabilities are server resolved and never inferred from plan labels:

```text
workspace:view workspace:create workspace:qualify workspace:edit
requirement:edit evidence:attach document:manage work:assign
clarification:draft clarification:approve clarification:confirm_sent
commercial:view commercial:edit commercial:approve
submission:prepare submission:approve submission:confirm_external
outcome:record audit:view export:create
team:manage billing:view billing:manage settings:manage
```

High-consequence separations:

- the clarification author cannot be the only external-handoff approver;
- package preparation is distinct from subscriber approval;
- opening an official portal is distinct from confirming an external submission;
- AXIGNAL never receives `submission:execute` or signature authority;
- cross-tenant identifiers return `404`, not object existence metadata.

## Frozen state contract

Every route implements: `loading`, `empty`, `ready`, `partial`, `stale`, `restricted`, `read_only`, `source_unavailable`, `recoverable_error`, `terminal_error`.

Every mutation implements: `idle`, `pending`, `persisted`, `partial_failure`, `rejected`, `recovery_available`.

Truth rules:

```text
AI draft != approved response
ready != submitted
handoff opened != sent
sent confirmed != accepted by buyer
award notice != signed contract
unknown != zero != not applicable != redacted
```

## Frozen API contract

The web BFF exposes:

```text
GET   /api/subscriber-workspace/bootstrap
POST  /api/subscriber-workspace/actions
GET   /api/subscriber-workspace/events?after=:cursor
```

The bootstrap response includes server-resolved `identity`, `tenant`, `roles`, `capabilities`, `entitlement`, `locale`, `theme`, route data, rights snapshot and fixture boundary.

Actions require `action_id`, `action_type`, `tenant_revision`, scoped payload and optional confirmation. Replay is idempotent by `action_id`. Mutations append an audit event and return the reconciled revision. Consequential actions fail closed on stale revision, missing capability, missing separation of duties, missing approval or cross-tenant scope.

## Fixture / real-data boundary

- Engineering fixtures require `AXIGNAL_SUBSCRIBER_WORKSPACE_FIXTURE_MODE=explicit`.
- The UI shows `ENGINEERING FIXTURE · NOT LIVE DATA` whenever fixtures are active.
- Fixture identifiers use `axfx_` and never share canonical namespaces.
- A missing or failed real adapter returns `source_unavailable`; it never loads fixtures automatically.
- Fixture mutations are server-persisted in an isolated tenant store and are reset only by an explicit test/admin action.
- Production builds reject fixture mode unless a separate explicit non-production environment marker is present.

## Frozen design tokens and component APIs

Extend `@axignal/design-tokens`; no second token system. Required families: canvas/panel/raised/overlay, primary-secondary-tertiary text, subtle/default/strong border, Signal Teal brand/selection, independent semantic fact/inference/prediction/contradiction/unknown/critical, type scale, compact/comfortable density, 40/44px controls, focus ring, overlay layers, chart/map categories, motion and responsive shell columns.

Shared components: `ProductShell`, `GlobalSidebar`, `GlobalHeader`, `WorkspaceSidebar`, `PageState`, `StatusBadge`, `AuthorityNotice`, `DataTable`, `DetailRail`, `MutationFeedback`, `ConfirmationDialog`, `EvidenceRail`, `LensSwitcher`, `SemanticGlobe`, `AccessibleGlobeTable`, `Timeline`, `CommandPalette`.

## Frozen events and acceptance IDs

Events: `route.viewed`, `lens.changed`, `opportunity.selected`, `workspace.opened`, `decision.recorded`, `requirement.updated`, `evidence.attached`, `task.assigned`, `clarification.approved`, `handoff.opened`, `external_action.confirmed`, `amendment.acknowledged`, `preflight.completed`, `outcome.recorded`, `mutation.denied`, `recovery.requested`.

Core acceptance IDs:

```text
AX-SW-E2E-001 authentication-to-command-center
AX-SW-E2E-002 opportunity-search-compare-investigate
AX-SW-E2E-003 pursue-decision-opens-workspace
AX-SW-E2E-004 blocking-requirement-evidence-assignment
AX-SW-E2E-005 clarification-approval-handoff-confirmation
AX-SW-E2E-006 amendment-impact-revalidation
AX-SW-E2E-007 readiness-official-handoff-outcome
AX-SW-SEC-001 cross-tenant-denial
AX-SW-SEC-002 role-and-entitlement-denial
AX-SW-SEC-003 external-authority-escalation-denial
AX-SW-A11Y-001 keyboard-core-journey
AX-SW-A11Y-002 nonvisual-globe-graph-timeline
AX-SW-VIS-001 desktop-dark-light-golden
AX-SW-VIS-002 tablet-mobile-reflow
AX-SW-PERF-001 shell-load-and-interaction-budget
```

## Locale contract

Launch engineering locales are exactly `en`, `es`, `fr`, `de`, `pt`, `it` per the current user decision and the P17 cross-library runtime. Original-language evidence, translation status and terminology provenance remain recoverable.

## Independent gate

Implementation may reach `AX_SUBSCRIBER_WORKSPACE_ENGINEERING_COMPLETE` only with exact-head automated and manual evidence. `FINAL_UX`, `CANONICAL_ACCEPTANCE` and `PUBLIC_LAUNCH` remain prohibited until the qualified-user study and independent Product, UX, Accessibility, Security and Privacy decisions exist.
