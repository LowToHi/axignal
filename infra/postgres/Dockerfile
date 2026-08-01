FROM pgvector/pgvector:pg17@sha256:7ae6051efd0e60444282c27c7e141af07f322ce033300e727a49c3dd11075e38 AS pgvector

FROM postgis/postgis:17-3.5@sha256:77e89c11c4779c394ebeeaac1099dafb77b728abc8cd45dcaf6c4695503a0c37

COPY --from=pgvector /usr/lib/postgresql/17/lib/vector.so /usr/lib/postgresql/17/lib/vector.so
COPY --from=pgvector /usr/share/postgresql/17/extension/vector.control /usr/share/postgresql/17/extension/vector.control
COPY --from=pgvector /usr/share/postgresql/17/extension/vector--*.sql /usr/share/postgresql/17/extension/

COPY init.sql /docker-entrypoint-initdb.d/010-axignal-extensions.sql
COPY 020-research-spine.sql /docker-entrypoint-initdb.d/020-axignal-research-spine.sql
COPY 025-research-runtime-grants.sql /docker-entrypoint-initdb.d/025-axignal-research-runtime-grants.sql
COPY 030-proposal-worker-boundary.sql /docker-entrypoint-initdb.d/030-axignal-proposal-worker.sql
COPY 035-deterministic-admission-runtime.sql /docker-entrypoint-initdb.d/035-axignal-admission-runtime.sql
COPY 040-bounded-human-review.sql /docker-entrypoint-initdb.d/040-axignal-bounded-human-review.sql
COPY 041-human-review-read-functions.sql /docker-entrypoint-initdb.d/041-axignal-human-review-read.sql
COPY 042-human-review-resolution.sql /docker-entrypoint-initdb.d/042-axignal-human-review-resolution.sql
COPY 043-human-review-grants.sql /docker-entrypoint-initdb.d/043-axignal-human-review-grants.sql
COPY 050-f2-runtime-spine.sql /docker-entrypoint-initdb.d/050-axignal-f2-runtime-spine.sql
COPY 060-f1-qualified-user-validation.sql /docker-entrypoint-initdb.d/060-axignal-f1-validation.sql
COPY 061-f1-validation-answer-key-boundary.sql /docker-entrypoint-initdb.d/061-axignal-f1-answer-key-boundary.sql
COPY 062-f1-validation-pgcrypto-boundary.sql /docker-entrypoint-initdb.d/062-axignal-f1-pgcrypto-boundary.sql
COPY 063-f1-controlled-study-export.sql /docker-entrypoint-initdb.d/063-axignal-f1-controlled-study-export.sql
COPY 070-ted-product-runtime.sql /docker-entrypoint-initdb.d/070-axignal-ted-product-runtime.sql
COPY 080-entitlement-token-ledger.sql /docker-entrypoint-initdb.d/080-axignal-entitlement-token-ledger.sql
COPY 081-entitlement-ledger-hardening.sql /docker-entrypoint-initdb.d/081-axignal-entitlement-ledger-hardening.sql
COPY 082-entitlement-expiry-sweep.sql /docker-entrypoint-initdb.d/082-axignal-entitlement-expiry-sweep.sql
COPY 090-trial-retention-lifecycle.sql /docker-entrypoint-initdb.d/090-axignal-trial-retention-lifecycle.sql
COPY 091-retention-pgcrypto-boundary.sql /docker-entrypoint-initdb.d/091-axignal-retention-pgcrypto-boundary.sql
COPY 100-stripe-paid-lifecycle.sql /docker-entrypoint-initdb.d/100-axignal-stripe-paid-lifecycle.sql
COPY 110-seat-governance.sql /docker-entrypoint-initdb.d/110-axignal-seat-governance.sql
COPY 120-identity-passwordless-core.sql /docker-entrypoint-initdb.d/120-axignal-identity-core.sql
COPY 121-identity-signup-webauthn-challenges.sql /docker-entrypoint-initdb.d/121-axignal-identity-signup.sql
COPY 122-identity-passkeys-sessions-recovery.sql /docker-entrypoint-initdb.d/122-axignal-identity-passkeys.sql
COPY 123-trial-abuse-runtime.sql /docker-entrypoint-initdb.d/123-axignal-trial-abuse.sql
COPY 124-identity-clone-detection-hardening.sql /docker-entrypoint-initdb.d/124-axignal-identity-clone-hardening.sql
COPY 130-organic-discovery-founder-admin.sql /docker-entrypoint-initdb.d/130-axignal-organic-discovery.sql
COPY 131-organic-discovery-alert-lifecycle.sql /docker-entrypoint-initdb.d/131-axignal-organic-alerts.sql
