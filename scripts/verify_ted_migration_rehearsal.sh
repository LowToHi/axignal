#!/usr/bin/env bash
set -euo pipefail

service="${AXIGNAL_POSTGRES_SERVICE:-postgres}"
rehearsal_db="${AXIGNAL_TED_MIGRATION_REHEARSAL_DB:-axignal_ted_migration_rehearsal}"
restore_db="${AXIGNAL_TED_MIGRATION_RESTORE_DB:-axignal_ted_migration_restore}"
dump_file="$(mktemp -t axignal-pre-ted-070-XXXXXX.dump)"

compose() { docker compose "$@"; }
admin_psql() {
  local database="$1"; shift
  compose exec -T "$service" psql -U axignal -d "$database" -v ON_ERROR_STOP=1 "$@"
}
query_scalar() {
  local database="$1" sql="$2"
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

base_migrations=(
  infra/postgres/init.sql
  infra/postgres/020-research-spine.sql
  infra/postgres/025-research-runtime-grants.sql
  infra/postgres/030-proposal-worker-boundary.sql
  infra/postgres/035-deterministic-admission-runtime.sql
  infra/postgres/040-bounded-human-review.sql
  infra/postgres/041-human-review-read-functions.sql
  infra/postgres/042-human-review-resolution.sql
  infra/postgres/043-human-review-grants.sql
  infra/postgres/050-f2-runtime-spine.sql
  infra/postgres/060-f1-qualified-user-validation.sql
  infra/postgres/061-f1-validation-answer-key-boundary.sql
  infra/postgres/062-f1-validation-pgcrypto-boundary.sql
  infra/postgres/063-f1-controlled-study-export.sql
)
for migration in "${base_migrations[@]}"; do
  admin_psql "$rehearsal_db" < "$migration"
done

admin_psql "$rehearsal_db" <<'SQL'
INSERT INTO tenant_private.research_runs (
  research_run_id,
  tenant_id,
  context_id,
  opportunity_id,
  question,
  state,
  source_plan,
  budgets,
  job_kind
) VALUES (
  '70000000-0000-4000-8000-000000000001',
  '70000000-0000-4000-8000-000000000002',
  'ctx_ted_pre070_snapshot',
  'opp_ted_pre070_snapshot',
  'Preserve the pre-070 ResearchRun through migration replay and restore.',
  'QUEUED',
  '[{"source_id":"world-bank-wdi"}]'::jsonb,
  '{"max_api_requests":1}'::jsonb,
  'STRUCTURED_SOURCE_OBSERVATION'
);
SQL

compose exec -T "$service" pg_dump \
  -U axignal -d "$rehearsal_db" --format=custom --no-owner --no-privileges > "$dump_file"

for _ in 1 2; do
  admin_psql "$rehearsal_db" < infra/postgres/070-ted-persistent-source.sql
  admin_psql "$rehearsal_db" < infra/postgres/071-ted-worker-idempotent-replay-grant.sql
done

test "$(query_scalar "$rehearsal_db" "SELECT count(*) FROM tenant_private.research_runs WHERE research_run_id='70000000-0000-4000-8000-000000000001';")" = "1"
test "$(query_scalar "$rehearsal_db" "SELECT to_regclass('axignal_global.procurement_notice_versions') IS NOT NULL;")" = "t"
test "$(query_scalar "$rehearsal_db" "SELECT to_regclass('axignal_global.procurement_retrieval_outbox_events') IS NOT NULL;")" = "t"
test "$(query_scalar "$rehearsal_db" "SELECT to_regclass('axignal_global.procurement_admission_outbox_events') IS NOT NULL;")" = "t"
test "$(query_scalar "$rehearsal_db" "SELECT admission_state='ADMITTED' AND NOT kill_switch FROM axignal_global.sources WHERE source_id='src_ted_search_api_v3';")" = "t"
test "$(query_scalar "$rehearsal_db" "SELECT config->>'product_profile_id'='ted-eforms-non-personal@1.0.0' FROM axignal_global.sources WHERE source_id='src_ted_search_api_v3';")" = "t"
test "$(query_scalar "$rehearsal_db" "SELECT rolcanlogin FROM pg_roles WHERE rolname='axignal_ted_worker';")" = "t"
test "$(query_scalar "$rehearsal_db" "SELECT rolcanlogin FROM pg_roles WHERE rolname='axignal_ted_admission_runtime';")" = "t"
test "$(query_scalar "$rehearsal_db" "SELECT has_table_privilege('axignal_ted_worker','axignal_global.canonical_claims','INSERT');")" = "f"
test "$(query_scalar "$rehearsal_db" "SELECT has_table_privilege('axignal_ted_admission_runtime','axignal_global.evidence_objects','UPDATE');")" = "f"
test "$(query_scalar "$rehearsal_db" "SELECT has_table_privilege('axignal_ted_worker','axignal_global.evidence_objects','INSERT');")" = "t"
test "$(query_scalar "$rehearsal_db" "SELECT has_column_privilege('axignal_ted_worker','axignal_global.candidate_claims','updated_at','UPDATE');")" = "t"
test "$(query_scalar "$rehearsal_db" "SELECT has_column_privilege('axignal_ted_worker','axignal_global.candidate_claims','state','UPDATE');")" = "f"
test "$(query_scalar "$rehearsal_db" "SELECT has_table_privilege('axignal_ted_admission_runtime','axignal_global.canonical_claims','INSERT');")" = "t"

compose exec -T "$service" pg_restore \
  -U axignal -d "$restore_db" --no-owner --no-privileges < "$dump_file"

test "$(query_scalar "$restore_db" "SELECT count(*) FROM tenant_private.research_runs WHERE research_run_id='70000000-0000-4000-8000-000000000001';")" = "1"
test "$(query_scalar "$restore_db" "SELECT to_regclass('axignal_global.procurement_notice_versions') IS NULL;")" = "t"
test "$(query_scalar "$restore_db" "SELECT to_regclass('axignal_global.procurement_retrieval_outbox_events') IS NULL;")" = "t"
test "$(query_scalar "$restore_db" "SELECT to_regclass('axignal_global.procurement_admission_outbox_events') IS NULL;")" = "t"

cat <<'JSON'
{
  "pre_070_snapshot_created": true,
  "migration_070_applied": true,
  "migration_071_applied": true,
  "migration_070_071_replay_idempotent": true,
  "seeded_research_run_preserved": true,
  "ted_worker_candidate_updated_at_only": true,
  "ted_worker_canonical_insert": false,
  "ted_admission_evidence_update": false,
  "pre_070_snapshot_restore_verified": true,
  "partial_state_detected": false
}
JSON
