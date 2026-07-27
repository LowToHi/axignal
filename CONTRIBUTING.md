# Contributing to AXIGNAL

AXIGNAL is governed by `AXIGNAL-GOAL-001`, `AGENTS.md`, the contract set and accepted ADRs.

## Before changing code

1. identify the active roadmap task;
2. list governing contracts and required skills;
3. confirm phase authority and dependencies;
4. define measurable acceptance evidence;
5. identify security, privacy, source-right and rollback impact.

A material change without a registered task MUST NOT be implemented silently.

## Branches

Use short-lived branches with one reviewable objective:

```text
agent/<capability>-v<version>
feat/<capability>
fix/<defect>
docs/<scope>
```

Do not combine contract redesign, infrastructure, product code and unrelated cleanup in one pull request.

## Pull requests

Every PR must state:

- Goal ID;
- task IDs;
- governing contracts and ADRs;
- scope and explicit exclusions;
- evidence produced;
- tests run;
- security/privacy/source-right impact;
- migration and rollback;
- unresolved hypotheses or failures.

Implementation authors may not approve their own gates.

## Required checks

At minimum, applicable PRs must pass:

```bash
python scripts/validate_canonical_naming.py .
pnpm typecheck
pnpm build
pnpm test:e2e --project=chromium-desktop
ruff check apps/api
pytest
```

Contract, schema, OpenAPI, infrastructure and source-right checks remain mandatory when affected.

## Product invariants

- Brand and domain are `AXIGNAL` and `axignal.com`.
- Generated text cannot write canonical claims directly.
- Interest and Knowledge Tides cannot prove an economic claim.
- Contradiction, uncertainty and missing coverage must remain visible.
- Globe, Graph, Timeline, Navigator and evidence share one InvestigationContext.
- Product screenshots and marketing claims must be reproducible and truthful.
- No personalised investment advice, execution, custody or trading is introduced silently.

## Synthetic fixtures

Prototype fixtures must be explicitly labelled synthetic and must never be represented as current market evidence.
