# AXIGNAL Architecture Decision Records

| ADR | Decision | Status |
|---|---|---|
| [ADR-001](ADR-001-brand-domain-repository.md) | AXIGNAL brand, axignal.com domain, axignal repository slug | ACCEPTED |
| [ADR-002](ADR-002-observation-not-personal-advice.md) | Product is economic observation and research, not personalised advice | ACCEPTED |
| [ADR-003](ADR-003-postgresql-canonical-claim-ledger.md) | PostgreSQL is the canonical claim ledger and graph source | ACCEPTED |
| [ADR-004](ADR-004-progressive-universe-admission.md) | Opportunity universes are admitted progressively through gates | ACCEPTED |
| [ADR-005](ADR-005-map-first-investigation-shell.md) | Map-first investigation shell with persistent evidence and time context | PROPOSED / VALIDATION REQUIRED |
| [ADR-006](ADR-006-layered-visual-system-candidate.md) | Layered brand, UI, epistemic and visualisation colour systems remain candidates pending evidence | PROPOSED / VALIDATION REQUIRED |
| [ADR-007](ADR-007-selected-investigation-shell-visual-reference.md) | Selected dark/light Investigation Shell composition is the fidelity target; exact production tokens remain unfrozen | ACCEPTED FOR PROTOTYPE FIDELITY |
| [ADR-008](ADR-008-hybrid-ci-shared-build-runner.md) | Hybrid CI uses GitHub-hosted validation plus a restricted shared-host build runner without Docker or product-secret access | ACCEPTED / IMPLEMENTATION REQUIRED |
| [ADR-009](ADR-009-one-pgvector-three-knowledge-domains.md) | One PostgreSQL/pgvector platform contains three isolated global, tenant-private and intent domains | ACCEPTED / IMPLEMENTATION REQUIRED |
| [ADR-010](ADR-010-local-ai-proposal-not-admission.md) | Local and external AI may propose evidence and Candidate Claims but never admit canonical truth | ACCEPTED / IMPLEMENTATION REQUIRED |
| [ADR-011](ADR-011-shared-traefik-private-pilot-edge.md) | The private pilot reuses the incumbent Traefik edge while AXIGNAL binds only to loopback | PROPOSED / REVIEW REQUIRED |
| [ADR-012](ADR-012-european-public-procurement-first-universe.md) | European Public Procurement Intelligence is the sole first commercial implementation wedge; TED remains under independent source admission | ACCEPTED / IMPLEMENTATION NOT ADMITTED |
| [ADR-013](ADR-013-b2g-procurement-commercial-and-global-source-program.md) | B2G procurement narrative, premium price bands, controlled seven-day trial and federated global official-source expansion | PROPOSED / VALIDATION REQUIRED |
| [ADR-014](ADR-014-bounded-ai-and-token-entitlements.md) | AXIGNAL-only AI scope, prohibited general assistance, one-million-token trial and unlimited paid monthly tokens | PROPOSED / IMPLEMENTATION AND ECONOMIC VALIDATION REQUIRED |

ADRs record durable decisions and consequences. A later decision MUST supersede rather than erase an accepted ADR.
