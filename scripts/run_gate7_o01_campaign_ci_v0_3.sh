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

EVALUATOR_HEAD="5a9b63056289b2b0851d9a88e712d4b8a24545dd"
EVALUATOR_TREE="89fb112a7ec2ca12da626409a0bb5132c0ee7ee0"
MANIFEST_REFERENCE="sha256:74ed362c8b856d586139062095c57a6d9a8944012bb9429dc4bb121ed6960d6d"
EXPECTED_BRANCH="agent/ax-gate7-o01-v03-real-campaign"

mkdir -p "$RESULT_DIR"
test "$(git rev-parse HEAD)" = "$AXIGNAL_EXACT_SHA"
test "$AXIGNAL_SOURCE_BRANCH" = "$EXPECTED_BRANCH"
test -f "$REQUEST_PATH"

target="$(jq -r '.target.head_sha' "$AUTHORITY_MANIFEST")"
target_tree="$(jq -r '.target.git_tree_sha' "$AUTHORITY_MANIFEST")"
test "sha256:$(sha256sum "$AUTHORITY_MANIFEST" | awk '{print $1}')" = "$MANIFEST_REFERENCE"
test "$(git rev-parse "${EVALUATOR_HEAD}^{tree}")" = "$EVALUATOR_TREE"
test "$(git rev-parse "${target}^{tree}")" = "$target_tree"
git merge-base --is-ancestor "$target" "$EVALUATOR_HEAD"
git merge-base --is-ancestor "$EVALUATOR_HEAD" HEAD

controller_parent="$(jq -r '.controller_parent_sha' "$REQUEST_PATH")"
test "$(git rev-parse HEAD^)" = "$controller_parent"
jq -e \
  --arg parent "$controller_parent" \
  --arg target "$target" \
  --arg manifest "$MANIFEST_REFERENCE" \
  '.schema_version == "axignal.o01-real-campaign-execution-request/v0.3" and
   .campaign_id == "AX-LIB-O01-TED-QALAG-ML-CONTROLS-v0.3" and
   .controller_parent_sha == $parent and
   .target_head_sha == $target and
   .manifest_reference == $manifest and
   .requested_by == "LowToHi" and
   .execution_mode == "REAL_BOUNDED_PRIVATE_EVIDENCE" and
   .execute == true and
   .one_shot == true and
   .authority_boundary.source_state == "CANDIDATE" and
   .authority_boundary.product_admitted == false and
   .authority_boundary.public_claims_authorised == false and
   .authority_boundary.public_launch == "NO_GO"' \
  "$REQUEST_PATH"

{
  printf 'controller_head_sha=%s\n' "$(git rev-parse HEAD)"
  printf 'controller_tree_sha=%s\n' "$(git rev-parse 'HEAD^{tree}')"
  printf 'controller_parent_sha=%s\n' "$controller_parent"
  printf 'source_branch=%s\n' "$AXIGNAL_SOURCE_BRANCH"
  printf 'evaluator_head_sha=%s\n' "$EVALUATOR_HEAD"
  printf 'evaluator_tree_sha=%s\n' "$EVALUATOR_TREE"
  printf 'target_head_sha=%s\n' "$target"
  printf 'target_tree_sha=%s\n' "$target_tree"
  printf 'manifest_reference=%s\n' "$MANIFEST_REFERENCE"
  printf 'execution_request_sha256=sha256:%s\n' "$(sha256sum "$REQUEST_PATH" | awk '{print $1}')"
} | tee "$RESULT_DIR/exact-head-and-request.txt"

python -m compileall -q \
  apps/api/src/axignal_api/gate7_o01_controls.py \
  apps/api/src/axignal_api/gate7_o01_multilingual.py \
  apps/api/src/axignal_api/gate7_o01_runtime.py \
  apps/api/tests/test_gate7_o01_multilingual.py \
  apps/api/tests/test_gate7_o01_runtime.py \
  apps/api/tests/test_o01_quality_controls.py \
  scripts/materialize_gate7_o01_quality_coverage_lag_plan_v0_3.py \
  scripts/measure_gate7_o01_multilingual_journeys.py \
  scripts/rehearse_gate7_o01_controls.py \
  scripts/run_gate7_o01_quality_coverage_lag_campaign_v0_3.py \
  scripts/verify_gate7_o01_quality_coverage_lag_contract_v0_3.py \
  scripts/verify_gate7_o01_v0_3_delta_contract.py
ruff check \
  apps/api/src/axignal_api/gate7_o01_controls.py \
  apps/api/src/axignal_api/gate7_o01_multilingual.py \
  apps/api/src/axignal_api/gate7_o01_runtime.py \
  apps/api/tests/test_gate7_o01_multilingual.py \
  apps/api/tests/test_gate7_o01_runtime.py \
  apps/api/tests/test_o01_quality_controls.py \
  scripts/materialize_gate7_o01_quality_coverage_lag_plan_v0_3.py \
  scripts/measure_gate7_o01_multilingual_journeys.py \
  scripts/rehearse_gate7_o01_controls.py \
  scripts/run_gate7_o01_quality_coverage_lag_campaign_v0_3.py \
  scripts/verify_gate7_o01_quality_coverage_lag_contract_v0_3.py \
  scripts/verify_gate7_o01_v0_3_delta_contract.py
pytest -q \
  apps/api/tests/test_gate7_o01_multilingual.py \
  apps/api/tests/test_gate7_o01_runtime.py \
  apps/api/tests/test_o01_quality_controls.py \
  apps/api/tests/test_o01_quality_campaign.py

