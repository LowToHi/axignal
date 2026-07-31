# 06 — AXIGNAL Current Execution State

Version: `1.5.0`
Status: `P00 ACCEPTED / P01 IN PROGRESS / ENGINEERING STACK THROUGH P26-T01 / P26 IN PROGRESS / P27 NOT STARTED / NO PUBLIC LAUNCH`
Goal ID: `AXIGNAL-GOAL-001`
Governing contract candidate: `31`
Decision: `ADR-016`
Canonical main: `main@b9a08a2a07d04d635164e161d1b27a7a53df8575`
Engineering-stack candidate: `e1e4999ecd1a7140d9b18ea4b5ad6f0a20e32073`
Canonical active task: `AX-GE2E-P01-T01`
Final launch task: `AX-GE2E-P27-T01` — not started

## 1. State-model warning

The repository has a deliberate split:

```text
canonical main
≠ stacked engineering branch
```

And:

```text
engineering E2E pass
≠ canonical acceptance
≠ product admission
≠ commercial availability
≠ public launch
```

Any status report that collapses these states is incorrect.

## 2. Canonical main truth

Canonical head:

```text
b9a08a2a07d04d635164e161d1b27a7a53df8575
```

Canonical programme state:

| Phase | Canonical state |
|---|---|
| P00 | `ACCEPTED` |
| P01 | `IN_PROGRESS` |
| P02–P24 | `BLOCKED` under v1.4 main authority |
| P25–P27 | Not present in canonical main at this record time |

P01 secondary evidence exists. Primary evidence remains missing.

```text
qualified unique participants          0 / 45
opportunity libraries with interviews  0 / 9
budget-authority participants          0 / 24
direct operators                       0 / 18
recent material failure incidents      0 / 27 minimum
negative-evidence cases                 0 / 10
```

Therefore:

```text
buyer personas validated      false
pricing validated             false
willingness to pay validated  false
P01 accepted                  false
```

## 3. Engineering-stack truth

Engineering stack head:

```text
e1e4999ecd1a7140d9b18ea4b5ad6f0a20e32073
```

Relationship to canonical main at the recorded comparison:

```text
391 commits ahead
0 commits behind
not merged
```

The stack contains extensive bounded engineering and exact-head CI evidence for P02–P26-T01. The stack does not override canonical dependency or human-acceptance gates.

## 4. Evidence-backed product chain in the stack

```text
persistent identity
→ passkey and revocable session
→ server-resolved tenant
→ seat and membership authority
→ Navigator
→ persistent ResearchRun
→ source or document evidence
→ Evidence Objects
→ Candidate Claims
→ deterministic admission
→ Claim Ledger
→ dossier and InvestigationContext
→ candidate Opportunity Operations and specialised workspaces
→ commercial and acceptance frameworks
→ organic-discovery and Founder Admin foundation
```

Models remain proposal-only and cannot admit canonical truth, select tenant authority, grant trials, assign seats, publish SEO pages, mutate Search Console or authorise launch.

## 5. Phase matrix

| Phase | Engineering state | Canonical state | Truth boundary |
|---|---|---|---|
| P00 | PASS | ACCEPTED | Governance accepted |
| P01 | IN_PROGRESS | IN_PROGRESS | Secondary research only |
| P02–P16 | Engineering evidence ready | Canonical acceptance blocked | No source or library commercial authority |
| P17–P23 | Engineering evidence ready | Canonical acceptance blocked | No public or commercial activation |
| P24 | Acceptance framework implemented | Canonical acceptance blocked | Current launch decision remains `NO_GO`; P24 is not final under v1.5 |
| P25-T01 | Exact-head E2E pass | Canonical acceptance blocked | Implemented but public signup and production providers blocked |
| P26-T01 | Exact-head E2E pass | Canonical acceptance blocked | Growth and Founder Admin foundation only |
| P26-T02 | Not started | Not started | Customer, trial and billing admin missing |
| P26-T03 | Not started | Not started | Risk, source, coverage and MCP admin missing |
| P26-T04 | Not started | Not started | Operations, SLO, DR and settings admin missing |
| P27-T01 | Not started | Not started | Only future final public-launch authority |

## 6. P25 identity and trial evidence

Engineering evidence present:

```text
persistent identity                 PASS
WebAuthn passkeys                   PASS
opaque revocable sessions          PASS
recovery codes and replacement     PASS
server-resolved tenant             PASS
trial per tenant/economic identity PASS
Gmail alias reuse                  PASS
weak-signal step-up                PASS
seven-day delayed start            PASS
two trial seats                    PASS
1,000,000-token ceiling            PASS
internal cost governance           PASS
one concurrent ResearchRun         PASS
append-only security ledgers       PASS
```

Still blocked or missing:

```text
public signup                      BLOCKED
production SMTP                    NOT CONFIGURED
production bot provider            NOT CONFIGURED
Google/Microsoft OIDC              NOT IMPLEMENTED
production SAML/SCIM acceptance    NOT PROVEN
production identity security sign-off MISSING
```

## 7. Seat-governance evidence

Candidate flat-tier capacities:

```text
CONTROLLED_TRIAL_7D   2 seats
PROFESSIONAL_MONTHLY  3 seats
TEAM_MONTHLY          15 seats
```

Engineering evidence includes:

- transactional reservation and activation;
- fourth Professional seat denied;
- sixteenth Team seat denied;
- concurrent final-seat protection;
- last-owner protection;
- downgrade conflict protection;
- roles and RLS;
- append-only audit.

