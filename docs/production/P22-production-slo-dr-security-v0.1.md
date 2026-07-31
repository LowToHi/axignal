# P22 — Producción, SLO, DR y aceptación de seguridad

**Task:** `AX-GE2E-P22-T01`  
**Baseline:** P21 exact head `ee196e3cd8d7027adf92eb40e04868a5ad6e7594`  
**Status:** engineering evidence ready; production and public traffic remain blocked.

## Objective

P22 defines the contract that must be satisfied before AXIGNAL can be deployed as an operated production service. It does not itself authorize production, public traffic, Stripe live, canonical activation, or external actions.

The phase separates four properties that must never be collapsed:

```text
DEPLOYABLE != OPERABLE != RECOVERABLE != PRODUCTION_AUTHORISED
```

A container that starts is not an operated service. A successful backup is not a verified restore. Green CI is not security acceptance. Engineering readiness is not release authority.

## Production release chain

```text
exact source revision
→ immutable build artifact
→ SBOM and artifact digest
→ security scans
→ staging deployment
→ liveness/readiness probes
→ synthetic smoke path
→ rollback exercise
→ SLO instrumentation
→ alert-route verification
→ isolated restore exercise
→ security acceptance
→ typed human production approval
→ bounded traffic activation
```

Every stage is fail-closed. Models, workers, browser clients and CI cannot grant production authority.

## SLO contract

The initial candidate objectives use a rolling 30-day window:

| Service | Objective |
|---|---|
| API | 99.90% availability; p95 ≤ 500 ms; p99 ≤ 1,200 ms |
| Web | 99.90% availability; p95 ≤ 1,500 ms; p99 ≤ 3,000 ms |
| Worker | 99.50% successful jobs; queue-age p95 ≤ 120 s |

These are operational objectives, not marketing guarantees or contractual SLAs.

The error-budget policy uses multi-window burn-rate alerts:

- 1-hour burn ≥ 14.4×: page;
- 6-hour burn ≥ 6×: page;
- 3-day burn ≥ 1×: ticket and release review;
- exhausted budget: production change freeze unless an incident commander authorizes mitigation.

Telemetry must be tenant-sanitized. Logs exclude credentials, payment-method data and private document bodies. Metrics must avoid unbounded tenant labels.

## Health and observability

Liveness answers whether the process is alive. Readiness answers whether it can safely accept work. Readiness fails closed when required dependencies are unavailable.

Required evidence includes:

- structured logs with correlation identifiers;
- bounded metrics for request rate, errors, latency, saturation and queue age;
- distributed traces without private payload bodies;
- synthetic probes for authenticated and unauthenticated critical paths;
- owned alerts linked to executable runbooks;
- append-only incident timelines.

## Backup and disaster recovery

| Asset | Candidate RPO | Candidate RTO |
|---|---:|---:|
| PostgreSQL durable state | 15 min | 60 min |
| Object/evidence store | 60 min | 240 min |
| Rebuildable application runtime | 0 min | 30 min |

Backup policy:

- encrypted at rest and in transit;
- digest verified;
- retained across 7-day, 35-day and 365-day classes;
- copied across a distinct failure domain;
- restored into an isolated target;
- consistency checked before declaring success.

A backup job reporting success is insufficient. The DR gate requires a measured restore with recovered-state age within RPO and elapsed recovery within RTO. Exercises may not mutate production data.

## Incident response

Incidents receive deterministic severity, named ownership and an append-only timeline. Security incidents use restricted evidence handling. Mitigation, recovery and failback are distinct states.

Post-incident reviews may add analysis and actions but cannot rewrite the historical incident record.

## Security acceptance

Required control families:

1. authenticated identity and server-resolved tenant;
2. least privilege and isolated mutation authority;
3. secret management without plaintext credentials;
4. dependency and container scanning;
5. immutable artifact integrity;
6. bounded network egress;
7. Stripe webhook signature, replay and idempotency controls;
8. append-only audit logging;
9. encrypted backups;
10. verified isolated restore;
11. incident response readiness;
12. privacy and data-rights enforcement.

Blocking rules:

- any open critical finding blocks production;
- a high finding requires explicit, typed and expiring risk acceptance;
- an expired acceptance blocks production automatically;
- CI evidence cannot sign security acceptance;
- a model cannot accept risk or authorize deployment.

Required artifacts include SBOM, vulnerability report, container scan, secret scan, IaC scan, threat-model delta, penetration-test scope, restore evidence, incident runbook and release manifest.

## Independent gates retained

P22 does not activate:

- Stripe live;
- public pricing;
- production credentials;
- public traffic;
- external publication;
- canonical source or claim authority.

Stripe live remains a separate final commercial activation after the AXIGNAL production surface is complete and the sandbox billing E2E is verified.

## Executable evidence

The bounded reference implementation covers:

- SLI calculation and latency compliance;
- multi-window error-budget alert decisions;
- production release gating;
- RPO/RTO restore decisions;
- critical/high finding policy;
- expiring risk acceptance;
- security acceptance;
- typed-human production readiness.

Dedicated validation verifies 48 invariants, 24 conformance fixtures and 16 adversarial cases while preserving zero production, public-traffic, Stripe-live, external-action and canonical-authority deltas.
