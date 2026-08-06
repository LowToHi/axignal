#!/usr/bin/env bash
set -Eeuo pipefail

service="${AXIGNAL_POSTGRES_SERVICE:-postgres}"
run_suffix="${GITHUB_RUN_ID:-$$}"
run_suffix="${run_suffix//[^0-9A-Za-z]/}"
run_suffix="${run_suffix:0:12}"
work_dir="$(mktemp -d -t axignal-full-migration-matrix-XXXXXX)"
declared_databases=()

compose() {
  docker compose "$@"
}

postgres_exec() {
  compose exec -T "$service" "$@"
}

create_database() {
  local database="$1"
  postgres_exec createdb -U axignal "$database"
  declared_databases+=("$database")
}

drop_database() {
  local database="$1"
  postgres_exec dropdb -U axignal --if-exists --force "$database" >/dev/null 2>&1 || true
}

psql_database() {
  local database="$1"
  shift
  compose exec -T "$service" psql \
    -X \
    -U axignal \
    -d "$database" \
    -v ON_ERROR_STOP=1 \
    "$@"
}

scalar() {
  local database="$1"
  local sql="$2"
  psql_database "$database" -Atc "$sql"
}

cleanup() {
  local database
  for database in "${declared_databases[@]}"; do
    drop_database "$database"
  done
  rm -rf "$work_dir"
}
trap cleanup EXIT

mapfile -t migration_entries < <(
  awk '
    $1 == "COPY" && $2 ~ /[.]sql$/ && $3 ~ /^[/]docker-entrypoint-initdb[.]d[/]/ {
      print "infra/postgres/" $2 "|" $3
    }
  ' infra/postgres/Dockerfile
)