Commercial activation remains blocked.

## 8. Candidate pricing truth

Current server-side candidate price book:

| Package | Candidate price | Seats | State |
|---|---:|---:|---|
| Controlled seven-day trial | `0 EUR` | 2 | `CANDIDATE_ONLY` |
| Professional | `149 EUR/month` | 3 | `CANDIDATE_ONLY` |
| Team | `399 EUR/month` | 15 | `CANDIDATE_ONLY` |
| Enterprise | Quote only | Contracted | `CANDIDATE_ONLY` |

Historical ranges remain hypothesis history and are not current technical authority.

Missing:

- buyer-budget evidence;
- willingness-to-pay evidence;
- complete external Stripe sandbox round trip;
- controlled live technical payment;
- independent paid customer;
- completed paid value workflow;
- retention and renewal;
- audited margin and support burden.

## 9. P26 organic-discovery evidence

P26-T01 engineering evidence present:

```text
IndexabilityGate                         PASS
append-only indexability decisions      PASS
versioned public snapshots              PASS
transactional tender hubs               PASS
Market Intelligence shell               PASS
robots, sitemap and structured data     PASS
Tender Alerts double opt-in             PASS
alert does not create identity/trial     PASS
CRM acquisition foundation              PASS
AI-citation ledger                       PASS
Founder Admin foundation                 PASS
Founder authority boundary               PASS
```

Public activation remains blocked:

```text
public indexing             BLOCKED
public Tender Alerts        BLOCKED
production email            NOT CONFIGURED
production bot verification NOT CONFIGURED
founder production principal NOT PROVISIONED
external citation imports   BLOCKED
```

## 10. Founder Operations completeness

Current live foundation modules:

- Overview;
- Organic SEO;
- Pages and Sitemaps;
- AI Citations;
- Tender Alerts;
- CRM.

Modules present as truthful read-only or blocked contracts, not complete mutation systems:

- Customers and Trials;
- Billing;
- Risk and Abuse;
- Sources and Coverage;
- Operations;
- Settings;
- Audit beyond current growth/founder events.

Therefore:

```text
P26-T01 PASS
P26 phase IN_PROGRESS
Founder Admin shell IMPLEMENTED
Founder Operations COMPLETE false
```

## 11. Google Search Console state

User-attested DNS TXT evidence has been recorded:

```text
google-site-verification=MSME8b9va1BRkZOAtEXp_zw0v5c1noDOpf3BrVJkIhA
```

Current truthful state:

```text
DNS verification evidence      PRESENT_BY_USER_ATTESTATION
property candidate             sc-domain:axignal.com
official API access            NOT PROVEN
Search Analytics retrieval     NOT PROVEN
URL Inspection retrieval       NOT PROVEN
sitemap mutation               NOT AUTHORISED
Founder OS GSC import          BLOCKED
```

Record: `data/growth/google-search-console-integration.v0.1.json`

## 12. Google Search Console MCP candidate

Candidate URL supplied by the human authority:

```text
https://mcpservers.org/es/servers/ahonn/mcp-server-gsc
```

Current state:

```text
DISCOVERED
IMPLEMENTATION IDENTITY NOT INDEPENDENTLY VERIFIED
MAINTAINER AND LICENCE NOT VERIFIED
SECURITY REVIEW MISSING
NOT PRODUCT-ADMITTED
NOT CONNECTED TO PRODUCTION
DEFAULT PERMISSION DENY
```

Any probe must be read-only, allowlisted, secret-isolated, audited and disposable. Destructive Search Console actions remain denied.

## 13. P24 and P27

P24 currently provides an engineering acceptance framework. It records missing real evidence and returns `NO_GO`.

Under Contract 31:

```text
P24 = acceptance framework
P27 = final exact-head public-launch gate
```

P27 must renew P22–P24 acceptance after P25 and P26 because those phases added identity, recovery, email, abuse, consent, public SEO, CRM, Founder Admin, Search Console and MCP attack surfaces.

## 14. Public-truth state

```json
{
  "product_finished": false,
  "public_launch_authorised": false,
  "partial_launch_allowed": false,
  "bounded_public_launch_allowed": false,
  "public_signup_authorised": false,
  "public_indexing_authorised": false,
  "public_tender_alerts_authorised": false,
  "live_self_service_billing_authorised": false,
  "global_coverage_claim_authorised": false,
  "production_mcp_authorised": false,
  "buyer_personas_validated": false,
  "pricing_validated": false,
  "opportunity_libraries_commercial": 0,
  "foundational_libraries_accepted": 0,
  "founder_operations_complete": false,
  "p27_started": false
}
```

## 15. Current authorised next work

Canonical evidence work:

```text
AX-GE2E-P01-T01
continue qualified buyer and workflow evidence
```

Engineering work permitted under Contract 31:

```text
AX-GE2E-P26-T02
Customers, Trials and Billing Administration
```

P26-T03 and T04 follow their dependencies. P27 cannot start until P26 is complete and all earlier canonical gates are capable of acceptance.

## 16. Rollback truth

- P00 governance rollback: tested.
- Phase-specific engineering rollback: recorded in stacked PRs.
- P25 and P26 isolated runtime kill switches: engineering-tested.
- Global product rollback on an accepted production head: not yet accepted.
- Search Console and MCP rollback: not applicable until admitted.
- Public launch rollback: not authorised because public launch is `NO_GO`.
