# 15 — AXIGNAL Global E2E Development Programme v1.5

Version: `1.5.0`
Status: `NORMATIVE CANDIDATE / HUMAN APPROVAL REQUIRED / NO PUBLIC LAUNCH`
Goal ID: `AXIGNAL-GOAL-001`
Programme: `P00–P27`
Contract: `31`
Decision: `ADR-016`
Canonical baseline: `main@b9a08a2a07d04d635164e161d1b27a7a53df8575`
Engineering-stack candidate: `e1e4999ecd1a7140d9b18ea4b5ad6f0a20e32073`

## 1. Programme rule

The programme distinguishes:

```text
engineering progress
≠ canonical acceptance
≠ product admission
≠ commercial availability
≠ public launch
```

A later phase may produce bounded engineering evidence before an earlier phase closes. That work remains canonically blocked until its dependencies and human gates pass.

## 2. Active execution chain

```text
P00 Canonical integration
→ P01 Buyer, workflow, budget and market evidence
→ P02 Global ontology and library contracts
→ P03 Security, identity and rights by design
→ P04 Source Admission Factory and Connector SDK
→ P05 Foundational libraries
→ P06 Multilingual and Document Intelligence
→ P07 Opportunity Operations Core
→ P08–P16 Opportunity libraries and workspaces
→ P17 Cross-library intelligence
→ P18 Intent Intelligence and Knowledge Tides
→ P19 Scenarios, calibration and outcomes
→ P20 Enterprise, API, private data and integrations
→ P21 Commercial runtime, pricing, Stripe and seat governance
→ P22 Production, SLO, DR, security, privacy and legal framework
→ P23 Product UX, B2G landing, copy and market shell
→ P24 Acceptance framework and evidence manifest
→ P25 Passwordless identity and trial-abuse governance
→ P26 Organic discovery, AI citations and Founder Operations
→ P27 Final exact-head re-acceptance and public-launch gate
```

P08–P16 may be engineered in parallel after their shared contracts exist. They cannot be canonically accepted before their dependencies.

## 3. Current status matrix

| Phase | Engineering state | Canonical state | Public/product authority |
|---|---|---|---|
| `P00` | `PASS` | `CANONICALLY_ACCEPTED` | Governance only |
| `P01` | Secondary evidence present | `IN_PROGRESS` | No buyer or pricing validation |
| `P02–P16` | Engineering stack present | `CANONICAL_ACCEPTANCE_BLOCKED` | No source/library commercial authority |
| `P17–P23` | Engineering evidence present | `CANONICAL_ACCEPTANCE_BLOCKED` | No public/product activation |
| `P24` | Acceptance framework implemented | `CANONICAL_ACCEPTANCE_BLOCKED` | `NO_GO`; not final after v1.5 |
| `P25-T01` | `ENGINEERING_E2E_PASS` | `CANONICAL_ACCEPTANCE_BLOCKED` | Public signup blocked |
| `P26-T01` | `ENGINEERING_E2E_PASS` | `CANONICAL_ACCEPTANCE_BLOCKED` | Public indexing and alerts blocked |
| `P26` | `ENGINEERING_IN_PROGRESS` | `CANONICAL_ACCEPTANCE_BLOCKED` | Founder Operations incomplete |
| `P27` | `NOT_STARTED` | `CANONICAL_NOT_STARTED` | Final launch authority absent |

## 4. P24 role

P24 is retained as a reusable acceptance framework covering:

- exact-head evidence binding;
- integrated-journey definitions;
- payment-evidence levels;
- typed human approvals;
- stop conditions;
- evidence-preserving rollback.

P24 cannot grant launch authority after later material phases exist.

## 5. P25 scope

`AX-GE2E-P25-T01` includes:

- persistent global identity;
- passkey-first WebAuthn registration and login;
- opaque revocable sessions;
- recovery codes and authenticator replacement;
- server-resolved tenant and membership;
- one trial per tenant or economic identity;
- strong and weak abuse signals;
- risk decisions and step-up;
- seven-day start on first admitted AI use;
- two seats;
- 1,000,000-token ceiling;
- internal cost and concurrency governance;
- append-only security, risk and abuse ledgers.

Engineering E2E is present. Production providers and public signup remain blocked.

## 6. P26 scope and tasks

### `AX-GE2E-P26-T01` — Organic Discovery and Founder Admin Foundation

State: `ENGINEERING_E2E_PASS / CANONICAL_ACCEPTANCE_BLOCKED`

Includes:

