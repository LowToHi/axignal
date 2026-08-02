# O01-A — Official online baseline

## Purpose

Establish the first retained online baseline for the official legal and technical
sources governing `AX-LIB-O01`. This phase creates evidence that human Legal and
Privacy/Data Rights authorities may review. It does not create their decisions.

## Scheduled flow

```text
scheduled workflow
→ exact-head checkout
→ allowlisted HTTPS retrieval
→ public-IP DNS validation and pinned TLS connection
→ bounded redirects, timeout and response size
→ normalized visible content
→ critical legal anchors
→ SHA-256 digests
→ retained online package
→ bounded evidence expiry
→ deduplicated notification
```

The governed documents are:

1. TED legal notice;
2. TED Search API 3.0 documentation;
3. Commission Decision 2011/833/EU on EUR-Lex.

## SSRF and retrieval boundary

Every request must satisfy all of the following:

- scheme is `https`;
- host is exactly allowlisted;
- port is `443`;
- URL credentials are absent;
- every DNS answer is globally routable;
- mixed public/private DNS answers are rejected;
- the TLS socket is connected to a validated address while certificate and SNI
  validation remain bound to the official hostname;
- redirects are followed manually, revalidated and limited to three;
- proxy environment variables are not used;
- response size is at most 5 MiB;
- timeout is at most 20 seconds;
- automation-challenge pages fail closed.

## Evidence package

The retained artifact contains:

- exact head SHA and Git tree;
- requested and final official URLs;
- publisher identity;
- observed timestamp;
- HTTP and content-type metadata;
- normalized content files;
- normalized-content SHA-256 digests;
- legal-anchor counts;
- validated and selected public network addresses;
- baseline package and artifact digest;
- calculated evidence expiry;
- material-change classification.

The first valid online observation is classified as
`BASELINE_ESTABLISHED`. Later observations are classified as
`NO_MATERIAL_CHANGE` or `MATERIAL_TERMS_CHANGE` by comparing normalized-content
hashes with the most recent unexpired default-branch artifact.

## Expiry

Evidence freshness is thirty days. The artifact is retained for thirty days,
but evidence expiry is capped three days earlier. Therefore the maximum
baseline validity is twenty-seven days from observation and never outlives its
retained artifact.

## Authority boundary

```text
OFFICIAL_ONLINE_BASELINE     evidence only
LEGAL approval               not generated
PRIVACY_DATA_RIGHTS approval not generated
human signature              not generated
source admission             false
campaign authority           false
public launch                NO_GO
```

A passing workflow returns:

```text
O01_OFFICIAL_BASELINE_PASS
```
