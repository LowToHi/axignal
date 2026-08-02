# Gate 7 — O01 TED source-admission disposition v0.1

## Purpose

This gate consumes the immutable O01-C v0.1 campaign result and decides whether
`src_ted_search_api_v3` may move from `CANDIDATE` to `PRODUCT_ADMITTED`.
It is deliberately separate from campaign execution and from Public Launch.

## Immutable evidence consumed

- campaign workflow run `30749337528`;
- job `91500445963`;
- retained artifact `8833930837`;
- artifact digest `sha256:6a3d55557d16459e546839a6170db02e618b3a4c31cfadf6761a0d2885dab47f`;
- controller head `57c893d41e4832f4fb50d8dabf4719275e70669b`;
- campaign result `O01_QUALITY_COVERAGE_LAG_FAIL`;
- TED diagnostic: expert-query token `ASC` rejected with HTTP 400.

The result is not rewritten or recalibrated. It produced no representative
sample and therefore cannot populate quality, lag, coverage or multilingual
metrics.

## Admission rule

TED is admitted only when every required dimension is current and `PASS`:

- Legal;
- technical;
- quality;
- rights;
- human authority;
- successful frozen campaign;
- minimum sample and country coverage;
- complete English, Spanish, French, German, Portuguese and Italian journeys;
- tested kill switch;
- tested rollback;
- zero fabricated evidence;
- no plaintext raw upload;
- no pre-admission claim contribution.

Missing, failed, partial or expired evidence blocks admission.

## Current disposition

```text
campaign result                  FAIL
representative sample            0
quality evidence                 MISSING
lag evidence                     MISSING
six-language journeys            MISSING
source kill-switch rehearsal     MISSING
rollback rehearsal               MISSING
Legal source admission           MISSING
rights admission                 MISSING
human source authority           MISSING

TED current state                CANDIDATE
TED product admission            false
claim contribution               false
source rejection                 false
retry                            new versioned contract only
public launch                    NO_GO
output                           O01_TED_SOURCE_ADMISSION_BLOCKED
```

The query-contract defect blocks admission but does not prove that TED itself
must be rejected. The source remains `CANDIDATE` until a new, separately
versioned and authorised campaign produces complete evidence.
