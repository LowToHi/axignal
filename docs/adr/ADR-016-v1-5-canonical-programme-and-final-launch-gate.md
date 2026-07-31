# ADR-016 — v1.5 Canonical Programme and Final Launch Authority

Status: `PROPOSED / HUMAN APPROVAL REQUIRED`
Date: `2026-07-31`
Goal ID: `AXIGNAL-GOAL-001`
Governing contract: `docs/contracts/31-global-e2e-development-contract-v1.5.md`
Supersedes: the active-programme and final-gate portions of ADR-015
Preserves: ADR-015 as immutable decision history

## Context

ADR-015 selected a finished global product before public launch and established Contract 30 with a P00–P24 programme. That decision remains strategically valid.

Subsequent engineering introduced material product surfaces after P24:

- P25 persistent identity, WebAuthn passkeys, revocable sessions, recovery and trial-abuse governance;
- P26 programmatic SEO, an IndexabilityGate, public procurement intelligence pages, Tender Alerts, CRM, AI-citation evidence and a Founder Admin control plane.

These surfaces add new security, privacy, consent, production, legal, operational and launch obligations. A launch decision executed before them cannot be the final exact-head acceptance decision.

The repository also now has two different truths:

```text
canonical main
= main@b9a08a2a07d04d635164e161d1b27a7a53df8575

engineering stack candidate
= e1e4999ecd1a7140d9b18ea4b5ad6f0a20e32073
```

Main retains P00 accepted and P01 in progress. The stacked engineering branches contain extensive P02–P26 evidence but do not constitute canonical acceptance.

## Decision

1. Adopt Contract 31 and the P00–P27 programme as the candidate canonical authority.
2. Retain P24 as an acceptance framework and evidence-manifest engine.
3. Remove P24's authority to launch the product after P25 and P26.
4. Make P27 the only final exact-head public-launch gate.
5. Preserve the no-partial-public-launch rule.
6. Replace the prior `BOUNDED_PUBLIC_LAUNCH` concept with private acceptance that is not publicly represented as launch.
7. Separate engineering and canonical state in every active roadmap and machine-readable state record.
8. Treat P25 as mandatory product scope.
9. Treat P26 as mandatory product scope and keep the phase in progress until T01–T04 are accepted.
10. Record Google Search Console DNS verification as evidence while keeping API access and data import unproven.
11. Register the user-provided Google Search Console MCP URL as a candidate connector only; no MCP server is admitted by catalogue presence.
12. Keep public signup, indexing, SMTP, external identity providers, live Stripe, MCP tools and commercial activation independently blocked.

## Programme consequence

```text
P00–P23 product and capability programme
→ P24 acceptance framework
→ P25 identity and trial-abuse governance
→ P26 organic acquisition and Founder Operations
→ P27 final exact-head re-acceptance and public-launch gate
```

## P26 decomposition

```text
P26-T01 Organic Discovery and Founder Admin Foundation
P26-T02 Customers, Trials and Billing Administration
P26-T03 Risk, Abuse, Sources and Coverage Administration
P26-T04 Operations, SLO, Incidents, DR, Settings and Audit Administration
```

P26-T01 passing does not imply that the entire Founder Admin is complete.

## Launch modes

Permitted:

```text
NO_GO
PRIVATE_ACCEPTANCE
ACCEPTED_FOR_PUBLIC_LAUNCH
```

Prohibited as a substitute for the contracted final product:

```text
BOUNDED_PUBLIC_LAUNCH
OPEN_PUBLIC_BETA
PUBLIC_PARTIAL_PRODUCT
```

Private acceptance may include paid organisations under explicit controlled terms. It must not include open signup, paid media representing launch or public claims of finished-product availability.

## Pricing consequence

The versioned server-side price book is the current technical source for candidate package definitions:

```text
CONTROLLED_TRIAL_7D   0 EUR       2 seats
PROFESSIONAL_MONTHLY  149 EUR     3 seats
TEAM_MONTHLY          399 EUR     15 seats
ENTERPRISE_CONTRACT   quote only
```

These prices remain `CANDIDATE_ONLY`. Historical price bands remain evidence of prior hypotheses and do not override the current candidate runtime. P01, P21 and P27 must validate final pricing.

## Search Console consequence

The DNS TXT verification value provided by the human authority is recorded as public verification evidence. It does not prove:

- successful Search Console API access;
- the exact property identifier returned by Google;
- a working Search Analytics import;
- permission for an MCP server;
- Founder OS mutation authority;
- public indexing approval.

## MCP consequence

The candidate URL:

```text
https://mcpservers.org/es/servers/ahonn/mcp-server-gsc
```

is registered as `DISCOVERED` and `NOT_PRODUCT_ADMITTED`.

Any MCP integration must start read-only and pass exact implementation identity, licence, supply-chain, authentication, secret, tool-permission, egress, prompt-injection, audit and kill-switch gates. Destructive tools are denied by default.

## Positive consequences

- final acceptance occurs on the actual final attack and product surface;
- engineering progress remains visible without being misrepresented as canonical acceptance;
- P24 evidence work is preserved rather than discarded;
- identity, trial abuse, SEO, consent and founder operations become mandatory launch dependencies;
- Search Console can be used as evidence without becoming publication authority;
- MCP adoption remains possible without bypassing connector governance;
- the no-partial-launch decision remains intact.

## Negative consequences

- the final launch moves after P26 completion and P27 re-acceptance;
- P22–P24 evidence must be renewed on the later exact head;
- additional founder-control-plane work is mandatory;
- Search Console and MCP integration require separate security and operational work;
- more documents and registries must distinguish canonical and engineering state.

## Alternatives rejected

### Keep P24 as final and treat P25/P26 as post-launch

Rejected. Identity, trial abuse, public SEO, consent and founder administration are launch-critical surfaces.

### Merge all engineering branches and declare the programme accepted

Rejected. CI and implementation evidence do not satisfy buyer, source, rights, paid, production, security and human-approval gates.

### Launch a bounded public cohort

Rejected as a public launch category. Private acceptance is permitted, but it must not be represented as a finished public product.

### Treat the Search Console DNS record as a complete integration

Rejected. DNS verification is only one evidence item.

### Install the listed MCP directly

Rejected. Third-party MCP discovery is not security admission or permission authority.

## Authority boundary

This ADR does not:

- activate Contract 31 before human approval and merge;
- accept P01;
- canonically accept P02–P26;
- admit any source or MCP;
- enable public signup or indexing;
- configure SMTP, Turnstile, OIDC, SAML or SCIM;
- enable Search Console API access;
- validate candidate prices;
- enable Stripe live;
- authorise public launch.

## Validation obligations

ADR-016 advances only when:

- Contract 31 is present and internally consistent;
- the active roadmap uses P00–P27;
- canonical and engineering state are separated;
- v1.5 task and programme registries validate;
- Search Console and MCP records preserve their truthful states;
- all public-activation booleans remain false;
- CI validates the exact branch;
- the human authority approves the change.

## Rollback

If rejected or superseded:

- preserve Contract 31 and ADR-016 as history;
- retain Contract 30 and ADR-015;
- leave P25/P26 engineering evidence intact;
- restore the previous active indexes through a recorded decision;
- keep public launch, signup, indexing, live billing and MCP access blocked;
- delete no evidence, ledgers or negative findings.
