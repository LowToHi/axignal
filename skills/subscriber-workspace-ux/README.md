# Subscriber Workspace UX/UI Skills

Status: `ACTIVE FOR SUBSCRIBER-FACING UX/UI WORK`

These skills convert the UX research and architecture into mandatory agent behavior. They supplement the canonical registry and do not expand product, data, legal, billing or external-action authority.

## Mandatory activation

Every material subscriber-facing UX/UI task activates all skills in `skills/subscriber-workspace-ux.registry.yaml`. A task may record a skill as `NOT_APPLICABLE` only with a written, contract-linked reason.

## Operating sequence

```text
inventory actual capability
→ bind governing contracts and permissions
→ map subscriber job and failure state
→ define route and state contract
→ define accessible interaction
→ map brand tokens and components
→ implement against real APIs
→ test component states
→ test browser and persistence E2E
→ run accessibility and visual regression
→ collect qualified-user evidence
→ independent acceptance
```

## Non-negotiable rules

1. Do not design from a static mock before verifying the underlying capability and API state.
2. Do not render a control that has no real action or explicit unavailable state.
3. Do not use the Globe as the sole route to tender work.
4. Do not collapse official facts, AXIGNAL inference, subscriber input and recommendations.
5. Do not hide amendments, stale evidence, missing coverage or invalidated approvals.
6. Do not infer tenant, role, approval, entitlement or source rights in the browser.
7. Do not introduce a component library's default visual language as AXIGNAL's identity.
8. Do not call automated accessibility scans sufficient.
9. Do not update visual snapshots without human review of every changed surface.
10. Do not declare the UX final before qualified B2G users meet the acceptance thresholds.

## Evidence required in every implementation PR

- exact base and head;
- routes and capabilities changed;
- activated skill IDs and versions;
- before/after functional inventory;
- screenshots at supported breakpoints and both themes;
- keyboard and screen-reader evidence;
- component interaction tests;
- Playwright E2E against real test APIs;
- visual regression result;
- accessibility result;
- performance result;
- unresolved limitations;
- rollback;
- explicit statement that engineering pass is not canonical UX acceptance.
