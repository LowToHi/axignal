# Gate 7 O01-D — TED source admission v0.2

## Purpose

This gate decides whether `src_ted_search_api_v3` may move from `CANDIDATE` to `PRODUCT_ADMITTED` after the successful O01-C v0.6-r4 quality, coverage, lag, multilingual and controls campaign.

Source admission is distinct from public-claim authority, complete O01 library acceptance, complete Gate 7 acceptance and production launch.

## Immutable evidence

```text
campaign output       O01_QUALITY_COVERAGE_LAG_PASS
execution commit      5291baa019a85c789d1961d73c198802e28c038a
workflow run          30763024434
real campaign job     91536955808
artifact              8838091687
artifact digest       sha256:a2328776b89ffaa44dde20649a5bee39711d7ac13b6bbc11c72e608631eca092
sample                180
countries observed    12
languages             de en es fr it pt
all thresholds        PASS
fabricated evidence   0
```

The content-addressed campaign registry preserves report-member digests, measured values and limitations.

## Required human authorities

All seven decisions are mandatory and independent:

1. `PRODUCT` — issue #148;
2. `SECURITY` — issue #149;
3. `PRIVACY_DATA_RIGHTS` — issue #150;
4. `LEGAL` — issue #151;
5. `SOURCE_QUALITY` — issue #152;
6. `UX_ACCESSIBILITY` — issue #153;
7. `HUMAN_COVERAGE_AUTHORITY` — issue #154.

Every comment must contain exactly:

```text
authority
decision
scope
manifest_reference
head_sha
reviewed_at
expires_at
signature
conditions
```

The decision must be posted in the assigned issue by a GitHub user whose login is bound into the `github-identity-v1` signature. All seven comments must target the same frozen SHA and the same manifest digest.

Missing, malformed, expired, rejected, wrong-issue, wrong-scope, wrong-head, wrong-manifest or bot-authored decisions block admission.

## Permitted transition

A complete pass permits only:

```text
source state                    PRODUCT_ADMITTED
bounded product use             true
bounded public claim input      false
O01 canonical state             IN_REVIEW
O01 claim decision              PENDING
Gate 7                          IN_PROGRESS
public launch                   NO_GO
```

## Limitations retained after admission

The campaign does not establish:

- exhaustive TED archive depth;
- an official provider publication-frequency claim;
- procurement coverage outside the twelve measured TED buyer-country strata;
- national or sub-threshold portals outside TED;
- absence of truncation risk beyond the frozen 200-notice country cap;
- rights to attachments, full source text, third-party works, protected marks or natural-person data;
- public API redistribution, marketing use, model training, bid submission or external notification delivery.

Therefore source admission cannot make `AX-LIB-O01` accepted or authorize a global procurement claim.

## Fail-closed outputs

```text
O01_TED_SOURCE_ADMISSION_PASS
O01_TED_SOURCE_ADMISSION_BLOCKED
```

Automation may validate and extract human decisions. It may not create approval, create a human signature without explicit human consent, alter a signed payload or expand the frozen authority boundary.
