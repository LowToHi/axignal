#!/usr/bin/env bash
set -euo pipefail

service="${AXIGNAL_POSTGRES_SERVICE:-postgres}"
rehearsal_db="${AXIGNAL_HUMAN_REVIEW_REHEARSAL_DB:-axignal_human_review_rehearsal}"
restore_db="${AXIGNAL_HUMAN_REVIEW_RESTORE_DB:-axignal_human_review_restore}"
dump_file="$(mktemp -t axignal-pre-human-review-XXXXXX.dump)"

compose() { docker compose "$@"; }
admin_psql() {
  local database="$1"
  shift
  compose exec -T "$service" psql -U axignal -d "$database" -v ON_ERROR_STOP=1 "$@"
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

for migration in \
  infra/postgres/init.sql \
  infra/postgres/020-research-spine.sql \
  infra/postgres/025-research-runtime-grants.sql \
  infra/postgres/030-proposal-worker-boundary.sql \
  infra/postgres/035-deterministic-admission-runtime.sql
do
  admin_psql "$rehearsal_db" < "$migration"
done

admin_psql "$rehearsal_db" <<'SQL'
INSERT INTO tenant_private.research_runs (
  research_run_id, tenant_id, context_id, opportunity_id, question, state,
  private_knowledge_authorised, source_plan, budgets, job_kind
) VALUES (
  '10000000-0000-4000-8000-000000000001',
  '10000000-0000-4000-8000-000000000002',
  'ctx_human_review_rehearsal',
  'opp_human_review_rehearsal',
  'Verify bounded human-review migration replay.',
  'HUMAN_REVIEW_REQUIRED',
  false,
  '[{"source_id":"world-bank-rer41"}]'::jsonb,
  '{"max_model_calls":1}'::jsonb,
  'DOCUMENT_PROPOSAL'
);

INSERT INTO axignal_global.source_objects (
  source_object_id, source_id, retrieval_key, request_url, retrieved_at,
  http_status, content_type, content_hash, raw_payload, rights_snapshot, lineage
) VALUES (
  '10000000-0000-4000-8000-000000000003',
  'world-bank-rer41',
  'human-review-rehearsal-source',
  'https://documents.worldbank.org/human-review-rehearsal',
  now(),
  200,
  'application/json',
  'sha256:1111111111111111111111111111111111111111111111111111111111111111',
  '{"text":"National forecasts do not establish Moscow property conditions."}'::jsonb,
  '{"rights_status":"COMMERCIAL_REUSE_WITH_ATTRIBUTION"}'::jsonb,
  '{}'::jsonb
);

INSERT INTO axignal_global.document_fragments (
  fragment_id, source_object_id, document_id, ordinal, start_char, end_char,
  text_content, content_hash, parser_version, security_scan_state
) VALUES (
  'frag_human_review_rehearsal',
  '10000000-0000-4000-8000-000000000003',
  'doc_human_review_rehearsal',
  0,
  0,
  70,
  'National forecasts do not establish Moscow property conditions.',
  'sha256:2222222222222222222222222222222222222222222222222222222222222222',
  'rehearsal-parser@0.1.0',
  'CLEAR'
);

INSERT INTO axignal_global.evidence_objects (
  evidence_id, source_object_id, source_id, evidence_key, title, relationship,
  subject_id, predicate, observed_at, payload, content_hash, rights_status, provisional
) VALUES (
  '10000000-0000-4000-8000-000000000004',
  '10000000-0000-4000-8000-000000000003',
  'world-bank-rer41',
  'human-review-rehearsal-evidence',
  'Human review rehearsal evidence',
  'CONTEXT',
  'opportunity_moscow_real_estate',
  'national_forecast_local_market_limitation',
  now(),
  jsonb_build_object(
    'fragment_id','frag_human_review_rehearsal',
    'quote_hash','sha256:2222222222222222222222222222222222222222222222222222222222222222',
    'text','National forecasts do not establish Moscow property conditions.'
  ),
  'sha256:3333333333333333333333333333333333333333333333333333333333333333',
  'COMMERCIAL_REUSE_WITH_ATTRIBUTION',
  true
);

INSERT INTO axignal_global.candidate_claims (
  candidate_claim_id, fingerprint, opportunity_id, subject_id, predicate,
  object_value, statement, kind, state, evidence_ids, producer_type,
  producer_id, method_version, relationship, assumptions, unknowns
) VALUES (
  '10000000-0000-4000-8000-000000000005',
  'sha256:4444444444444444444444444444444444444444444444444444444444444444',
  'opp_human_review_rehearsal',
  'opportunity_moscow_real_estate',
  'national_forecast_local_market_limitation',
  '{"scope":"national_macro_context"}'::jsonb,
  'National forecasts do not establish Moscow property-market conditions.',
  'LIMITATION',
  'HUMAN_REVIEW_REQUIRED',
  ARRAY['10000000-0000-4000-8000-000000000004'::uuid],
  'LOCAL_MODEL',
  'rehearsal-model',
  'institutional-claim-extraction@0.1.0',
  'ADVERSE',
  '[]'::jsonb,
  '[]'::jsonb
);

INSERT INTO axignal_global.admission_handoffs (
  admission_handoff_id, tenant_id, research_run_id, state,
  candidate_claim_ids, package, package_hash
) VALUES (
  '10000000-0000-4000-8000-000000000006',
  '10000000-0000-4000-8000-000000000002',
  '10000000-0000-4000-8000-000000000001',
  'HUMAN_REVIEW_REQUIRED',
  ARRAY['10000000-0000-4000-8000-000000000005'::uuid],
  '{"schema_version":1}'::jsonb,
  'sha256:5555555555555555555555555555555555555555555555555555555555555555'
);

INSERT INTO axignal_global.admission_batches (
  admission_batch_id, policy_version, state, candidate_claim_ids,
  decision_summary, decided_at
) VALUES (
  '10000000-0000-4000-8000-000000000007',
  'document-observed-fact@0.1.0',
  'DECIDED',
  ARRAY['10000000-0000-4000-8000-000000000005'::uuid],
  '{"human_review_required":1}'::jsonb,
  now()
);

INSERT INTO axignal_global.admission_decisions (
  admission_decision_id, admission_batch_id, admission_handoff_id,
  candidate_claim_id, outcome, policy_version, gate_results,
  rejection_reasons, human_review_required
) VALUES (
  '10000000-0000-4000-8000-000000000008',
  '10000000-0000-4000-8000-000000000007',
  '10000000-0000-4000-8000-000000000006',
  '10000000-0000-4000-8000-000000000005',
  'HUMAN_REVIEW_REQUIRED',
  'document-observed-fact@0.1.0',
  '{
    "HANDOFF_SCHEMA_VALID":true,
    "PACKAGE_HASH_VALID":true,
    "SOURCE_STILL_ADMITTED":true,
    "SOURCE_KILL_SWITCH_OFF":true,
    "RIGHTS_STILL_VALID":true,
    "RAW_OBJECT_HASH_VALID":true,
    "PRODUCER_AUTHORITY_SEPARATED":true,
    "POLICY_VERSION_PINNED":true
  }'::jsonb,
  '["candidate_class_not_auto_admissible"]'::jsonb,
  true
);
SQL