python scripts/verify_gate7_o01_v0_3_delta_contract.py \
  --materialized-output "$RESULT_DIR/materialized-execution-contract.v0.3.json" \
  | tee "$RESULT_DIR/delta-contract-result.json"
python scripts/materialize_gate7_o01_quality_coverage_lag_plan_v0_3.py \
  --output "$PLAN_PATH" | tee "$RESULT_DIR/plan-materialization-result.json"
python scripts/verify_gate7_o01_quality_coverage_lag_contract_v0_3.py \
  --plan "$PLAN_PATH" | tee "$RESULT_DIR/plan-contract-result.json"

baseline_id="$(jq -r '.official_evidence.artifact_id' "$AUTHORITY_MANIFEST")"
baseline_digest="$(jq -r '.official_evidence.artifact_digest' "$AUTHORITY_MANIFEST")"
gh api "/repos/${GITHUB_REPOSITORY}/actions/artifacts/${baseline_id}" \
  > "$RESULT_DIR/baseline-artifact-metadata.json"
jq -e --arg digest "$baseline_digest" \
  '.expired == false and .digest == $digest' \
  "$RESULT_DIR/baseline-artifact-metadata.json"

diagnostic_id="$(jq -r '.remediation_evidence.artifact_id' "$AUTHORITY_MANIFEST")"
diagnostic_digest="$(jq -r '.remediation_evidence.artifact_digest' "$AUTHORITY_MANIFEST")"
gh api "/repos/${GITHUB_REPOSITORY}/actions/artifacts/${diagnostic_id}" \
  > "$RESULT_DIR/diagnostic-artifact-metadata.json"
jq -e --arg digest "$diagnostic_digest" \
  '.expired == false and .digest == $digest' \
  "$RESULT_DIR/diagnostic-artifact-metadata.json"

gh api --paginate \
  "/repos/${GITHUB_REPOSITORY}/issues/124/comments?per_page=100" \
  --slurp | jq '[.[][]]' > /tmp/o01-v0-3-legal.json
gh api --paginate \
  "/repos/${GITHUB_REPOSITORY}/issues/125/comments?per_page=100" \
  --slurp | jq '[.[][]]' > /tmp/o01-v0-3-privacy.json
python scripts/extract_gate7_o01_campaign_authority.py \
  --manifest "$AUTHORITY_MANIFEST" \
  --legal-comments /tmp/o01-v0-3-legal.json \
  --privacy-comments /tmp/o01-v0-3-privacy.json \
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
authority = json.loads(authority_path.read_text(encoding="utf-8"))
receipt = {
    "schema_version": "axignal.o01-network-authority-gate/v0.3",
    "status": "PASS",
    "output": "O01_CAMPAIGN_AUTHORISED",
    "verified_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    "authority_result_sha256": "sha256:" + hashlib.sha256(authority_path.read_bytes()).hexdigest(),
    "execution_request_sha256": "sha256:" + hashlib.sha256(request_path.read_bytes()).hexdigest(),
    "network_dispatch_enabled_after_receipt": True,
    "source_state": "CANDIDATE",
    "public_launch": "NO_GO",
}
(result_dir / "network-authority-gate.v0.3.json").write_text(
    json.dumps(receipt, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
PY

test ! -e "$KILL_SWITCH_PATH"
python scripts/rehearse_gate7_o01_controls.py preflight \
  --signal-path "$KILL_SWITCH_PATH" \
  --checkpoint "$RESULT_DIR/pre-campaign-boundary.v0.3.json" \
  --output "$RESULT_DIR/operational-controls-preflight.v0.3.json" \
  | tee "$RESULT_DIR/operational-controls-preflight-console.json"
test ! -e "$KILL_SWITCH_PATH"
jq -e \
  '.status == "PASS" and .kill_switch.pass == true and .kill_switch.requests_after_activation == 0 and .external_network_requests == 0' \
  "$RESULT_DIR/operational-controls-preflight.v0.3.json"

test ! -e "$RAW_TMP_DIR"
python scripts/run_gate7_o01_quality_coverage_lag_campaign_v0_3.py \
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
  -cf - -C "$RAW_TMP_DIR" . | gzip -n > /tmp/o01-v0-3-raw.tar.gz
plaintext_sha="sha256:$(sha256sum /tmp/o01-v0-3-raw.tar.gz | awk '{print $1}')"
openssl cms -encrypt -binary -aes256 \
  -in /tmp/o01-v0-3-raw.tar.gz -outform DER \
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
    "canonical_telephone_field": "organisation-tel-buyer",
}
(result_dir / "raw-retention.v0.1.json").write_text(
    json.dumps(payload, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
PY
rm -rf "$RAW_TMP_DIR" /tmp/o01-v0-3-raw.tar.gz
test ! -e "$RAW_TMP_DIR"

python scripts/rehearse_gate7_o01_controls.py finalise \
  --preflight "$RESULT_DIR/operational-controls-preflight.v0.3.json" \
  --checkpoint "$RESULT_DIR/pre-campaign-boundary.v0.3.json" \
  --preliminary "$RESULT_DIR/preliminary-result.v0.1.json" \
  --notification-ledger "$RESULT_DIR/notification-ledger.v0.1.jsonl" \
  --raw-retention "$RESULT_DIR/raw-retention.v0.1.json" \
  --output "$RESULT_DIR/operational-controls.v0.1.json"
python scripts/verify_gate7_o01_quality_coverage_lag_contract_v0_3.py \
  --plan "$PLAN_PATH" --result-dir "$RESULT_DIR" \
  | tee "$RESULT_DIR/final-result.json"
