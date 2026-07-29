# AX-F8-T14 — TED Runtime Security Review

Status: `PASS / PRIVATE-PILOT PRODUCT RUNTIME`

Review date: `2026-07-29`

Review mechanism: independent automated boundary review plus adversarial API, worker and PostgreSQL tests. This record does not claim an external penetration test or public-GA certification.

## Decision

The bounded TED Search profile may run for authenticated private-pilot organisations. Activation is source-specific and does not enable arbitrary institutional sources, public trials, billing, unrestricted browsing or model authority.

## Reviewed chain

```text
authenticated web session
→ short-lived signed server assertion
→ server-resolved tenant
→ request-schema allowlist
→ PostgreSQL FORCE RLS
→ transactional outbox
→ bounded research worker
→ fixed TED HTTPS endpoint and query
→ sanitised non-personal projection
→ deterministic Candidate Claims
→ deterministic canonical admission
→ attributed dossier
```

## Passed controls

- missing, forged and expired identity assertions return `401`;
- identity assertions bind audience, subject, email, tenant, issue time and expiry;
- the maximum assertion lifetime is 300 seconds and signatures use constant-time comparison;
- request bodies reject undeclared fields, including a client-supplied `tenant_id`;
- the tenant comes only from the verified server assertion;
- tenant tables use PostgreSQL `FORCE ROW LEVEL SECURITY`;
- a second tenant receives `404` for the completed ResearchRun;
- application, worker, proposal, admission and review authorities remain separated;
- the user, web process and proposal models cannot write canonical Claims;
- TED uses a fixed HTTPS host, path, query, field allowlist, page and size budget;
- redirects, non-JSON responses, invalid publication identifiers and oversized responses fail closed;
- contact, email, phone and person fields are prohibited;
- tenant-private knowledge is rejected by the TED route;
- raw API redistribution, bulk redistribution and model training are prohibited;
- the workflow flag and source kill switch independently stop execution;
- the source kill switch is evaluated before network retrieval;
- rollback preserves prior append-only evidence and canonical history;
- TED live activation uses `AXIGNAL_TED_LIVE_SOURCES_ENABLED` and does not enable all live sources.

## Residual risk accepted for the private pilot

A valid internal identity assertion can be replayed during its short lifetime. The accepted boundary requires TLS, private backend networking, a trusted web gateway and a maximum assertion lifetime of 300 seconds. Public API exposure, third-party gateway federation and general availability remain prohibited until nonce or request-id replay protection is introduced and independently tested.

The Search API profile is intentionally narrow. It is not authority for complete procurement analysis, supplier eligibility, win probability, profitability, legal conclusions or bid execution.

## Separation of gates

This security decision accepts the runtime for a controlled authenticated pilot. Qualified B2G buyer research, willingness to pay, paid evidence, trial entitlements and public commercial launch remain governed by `AX-F9-T15`; they are not represented as security evidence for `AX-F8-T14`.

## Reproducible evidence

- `scripts/verify_ted_security_review.py`
- `apps/api/tests/test_ted_product_runtime.py`
- `scripts/verify_ted_persistent_e2e.py`
- `scripts/benchmark_ted_product_runtime.py`
- `.github/workflows/ted-product-runtime.yml`

The review fails closed when any required source, identity, tenancy, authority, privacy, export, activation or rollback invariant drifts.