if (( ${#migration_entries[@]} < 20 )); then
  echo "Expected at least 20 ordered PostgreSQL migrations in infra/postgres/Dockerfile" >&2
  exit 1
fi

migration_sources=()
migration_targets=()
declare -A seen_sources=()
declare -A seen_targets=()

for entry in "${migration_entries[@]}"; do
  source_path="${entry%%|*}"
  target_path="${entry#*|}"
  target_name="${target_path##*/}"

  if [[ ! -f "$source_path" ]]; then
    echo "Migration declared by Dockerfile does not exist: $source_path" >&2
    exit 1
  fi
  if [[ -n "${seen_sources[$source_path]:-}" ]]; then
    echo "Duplicate migration source in Dockerfile: $source_path" >&2
    exit 1
  fi
  if [[ -n "${seen_targets[$target_name]:-}" ]]; then
    echo "Duplicate migration target in Dockerfile: $target_name" >&2
    exit 1
  fi

  seen_sources[$source_path]=1
  seen_targets[$target_name]=1
  migration_sources+=("$source_path")
  migration_targets+=("$target_name")
done

actual_order="$(printf '%s\n' "${migration_targets[@]}")"
sorted_order="$(printf '%s\n' "${migration_targets[@]}" | LC_ALL=C sort)"
if [[ "$actual_order" != "$sorted_order" ]]; then
  echo "PostgreSQL Docker init migrations are not lexicographically ordered" >&2
  diff -u <(printf '%s\n' "$sorted_order") <(printf '%s\n' "$actual_order") || true
  exit 1
fi

supported_checkpoints=(
  "020-axignal-research-spine.sql"
  "043-axignal-human-review-grants.sql"
  "050-axignal-f2-runtime-spine.sql"
  "070-axignal-ted-product-runtime.sql"
  "082-axignal-entitlement-expiry-sweep.sql"
  "091-axignal-retention-pgcrypto-boundary.sql"
  "100-axignal-stripe-paid-lifecycle.sql"
  "110-axignal-seat-governance.sql"
  "124-axignal-identity-clone-hardening.sql"
  "131-axignal-organic-alerts.sql"
)

for checkpoint in "${supported_checkpoints[@]}"; do
  if [[ -z "${seen_targets[$checkpoint]:-}" ]]; then
    echo "Supported migration checkpoint is missing from Dockerfile: $checkpoint" >&2
    exit 1
  fi
done

apply_range() {
  local database="$1"
  local start_index="$2"
  local end_index="$3"
  local index

  if (( start_index > end_index )); then
    return
  fi

  for (( index = start_index; index <= end_index; index++ )); do
    echo "[$database] applying ${migration_targets[$index]}"
    psql_database "$database" < "${migration_sources[$index]}"
  done
}

schema_fingerprint() {
  local database="$1"
  postgres_exec pg_dump \
    -U axignal \
    -d "$database" \
    --schema-only \
    --no-owner \
    --exclude-schema=axignal_migration_audit \
    | grep -Ev '^(--|SET |SELECT pg_catalog[.]set_config|\\restrict |\\unrestrict |$)' \
    | sha256sum \
    | awk '{print $1}'
}

seed_sentinel() {
  local database="$1"
  local checkpoint="$2"

  psql_database "$database" -v checkpoint="$checkpoint" <<'SQL'
CREATE SCHEMA IF NOT EXISTS axignal_migration_audit;
CREATE TABLE IF NOT EXISTS axignal_migration_audit.sentinels (
  checkpoint text PRIMARY KEY,
  payload jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
INSERT INTO axignal_migration_audit.sentinels (checkpoint, payload)
VALUES (:'checkpoint', jsonb_build_object('preserve', true, 'checkpoint', :'checkpoint'))
ON CONFLICT (checkpoint) DO UPDATE SET payload = EXCLUDED.payload;
SQL

  if [[ "$(scalar "$database" "SELECT to_regclass('axignal_global.sources') IS NOT NULL;")" == "t" ]]; then
    psql_database "$database" -v checkpoint="$checkpoint" <<'SQL'
UPDATE axignal_global.sources
SET config = config || jsonb_build_object('migration_matrix_sentinel', :'checkpoint')
WHERE source_id = 'world-bank-wdi';
SQL
  fi
}

verify_sentinel() {
  local database="$1"
  local checkpoint="$2"

  test "$(scalar "$database" "SELECT count(*) FROM axignal_migration_audit.sentinels WHERE checkpoint = '$checkpoint' AND payload->>'preserve' = 'true';")" = "1"

  if [[ "$(scalar "$database" "SELECT to_regclass('axignal_global.sources') IS NOT NULL;")" == "t" ]]; then
    test "$(scalar "$database" "SELECT count(*) FROM axignal_global.sources WHERE source_id = 'world-bank-wdi' AND config->>'migration_matrix_sentinel' = '$checkpoint';")" = "1"
  fi
}

reference_database="axrc_ref_${run_suffix}"
create_database "$reference_database"
apply_range "$reference_database" 0 "$(( ${#migration_sources[@]} - 1 ))"
reference_fingerprint="$(schema_fingerprint "$reference_database")"

printf '{\n'
printf '  "migration_count": %d,\n' "${#migration_sources[@]}"
printf '  "reference_schema_fingerprint": "%s",\n' "$reference_fingerprint"
printf '  "checkpoints": [\n'

first_result=true
checkpoint_number=0
for checkpoint in "${supported_checkpoints[@]}"; do
  checkpoint_index=-1
  for index in "${!migration_targets[@]}"; do
    if [[ "${migration_targets[$index]}" == "$checkpoint" ]]; then
      checkpoint_index="$index"
      break
    fi
  done

  if (( checkpoint_index < 0 )); then
    echo "Unable to resolve checkpoint index: $checkpoint" >&2
    exit 1
  fi

  checkpoint_number=$(( checkpoint_number + 1 ))
  candidate_database="axrc_m${checkpoint_number}_${run_suffix}"
  restore_database="axrc_r${checkpoint_number}_${run_suffix}"
  snapshot_file="$work_dir/${checkpoint_number}.dump"

  create_database "$candidate_database"
  apply_range "$candidate_database" 0 "$checkpoint_index"
  seed_sentinel "$candidate_database" "$checkpoint"
  prefix_fingerprint="$(schema_fingerprint "$candidate_database")"

  postgres_exec pg_dump \
    -U axignal \
    -d "$candidate_database" \
    --format=custom \
    --no-owner > "$snapshot_file"

  apply_range "$candidate_database" "$(( checkpoint_index + 1 ))" "$(( ${#migration_sources[@]} - 1 ))"
  verify_sentinel "$candidate_database" "$checkpoint"
  upgraded_fingerprint="$(schema_fingerprint "$candidate_database")"

  if [[ "$upgraded_fingerprint" != "$reference_fingerprint" ]]; then
    echo "Final schema mismatch after upgrading from $checkpoint" >&2
    echo "reference=$reference_fingerprint" >&2
    echo "upgraded=$upgraded_fingerprint" >&2
    exit 1
  fi

  create_database "$restore_database"
  postgres_exec pg_restore \
    -U axignal \
    -d "$restore_database" \
    --exit-on-error \
    --no-owner < "$snapshot_file"

  verify_sentinel "$restore_database" "$checkpoint"
  restored_fingerprint="$(schema_fingerprint "$restore_database")"
  if [[ "$restored_fingerprint" != "$prefix_fingerprint" ]]; then
    echo "Snapshot restore schema mismatch for $checkpoint" >&2
    echo "before_snapshot=$prefix_fingerprint" >&2
    echo "after_restore=$restored_fingerprint" >&2
    exit 1
  fi

  if [[ "$first_result" == "false" ]]; then
    printf ',\n'
  fi
  first_result=false
  printf '    {"checkpoint": "%s", "upgrade_to_head": true, "schema_equivalent": true, "authority_grants_equivalent": true, "sentinel_preserved": true, "snapshot_restore": true}' "$checkpoint"

  drop_database "$candidate_database"
  drop_database "$restore_database"
  rm -f "$snapshot_file"
done

printf '\n  ],\n'
printf '  "all_supported_paths_passed": true\n'
printf '}\n'
