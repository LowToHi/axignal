#!/usr/bin/env bash
set -euo pipefail

: "${AXIGNAL_EXACT_SHA:?}"
: "${AXIGNAL_SOURCE_BRANCH:?}"
: "${PLAN_PATH:?}"
: "${AUTHORITY_MANIFEST:?}"
: "${REQUEST_PATH:?}"
: "${RESULT_DIR:?}"
: "${RAW_TMP_DIR:?}"
: "${KILL_SWITCH_PATH:?}"
: "${GITHUB_REPOSITORY:?}"

TARGET_HEAD="b66dfbdcca0198faaabf5d346018b5496f3a5287"
MANIFEST_REFERENCE="sha256:227d636f6c22cfaeb8b44014ad455e3bb21907f1ffe5be68a847b1a9235144ca"
EXPECTED_BRANCH="agent/ax-gate7-o01-v06-execute-query"
CAMPAIGN_ID="AX-LIB-O01-TED-QALAG-ML-CONTROLS-v0.6"
PRIOR_ARTIFACT_ID="8837674401"
PRIOR_RUN_ID="30761651795"
REMEDIATION_PATH="data/acceptance/campaigns/AX-LIB-O01-stage-timing-remediation.v0.6-r1.json"

mkdir -p "$RESULT_DIR"
test "$(git rev-parse HEAD)" = "$AXIGNAL_EXACT_SHA"
test "$AXIGNAL_SOURCE_BRANCH" = "$EXPECTED_BRANCH"
test -f "$REQUEST_PATH"
test -f "$REMEDIATION_PATH"
test "sha256:$(sha256sum "$AUTHORITY_MANIFEST" | awk '{print $1}')" = "$MANIFEST_REFERENCE"
test "$(jq -r '.target.head_sha' "$AUTHORITY_MANIFEST")" = "$TARGET_HEAD"
git merge-base --is-ancestor "$TARGET_HEAD" HEAD

controller_parent="$(jq -r '.controller_parent_sha' "$REQUEST_PATH")"
test "$(git rev-parse HEAD^)" = "$controller_parent"
jq -e \
  --arg parent "$controller_parent" \
  --arg target "$TARGET_HEAD" \
  --arg manifest "$MANIFEST_REFERENCE" \
  --arg campaign "$CAMPAIGN_ID" \
  '.schema_version == "axignal.o01-real-campaign-execution-request/v0.6-r1" and
   .campaign_id == $campaign and
   .controller_parent_sha == $parent and
   .target_head_sha == $target and
   .manifest_reference == $manifest and
   .requested_by == "LowToHi" and
   .execution_mode == "REAL_BOUNDED_PRIVATE_EVIDENCE" and
   .execute == true and
   .one_shot == true and
   .stage_timing_correction == true and
   .check_query_syntax == false and
   .source_scope == "ALL" and
   .authority_boundary.source_state == "CANDIDATE" and
   .authority_boundary.product_admitted == false and
   .authority_boundary.public_claims_authorised == false and
   .authority_boundary.public_launch == "NO_GO"' \
  "$REQUEST_PATH"

jq -e \
  --argjson artifact "$PRIOR_ARTIFACT_ID" \
  --argjson run "$PRIOR_RUN_ID" \
  '.change_class == "REPORTING_AND_INSTRUMENTATION_CORRECTION" and
   .experimental_contract_delta == false and
   .observed_failure.artifact_id == $artifact and
   .observed_failure.workflow_run_id == $run and
   .observed_failure.sample_count == 180 and
   .observed_failure.normalisation_lag_p95_seconds > 126 and
   .observed_failure.all_other_thresholds_passed == true and
   .root_cause.classification == "BATCH_QUEUE_WAIT_MISLABELLED_AS_NORMALISATION_STAGE_DURATION" and
   .solution.queue_wait == "disclosed separately and not thresholded as local normalisation" and
   .authority_boundary_unchanged == true and
   .invariants.thresholds_unchanged == true' \
  "$REMEDIATION_PATH"

