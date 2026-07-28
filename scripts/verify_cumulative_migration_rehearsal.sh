#!/usr/bin/env bash
set -euo pipefail

service="${AXIGNAL_POSTGRES_SERVICE:-postgres}"
rehearsal_db="${AXIGNAL_MIGRATION_REHEARSAL_DB:-axignal_migration_rehearsal}"
restore_db="${AXIGNAL_MIGRATION_RESTORE_DB:-axignal_migration_restore}"
dump_file="$(mktemp -t axignal-pre-migration-XXXXXX.dump)"

compose() {
  docker compose "$@"
}

admin_psql() {
  local database="$1"
  shift
  compose exec -T "$service" psql \
    -U axignal \
    -d "$database" \
    -v ON_ERROR_STOP=1 \
    "$@"
}

query_scalar() {
  local database="$1"
  local sql="$2"
  admin_psql "$database" -Atc "$sql"
}

cleanup() {
  compose exec -T "$service" dropdb -U axignal --if-exists --force "$rehearsal_db" >/dev/null 2>&1 || true
  compose exec -T "$service" dropdb -U axignal --if-exists --force "$restore_db" >/dev/null 2>&1 || true
  rm -f "$dump_file"
}
trap cleanup EXIT

for database in "$rehearsal_db" "$restore_db"; do
  compose exec -T "$service" dropdb -U axignal --if-exists --force "$database" >/dev/null
  compose exec -T "$service" createdb -U axignal "$database"
done

# Reconstruct the last stable database shape before proposal/admission migrations.
admin_psql "$rehearsal_db" < infra/postgres/init.sql
admin_psql "$rehearsal_db" < infra/postgres/020-research-spine.sql

admin_psql "$rehearsal_db" <<'SQL'
INSERT INTO axignal_global.source_objects (
  source_object_id,
  source_id,
  retrieval_key,
  request_url,
  retrieved_at,
  http_status,
  content_type,
  content_hash,
  raw_payload,
  rights_snapshot,
  lineage
) VALUES (
  '00000000-0000-0000-0000-000000000101',
  'world-bank-wdi',
  'migration-rehearsal-source-object',
  'https://api.worldbank.org/v2/country/RUS/indicator/FP.CPI.TOTL.ZG',
  '2026-07-27T00:00:00Z',
  200,
  'application/json',
  'sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
  '{"value": 2.3, "period": "2018"}'::jsonb,
  '{"rights_status": "COMMERCIAL_REUSE_WITH_ATTRIBUTION", "license_id": "CC-BY-4.0"}'::jsonb,
  '{"fixture": "migration-rehearsal"}'::jsonb
);

INSERT INTO axignal_global.evidence_objects (
  evidence_id,
  source_object_id,
  source_id,
  evidence_key,
  title,
  relationship,
  subject_id,
  predicate,
  observed_at,
  numeric_value,
  unit,
  payload,
  content_hash,
  rights_status,
  provisional
) VALUES (
  '00000000-0000-0000-0000-000000000102',
  '00000000-0000-0000-0000-000000000101',
  'world-bank-wdi',
  'migration-rehearsal-evidence',
  'Migration rehearsal evidence',
  'SUPPORT',
  'geo_country_rus',
  'real_gdp_growth_annual_pct',
  '2018-12-31T00:00:00Z',
  2.3,
  'percent_annual',
  '{"value": 2.3, "period": "2018", "unit": "percent_annual"}'::jsonb,
  'sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',
  'COMMERCIAL_REUSE_WITH_ATTRIBUTION',
  true
);

INSERT INTO axignal_global.candidate_claims (
  candidate_claim_id,
  fingerprint,
  opportunity_id,
  subject_id,
  predicate,
  object_value,
  statement,
  kind,
  state,
  evidence_ids,
  producer_type,
  producer_id,
  method_version
) VALUES (
  '00000000-0000-0000-0000-000000000103',
  'sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
  'opp_migration_rehearsal',
  'geo_country_rus',
  'real_gdp_growth_annual_pct',
  '{"value": 2.3, "period": "2018", "unit": "percent_annual"}'::jsonb,
  'Real GDP growth was 2.3 percent in 2018.',
  'FACT',
  'ADMISSION_QUEUED',
  ARRAY['00000000-0000-0000-0000-000000000102'::uuid],
  'DETERMINISTIC_PARSER',
  'migration-rehearsal-parser',
  'migration-rehearsal@0.1.0'
);

