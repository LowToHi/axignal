#!/usr/bin/env bash
set -euo pipefail

service="${AXIGNAL_POSTGRES_SERVICE:-postgres}"
run_suffix="${GITHUB_RUN_ID:-$$}"

compose() { docker compose "$@"; }
psql_db() {
  local database="$1"; shift
  compose exec -T "$service" psql -U axignal -d "$database" -v ON_ERROR_STOP=1 "$@"
}
scalar() {
  local database="$1"
  local sql="$2"
  psql_db "$database" -Atc "$sql"
}

migrations=(
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
  infra/postgres/070-ted-product-runtime.sql
  infra/postgres/080-entitlement-token-ledger.sql
  infra/postgres/081-entitlement-ledger-hardening.sql
  infra/postgres/082-entitlement-expiry-sweep.sql
  infra/postgres/090-trial-retention-lifecycle.sql
  infra/postgres/091-retention-pgcrypto-boundary.sql
  infra/postgres/100-stripe-paid-lifecycle.sql
  infra/postgres/110-seat-governance.sql
  infra/postgres/120-identity-passwordless-core.sql
  infra/postgres/121-identity-signup-webauthn-challenges.sql
  infra/postgres/122-identity-passkeys-sessions-recovery.sql
  infra/postgres/123-trial-abuse-runtime.sql
  infra/postgres/124-identity-clone-detection-hardening.sql
  infra/postgres/130-organic-discovery-founder-admin.sql
  infra/postgres/131-organic-discovery-alert-lifecycle.sql
)

# These checkpoints represent material historical database shapes. Each path is
# restored from a snapshot at that checkpoint and then upgraded to HEAD.
checkpoints=(1 8 9 14 18 21 26 27)
checkpoint_labels=(020 043 050 070 090 110 124 130)

created_databases=()
created_dumps=()
cleanup() {
  for database in "${created_databases[@]:-}"; do
    compose exec -T "$service" dropdb -U axignal --if-exists --force "$database" >/dev/null 2>&1 || true
  done
  for dump_file in "${created_dumps[@]:-}"; do
    rm -f "$dump_file"
  done
}
trap cleanup EXIT

assert_source_anchor() {
  local database="$1"
  test "$(scalar "$database" "SELECT count(*) FROM axignal_global.sources WHERE source_id='world-bank-wdi';")" = "1"
}

assert_head_schema() {
  local database="$1"
  test "$(scalar "$database" "SELECT to_regclass('axignal_global.scheduled_jobs') IS NOT NULL;")" = "t"
  test "$(scalar "$database" "SELECT to_regclass('tenant_private.billing_selections') IS NOT NULL;")" = "t"
  test "$(scalar "$database" "SELECT to_regclass('tenant_private.seat_assignments') IS NOT NULL;")" = "t"
  test "$(scalar "$database" "SELECT to_regclass('identity_private.users') IS NOT NULL;")" = "t"
  test "$(scalar "$database" "SELECT to_regclass('identity_private.identity_sessions') IS NOT NULL;")" = "t"
  test "$(scalar "$database" "SELECT to_regclass('growth_private.seo_page_candidates') IS NOT NULL;")" = "t"
  test "$(scalar "$database" "SELECT to_regclass('growth_private.alert_subscriptions') IS NOT NULL;")" = "t"
  assert_source_anchor "$database"
}

apply_range() {
  local database="$1"
  local start_index="$2"
  local end_index="$3"
  local index
  for ((index=start_index; index<=end_index; index++)); do
    psql_db "$database" < "${migrations[$index]}"
  done
}

# Validate that the migration manifest and the PostgreSQL image initialization
# order cannot silently diverge.
mapfile -t dockerfile_migrations < <(
  sed -nE 's|^COPY ([^ ]+\.sql) /docker-entrypoint-initdb\.d/[^ ]+$|infra/postgres/\1|p' \
    infra/postgres/Dockerfile
)
test "${#dockerfile_migrations[@]}" = "${#migrations[@]}"
for index in "${!migrations[@]}"; do
  test "${dockerfile_migrations[$index]}" = "${migrations[$index]}"
  test -f "${migrations[$index]}"
done

# Fresh database to HEAD proves the complete chain independently from Docker's
# entrypoint mechanism.
fresh_db="axignal_full_chain_${run_suffix}"
created_databases+=("$fresh_db")
compose exec -T "$service" createdb -U axignal "$fresh_db"
apply_range "$fresh_db" 0 "$((${#migrations[@]} - 1))"
assert_head_schema "$fresh_db"

validated_paths=()
for matrix_index in "${!checkpoints[@]}"; do
  checkpoint="${checkpoints[$matrix_index]}"
  label="${checkpoint_labels[$matrix_index]}"
  source_db="axignal_upgrade_${label}_${run_suffix}"
  restored_db="axignal_upgrade_${label}_restored_${run_suffix}"
  dump_file="$(mktemp -t "axignal-upgrade-${label}-XXXXXX.dump")"
  created_databases+=("$source_db" "$restored_db")
  created_dumps+=("$dump_file")

  compose exec -T "$service" createdb -U axignal "$source_db"
  compose exec -T "$service" createdb -U axignal "$restored_db"

  apply_range "$source_db" 0 "$checkpoint"
  assert_source_anchor "$source_db"

  compose exec -T "$service" pg_dump \
    -U axignal \
    -d "$source_db" \
    --format=custom \
    --no-owner \
    --no-privileges > "$dump_file"

  compose exec -T "$service" pg_restore \
    -U axignal \
    -d "$restored_db" \
    --no-owner \
    --no-privileges < "$dump_file"

  assert_source_anchor "$restored_db"
  if (( checkpoint + 1 < ${#migrations[@]} )); then
    apply_range "$restored_db" "$((checkpoint + 1))" "$((${#migrations[@]} - 1))"
  fi
  assert_head_schema "$restored_db"
  validated_paths+=("${label}->HEAD")
done

printf '{\n'
printf '  "migration_count": %s,\n' "${#migrations[@]}"
printf '  "fresh_database_to_head": true,\n'
printf '  "dockerfile_manifest_matches": true,\n'
printf '  "snapshot_upgrade_paths": ['
for index in "${!validated_paths[@]}"; do
  if (( index > 0 )); then printf ', '; fi
  printf '"%s"' "${validated_paths[$index]}"
done
printf '],\n'
printf '  "source_anchor_preserved": true,\n'
printf '  "head_schema_verified": true,\n'
printf '  "partial_state_detected": false\n'
printf '}\n'