{
  printf 'controller_head_sha=%s\n' "$(git rev-parse HEAD)"
  printf 'controller_tree_sha=%s\n' "$(git rev-parse 'HEAD^{tree}')"
  printf 'controller_parent_sha=%s\n' "$controller_parent"
  printf 'target_head_sha=%s\n' "$TARGET_HEAD"
  printf 'manifest_reference=%s\n' "$MANIFEST_REFERENCE"
  printf 'execution_request_sha256=sha256:%s\n' "$(sha256sum "$REQUEST_PATH" | awk '{print $1}')"
  printf 'remediation_sha256=sha256:%s\n' "$(sha256sum "$REMEDIATION_PATH" | awk '{print $1}')"
} | tee "$RESULT_DIR/exact-head-and-request.txt"

python -m compileall -q \
  apps/api/src/axignal_api/o01_quality_stage_timing.py \
  apps/api/tests/test_o01_quality_stage_timing.py \
  scripts/run_gate7_o01_quality_coverage_lag_campaign_v0_6_r1.py
ruff check \
  apps/api/src/axignal_api/o01_quality_stage_timing.py \
  apps/api/tests/test_o01_quality_stage_timing.py \
  scripts/run_gate7_o01_quality_coverage_lag_campaign_v0_6_r1.py
pytest -q \
  apps/api/tests/test_o01_quality_stage_timing.py \
  apps/api/tests/test_gate7_o01_multilingual.py \
  apps/api/tests/test_gate7_o01_runtime.py \
  apps/api/tests/test_o01_quality_controls.py \
  apps/api/tests/test_o01_quality_campaign.py

python scripts/verify_gate7_o01_v0_6_execution_contract.py \
  --materialized-output "$RESULT_DIR/materialized-execution-contract.v0.6.json" \
  | tee "$RESULT_DIR/execution-contract-result.json"
python scripts/materialize_gate7_o01_quality_coverage_lag_plan_v0_6.py \
  --output "$PLAN_PATH" | tee "$RESULT_DIR/plan-materialization-result.json"
python scripts/verify_gate7_o01_quality_coverage_lag_contract_v0_6.py \
  --plan "$PLAN_PATH" | tee "$RESULT_DIR/plan-contract-result.json"

for evidence_class in official_evidence execution_evidence; do
  id="$(jq -r ".${evidence_class}.artifact_id" "$AUTHORITY_MANIFEST")"
  digest="$(jq -r ".${evidence_class}.artifact_digest" "$AUTHORITY_MANIFEST")"
  gh api "/repos/${GITHUB_REPOSITORY}/actions/artifacts/${id}" \
    > "$RESULT_DIR/${evidence_class}-artifact-metadata.json"
  jq -e --arg digest "$digest" \
    '.expired == false and .digest == $digest' \
    "$RESULT_DIR/${evidence_class}-artifact-metadata.json"
done

gh api "/repos/${GITHUB_REPOSITORY}/actions/artifacts/${PRIOR_ARTIFACT_ID}" \
  > "$RESULT_DIR/prior-campaign-artifact-metadata.json"
jq -e --argjson run "$PRIOR_RUN_ID" \
  '.expired == false and .workflow_run.id == $run' \
  "$RESULT_DIR/prior-campaign-artifact-metadata.json"
gh api "/repos/${GITHUB_REPOSITORY}/actions/artifacts/${PRIOR_ARTIFACT_ID}/zip" \
  > /tmp/o01-v0-6-prior.zip
mkdir -p "$RESULT_DIR/prior-campaign"
unzip -q /tmp/o01-v0-6-prior.zip -d "$RESULT_DIR/prior-campaign"
prior_final="$(find "$RESULT_DIR/prior-campaign" -name final-result.json -type f | head -n 1)"
test -n "$prior_final"
jq -e \
  '.output == "O01_QUALITY_COVERAGE_LAG_FAIL" and
   .sample_count == 180 and
   .criteria.HUMAN_AUTHORITY_CURRENT == true and
   .criteria.RAW_RESPONSES_RETAINED_SECURELY == true and
   .criteria.MULTILINGUAL_JOURNEYS_COMPLETE == true and
   .criteria.KILL_SWITCH_TESTED == true and
   .criteria.ROLLBACK_TESTED == true and
   .thresholds.checks.normalisation_lag_p95_seconds.pass == false and
   ([.thresholds.checks | to_entries[] | select(.key != "normalisation_lag_p95_seconds") | .value.pass] | all)' \
  "$prior_final"

