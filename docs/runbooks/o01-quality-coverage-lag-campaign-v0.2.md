# O01-C v0.2 — Real TED quality, coverage, lag and multilingual campaign

## Purpose

Execute the private, bounded remediation campaign authorised under O01-B v0.2. The campaign exists only to produce retained evidence for a later O01-D source-admission decision.

It does not admit TED, authorise public claims, enable public redistribution, permit marketing, train a model, submit a bid or deliver an external notification.

## Immutable lineage

```text
campaign                         AX-LIB-O01-TED-QALAG-ML-CONTROLS-v0.2
approved execution target        63b210b12988b26be04abed3701f8d97ffccebad
approved target tree             2d02c1d616516a14168b6c378d2d3352d2750da2
authority evaluator              488cedd13ff7771324fdeaa4717bd17f2d6294b7
evaluator tree                   bb23c60e8b647951681754bbc77d37930a542636
execution contract               sha256:f86672f2925343fccc61ebe0cb1085a470bbb54d062f1f936eed9347854ff3a3
campaign plan                    sha256:cae7894ca905ae7b0d0085699d6b9e75d08e684b70d58f6398594dad46fc5c97
authority manifest               sha256:e608b2d464c005aab5efff6f2e9689b7cd29c78941a1f45336eab91b87d58de6
authority artifact               8835414821
authority artifact digest        sha256:20fa305b6647ff30c2d410d20107ecd1632fa94a5897ec273fb3a437c3b30802
authority effective expiry       2026-08-28T10:00:00Z
```

## Sole remediation

```text
v0.1  SORT BY publication-number ASC
v0.2  SORT BY publication-number
```

No other query, sample, country, language, field, threshold, retention or network-budget delta is permitted.

## Frozen execution budget

```text
countries                         12
languages                          6
sample target                    180
target per country                15
pages per country                  2
page size                        100
maximum network requests          60
maximum attempts per request       2
plaintext raw upload           false
source state               CANDIDATE
public launch                  NO_GO
```

The normal path uses 24 retained-projection requests, 24 ephemeral contact-classification requests and at most one bounded history probe. The history probe is non-authoritative and fails closed without creating a historical-coverage claim.

## Operational sequence

1. Prove exact controller, evaluator and approved target ancestry.
2. Validate the frozen plan against the approved execution-contract digest.
3. Verify the authorised O01-B v0.2 artifact and retained official-source baseline.
4. Re-materialise both current human decisions from issues `#124` and `#125`.
5. Rehearse the same runner-local kill-switch guard used by every v0.2 network dispatch.
6. Retain the pre-campaign `CANDIDATE`, no-claim, no-notification checkpoint.
7. Execute the frozen TED Search API requests.
8. Measure the `de`, `en`, `es`, `fr`, `it` and `pt` ingestion, normalisation, search and presentation journeys from the real retained projection.
9. Seal allowlisted raw responses as CMS EnvelopedData with AES-256 and remove plaintext.
10. Verify the observed post-campaign boundary against the retained checkpoint.
11. Evaluate all quality, lag, coverage, multilingual, kill-switch and rollback criteria.
12. Upload retained evidence even when the campaign fails.

## Kill switch

The controller checks a runner-local atomic signal file immediately before every TED network dispatch. Activation blocks the next dispatch before the network budget is consumed. The preflight proves that an activated signal produces zero dispatches and removes the rehearsal signal before the real campaign starts.

The real signal path is:

```text
/tmp/axignal-o01-v0-2.kill
```

The control is local to the isolated campaign runner. It does not create an external standing authority or remote command channel.

## Rollback

The campaign does not mutate product admission state. Before network access it retains the canonical state:

```text
source_state                  CANDIDATE
product_admitted              false
public_claim_contribution     false
external_notifications_sent   0
contact_values_persisted      false
raw_plaintext_uploaded        false
```

After execution and raw sealing, the controller derives the observed state from real campaign evidence and requires an exact match with that checkpoint. Any mismatch produces `O01_OPERATIONAL_CONTROLS_FAIL`.

## Pass and failure semantics

A workflow conclusion of `success` means the controller executed correctly. Campaign admission evidence passes only when the final retained result is:

```text
O01_QUALITY_COVERAGE_LAG_PASS
```

Any missing, expired, partial, malformed or below-threshold evidence produces:

```text
O01_QUALITY_COVERAGE_LAG_FAIL
```

A campaign failure does not reject TED. TED remains `CANDIDATE`; O01-D must separately decide whether admission remains blocked.

## Permanent prohibitions

```text
TED product admission              false
public claims                      false
public redistribution              false
contact marketing                  false
model training                     false
bid submission                     false
external notification delivery     false
public launch                      NO_GO
```
