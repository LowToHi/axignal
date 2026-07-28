#!/usr/bin/env bash
set -euo pipefail

service="${AXIGNAL_POSTGRES_SERVICE:-postgres}"
rehearsal_db="${AXIGNAL_F2_MIGRATION_DB:-axignal_f2_migration_rehearsal}"
restore_db="${AXIGNAL_F2_RESTORE_DB:-axignal_f2_migration_restore}"
dump_file="$(mktemp -t axignal-pre-f2-XXXXXX.dump)"

compose() { docker compose "$@"; }
psql_db() {
  local database="$1"; shift
  compose exec -T "$service" psql -U axignal -d "$database" -v ON_ERROR_STOP=1 "$@"
}
scalar() { local database="$1"; local sql="$2"; psql_db "$database" -Atc "$sql"; }
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

baseline=(
  infra/postgres/init.sql
  infra/postgres/020-research-spine.sql
  infra/postgres/025-research-runtime-grants.sql
  infra/postgres/030-proposal-worker-boundary.sql
  infra/postgres/035-deterministic-admission-runtime.sql
  infra/postgres/040-bounded-human-review.sql
  infra/postgres/041-human-review-read-functions.sql
  infra/postgres/042-human-review-resolution.sql
  infra/postgres/043-human-review-grants.sql
)
for migration in "${baseline[@]}"; do psql_db "$rehearsal_db" < "$migration"; done

test "$(scalar "$rehearsal_db" "SELECT count(*) FROM axignal_global.sources WHERE source_id='world-bank-wdi';")" = "1"
compose exec -T "$service" pg_dump -U axignal -d "$rehearsal_db" \
  --format=custom --no-owner --no-privileges > "$dump_file"

for pass in 1 2; do psql_db "$rehearsal_db" < infra/postgres/050-f2-runtime-spine.sql; done

test "$(scalar "$rehearsal_db" "SELECT to_regclass('axignal_global.scheduled_jobs') IS NOT NULL;")" = "t"
test "$(scalar "$rehearsal_db" "SELECT to_regclass('axignal_global.scheduler_events') IS NOT NULL;")" = "t"
test "$(scalar "$rehearsal_db" "SELECT rolcanlogin FROM pg_roles WHERE rolname='axignal_scheduler_login';")" = "t"
test "$(scalar "$rehearsal_db" "SELECT has_table_privilege('axignal_scheduler_login','axignal_global.canonical_claims','INSERT');")" = "f"
test "$(scalar "$rehearsal_db" "SELECT has_function_privilege('axignal_scheduler_login','axignal_global.schedule_maintenance_job(text,text,jsonb,uuid,timestamptz,integer,jsonb)','EXECUTE');")" = "t"

first="$(scalar "$rehearsal_db" "SELECT axignal_global.schedule_maintenance_job('VERIFY_RUNTIME_HEALTH','f2-rehearsal-idempotency','{}'::jsonb,NULL,NULL,3,'{}'::jsonb);")"
second="$(scalar "$rehearsal_db" "SELECT axignal_global.schedule_maintenance_job('VERIFY_RUNTIME_HEALTH','f2-rehearsal-idempotency','{}'::jsonb,NULL,NULL,3,'{}'::jsonb);")"
test "$first" = "$second"
test "$(scalar "$rehearsal_db" "SELECT count(*) FROM axignal_global.scheduled_jobs WHERE idempotency_key='f2-rehearsal-idempotency';")" = "1"
test "$(scalar "$rehearsal_db" "SELECT count(*) FROM axignal_global.scheduler_outbox_events WHERE scheduled_job_id='$first';")" = "1"

compose exec -T "$service" pg_restore -U axignal -d "$restore_db" \
  --no-owner --no-privileges < "$dump_file"
test "$(scalar "$restore_db" "SELECT to_regclass('axignal_global.scheduled_jobs') IS NULL;")" = "t"
test "$(scalar "$restore_db" "SELECT count(*) FROM axignal_global.sources WHERE source_id='world-bank-wdi';")" = "1"

cat <<'JSON'
{
  "f2_migration_applied": 50,
  "migration_replay_idempotent": true,
  "scheduler_role_separated": true,
  "scheduler_canonical_insert": false,
  "scheduler_function_execute": true,
  "idempotent_schedule_singleton": true,
  "snapshot_restore_verified": true,
  "partial_state_detected": false
}
JSON
