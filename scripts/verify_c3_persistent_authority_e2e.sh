#!/usr/bin/env bash
set -Eeuo pipefail

service="${AXIGNAL_POSTGRES_SERVICE:-postgres}"
run_suffix="${GITHUB_RUN_ID:-$$}"
run_suffix="${run_suffix//[^0-9A-Za-z]/}"
run_suffix="${run_suffix:0:12}"
database="axrc_c3_${run_suffix}"
restore_database="axrc_c3r_${run_suffix}"
upgrade_database="axrc_c3u_${run_suffix}"
work_dir="$(mktemp -d -t axignal-c3-persistent-authority-XXXXXX)"
snapshot_file="$work_dir/c3-authority.dump"

as_of="2026-08-04T12:00:00Z"
tenant_a="33333333-3333-4333-8333-333333333331"
tenant_b="33333333-3333-4333-8333-333333333332"
encryption_key="c3-test-encryption-key-with-at-least-32-bytes"
origin_schema_migration="140-subscriber-persistent-authority.sql"
final_schema_migration="142-c4-axent-upgrade-hardening.sql"

compose() {
  docker compose "$@"
}

postgres_exec() {
  compose exec -T "$service" "$@"
}

psql_database() {
  local target_database="$1"
  shift
  compose exec -T "$service" psql \
    -X -q -U axignal -d "$target_database" -v ON_ERROR_STOP=1 "$@"
}

scalar() {
  local target_database="$1"
  local sql="$2"
  psql_database "$target_database" -Atc "$sql"
}

tenant_scalar() {
  local target_database="$1"
  local tenant_id="$2"
  local sql="$3"
  psql_database "$target_database" -At <<SQL
BEGIN;
SET LOCAL ROLE axignal_app;
SET LOCAL app.tenant_id = '$tenant_id';
$sql
COMMIT;
SQL
}

tenant_exec() {
  local target_database="$1"
  local tenant_id="$2"
  local sql="$3"
  psql_database "$target_database" <<SQL
BEGIN;
SET LOCAL ROLE axignal_app;
SET LOCAL app.tenant_id = '$tenant_id';
$sql
COMMIT;
SQL
}

retention_scalar() {
  local target_database="$1"
  local sql="$2"
  psql_database "$target_database" -At <<SQL
BEGIN;
SET LOCAL ROLE axignal_retention_worker;
$sql
COMMIT;
SQL
}

expect_tenant_failure() {
  local target_database="$1"
  local tenant_id="$2"
  local expected="$3"
  local sql="$4"
  local output
  set +e
  output="$(tenant_exec "$target_database" "$tenant_id" "$sql" 2>&1)"
  local status=$?
  set -e
  if [[ "$status" -eq 0 ]]; then
    echo "Expected tenant-scoped statement to fail: $expected" >&2
    exit 1
  fi
  grep -F "$expected" <<<"$output" >/dev/null
}

expect_owner_failure() {
  local target_database="$1"
  local expected="$2"
  local sql="$3"
  local output
  set +e
  output="$(psql_database "$target_database" -c "$sql" 2>&1)"
  local status=$?
  set -e
  if [[ "$status" -eq 0 ]]; then
    echo "Expected owner statement to fail: $expected" >&2
    exit 1
  fi
  grep -F "$expected" <<<"$output" >/dev/null
}

apply_migrations() {
  local target_database="$1"
  shift
  local migration
  for migration in "$@"; do
    psql_database "$target_database" < "$migration"
  done
}

canonical_data_hash() {
  local target_database="$1"
  postgres_exec pg_dump -U axignal -d "$target_database" \
    --data-only --inserts --column-inserts --no-owner --no-privileges |
    awk '
      /^--/ { next }
      /^SET / { next }
      /^SELECT pg_catalog[.]set_config/ { next }
      /^\\restrict / { next }
      /^\\unrestrict / { next }
      NF { print }
    ' |
    LC_ALL=C sort |
    sha256sum |
    awk '{print $1}'
}

canonical_schema_authority_hash() {
  local target_database="$1"
  postgres_exec pg_dump -U axignal -d "$target_database" \
    --schema-only --no-owner |
    awk '
      /^--/ { next }
      /^SET / { next }
      /^SELECT pg_catalog[.]set_config/ { next }
      /^\\restrict / { next }
      /^\\unrestrict / { next }
      NF { print }
    ' |
    sha256sum |
    awk '{print $1}'
}

