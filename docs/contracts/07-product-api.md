# 07 — Product API Contract

Version: `0.1.0`
Status: `NORMATIVE`

## 1. Purpose

The AXIGNAL API exposes authorised, structured product state. It MUST not expose internal prompts, restricted raw data, secrets or unadmitted candidate claims.

## 2. API principles

- REST/JSON foundation API using OpenAPI 3.1.
- Stable version prefix: `/v1`.
- Cursor pagination for large collections.
- UTC timestamps in RFC 3339.
- Explicit currency, unit, geography and source scope.
- Deterministic resource identifiers.
- Idempotency keys for mutating operations.
- ETags or equivalent cache validators for stable reads.
- Structured errors using `application/problem+json` where practical.
- Entitlement and source-rights enforcement on every response.

## 3. Primary resources

### Claims

`GET /v1/claims`

`GET /v1/claims/{claim_id}`

`GET /v1/claims/{claim_id}/history`

`GET /v1/claims/{claim_id}/evidence`

`GET /v1/claims/{claim_id}/relations`

### Opportunities

`GET /v1/opportunities`

`GET /v1/opportunities/{opportunity_id}`

`GET /v1/opportunities/{opportunity_id}/claims`

`GET /v1/opportunities/{opportunity_id}/scenarios`

### Markets and entities

`GET /v1/markets`

`GET /v1/markets/{market_id}`

`GET /v1/entities`

`GET /v1/entities/{entity_id}`

### Climate and trends

`GET /v1/climate`

`GET /v1/trends`

`GET /v1/timeseries/{series_id}`

### Geography

`GET /v1/geo/layers`

`GET /v1/geo/tiles/{layer}/{z}/{x}/{y}`

`GET /v1/geo/regions/{region_id}`

### Graph

`GET /v1/graph/neighbours`

`GET /v1/graph/paths`

`POST /v1/graph/query`

### Search

`GET /v1/search`

Search MUST return match explanation metadata when semantic ranking materially affects result order.

### User workspaces

`GET /v1/watchlists`

`POST /v1/watchlists`

`PATCH /v1/watchlists/{watchlist_id}`

`DELETE /v1/watchlists/{watchlist_id}`

`POST /v1/watchlists/{watchlist_id}/items`

`DELETE /v1/watchlists/{watchlist_id}/items/{item_id}`

### Alerts

`GET /v1/alerts`

`PATCH /v1/alerts/{alert_id}`

### Exports

`POST /v1/exports`

`GET /v1/exports/{export_id}`

Exports MUST honour source-specific restrictions and retention rules.

## 4. Filtering

Collection resources SHOULD support typed filters such as:

- `geography`;
- `sector`;
- `universe`;
- `asset_class`;
- `claim_type`;
- `epistemic_status`;
- `maturity`;
- `observed_after`;
- `observed_before`;
- `valid_at`;
- `freshness_min`;
- `evidence_strength_min`;
- `contradiction_pressure_max`;
- `source_id`;
- `currency`;
- `liquidity_band`;
- `ticket_band`.

Filters MUST describe objective data state, not user suitability.

## 5. Response envelopes

A collection response MUST include:

```json
{
  "data": [],
  "meta": {
    "request_id": "...",
    "as_of": "...",
    "coverage": {},
    "next_cursor": null
  }
}
```

Material analytical resources MUST include:

- `as_of`;
- `method_version`;
- `coverage`;
- `freshness`;
- `rights` or export constraints;
- `uncertainty` where applicable.

## 6. Error model

Canonical error fields:

- `type`;
- `title`;
- `status`;
- `detail`;
- `instance`;
- `request_id`;
- `code`;
- optional field-level violations.

Required domain codes include:

- `ENTITLEMENT_REQUIRED`
- `SOURCE_RESTRICTED`
- `EXPORT_NOT_PERMITTED`
- `CLAIM_EXPIRED`
- `INSUFFICIENT_EVIDENCE`
- `COVERAGE_UNAVAILABLE`
- `RATE_LIMITED`
- `INVALID_CURSOR`
- `CONFLICTING_VERSION`

## 7. Authentication

The API MUST support OAuth 2.1/OIDC-compatible access tokens for first-party and enterprise integrations.

API keys MAY be offered for server-to-server access but MUST be:

- hashed at rest;
- scoped;
- rate limited;
- rotatable;
- revocable;
- organisation-bound;
- visible only once at creation.

## 8. Entitlements

Entitlements MUST be evaluated by:

- plan;
- workspace;
- universe;
- source rights;
- geographic rights;
- export rights;
- API quota;
- data freshness tier;
- user role.

The API MUST return an explicit entitlement error, not silently truncate a result in a way that changes interpretation.

## 9. Rate limits

Rate limits MUST be plan-specific and returned via standard headers.

Limits SHOULD distinguish:

- standard reads;
- semantic search;
- graph traversal;
- tile access;
- exports;
- expensive analytical queries.

## 10. Versioning

Breaking changes require a new major API version.

Non-breaking additions MAY occur within `/v1`.

Schema fields MUST NOT change meaning without a version change. Deprecated fields MUST include migration guidance and a published removal date.

## 11. Webhooks

Enterprise plans MAY subscribe to:

- claim state changes;
- material opportunity changes;
- scenario drift;
- source suspension;
- export completion;
- entitlement changes.

Webhook deliveries MUST be signed, replay-resistant, retryable and idempotent.

## 12. Graph query safety

The public graph API MUST expose bounded, typed operations. It MUST NOT expose unrestricted database query languages directly.

Limits MUST cover:

- traversal depth;
- node count;
- edge types;
- execution time;
- restricted-node leakage;
- tenant-private data.

## 13. AI explanation endpoint

A future explanation endpoint MAY generate summaries from authorised canonical resources.

It MUST return:

- cited resource IDs;
- generation timestamp;
- model metadata appropriate for audit;
- clear distinction between retrieved and generated content;
- no authority to create canonical claims.

## 14. Acceptance criteria

The API contract is accepted when:

- OpenAPI validates;
- generated clients compile;
- authentication and entitlements are integration-tested;
- restricted source data cannot leak through search, graph or exports;
- cursor pagination is stable;
- error codes are documented;
- material resources include `as_of`, coverage and method metadata;
- backward compatibility tests are active;
- rate-limit and idempotency behaviour are tested.
