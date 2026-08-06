# P26-T01 — Organic Discovery, Programmatic SEO & AI Citation Governance

Task: `AX-GE2E-P26-T01`

Status: `IMPLEMENTED IN STACKED DRAFT / PUBLIC ACTIVATION BLOCKED`

## Purpose

P26 turns AXIGNAL's governed procurement dataset into an acquisition surface without treating every filter combination as an indexable page.

```text
source libraries
→ normalisation and enrichment
→ SEO page candidate
→ deterministic IndexabilityGate
→ founder review
→ versioned public snapshot
→ sitemap and structured data
→ tender alert
→ passwordless account
→ governed trial
```

The following boundaries are normative:

```text
dataset != indexable page
generated page != published page
crawlable != indexed
indexed != ranked
traffic != qualified buyer
alert subscriber != trial user
AI citation != endorsement
CI pass != public indexing approval
```

## Page classes

- `TENDER_HUB`: transactional country × sector opportunity page.
- `MARKET_INTELLIGENCE`: aggregate procurement market analysis.
- `TENDER_DETAIL`: selective long-tail page for a sufficiently enriched notice.

Arbitrary facets remain product search state and must not become public URLs automatically.

## IndexabilityGate

Policy: `indexability-gate@1.0.0`.

A candidate is admitted only when it satisfies:

- sufficient active inventory;
- sufficient buyer diversity;
- demand score;
- data quality;
- content uniqueness;
- source coverage;
- content depth;
- maximum freshness age;
- non-synthetic data.

A decision is persisted append-only as `INDEX`, `NOINDEX` or `HOLD`. A founder cannot publish a page that has not reached `INDEXABLE`.

## Snapshot authority

Publication creates an expiring, content-addressed snapshot containing:

- version;
- content hash;
- methodology version;
- source count;
- metrics;
- source URLs;
- publication actor and time;
- expiry time.

Only current non-synthetic `PUBLISHED` snapshots can appear in the public page API or sitemap.

## SEO and AI citation surface

Public pages expose:

- canonical URL;
- `CollectionPage` and `Dataset` JSON-LD;
- `isBasedOn` source provenance;
- `dateModified`;
- temporal and spatial coverage;
- methodology version;
- visible freshness and coverage limitations.

Crawler policy:

- Googlebot, Bingbot and OAI-SearchBot may discover admitted public pages;
- GPTBot is disallowed for model-training access;
- admin, API, account, workspace and token routes are private;
- the authenticated workspace is always `noindex`.

`llms.txt` describes the public information contract but does not create a second corpus or override robots.txt.

## Tender Alerts

Alert capture is an independent consent lifecycle:

```text
request
→ bot verification
→ PENDING_CONFIRMATION
→ email delivery
→ explicit POST confirmation
→ ACTIVE
```

Email scanners cannot confirm by opening a URL. Delivery failure triggers compensating suppression. An alert never creates:

- identity;
- tenant;
- seat;
- trial;
- paid package.

## Founder Control Plane

Route: `/admin`.

Production authority is the intersection of:

```text
valid passwordless session
∩ recent AAL2 passkey verification
∩ server-side founder subject allowlist
∩ active founder_admin_principal in PostgreSQL
∩ typed SECURITY DEFINER operation
∩ append-only audit event
```

Tenant seat membership is not global founder authority. The browser cannot declare founder status.

Modules:

- Overview;
- Organic SEO;
- Pages & Sitemaps;
- AI Citations;
- Tender Alerts;
- CRM;
- Customers & Trials;
- Billing;
- Risk & Abuse;
- Sources & Coverage;
- Operations;
- Settings;
- Audit.

Only modules backed by current authority are mutable. Blocked or read-only modules display their contract rather than simulating functionality.

## CRM boundary

The P26 CRM stores acquisition contacts, consent and lifecycle stage. It does not become identity or billing authority.

```text
CRM contact != user
CRM stage != risk decision
lead score != entitlement
trial stage != active trial
customer stage != paid subscription authority
```

## AI citation governance

Citation events record:

- provider;
- surface;
- cited URL;
- HMAC-protected grounding query;
- source of observation;
- observed time;
- metadata;
- recording actor.

Citation events are append-only and represent observed evidence, not endorsement or ranking guarantees.

## Activation gates

The following remain independently blocked outside the isolated E2E topology:

- public indexing;
- public alert capture;
- production email provider;
- production Turnstile credentials;
- founder production principal provisioning;
- Search Console connection;
- Bing Webmaster connection;
- external citation import;
- live Stripe;
- commercial activation.