require_equal() {
  local label="$1"
  local left="$2"
  local right="$3"
  if [[ "$left" != "$right" ]]; then
    printf '%s drifted\n%s\n!=\n%s\n' "$label" "$left" "$right" >&2
    exit 1
  fi
}

assert_origin_authority() {
  local target_database="$1"
  test "$(scalar "$target_database" "
SELECT has_function_privilege(
  'axignal_app',
  'tenant_private.create_axent_conversation(text,text,text,text,timestamptz)'::regprocedure,
  'EXECUTE'
);")" = "t"
  test "$(scalar "$target_database" "
SELECT to_regprocedure(
  'tenant_private.create_axent_conversation_idempotent(text,text,text,text,text,timestamptz)'
) IS NULL;")" = "t"
}

assert_final_authority() {
  local target_database="$1"
  test "$(scalar "$target_database" "
SELECT
  NOT has_function_privilege(
    'axignal_app',
    'tenant_private.create_axent_conversation(text,text,text,text,timestamptz)'::regprocedure,
    'EXECUTE'
  )
  AND NOT has_function_privilege(
    'axignal_app',
    'tenant_private.append_axent_message(uuid,text,text,text,text,timestamptz)'::regprocedure,
    'EXECUTE'
  )
  AND NOT has_function_privilege(
    'axignal_app',
    'tenant_private.export_axent_conversation(uuid,text,text,timestamptz)'::regprocedure,
    'EXECUTE'
  )
  AND NOT has_function_privilege(
    'axignal_app',
    'tenant_private.request_axent_conversation_deletion(uuid,timestamptz,text,timestamptz)'::regprocedure,
    'EXECUTE'
  )
  AND has_function_privilege(
    'axignal_app',
    'tenant_private.create_axent_conversation_idempotent(text,text,text,text,text,timestamptz)'::regprocedure,
    'EXECUTE'
  )
  AND has_function_privilege(
    'axignal_app',
    'tenant_private.append_axent_message_idempotent(uuid,text,text,text,text,text,text,timestamptz)'::regprocedure,
    'EXECUTE'
  )
  AND has_function_privilege(
    'axignal_app',
    'tenant_private.list_axent_conversations(text,integer)'::regprocedure,
    'EXECUTE'
  )
  AND has_function_privilege(
    'axignal_app',
    'tenant_private.export_axent_conversation_for_identity(uuid,text,text,text,timestamptz)'::regprocedure,
    'EXECUTE'
  )
  AND has_function_privilege(
    'axignal_app',
    'tenant_private.request_axent_conversation_deletion_for_identity(uuid,text,timestamptz,text,timestamptz)'::regprocedure,
    'EXECUTE'
  );")" = "t"
}

cleanup() {
  postgres_exec dropdb -U axignal --if-exists --force "$upgrade_database" >/dev/null 2>&1 || true
  postgres_exec dropdb -U axignal --if-exists --force "$restore_database" >/dev/null 2>&1 || true
  postgres_exec dropdb -U axignal --if-exists --force "$database" >/dev/null 2>&1 || true
  rm -rf "$work_dir"
}
trap cleanup EXIT

postgres_exec createdb -U axignal "$database"
mapfile -t migrations < <(
  awk '
    $1 == "COPY" && $2 ~ /[.]sql$/ && $3 ~ /^[/]docker-entrypoint-initdb[.]d[/]/ {
      print "infra/postgres/" $2
    }
  ' infra/postgres/Dockerfile
)

