# E2E-2 — Happy path without fixtures

## Authority

```text
parent branch  release/axignal-e2e-final
parent SHA     9bbc60b9cfd46f52eef544eb8f91f4d5ddf21878
parent tree    db28fdea036c04980d0b33b77c756288bc9b4066
parent result  AX_E2E_SINGLE_CANDIDATE_PASS
```

E2E-2 is a child of the closed E2E-1 candidate. It does not rewrite E2E-1, merge to `main`, activate production or expand the frozen scope.

## Visible authority chain

```text
verified email
→ resident WebAuthn passkey with user verification
→ opaque revocable PostgreSQL session
→ tenant resolved by the server
→ signed Professional payment lifecycle
→ ACTIVE paid entitlement
→ explicit ORG_OWNER seat allocation
→ typed role and capability decision
→ Navigator creates persistent TED ResearchRun
→ Valkey queue and bounded worker
→ live admitted TED acquisition
→ persistent evidence and candidate claims
→ deterministic admission
→ persistent canonical claims and dossier
→ live InvestigationContext projection
→ persistent subscriber workspace
→ persistent document
→ content-addressed Markdown export
→ append-only tenant audit
```

## Main-path fixture removal

The root subscriber entrypoint no longer imports or silently falls back to:

- `InvestigationShell`;
- `SubscriberWorkspaceApp` fixture projection;
- `subscriber-workspace-server` JSON store;
- any `axfx_*` opportunity, message, claim, metric or document.

Missing authentication, disabled workspace configuration, any configured fixture mode, API unavailability, incomplete ResearchRun or missing entitlement produces an explicit visible state. No fixture data is substituted.

The historical fixture components remain repository history and may support isolated design tests, but they are not reachable from the main subscriber entrypoint and hold no runtime authority.

## Persistence model

Migration `140-subscriber-workspace-live.sql` adds tenant-private:

- workspaces bound to a completed ResearchRun and persistent dossier;
- versioned documents;
- immutable content-addressed Markdown exports;
- append-only audit events.

All four tables use forced PostgreSQL RLS. Application mutation is least-privilege; exports and audit events cannot be updated or deleted by the application role.

## Required exact-head evidence

The dedicated workflow must prove on one exact SHA:

1. E2E-1 ancestry and contract integrity;
2. focused Ruff, Python tests, TypeScript, unit tests and production builds;
3. migration installation and healthy PostgreSQL/API/web topology;
4. passwordless passkey registration and revocable session authority;
5. Professional selection and signed deterministic payment confirmation;
6. active paid entitlement and `ORG_OWNER` seat bootstrap;
7. visible no-fixture bootstrap with typed capabilities;
8. live TED ResearchRun through the real worker;
9. polling until terminal completion;
10. persisted evidence, candidate claims, canonical claims and dossier;
11. InvestigationContext populated exclusively from that run;
12. persistent workspace and document creation;
13. content-addressed Markdown export and authenticated download;
14. page reload preserving run, dossier, workspace, document and audit;
15. independent SQL verification of RLS, zero cross-tenant visibility, export digest, append-only audit and zero `axfx_*` residue;
16. artifact sanitation and complete teardown.

Only after every condition passes may the workflow emit:

```text
AX_E2E_HAPPY_PATH_NO_FIXTURES_PASS
```

## Scope exclusions

This phase does not require:

- completion of secondary modules;
- completion of every Founder Admin view;
- automation of every enterprise workflow;
- perfect parity for every usage variant;
- external user UX validation;
- live Stripe;
- public launch.

## Current state

```text
implementation   COMPLETE CANDIDATE
exact-head CI    PENDING
E2E-2            OPEN
public launch    NO_GO
```
