# P13 — Sovereign & Macro Library + Strategy Workspace

Status: `ENGINEERING FOUNDATION / CANONICAL ACTIVATION BLOCKED`

Task: `AX-GE2E-P13-T01`  
Frozen base: `96b89d8e7bdd7712dae476eeb97e1240c7846f22`

P13 binds `AX-LIB-O06` to the Country and Market Strategy Workspace.

It preserves country scope, series identity, observation period, publication
time, retrieval time, vintage, revision, unit, currency and methodology.
Observed values, forecasts, scenarios and targets are never interchangeable.

Budget proposal, appropriation, allocation, commitment, obligation, contracted
value, disbursement and payment remain separate states. Policy adoption does
not prove implementation, and a programme announcement does not prove funding.

Materialised evidence:

- 8 bounded modules;
- 32 record types;
- 48 invariants;
- 12 lifecycle states;
- 11 pipeline stages;
- 40 conformance fixtures;
- 72 adversarial cases;
- deterministic reference verifier;
- byte-exact rollback to P12.

Models remain proposal-only. Workers remain bounded. Publication,
representation, budget allocation and capital commitment require typed human
authority. All seven macro catalogue sources remain unreviewed and
not product-admitted.

## Validation workflow

GitHub Actions executes `P13 Sovereign Macro Validation` on every P13 branch
push and on pull-request changes affecting the P13 contract. The workflow runs
the deterministic verifier and the byte-exact rollback rehearsal.
