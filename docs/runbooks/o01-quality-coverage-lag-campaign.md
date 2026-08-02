# O01-C — Real TED quality, coverage and lag campaign

## Purpose

Execute one real, bounded and reproducible TED Search API campaign against the exact O01 target authorised by the current Legal and Privacy/Data Rights envelope.

This phase measures evidence. It does not admit TED to the product, authorise public claims, redistribute TED data, enable contact marketing, train a model or present an offer.

## Frozen authority

```text
campaign target
b754b5641e5f17c5a084434aace4f939a4be0e84

target tree
615efd6e8a7f3369292775dbcf3223f8cc006f29

O01-B evaluator
3c421d0b8e48c009f5361d4156fd8c1dc07c8101

manifest reference
sha256:0c722eb4b02c4446ac26154b6ade49e1efb7b5c7787f8ac4925a0af8dd3d7898

authority expiry
2026-08-27T23:59:59Z
```

The controller may be a descendant of the evaluator, but it must prove that the authorised target and evaluator remain exact ancestors with their frozen trees. It may not change the campaign target or authority manifest.

## Sampling plan

The plan is committed before any campaign request:

- measurement window: 2026-07-01 through 2026-07-31;
- twelve buyer-country strata;
- six target presentation languages;
- all notice types observed inside TED `ACTIVE` scope;
- two pages of at most 100 notices per country;
- deterministic SHA-256 selection of fifteen notices per country;
- target sample: 180 notices;
- maximum Search API request budget: 60;
- maximum two attempts for any request;
- no adaptive query, field, page or threshold changes during execution.

The plan digest is copied into the retained sampling manifest. A different digest means a different campaign.

## Official API boundaries

The only acquisition endpoint is:

```text
https://api.ted.europa.eu/v3/notices/search
```

Controls:

- HTTPS oly;
- exact host allowlist;
- port 443 only;
- every DNS answer must be globally routable;
- TLS certificate and SNI remain bound to the official hostname;
- no proxy environment;
- no API key or credentials;
- response size, request count, retry and page limits are frozen;
- no redirect to another host;
- no notice XML, notice HTML, attachments or third-party works.

Official documentation records pagination mode as capped at 15,000 matching notices, 250 notices per page and 10,000 returned fields per page. The campaign intentionally stays below those limits and reports any stratum whose matching population exceeds the frozen two-page retrieval cap.

## Raw response retention

The retained raw evidence is the exact HTTP response body for the **allow-listed Search API field projection only**. It excludes contact fields, full notices, attachments and source-native full text.

Plaintext raw responses exist only under the ephemeral runner `/tmp` directory. Before artifact upload they are:

1. packed into a deterministic tar/gzip archive;
2. hashed with SHA-256;
3. encrypted as CMS EnvelopedData with AES-256 using the committed recipient certificate;
4. structurally verified;
5. deleted together with the plaintext archive.

Only `raw-responses.cms`, its digests and the retention manifest enter the GitHub artifact. The matching private key must never be committed, pasted into issues or stored in CI.

To decrypt locally:

```bash
scripts/decrypt_gate7_o01_raw_responses.sh \
  raw-responses.cms \
  data/acceptance/keys/o01-evidence-recipient-cert.pem \
  /secure/path/o01-evidence-private-key.pem \
  raw-retention.v0.1.json \
  /secure/output/o01-raw
```

## Contact-channel measurement

Contact fields are requested in a separate projection and processed only in memory. Values are never written to disk, logs, reports or artifacts.

The report retains only:

- number of classified endpoints;
- aggregate data-class counts;
- aggregate policy-decision counts;
- conformance ratio against the frozen O01 contact policy matrix.

This is policy-conformance evidence, not proof that every source contact has been semantically or legally classified by a human.

## Quality definitions

Accuracy metrics measure AXIGNAL transformation fidelity against source-projected TED Search API fields. They do not assert that the publisher entered factually or legally correct information.

Conditional metrics include their numerator and denominator. Missing source fields are measured separately rather than guessed.

## Lag definitions

- `source_publication_lag`: publication date at 00:00 UTC to first campaign retrieval;
- `source_availability_lag`: the same interval reported explicitly as an upper bound because a historical one-shot campaign cannot observe the exact first-availability instant;
- `AXIGNAL_acquisition_lag`: request start to complete response body;
- `normalisation_lag`: response completion to normalised record;
- `indexing_lag`: normalised record to in-memory indexed record;
- `subscriber_notification_lag`: index completion to private notification-ledger enqueue.

No external email, webhook, message or marketing communication is sent.

## Outputs

```text
sampling-manifest.v0.1.json
sanitised-sample-inventory.v0.1.jsonl
coverage-report.v0.1.json
quality-report.v0.1.json
lag-report.v0.1.json
network-ledger.v0.1.json
notification-ledger.v0.1.jsonl
raw-responses.cms
raw-retention.v0.1.json
final-result.json
```

## Pass and fail

The final verifier never edits thresholds. It applies the committed plan to the retained evidence and emits exactly one of:

```text
O01_QUALITY_COVERAGE_LAG_PASS
O01_QUALITY_COVERAGE_LAG_FAIL
```

Minimum mandatory criteria:

```text
SAMPLE_FROZEN                       = true
RAW_RESPONSES_RETAINED_SECURELY     = true
QUALITY_REPORT_COMPLETE             = true
LAG_REPORT_COMPLETE                 = true
COVERAGE_LIMITATIONS_DISCLOSED      = true
FABRICATED_EVIDENCE                 = 0
```

A FAIL remains valid evidence and must not be rewritten as a PASS by changing the sample or thresholds after execution.