gh api --paginate \
  "/repos/${GITHUB_REPOSITORY}/issues/124/comments?per_page=100" \
  --slurp | jq '[.[][]]' > /tmp/o01-v0-6-r1-legal.json
gh api --paginate \
  "/repos/${GITHUB_REPOSITORY}/issues/125/comments?per_page=100" \
  --slurp | jq '[.[][]]' > /tmp/o01-v0-6-r1-privacy.json
python scripts/extract_gate7_o01_campaign_authority.py \
  --manifest "$AUTHORITY_MANIFEST" \
  --legal-comments /tmp/o01-v0-6-r1-legal.json \
  --privacy-comments /tmp/o01-v0-6-r1-privacy.json \
  --output-dir "$RESULT_DIR/current-authority" \
  --require-authorised | tee "$RESULT_DIR/current-authority-result.json"
jq -e \
  '.execution_authorised == true and
   .output == "O01_CAMPAIGN_AUTHORISED" and
   .legal == "APPROVED_CURRENT" and
   .privacy_data_rights == "APPROVED_CURRENT" and
   .head_match == true and
   .manifest_match == true and
   .signatures_human == true and
   .expiry_within_evidence == true' \
  "$RESULT_DIR/current-authority/result.v0.1.json"

AUTHORITY_RESULT="$RESULT_DIR/current-authority/result.v0.1.json" \
REQUEST_PATH="$REQUEST_PATH" RESULT_DIR="$RESULT_DIR" python - <<'PY'
import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path

