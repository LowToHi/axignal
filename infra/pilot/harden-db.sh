#!/usr/bin/env bash
set -euo pipefail

: "${AXIGNAL_POSTGRES_USER:?required}"
: "${AXIGNAL_POSTGRES_DB:?required}"
: "${AXIGNAL_POSTGRES_PASSWORD:?required}"
: "${AXIGNAL_PROPOSAL_DB_PASSWORD:?required}"
: "${AXIGNAL_ADMISSION_DB_PASSWORD:?required}"
: "${AXIGNAL_HUMAN_REVIEW_DB_PASSWORD:?required}"
: "${AXIGNAL_VALIDATION_DB_PASSWORD:?required}"
: "${AXIGNAL_VALIDATION_ANALYST_DB_PASSWORD:?required}"
: "${AXIGNAL_SCHEDULER_DB_PASSWORD:?required}"

max_attempts="${AXIGNAL_DB_HARDENING_MAX_ATTEMPTS:-30}"
retry_seconds="${AXIGNAL_DB_HARDENING_RETRY_SECONDS:-2}"
if ! [[ "$max_attempts" =~ ^[1-9][0-9]*$ ]]; then
  printf '{"status":"FAIL","reason":"invalid_max_attempts"}\n' >&2
  exit 2
fi
if ! [[ "$retry_seconds" =~ ^[1-9][0-9]*$ ]]; then
  printf '{"status":"FAIL","reason":"invalid_retry_seconds"}\n' >&2
  exit 2
fi

export PGPASSWORD="$AXIGNAL_POSTGRES_PASSWORD"
for ((attempt = 1; attempt <= max_attempts; attempt++)); do
  # The official PostgreSQL entrypoint exposes a temporary local server while
  # applying init scripts, then stops it before starting the final TCP server.
  # Compose can observe pg_isready during that temporary phase. Retry the real
  # network transaction so db-hardening cannot fail in the restart window.
  if psql --host postgres --username "$AXIGNAL_POSTGRES_USER" --dbname "$AXIGNAL_POSTGRES_DB" \
    --set=ON_ERROR_STOP=1 \
    --set=proposal_password="$AXIGNAL_PROPOSAL_DB_PASSWORD" \
    --set=admission_password="$AXIGNAL_ADMISSION_DB_PASSWORD" \
    --set=human_review_password="$AXIGNAL_HUMAN_REVIEW_DB_PASSWORD" \
    --set=validation_password="$AXIGNAL_VALIDATION_DB_PASSWORD" \
    --set=validation_analyst_password="$AXIGNAL_VALIDATION_ANALYST_DB_PASSWORD" \
    --set=scheduler_password="$AXIGNAL_SCHEDULER_DB_PASSWORD" <<'SQL'
ALTER ROLE axignal_proposal_worker PASSWORD :'proposal_password';
ALTER ROLE axignal_admission_runtime_login PASSWORD :'admission_password';
ALTER ROLE axignal_human_reviewer_login PASSWORD :'human_review_password';
ALTER ROLE axignal_validation_runtime_login PASSWORD :'validation_password';
ALTER ROLE axignal_validation_analyst_login PASSWORD :'validation_analyst_password';
ALTER ROLE axignal_scheduler_login PASSWORD :'scheduler_password';
SQL
  then
    printf '{"runtime_credentials_rotated":true,"status":"PASS","attempts":%d}\n' "$attempt"
    exit 0
  fi

  if ((attempt == max_attempts)); then
    printf '{"runtime_credentials_rotated":false,"status":"FAIL","reason":"postgres_not_ready","attempts":%d}\n' "$attempt" >&2
    exit 1
  fi
  sleep "$retry_seconds"
done