INSERT INTO tenant_private.research_runs (
  research_run_id,
  tenant_id,
  context_id,
  opportunity_id,
  question,
  state,
  source_plan,
  budgets,
  actual_usage,
  evidence_ids,
  candidate_claim_ids
) VALUES (
  '00000000-0000-0000-0000-000000000104',
  '00000000-0000-0000-0000-000000000200',
  'ctx_migration_rehearsal',
  'opp_migration_rehearsal',
  'Verify cumulative migrations preserve existing governed research data.',
  'ADMISSION_PENDING',
  '[{"source_id": "world-bank-wdi"}]'::jsonb,
  '{"max_api_requests": 1}'::jsonb,
  '{"api_requests": 1}'::jsonb,
  ARRAY['00000000-0000-0000-0000-000000000102'::uuid],
  ARRAY['00000000-0000-0000-0000-000000000103'::uuid]
);
SQL

# Capture a restorable pre-025 snapshot before applying the accumulated migrations.
compose exec -T "$service" pg_dump \
  -U axignal \
  -d "$rehearsal_db" \
  --format=custom \
  --no-owner \
  --no-privileges > "$dump_file"

after_baseline_count="$(query_scalar "$rehearsal_db" "SELECT count(*) FROM tenant_private.research_runs WHERE research_run_id = '00000000-0000-0000-0000-000000000104';")"
test "$after_baseline_count" = "1"

migrations=(
  infra/postgres/025-research-runtime-grants.sql
  infra/postgres/030-proposal-worker-boundary.sql
  infra/postgres/035-deterministic-admission-runtime.sql
)

for migration in "${migrations[@]}"; do
  admin_psql "$rehearsal_db" < "$migration"
done

# Reapply the same sequence to prove idempotent deployment/restart behaviour.
for migration in "${migrations[@]}"; do
  admin_psql "$rehearsal_db" < "$migration"
done

test "$(query_scalar "$rehearsal_db" "SELECT count(*) FROM axignal_global.source_objects WHERE source_object_id = '00000000-0000-0000-0000-000000000101';")" = "1"
test "$(query_scalar "$rehearsal_db" "SELECT count(*) FROM axignal_global.evidence_objects WHERE evidence_id = '00000000-0000-0000-0000-000000000102' AND numeric_value = 2.3;")" = "1"
test "$(query_scalar "$rehearsal_db" "SELECT count(*) FROM axignal_global.candidate_claims WHERE candidate_claim_id = '00000000-0000-0000-0000-000000000103' AND state = 'ADMISSION_QUEUED';")" = "1"
test "$(query_scalar "$rehearsal_db" "SELECT count(*) FROM tenant_private.research_runs WHERE research_run_id = '00000000-0000-0000-0000-000000000104' AND job_kind = 'STRUCTURED_SOURCE_OBSERVATION' AND state = 'ADMISSION_PENDING';")" = "1"
test "$(query_scalar "$rehearsal_db" "SELECT to_regclass('axignal_global.document_fragments') IS NOT NULL;")" = "t"
test "$(query_scalar "$rehearsal_db" "SELECT to_regclass('axignal_global.admission_decisions') IS NOT NULL;")" = "t"
test "$(query_scalar "$rehearsal_db" "SELECT has_table_privilege('axignal_proposal_worker', 'axignal_global.canonical_claims', 'INSERT');")" = "f"
test "$(query_scalar "$rehearsal_db" "SELECT has_table_privilege('axignal_admission_runtime_login', 'axignal_global.evidence_objects', 'UPDATE');")" = "f"
test "$(query_scalar "$rehearsal_db" "SELECT rolcanlogin FROM pg_roles WHERE rolname = 'axignal_admission_runtime_login';")" = "t"

# Restore the pre-migration snapshot into a clean database. This is the tested
# rollback mechanism until production-specific down migrations are authorised.
compose exec -T "$service" pg_restore \
  -U axignal \
  -d "$restore_db" \
  --no-owner \
  --no-privileges < "$dump_file"

test "$(query_scalar "$restore_db" "SELECT count(*) FROM tenant_private.research_runs WHERE research_run_id = '00000000-0000-0000-0000-000000000104';")" = "1"
test "$(query_scalar "$restore_db" "SELECT to_regclass('axignal_global.document_fragments') IS NULL;")" = "t"
test "$(query_scalar "$restore_db" "SELECT to_regclass('axignal_global.admission_decisions') IS NULL;")" = "t"
test "$(query_scalar "$restore_db" "SELECT NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'tenant_private' AND table_name = 'research_runs' AND column_name = 'job_kind');")" = "t"

cat <<'JSON'
{
  "baseline_snapshot_created": true,
  "cumulative_migrations_applied": [25, 30, 35],
  "migration_replay_idempotent": true,
  "seeded_data_preserved": true,
  "proposal_worker_canonical_insert": false,
  "admission_runtime_evidence_update": false,
  "snapshot_restore_verified": true,
  "partial_state_detected": false
}
JSON
