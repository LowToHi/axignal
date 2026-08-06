# O01-C v0.3 — real quality, coverage, lag and multilingual campaign

## Purpose

Execute exactly one private and bounded TED Search API evidence campaign after the current `LEGAL` and `PRIVACY_DATA_RIGHTS` decisions are reconstructed from their human-authored GitHub issue comments and evaluated against the exact v0.3 head, manifest and evidence-expiry boundary.

The campaign does not admit TED, create a public claim, authorise public redistribution, enable contact marketing, train a model, submit a bid, deliver an external notification or change `PUBLIC_LAUNCH=NO_GO`.

## Exact authority target

```text
campaign_id          AX-LIB-O01-TED-QALAG-ML-CONTROLS-v0.3
target_head_sha      e9621735c75b51372a6e8f6864cd18a6f42a687c
target_tree_sha      2edd7ff4eec113aabcba1a70cb76a032bfd785b7
manifest_reference   sha256:74ed362c8b856d586139062095c57a6d9a8944012bb9429dc4bb121ed6960d6d
maximum_expiry       2026-08-28T10:00:00Z
```

The only experimental change from v0.2 is:

```text
/fields/ephemeral_contact_projection/3
buyer-tel -> organisation-tel-buyer
```

The retained diagnostic proves that TED rejects `buyer-tel` and accepts `organisation-tel-buyer`, including inside the complete corrected ephemeral projection. No contact values or raw response bodies were retained by that diagnostic.

## Controller architecture

The controller has five fail-closed layers:

1. **Exact lineage:** the target and evaluator commits, trees and manifest digest must exist and be ancestors of the controller.
2. **Exact materialisation:** the v0.3 execution contract is derived from the immutable v0.2 base through the admitted delta only; the real campaign plan must equal that materialised contract plus the typed authority binding.
3. **One-shot request:** the execution-request commit must have the frozen controller SHA as its immediate parent. A later commit cannot reuse the request.
4. **Live human authority:** the workflow fetches issues `#124` and `#125`, verifies both GitHub-identity signatures and requires `O01_CAMPAIGN_AUTHORISED` before enabling the network dispatcher.
5. **Operational boundary:** the dispatcher is wrapped by the real kill switch, raw plaintext is runner-ephemeral, allow-listed projections are sealed as CMS EnvelopedData and rollback restores the exact `CANDIDATE`/no-claim/no-notification checkpoint.

## Execution sequence

```text
static CI
-> exact delta materialisation
-> exact plan verification
-> one-shot parent binding
-> retained official evidence verification
-> retained telephone diagnostic verification
-> live LEGAL reconstruction
-> live PRIVACY_DATA_RIGHTS reconstruction
-> O01_CAMPAIGN_AUTHORISED receipt
-> kill-switch preflight with zero external requests
-> bounded TED acquisition
-> multilingual journeys
-> encrypted raw sealing
-> plaintext purge
-> rollback verification
-> final threshold evaluation
```

No TED request is permitted before the authority receipt exists.

## Frozen network and data budget

```text
allowed host                 api.ted.europa.eu
endpoint                     /v3/notices/search
authentication               none
countries                    12
languages                    de,en,es,fr,it,pt
pages per country            2
page size                    100
maximum requests             60
maximum attempts/request     2
operational request floor    2 seconds
raw plaintext upload         false
contact-value persistence    false
external notifications       0
```

## Pass and failure semantics

The only campaign pass is:

```text
O01_QUALITY_COVERAGE_LAG_PASS
```

A missing, invalid, stale or mismatched authority decision stops before network access. Any HTTP, parsing, privacy, retention, control, multilingual, quality, coverage, lag or threshold failure produces:

```text
O01_QUALITY_COVERAGE_LAG_FAIL
```

Failure does not reject TED and does not admit it. TED remains `CANDIDATE`; O01-D remains a separate human source-admission decision.

## Permanent boundary

```text
TED source state                  CANDIDATE
TED product admission             false
public claims                     false
public redistribution             false
contact marketing                 false
model training                    false
bid submission                    false
external notification delivery    false
public launch                     NO_GO
```
