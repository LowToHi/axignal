# AX-LIB-O01 O01-E — Historical depth, update frequency and publication lag

## Objective

Close the three remaining technical evidence blocks for the product-admitted TED Search API source without converting bounded product admission into a public coverage claim.

```text
historical_depth     MISSING -> PASS
update_frequency     MISSING -> PASS
publication_lag      MISSING -> PASS
```

A successful campaign may recommend:

```text
AX-LIB-O01 canonical_state   IN_REVIEW -> ACCEPTED
AX-LIB-O01 claim_decision    PENDING   -> DENIED
```

`DENIED` is intentional: TED alone does not establish worldwide public-procurement coverage. Gate 7 remains `IN_PROGRESS` and public launch remains `NO_GO`.

## Frozen public boundaries

The campaign distinguishes three different concepts:

1. **Public TED search depth** — the rolling public window exposed by TED's `All notices` search scope.
2. **Non-public internal archive** — explicitly outside the campaign and outside AXIGNAL authority.
3. **Exhaustive ingestion** — not performed; the boundary is characterised using count-only queries and one validating notice.

The frequency contract combines:

- the official annual OJ S release calendar;
- TED's declared Monday-to-Friday ordinary publication schedule;
- presence of twenty recent scheduled editions in Search API;
- reachability of ten recent daily packages.

The lag contract is conservative:

```text
publication-to-AXIGNAL upper bound
  = official website availability deadline
  + measured Search API request duration
```

It is not an exact first-seen timestamp and must never be represented as one.

## Network and retention controls

```text
allowed hosts                 api.ted.europa.eu
                              docs.ted.europa.eu
                              ted.europa.eu
maximum requests              60
maximum attempts/request      2
request timeout               30 s
raw notice payload retained   false
daily package body retained   false
contact values retained       false
fabricated evidence           0
synthetic evidence            0
```

All HTTP connections use the existing public-address DNS validation and pinned-address TLS connection. Redirects are accepted only when the destination remains inside the exact HTTPS allowlist.

## One-shot execution

The real campaign is disabled unless the exact branch head adds only:

```text
data/acceptance/campaigns/
AX-LIB-O01-history-frequency-lag-execution-request.v0.1.json
```

The request must:

- be absent from its parent;
- name the exact parent SHA;
- bind the exact plan SHA-256;
- target `LowToHi/axignal`;
- target `agent/ax-gate7-o01-e-history-frequency-lag`;
- declare `execute=true` and `one_shot=true`.

Any mismatch fails closed. After successful evidence retention and durable closure, the request must be deleted.

## Execution sequence

1. Validate exact checkout, Python compilation, Ruff, unit tests and plan contract.
2. Verify the retained O01-D admission artifact and current source-admission expiry.
3. Recheck four official TED documents by required semantic anchors.
4. Download and parse the official 2025 and 2026 release calendars.
5. Binary-search the earliest public Search API date using count-only queries.
6. Prove that the preceding date has zero results and validate one earliest notice.
7. Check twenty recent scheduled editions in Search API.
8. Probe ten recent daily packages without retaining their bodies.
9. Calculate the declared and observed update-frequency evidence.
10. Calculate the conservative publication-to-AXIGNAL upper-bound distribution.
11. Verify every threshold, privacy boundary and authority boundary.
12. Upload only the allowlisted evidence package.

## Stop conditions

Stop immediately and retain a fail-closed report when any of these conditions occurs:

- source admission is absent, expired or no longer `PRODUCT_ADMITTED`;
- plan or one-shot request digest mismatch;
- official source anchors change or disappear;
- release calendar cannot be parsed deterministically;
- Search API omits its total count;
- the day before the inferred public boundary is not empty;
- a measured threshold fails;
- the request budget is exceeded;
- a raw notice, XML package, contact value, secret or private key is retained;
- any public, global, exhaustive or exact-first-seen claim becomes enabled.

## Success output

```text
O01_HISTORY_FREQUENCY_LAG_PASS
```

Success closes O01-E only. It does not close Gate 7, authorise a global claim, merge the stacked PR, or authorise production launch.