origin_migrations=()
forward_migrations=()
for migration in "${migrations[@]}"; do
  migration_name="${migration##*/}"
  migration_number="${migration_name%%-*}"
  if [[ ! "$migration_number" =~ ^[0-9]+$ ]]; then
    echo "C3 migration has no numeric prefix: $migration" >&2
    exit 1
  fi
  migration_number=$((10#$migration_number))
  if (( migration_number <= 140 )); then
    origin_migrations+=("$migration")
  elif (( migration_number <= 142 )); then
    forward_migrations+=("$migration")
  else
    echo "C3 comparator does not admit migration beyond 142: $migration" >&2
    exit 1
  fi
done

test "${origin_migrations[-1]##*/}" = "$origin_schema_migration"
test "${#forward_migrations[@]}" = "2"
test "${forward_migrations[0]##*/}" = "141-c4-axent-idempotency.sql"
test "${forward_migrations[1]##*/}" = "$final_schema_migration"

apply_migrations "$database" "${origin_migrations[@]}"
assert_origin_authority "$database"

psql_database "$database" <<SQL
INSERT INTO tenant_private.workspace_lifecycle (
  tenant_id, state, policy_version, created_at, updated_at
) VALUES
  ('$tenant_a', 'ACTIVE', 'c3-persistent-authority@1.0.0', '$as_of', '$as_of'),
  ('$tenant_b', 'ACTIVE', 'c3-persistent-authority@1.0.0', '$as_of', '$as_of');
SQL

workspace_id="$(tenant_scalar "$database" "$tenant_a" "
SELECT workspace_id
FROM tenant_private.create_subscriber_workspace(
  'opp-c3-main', 'C3 authoritative bid workspace',
  '$as_of'::timestamptz + interval '10 days',
  'usr-owner', '$as_of'
);")"

requirement_id="$(tenant_scalar "$database" "$tenant_a" "
SELECT requirement_id
FROM tenant_private.create_subscriber_requirement(
  '$workspace_id', 'Audited revenue threshold', 'ELIGIBILITY', true,
  'notice:section-III.1', 'usr-owner', '$as_of'
);")"

tenant_exec "$database" "$tenant_a" "
SELECT tenant_private.record_subscriber_decision(
  '$workspace_id', 'PURSUE', 'usr-owner', '$as_of'
);
SELECT tenant_private.set_subscriber_requirement_status(
  '$requirement_id', 'MET', 'usr-owner', '$as_of'
);"

expect_tenant_failure "$database" "$tenant_a" "submission_evidence_insufficient" "
SELECT tenant_private.prepare_subscriber_submission(
  '$workspace_id', 'usr-preparer', '$as_of'
);"

tenant_exec "$database" "$tenant_a" "
SELECT tenant_private.attach_subscriber_evidence(
  '$workspace_id', '$requirement_id', 'Audited accounts FY2025',
  'SUBSCRIBER_DOCUMENT', 'VERIFIED', 'document:audited-accounts-2025',
  'sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
  '$as_of', '$as_of'::timestamptz + interval '365 days',
  'usr-owner', '$as_of'
);"

amendment_id="$(tenant_scalar "$database" "$tenant_a" "
SELECT amendment_id
FROM tenant_private.record_subscriber_amendment(
  '$workspace_id', 'Deadline correction', 'notice:amendment-1',
  '$as_of', 'usr-owner', '$as_of'
);")"

expect_tenant_failure "$database" "$tenant_a" "submission_amendment_acknowledgement_required" "
SELECT tenant_private.prepare_subscriber_submission(
  '$workspace_id', 'usr-preparer', '$as_of'
);"

tenant_exec "$database" "$tenant_a" "
SELECT tenant_private.acknowledge_subscriber_amendment(
  '$amendment_id', 'usr-owner', '$as_of'
);
SELECT tenant_private.prepare_subscriber_submission(
  '$workspace_id', 'usr-preparer', '$as_of'
);"

expect_tenant_failure "$database" "$tenant_a" "submission_separation_of_duties_required" "
SELECT tenant_private.approve_subscriber_submission(
  '$workspace_id', 'usr-preparer', '$as_of'
);"

tenant_exec "$database" "$tenant_a" "
SELECT tenant_private.approve_subscriber_submission(
  '$workspace_id', 'usr-approver', '$as_of'
);"

test "$(tenant_scalar "$database" "$tenant_a" "
SELECT tenant_private.subscriber_workspace_readiness(
  '$workspace_id', '$as_of'
)->>'submission_ready';")" = "true"

tenant_exec "$database" "$tenant_a" "
SELECT tenant_private.set_subscriber_requirement_status(
  '$requirement_id', 'BLOCKED', 'usr-reviewer', '$as_of'
);"

test "$(tenant_scalar "$database" "$tenant_a" "
SELECT tenant_private.subscriber_workspace_readiness(
  '$workspace_id', '$as_of'
)->>'submission_ready';")" = "false"
test "$(scalar "$database" "
SELECT count(*) FROM tenant_private.subscriber_audit_events
WHERE tenant_id = '$tenant_a' AND event_type = 'SUBMISSION_INVALIDATED';")" = "1"

tenant_exec "$database" "$tenant_a" "
SELECT tenant_private.set_subscriber_requirement_status(
  '$requirement_id', 'MET', 'usr-reviewer', '$as_of'
);
SELECT tenant_private.prepare_subscriber_submission(
  '$workspace_id', 'usr-preparer', '$as_of'
);
SELECT tenant_private.approve_subscriber_submission(
  '$workspace_id', 'usr-approver', '$as_of'
);"

for offset in "-1 day" "0 days" "29 days" "30 days"; do
  tenant_exec "$database" "$tenant_a" "
  SELECT tenant_private.create_subscriber_workspace(
    'opp-c3-$offset', 'Deadline boundary $offset',
    '$as_of'::timestamptz + interval '$offset',
    'usr-owner', '$as_of'
  );"
done

test "$(tenant_scalar "$database" "$tenant_a" "
SELECT tenant_private.subscriber_workspace_summary('$as_of')
  ->>'deadlines_next_30_days';")" = "3"

expect_tenant_failure "$database" "$tenant_b" "subscriber_workspace_not_found" "
SELECT tenant_private.subscriber_workspace_readiness(
  '$workspace_id', '$as_of'
);"

expect_owner_failure "$database" "AXIGNAL_C3_LEDGER_APPEND_ONLY" "
UPDATE tenant_private.subscriber_audit_events
SET event_type = 'WORKSPACE_CREATED'
WHERE audit_event_id = (
  SELECT audit_event_id FROM tenant_private.subscriber_audit_events
  WHERE tenant_id = '$tenant_a' ORDER BY event_sequence LIMIT 1
);"

conversation_id="$(tenant_scalar "$database" "$tenant_a" "
SELECT conversation_id
FROM tenant_private.create_axent_conversation(
  'usr-owner', 'C3 retained conversation', 'EPHEMERAL_30D',
  'usr-owner', '$as_of'
);")"

tenant_exec "$database" "$tenant_a" "
SELECT tenant_private.append_axent_message(
  '$conversation_id', 'USER', 'confidential procurement question',
  '$encryption_key', 'usr-owner', '$as_of'
);
SELECT tenant_private.append_axent_message(
  '$conversation_id', 'ASSISTANT', 'proposal-only governed answer',
  '$encryption_key', 'axent', '$as_of'
);"

test "$(scalar "$database" "
SELECT count(*) FROM tenant_private.axent_messages
WHERE tenant_id = '$tenant_a'
  AND position(convert_to('confidential procurement question', 'UTF8') in ciphertext) > 0;")" = "0"

exported="$(tenant_scalar "$database" "$tenant_a" "
SELECT tenant_private.export_axent_conversation(
  '$conversation_id', '$encryption_key', 'usr-exporter', '$as_of'
)::text;")"
grep -F 'confidential procurement question' <<<"$exported" >/dev/null
grep -F 'proposal-only governed answer' <<<"$exported" >/dev/null

expect_tenant_failure "$database" "$tenant_b" "axent_conversation_not_found" "
SELECT tenant_private.export_axent_conversation(
  '$conversation_id', '$encryption_key', 'usr-foreign', '$as_of'
);"

legal_hold_id="$(tenant_scalar "$database" "$tenant_a" "
SELECT legal_hold_id
FROM tenant_private.place_axent_legal_hold(
  '$conversation_id', 'active dispute', 'usr-legal', '$as_of'
);")"

tenant_exec "$database" "$tenant_a" "
SELECT tenant_private.request_axent_conversation_deletion(
  '$conversation_id', '$as_of'::timestamptz + interval '1 day',
  'usr-owner', '$as_of'
);"

test "$(retention_scalar "$database" "
SELECT tenant_private.purge_due_axent_conversations(
  'retention-worker', '$as_of'::timestamptz + interval '31 days'
);")" = "0"

expect_owner_failure "$database" "AXENT_LEGAL_HOLD_ACTIVE" "
BEGIN;
SELECT set_config('app.retention_purge', '1', true);
DELETE FROM tenant_private.workspace_lifecycle WHERE tenant_id = '$tenant_a';
COMMIT;"

postgres_exec pg_dump -U axignal -d "$database" --format=custom --no-owner > "$snapshot_file"
postgres_exec createdb -U axignal "$restore_database"
postgres_exec pg_restore -U axignal -d "$restore_database" --exit-on-error --no-owner < "$snapshot_file"
postgres_exec createdb -U axignal "$upgrade_database"
postgres_exec pg_restore -U axignal -d "$upgrade_database" --exit-on-error --no-owner < "$snapshot_file"

origin_source_data_hash="$(canonical_data_hash "$database")"
origin_restore_data_hash="$(canonical_data_hash "$restore_database")"
origin_source_schema_authority_hash="$(canonical_schema_authority_hash "$database")"
origin_restore_schema_authority_hash="$(canonical_schema_authority_hash "$restore_database")"

require_equal "C3 schema-140 data-plane hash" \
  "$origin_source_data_hash" "$origin_restore_data_hash"
require_equal "C3 schema-140 schema/authority hash" \
  "$origin_source_schema_authority_hash" "$origin_restore_schema_authority_hash"
assert_origin_authority "$restore_database"
assert_origin_authority "$upgrade_database"

test "$(tenant_scalar "$restore_database" "$tenant_a" "
SELECT tenant_private.subscriber_workspace_readiness(
  '$workspace_id', '$as_of'
)->>'submission_ready';")" = "true"
restored_export="$(tenant_scalar "$restore_database" "$tenant_a" "
SELECT tenant_private.export_axent_conversation(
  '$conversation_id', '$encryption_key', 'usr-restore-verifier', '$as_of'
)::text;")"
grep -F 'confidential procurement question' <<<"$restored_export" >/dev/null
test "$(scalar "$restore_database" "
SELECT count(*) FROM tenant_private.axent_legal_holds
WHERE conversation_id = '$conversation_id' AND released_at IS NULL;")" = "1"

apply_migrations "$restore_database" "${forward_migrations[@]}"
apply_migrations "$upgrade_database" "${forward_migrations[@]}"

final_restore_data_hash="$(canonical_data_hash "$restore_database")"
final_upgrade_data_hash="$(canonical_data_hash "$upgrade_database")"
final_restore_schema_authority_hash="$(canonical_schema_authority_hash "$restore_database")"
final_upgrade_schema_authority_hash="$(canonical_schema_authority_hash "$upgrade_database")"

require_equal "C3 schema-142 data-plane hash" \
  "$final_restore_data_hash" "$final_upgrade_data_hash"
require_equal "C3 schema-142 schema/authority hash" \
  "$final_restore_schema_authority_hash" "$final_upgrade_schema_authority_hash"
if [[ "$origin_restore_schema_authority_hash" = "$final_restore_schema_authority_hash" ]]; then
  echo "C3 schema identity did not advance from 140 to 142" >&2
  exit 1
fi
assert_final_authority "$restore_database"
assert_final_authority "$upgrade_database"

tenant_exec "$database" "$tenant_a" "
SELECT tenant_private.release_axent_legal_hold(
  '$legal_hold_id', 'usr-legal', '$as_of'::timestamptz + interval '2 days'
);"

test "$(retention_scalar "$database" "
SELECT tenant_private.purge_due_axent_conversations(
  'retention-worker', '$as_of'::timestamptz + interval '31 days'
);")" = "1"
test "$(scalar "$database" "
SELECT count(*) FROM tenant_private.axent_conversations
WHERE conversation_id = '$conversation_id';")" = "0"
test "$(scalar "$database" "
SELECT count(*) FROM tenant_private.axent_audit_events
WHERE tenant_id = '$tenant_a' AND conversation_id = '$conversation_id'
  AND event_type = 'CONVERSATION_PURGED';")" = "1"

terminal_conversation_id="$(tenant_scalar "$database" "$tenant_a" "
SELECT conversation_id
FROM tenant_private.create_axent_conversation(
  'usr-owner', 'Terminal purge sentinel', 'STANDARD_90D',
  'usr-owner', '$as_of'::timestamptz + interval '32 days'
);")"
tenant_exec "$database" "$tenant_a" "
SELECT tenant_private.append_axent_message(
  '$terminal_conversation_id', 'SYSTEM', 'terminal purge sentinel payload',
  '$encryption_key', 'axent', '$as_of'::timestamptz + interval '32 days'
);
SELECT tenant_private.request_workspace_deletion(
  'usr-owner', '$as_of'::timestamptz + interval '33 days',
  '$as_of'::timestamptz + interval '32 days'
);"

test "$(retention_scalar "$database" "
SELECT tenant_private.queue_due_workspace_purges(
  '$as_of'::timestamptz + interval '34 days'
);")" = "1"

deletion_id="$(retention_scalar "$database" "
SELECT deletion_id
FROM tenant_private.claim_workspace_purge(
  'c3-retention-worker', '$as_of'::timestamptz + interval '34 days', 300
);")"
test -n "$deletion_id"

retention_scalar "$database" "
SELECT deletion_id
FROM tenant_private.purge_claimed_workspace(
  '$deletion_id', 'c3-retention-worker',
  '$as_of'::timestamptz + interval '34 days'
);" >/dev/null

test "$(scalar "$database" "
SELECT count(*) FROM tenant_private.subscriber_workspaces
WHERE tenant_id = '$tenant_a';")" = "0"
test "$(scalar "$database" "
SELECT count(*) FROM tenant_private.axent_conversations
WHERE tenant_id = '$tenant_a';")" = "0"
test "$(scalar "$database" "
SELECT count(*) FROM axignal_global.c3_terminal_purge_receipts
WHERE tenant_hash = 'sha256:' || encode(digest('$tenant_a', 'sha256'), 'hex')
  AND (object_counts->>'subscriber_workspaces')::integer >= 1
  AND (object_counts->>'axent_conversations')::integer = 1;")" = "1"
test "$(scalar "$database" "
SELECT count(*) FROM axignal_global.deletion_tombstones
WHERE deletion_id = '$deletion_id';")" = "1"

event_count="$(scalar "$restore_database" "
SELECT count(*) FROM tenant_private.subscriber_audit_events
WHERE tenant_id = '$tenant_a';")"
message_count="$(scalar "$restore_database" "
SELECT count(*) FROM tenant_private.axent_messages
WHERE tenant_id = '$tenant_a';")"

cat <<JSON
{
  "schema": "axignal.c3-persistent-authority-e2e.v1",
  "status": "PASS",
  "source_database": "$database",
  "restored_database": "$restore_database",
  "workspace_id": "$workspace_id",
  "origin_schema_migration": "$origin_schema_migration",
  "final_schema_migration": "$final_schema_migration",
  "origin_source_data_hash": "$origin_source_data_hash",
  "origin_restored_data_hash": "$origin_restore_data_hash",
  "origin_source_schema_authority_hash": "$origin_source_schema_authority_hash",
  "origin_restored_schema_authority_hash": "$origin_restore_schema_authority_hash",
  "final_restored_data_hash": "$final_restore_data_hash",
  "final_comparison_data_hash": "$final_upgrade_data_hash",
  "final_restored_schema_authority_hash": "$final_restore_schema_authority_hash",
  "final_comparison_schema_authority_hash": "$final_upgrade_schema_authority_hash",
  "same_schema_140_equivalence": "PASS",
  "deterministic_141_142_replay": "PASS",
  "final_authority_contraction": "PASS",
  "consecutive_cycle_comparator": "PASS",
  "evidence_sufficiency_enforced": true,
  "submission_readiness_enforced": true,
  "separation_of_duties_enforced": true,
  "submission_invalidation_audited": true,
  "deadlines_next_30_days_half_open": true,
  "cross_tenant_workspace_access": "DENIED",
  "typed_audit_append_only": true,
  "axent_ciphertext_at_rest": true,
  "axent_export_tenant_scoped": true,
  "axent_legal_hold": "ENFORCED",
  "axent_conversation_deletion": "PASS",
  "terminal_workspace_purge": "PASS",
  "c3_purge_receipt": "PASS",
  "snapshot_restore": "PASS",
  "restored_audit_event_count": $event_count,
  "restored_axent_message_count": $message_count,
  "external_calls": 0,
  "model_calls": 0,
  "public_launch_authorized": false
}
JSON
