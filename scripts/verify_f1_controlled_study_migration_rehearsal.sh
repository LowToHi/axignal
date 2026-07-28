#!/usr/bin/env bash
set -euo pipefail

service="${AXIGNAL_POSTGRES_SERVICE:-postgres}"
rehearsal_db="${AXIGNAL_F1_STUDY_MIGRATION_DB:-axignal_f1_study_migration_rehearsal}"
restore_db="${AXIGNAL_F1_STUDY_RESTORE_DB:-axignal_f1_study_migration_restore}"
dump_file="$(mktemp -t axignal-pre-f1-study-XXXXXX.dump)"

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
  infra/postgres/050-f2-runtime-spine.sql
  infra/postgres/060-f1-qualified-user-validation.sql
  infra/postgres/061-f1-validation-answer-key-boundary.sql
  infra/postgres/062-f1-validation-pgcrypto-boundary.sql
)
for migration in "${baseline[@]}"; do psql_db "$rehearsal_db" < "$migration"; done

compose exec -T "$service" pg_dump -U axignal -d "$rehearsal_db" \
  --format=custom --no-owner --no-privileges > "$dump_file"

for pass in 1 2; do
  psql_db "$rehearsal_db" < infra/postgres/063-f1-controlled-study-export.sql
done

test "$(scalar "$rehearsal_db" "SELECT rolcanlogin FROM pg_roles WHERE rolname='axignal_validation_analyst_login';")" = "t"
test "$(scalar "$rehearsal_db" "SELECT has_table_privilege('axignal_validation_analyst_login','evaluation.validation_sessions','SELECT');")" = "f"
test "$(scalar "$rehearsal_db" "SELECT has_table_privilege('axignal_validation_analyst_login','axignal_global.canonical_claims','INSERT');")" = "f"
test "$(scalar "$rehearsal_db" "SELECT has_function_privilege('axignal_validation_analyst_login','evaluation.export_validation_study(uuid,text)','EXECUTE');")" = "t"

compose exec -T "$service" pg_restore -U axignal -d "$restore_db" \
  --no-owner --no-privileges < "$dump_file"
test "$(scalar "$restore_db" "SELECT to_regprocedure('evaluation.export_validation_study(uuid,text)') IS NULL;")" = "t"
test "$(scalar "$restore_db" "SELECT to_regclass('evaluation.validation_sessions') IS NOT NULL;")" = "t"

cat <<'JSON'
{
  "f1_controlled_study_migration_applied": 63,
  "migration_replay_idempotent": true,
  "analyst_role_separated": true,
  "analyst_direct_table_read": false,
  "analyst_canonical_insert": false,
  "analyst_export_function_execute": true,
  "pre_063_snapshot_restore_verified": true,
  "partial_state_detected": false
}
JSON