- IndexabilityGate;
- versioned public snapshots;
- transactional procurement hubs;
- Market Intelligence pages;
- sitemap, robots and structured data;
- Tender Alerts double opt-in;
- CRM contact and consent foundation;
- AI-citation ledger;
- Founder Admin shell and currently authorised growth modules.

### `AX-GE2E-P26-T02` — Customers, Trials and Billing Administration

State: `NOT_STARTED`

Must implement:

- customer and organisation lookup;
- trial eligibility, state, usage and manual-review operations;
- subscriptions and entitlements;
- invoices, credit notes and payment state;
- upgrades, downgrades and cancellation;
- dunning, disputes and refunds;
- seat and billing reconciliation;
- typed authority and audit;
- no direct provider-state fabrication.

### `AX-GE2E-P26-T03` — Risk, Abuse, Sources and Coverage Administration

State: `NOT_STARTED`

Must implement:

- risk-decision review and overrides;
- abuse cases and false-positive controls;
- source registry;
- legal, rights, quality and lifecycle state;
- coverage and gap disclosure;
- source admission, suspension and revocation workflows;
- connector and MCP inventory;
- independent kill switches;
- no browser or model source admission.

### `AX-GE2E-P26-T04` — Operations, SLO, Incidents, DR, Settings and Audit

State: `NOT_STARTED`

Must implement:

- worker and queue visibility;
- SLO and error-budget views;
- incident timeline and ownership;
- backup and restore evidence;
- feature flags and kill switches;
- safe configuration;
- secret-reference status without secret disclosure;
- immutable audit;
- emergency and break-glass controls;
- role and step-up enforcement.

## 7. Search Console programme

A DNS TXT Search Console verification value has been provided for `axignal.com`.

Current state:

```text
DNS verification evidence    USER_ATTESTED_PRESENT
property candidate           sc-domain:axignal.com
API capability discovery     MISSING
Search Analytics read        MISSING
Founder OS import            BLOCKED
indexing activation          BLOCKED
```

Search Console admission requires official API evidence, least privilege, secret isolation, audit, revocation and a kill switch.

## 8. GSC MCP candidate

User-provided catalogue URL:

```text
https://mcpservers.org/es/servers/ahonn/mcp-server-gsc
```

Current state:

```text
DISCOVERED
UNVERIFIED_IMPLEMENTATION
NOT_SECURITY_REVIEWED
NOT_PRODUCT_ADMITTED
READ_ONLY_REQUIRED_IF_PROBED
```

No MCP tool may mutate Search Console, sitemaps, sites, permissions or Founder OS state until independently authorised.

## 9. P27 scope

`AX-GE2E-P27-T01` must:

1. bind exact accepted heads for P00–P26;
2. renew P22 security, privacy, legal, SLO and DR evidence on the final head;
3. execute P24 integrated journeys against the final head;
4. validate P25 identity, recovery, trial and abuse in the accepted environment;
5. validate P26 public discovery, consent, CRM and Founder Operations;
6. validate all connected providers and MCPs or explicitly exclude them from launch scope;
7. validate complete Stripe sandbox and authorised live-boundary evidence;
8. bind buyer, pricing, paid value, retention, renewal, margin and support evidence;
9. confirm seven foundational and nine opportunity-library gates;
10. confirm multilingual and accessibility gates;
11. bind typed human approvals to one immutable manifest digest;
12. return only `ACCEPTED_FOR_PUBLIC_LAUNCH`, `IN_PROGRESS` or `REJECTED`.

## 10. No-launch invariant

```json
{
  "public_launch_authorised": false,
  "partial_launch_allowed": false,
  "bounded_public_launch_allowed": false,
  "public_signup_authorised": false,
  "public_indexing_authorised": false,
  "public_tender_alerts_authorised": false,
  "live_self_service_billing_authorised": false,
  "global_coverage_claim_authorised": false,
  "production_mcp_authorised": false
}
```

These values may change only through P27 and explicit human approval.

## 11. Private acceptance

Private acceptance may proceed only with:

- explicitly admitted organisations;
- controlled terms and disclosed maturity;
- no open signup;
- no public-launch claim;
- no paid media representing availability;
- auditable access and billing;
- source and coverage disclosure;
- independent suspension and rollback;
- preserved customer work and financial evidence.

## 12. Historical programme

- F0–F12 remain implementation history.
- P00–P24 v1.4 records remain audit history.
- Contract 30 and ADR-015 remain preserved.
- Engineering PRs retain their exact-head evidence.
- Contract 31 and ADR-016 govern only after approval and merge.
