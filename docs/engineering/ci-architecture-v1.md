# AXIGNAL CI architecture v1

## Decision

Pull-request validation is governed by three exact-head gates:

- `AXIGNAL PR Gate — Core`;
- `AXIGNAL PR Gate — Runtime`;
- `AXIGNAL PR Gate — Domain`.

The gates compute the delta from the previous PR head to the current head. Existing validation workflows remain intact as reusable suites and no longer listen directly to every pull-request synchronization.

## Modes

- **Incremental:** run only suites whose original path contract matches the current commit delta.
- **Always:** run the canonical contract authority on every head.
- **Full-only:** run expensive cross-cutting audits only for a full-matrix candidate.
- **Full matrix:** activated by the `ci:full-matrix` label, manual gate dispatch, or a change to the CI routing architecture itself.

## Preserved authority

- Exact-head checkout remains mandatory.
- Existing verifier commands, security boundaries, migrations, browser tests, external-source probes and rollback rehearsals are not deleted.
- A changed workflow file selects its own suite.
- Push validation on `main` remains available.
- Broad `agent/**` push triggers are removed to prevent duplicate push and pull-request executions.
- Release and specialised operational workflows retain their narrow pull-request boundaries and stay outside the ordinary 52-suite matrix.

## Fail-closed invariants

`python scripts/ci/verify_ci_architecture.py` rejects:

- unmanaged direct pull-request workflows outside the documented specialised exceptions;
- registered suites without `workflow_call`;
- duplicate or missing group membership;
- broad `agent/**` push triggers;
- gate groups larger than the design budget.