compose exec -T "$service" pg_dump \
  -U axignal -d "$rehearsal_db" --format=custom --no-owner --no-privileges > "$dump_file"

for migration in infra/postgres/040-bounded-human-review.sql infra/postgres/041-human-review-read-functions.sql infra/postgres/042-human-review-resolution.sql infra/postgres/043-human-review-grants.sql; do
  admin_psql "$rehearsal_db" < "$migration"
done
for migration in infra/postgres/040-bounded-human-review.sql infra/postgres/041-human-review-read-functions.sql infra/postgres/042-human-review-resolution.sql infra/postgres/043-human-review-grants.sql; do
  admin_psql "$rehearsal_db" < "$migration"
done

test "$(query_scalar "$rehearsal_db" "SELECT count(*) FROM tenant_private.human_review_cases WHERE admission_decision_id='10000000-0000-4000-8000-000000000008';")" = "1"
test "$(query_scalar "$rehearsal_db" "SELECT count(*) FROM tenant_private.human_review_events WHERE human_review_case_id=(SELECT human_review_case_id FROM tenant_private.human_review_cases WHERE admission_decision_id='10000000-0000-4000-8000-000000000008') AND event_type='CASE_OPENED';")" = "1"
test "$(query_scalar "$rehearsal_db" "SELECT has_table_privilege('axignal_human_reviewer_login','axignal_global.canonical_claims','INSERT');")" = "f"
test "$(query_scalar "$rehearsal_db" "SELECT has_function_privilege('axignal_human_reviewer_login','tenant_private.resolve_human_review_case(uuid,text,text,text,text,text)','EXECUTE');")" = "t"

compose exec -T "$service" pg_restore \
  -U axignal -d "$restore_db" --no-owner --no-privileges < "$dump_file"

test "$(query_scalar "$restore_db" "SELECT count(*) FROM axignal_global.admission_decisions WHERE admission_decision_id='10000000-0000-4000-8000-000000000008';")" = "1"
test "$(query_scalar "$restore_db" "SELECT to_regclass('tenant_private.human_review_cases') IS NULL;")" = "t"
test "$(query_scalar "$restore_db" "SELECT NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='tenant_private' AND table_name='dossiers' AND column_name='human_review_context');")" = "t"

cat <<'JSON'
{
  "human_review_migration_applied": 40,
  "migration_replay_idempotent": true,
  "existing_decision_backfilled_once": true,
  "case_open_event_backfilled_once": true,
  "reviewer_canonical_insert": false,
  "review_function_execute": true,
  "snapshot_restore_verified": true,
  "partial_state_detected": false
}
JSON
