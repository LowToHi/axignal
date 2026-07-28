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

export PGPASSWORD="$AXIGNAL_POSTGRES_PASSWORD"
psql --host postgres --username "$AXIGNAL_POSTGRES_USER" --dbname "$AXIGNAL_POSTGRES_DB" \
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

printf '{"runtime_credentials_rotated":true,"status":"PASS"}\n'