authority_path = Path(os.environ["AUTHORITY_RESULT"])
request_path = Path(os.environ["REQUEST_PATH"])
result_dir = Path(os.environ["RESULT_DIR"])
receipt = {
    "schema_version": "axignal.o01-network-authority-gate/v0.6-r1",
    "status": "PASS",
    "output": "O01_CAMPAIGN_AUTHORISED",
    "verified_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    "authority_result_sha256": "sha256:" + hashlib.sha256(authority_path.read_bytes()).hexdigest(),
    "execution_request_sha256": "sha256:" + hashlib.sha256(request_path.read_bytes()).hexdigest(),
    "network_dispatch_enabled_after_receipt": True,
    "stage_timing_correction": True,
    "check_query_syntax": False,
    "source_scope": "ALL",
    "source_state": "CANDIDATE",
    "public_launch": "NO_GO",
}
(result_dir / "network-authority-gate.v0.6-r1.json").write_text(
    json.dumps(receipt, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
PY

test ! -e "$KILL_SWITCH_PATH"
python scripts/rehearse_gate7_o01_controls.py preflight \
  --signal-path "$KILL_SWITCH_PATH" \
  --checkpoint "$RESULT_DIR/pre-campaign-boundary.v0.6-r1.json" \
  --output "$RESULT_DIR/operational-controls-preflight.v0.6-r1.json" \
  | tee "$RESULT_DIR/operational-controls-preflight-console.json"
test ! -e "$KILL_SWITCH_PATH"
jq -e \
  '.status == "PASS" and .kill_switch.pass == true and .kill_switch.requests_after_activation == 0 and .external_network_requests == 0' \
  "$RESULT_DIR/operational-controls-preflight.v0.6-r1.json"

python scripts/run_gate7_o01_quality_coverage_lag_campaign_v0_6_r1.py \
  --plan "$PLAN_PATH" \
  --authority-envelope "$RESULT_DIR/current-authority/campaign-authority-envelope.v0.1.json" \
  --raw-dir "$RAW_TMP_DIR" \
  --output-dir "$RESULT_DIR" \
  --kill-switch-path "$KILL_SWITCH_PATH" \
  | tee "$RESULT_DIR/campaign-run-result.json"
python scripts/measure_gate7_o01_multilingual_journeys.py \
  --plan "$PLAN_PATH" \
  --raw-dir "$RAW_TMP_DIR" \
  --output "$RESULT_DIR/multilingual-journeys.v0.1.json" \
  | tee "$RESULT_DIR/multilingual-journeys-console.json"

test -d "$RAW_TMP_DIR"
raw_file_count="$(find "$RAW_TMP_DIR" -type f | wc -l | tr -d ' ')"
raw_bytes="$(du -sb "$RAW_TMP_DIR" | awk '{print $1}')"
tar --sort=name --mtime='@0' --owner=0 --group=0 --numeric-owner \
  -cf - -C "$RAW_TMP_DIR" . | gzip -n > /tmp/o01-v0-6-r1-raw.tar.gz
plaintext_sha="sha256:$(sha256sum /tmp/o01-v0-6-r1-raw.tar.gz | awk '{print $1}')"
openssl cms -encrypt -binary -aes256 \
  -in /tmp/o01-v0-6-r1-raw.tar.gz -outform DER \
  -out "$RESULT_DIR/raw-responses.cms" \
  data/acceptance/keys/o01-evidence-recipient-cert.pem
openssl cms -cmsout -inform DER -in "$RESULT_DIR/raw-responses.cms" \
  -print > /dev/null
ciphertext_sha="sha256:$(sha256sum "$RESULT_DIR/raw-responses.cms" | awk '{print $1}')"
fingerprint="$(openssl x509 \
  -in data/acceptance/keys/o01-evidence-recipient-cert.pem \
  -noout -fingerprint -sha256 | cut -d= -f2 | tr -d ':')"
RAW_FILE_COUNT="$raw_file_count" RAW_BYTES="$raw_bytes" \
PLAINTEXT_SHA="$plaintext_sha" CIPHERTEXT_SHA="$ciphertext_sha" \
FINGERPRINT="$fingerprint" RESULT_DIR="$RESULT_DIR" python - <<'PY'
import json
import os
from pathlib import Path

result_dir = Path(os.environ["RESULT_DIR"])
payload = {
    "status": "SEALED",
    "format": "CMS_ENVELOPED_DATA",
    "content_encryption": "AES-256-CBC",
    "ciphertext_file": "raw-responses.cms",
    "ciphertext_sha256": os.environ["CIPHERTEXT_SHA"],
    "plaintext_archive_sha256": os.environ["PLAINTEXT_SHA"],
    "plaintext_file_count": int(os.environ["RAW_FILE_COUNT"]),
    "plaintext_directory_bytes": int(os.environ["RAW_BYTES"]),
    "plaintext_removed": True,
    "plaintext_uploaded": False,
    "cms_structure_verified": True,
    "recipient_certificate_sha256_fingerprint": os.environ["FINGERPRINT"],
    "contact_values_in_plaintext_projection": False,
    "full_notice_payloads_retrieved": False,
    "stage_timing_correction": True,
    "check_query_syntax": False,
    "source_scope": "ALL",
}
(result_dir / "raw-retention.v0.1.json").write_text(
    json.dumps(payload, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
PY
rm -rf "$RAW_TMP_DIR" /tmp/o01-v0-6-r1-raw.tar.gz
test ! -e "$RAW_TMP_DIR"

python scripts/rehearse_gate7_o01_controls.py finalise \
  --preflight "$RESULT_DIR/operational-controls-preflight.v0.6-r1.json" \
  --checkpoint "$RESULT_DIR/pre-campaign-boundary.v0.6-r1.json" \
  --preliminary "$RESULT_DIR/preliminary-result.v0.1.json" \
  --notification-ledger "$RESULT_DIR/notification-ledger.v0.1.jsonl" \
  --raw-retention "$RESULT_DIR/raw-retention.v0.1.json" \
  --output "$RESULT_DIR/operational-controls.v0.1.json"
python scripts/verify_gate7_o01_quality_coverage_lag_contract_v0_6.py \
  --plan "$PLAN_PATH" --result-dir "$RESULT_DIR" \
  | tee "$RESULT_DIR/final-result.json"
jq -e \
  '.output == "O01_QUALITY_COVERAGE_LAG_PASS" and
   .sample_count == 180 and
   .thresholds.checks.normalisation_lag_p95_seconds.pass == true' \
  "$RESULT_DIR/final-result.json"
jq -e \
  '.measurement_semantics.queue_wait_disclosed_separately == true and
   .queueing_context.thresholded_as_normalisation_lag == false and
   .measurement_semantics.fabricated_evidence == 0' \
  "$RESULT_DIR/lag-report.v0.1.json"
