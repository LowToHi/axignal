# Google Search Console and MCP Governance v0.1

Status: `DNS EVIDENCE RECORDED / API AND MCP NOT ADMITTED`
Goal ID: `AXIGNAL-GOAL-001`
Contract: `31`
Decision: `ADR-016`
Record: `data/growth/google-search-console-integration.v0.1.json`

## 1. Purpose

This document governs Google Search Console evidence and any MCP connector used to access it.

The integration supports P26 organic-discovery diagnostics and P27 launch evidence. It does not become page-publication, product, tenant, billing or canonical-claim authority.

## 2. Current evidence

The human authority provided this DNS TXT record for `axignal.com`:

```text
google-site-verification=MSME8b9va1BRkZOAtEXp_zw0v5c1noDOpf3BrVJkIhA
```

The record is classified as public DNS verification material, not an application secret.

Current truthful state:

```text
DNS verification evidence     USER_ATTESTED_PRESENT
property candidate            sc-domain:axignal.com
official API access           NOT PROVEN
Search Analytics retrieval    NOT PROVEN
URL Inspection retrieval      NOT PROVEN
sitemap mutation              NOT AUTHORISED
Founder OS import             BLOCKED
public indexing               BLOCKED
```

The token proves no more than the declared DNS verification state. A live API response is required to establish the property identifier and accessible capabilities.

## 3. Official API admission

The preferred production integration is the official Google Search Console API under a least-privilege identity.

Admission requires:

1. API enabled in an approved Google Cloud project;
2. exact OAuth client or service-account identity recorded through a secret reference;
3. no credential JSON, refresh token or private key in the repository;
4. property discovery through the official API;
5. one bounded read-only Search Analytics request;
6. explicit query dimensions, date range and row limits;
7. rate-limit, retry and error handling;
8. append-only integration audit;
9. retention and privacy policy for imported query/page data;
10. revocation and kill switch;
11. typed founder or integration authority;
12. P27 inclusion or explicit exclusion from launch scope.

## 4. Permitted uses

After admission, Search Console data may support:

- clicks, impressions, CTR and average-position analysis;
- query-to-page analysis;
- country and device segmentation;
- indexing and crawl diagnostics;
- sitemap monitoring;
- page-decay and cannibalisation investigation;
- comparison of admitted SEO snapshots with observed search performance;
- organic-funnel measurement;
- identification of candidates for human review.

## 5. Prohibited authority

Search Console data cannot by itself:

- publish a page;
- set `INDEXABLE`;
- override the IndexabilityGate;
- remove a page;
- prove product-market fit;
- prove a visitor is a qualified buyer;
- grant a trial;
- change a price;
- admit a source;
- create a canonical claim;
- authorise public launch.

## 6. Candidate MCP

Candidate catalogue URL supplied by the human authority:

```text
https://mcpservers.org/es/servers/ahonn/mcp-server-gsc
```

Current state:

```text
DISCOVERED
USER-PROVIDED CATALOGUE ENTRY
IMPLEMENTATION IDENTITY NOT INDEPENDENTLY VERIFIED
MAINTAINER NOT VERIFIED
LICENCE NOT VERIFIED
SECURITY REVIEW MISSING
NOT PRODUCT-ADMITTED
NOT CONNECTED TO PRODUCTION
```

A registry page is discovery evidence only. MCP catalogue presence does not equal connector admission. AXIGNAL must identify the exact code repository and release before execution.

## 7. MCP threat boundary

A third-party MCP server can influence an agent through:

- self-declared tool descriptions;
- untrusted tool output;
- dependency or release compromise;
- OAuth or service-account misuse;
- overly broad tool permissions;
- prompt injection contained in external data;
- arbitrary egress or shell execution;
- destructive Search Console actions;
- credential leakage;
- confused-deputy access to Founder OS.

MCP servers therefore use the same Source Admission Factory discipline as external connectors, with additional tool-level controls.

## 8. Default MCP policy

```text
default server state     DENY
default tool state       DENY
default probe mode       READ_ONLY
credentials              SECRET REFERENCE ONLY
destructive tools        DISABLED
arbitrary shell          DISABLED
arbitrary browser        DISABLED
Founder OS mutations     TYPED INTERNAL API ONLY
```

Candidate read-only tool classes:

- list verified properties;
- read Search Analytics;
- inspect URL/index status where supported;
- read sitemap state.

Denied by default:

- add or delete a site;
- submit or delete a sitemap;
- add, remove or change users;
- alter DNS;
- reveal credentials;
- execute arbitrary commands;
- perform arbitrary browser automation;
- bypass the IndexabilityGate;
- mutate CRM, billing, trials or launch state.

## 9. MCP admission checklist

Every candidate must provide:

- exact repository URL and immutable release reference;
- maintainer identity and activity review;
- licence and redistribution terms;
- dependency manifest and vulnerability scan;
- tool list with read/write/destructive classification;
- protocol transport and network exposure;
- authentication flow;
- requested Google scopes;
- secret-storage design;
- input and output schemas;
- rate limits;
- data retention;
- prompt-injection controls;
- egress allowlist;
- per-tool allowlist;
- test evidence;
- audit events;
- kill switch;
- rollback;
- human security and product approval.

## 10. Founder OS integration

The Founder Admin may eventually display:

- verified properties;
- last successful import;
- query and page performance;
- sitemap state;
- index coverage and errors;
- crawl anomalies;
- page and query decay;
- citation and conversion correlation;
- connector health and permission state.

The dashboard must display evidence state explicitly:

```text
LIVE_API
IMPORTED_SNAPSHOT
STALE
PARTIAL
UNAVAILABLE
BLOCKED
```

It must never fabricate live status from fixtures or a DNS token.

## 11. Data minimisation

Imported Search Console data should be limited to fields required for SEO diagnostics and acquisition analytics. Query strings can expose sensitive or identifying intent and must receive:

- purpose limitation;
- access control;
- retention rules;
- export rules;
- logging minimisation;
- deletion or aggregation policy;
- no use as identity or fraud proof.

## 12. Acceptance tests

A production candidate must prove:

```text
list property                      PASS
read Search Analytics              PASS
least-privilege scope              PASS
secret absent from repository      PASS
audit event                        PASS
rate limit and retry               PASS
revocation                         PASS
kill switch                        PASS
destructive tool denial            PASS
cross-tenant leakage               0
Founder authority bypass           0
public indexing changed by import  0
```

## 13. Truth boundaries

```text
DNS token != API access
API access != MCP admission
MCP catalogue presence does not equal connector admission
MCP admission != unrestricted tools
Search Console data != canonical truth
impression != qualified visitor
click != signup
signup != trial
trial != customer
citation != endorsement
indexing != ranking
ranking != revenue
```
