#!/usr/bin/env bash
set -euo pipefail

: "${AXIGNAL_EXACT_SHA:?}"
: "${PLAN_PATH:?}"
: "${AUTHORITY_MANIFEST:?}"
: "${RESULT_DIR:?}"
: "${RAW_TMP_DIR:?}"
: "${KILL_SWITCH_PATH:?}"
: "${GITHUB_REPOSITORY:?}"

test "$(git rev-parse HEAD)" = "$AXIGNAL_EXACT_SHA"
mkdir -p "$RESULT_DIR"
evaluator="$(jq -r '.authority.evaluator_head_sha' "$PLAN_PATH")"
evaluator_tree="$(jq -r '.authority.evaluator_tree_sha' "$PLAN_PATH")"
target="$(jq -r '.authority.target_head_sha' "$PLAN_PATH")"
target_tree="$(jq -r '.authority.target_tree_sha' "$PLAN_PATH")"
test "$(git rev-parse "${evaluator}^{tree}")" = "$evaluator_tree"
test "$(git rev-parse "${target}^{tree}")" = "$target_tree"
git merge-base --is-ancestor "$target" "$evaluator"
git merge-base --is-ancestor "$evaluator" HEAD
{
  printf 'controller_head_sha=%s\n' "$(git rev-parse HEAD)"
  printf 'controller_tree_sha=%s\n' "$(git rev-parse 'HEAD^{tree}')"
  printf 'evaluator_head_sha=%s\n' "$evaluator"
  printf 'evaluator_tree_sha=%s\n' "$evaluator_tree"
  printf 'target_head_sha=%s\n' "$target"
  printf 'target_tree_sha=%s\n' "$target_tree"
} | tee "$RESULT_DIR/exact-head.txt"

python -m compileall -q \
  apps/api/src/axignal_api/gate7_o01_controls.py \
  apps/api/src/axignal_api/gate7_o01_multilingual.py \
  apps/api/src/axignal_api/gate7_o01_runtime.py \
  apps/api/tests/test_gate7_o01_multilingual.py \
  apps/api/tests/test_gate7_o01_runtime.py \
  apps/api/tests/test_o01_quality_controls.py \
  scripts/measure_gate7_o01_multilingual_journeys.py \
  scripts/rehearse_gate7_o01_controls.py \
  scripts/run_gate7_o01_quality_coverage_lag_campaign_v0_2.py \
  scripts/verify_gate7_o01_quality_coverage_lag_contract_v0_2.py
ruff check \
  apps/api/src/axignal_api/gate7_o01_controls.py \
  apps/api/src/axignal_api/gate7_o01_multilingual.py \
  apps/api/src/axignal_api/gate7_o01_runtime.py \
  apps/api/tests/test_gate7_o01_multilingual.py \
  apps/api/tests/test_gate7_o01_runtime.py \
  apps/api/tests/test_o01_quality_controls.py \
  scripts/measure_gate7_o01_multilingual_journeys.py \
  scripts/rehearse_gate7_o01_controls.py \
  scripts/run_gate7_o01_quality_coverage_lag_campaign_v0_2.py \
  scripts/verify_gate7_o01_quality_coverage_lag_contract_v0_2.py
pytest -q \
  apps/api/tests/test_gate7_o01_multilingual.py \
  apps/api/tests/test_gate7_o01_runtime.py \
  apps/api/tests/test_o01_quality_controls.py \
  apps/api/tests/test_o01_quality_campaign.py
python scripts/verify_gate7_o01_quality_coverage_lag_contract_v0_2.py \
  --plan "$PLAN_PATH" | tee "$RESULT_DIR/plan-contract-result.json"

authority_artifact_id="$(jq -r '.authority.authority_artifact_id' "$PLAN_PATH")"
authority_artifact_digest="$(jq -r '.authority.authority_artifact_digest' "$PLAN_PATH")"
gh api "/repos/${GITHUB_REPOSITORY}/actions/artifacts/${authority_artifact_id}" \
  > "$RESULT_DIR/authority-artifact-metadata.json"
jq -e --arg digest "$authority_artifact_digest" \
  '.expired == false and .digest == $digest' \
  "$RESULT_DIR/authority-artifact-metadata.json"

baseline_id="$(jq -r '.official_evidence.artifact_id' "$AUTHORITY_MANIFEST")"
baseline_artifact_digest="$(jq -r '.official_evidence.artifact_digest' "$AUTHORITY_MANIFEST")"
gh api "/repos/${GITHUB_REPOSITORY}/actions/artifacts/${baseline_id}" \
  > "$RESULT_DIR/baseline-artifact-metadata.json"
jq -e --arg digest "$baseline_artifact_digest" \
  '.expired == false and .digest == $digest' \
  "$RESULT_DIR/baseline-artifact-metadata.json"
gh api "/repos/${GITHUB_REPOSITORY}/actions/artifacts/${baseline_id}/zip" \
  > /tmp/o01-v0-2-baseline.zip
mkdir -p "$RESULT_DIR/official-baseline"
unzip -q /tmp/o01-v0-2-baseline.zip -d "$RESULT_DIR/official-baseline"
baseline="$(find "$RESULT_DIR/official-baseline" \
  -name 'official-online-baseline.v0.1.json' -type f | head -n 1)"
test -n "$baseline"
BASELINE_PATH="$baseline" python - <<'PY'
import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path

manifest = json.loads(Path(os.environ["AUTHORITY_MANIFEST"]).read_text())
path = Path(os.environ["BASELINE_PATH"])
baseline = json.loads(path.read_text())
evidence = manifest["official_evidence"]
assert "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest() == evidence["baseline_digest"]
assert baseline["baseline_payload_digest"] == evidence["baseline_payload_digest"]
assert baseline["exact_head_sha"] == "b754b5641e5f17c5a084434aace4f939a4be0e84"
assert baseline["git_tree_sha"] == "615efd6e8a7f3369292775dbcf3223f8cc006f29"
assert baseline["official_online_baseline"] == "PRESENT"
assert baseline["official_terms_available"] is True
assert baseline["evidence_expiry"] == evidence["evidence_expires_at"]
assert datetime.now(UTC) < datetime.fromisoformat(
    evidence["evidence_expires_at"].replace("Z", "+00:00")
)
for document in baseline["documents"].values():
    assert document["status"] == "PASS"
    assert document["critical_anchors_present"] == document["critical_anchors_expected"]
PY

gh api --paginate \
  "/repos/${GITHUB_REPOSITORY}/issues/124/comments?per_page=100" \
  --slurp | jq '[.[][]]' > /tmp/o01-v0-2-legal.json
gh api --paginate \
  "/repos/${GITHUB_REPOSITORY}/issues/125/comments?per_page=100" \
  --slurp | jq '[.[][]]' > /tmp/o01-v0-2-privacy.json
python scripts/extract_gate7_o01_campaign_authority.py \
  --manifest "$AUTHORITY_MANIFEST" \
  --legal-comments /tmp/o01-v0-2-legal.json \
  --privacy-comments /tmp/o01-v0-2-privacy.json \
  --output-dir "$RESULT_DIR/current-authority" \
  --require-authorised | tee "$RESULT_DIR/current-authority-result.json"
jq -e \
  '.execution_authorised == true and .output == "O01_CAMPAIGN_AUTHORISED" and .legal == "APPROVED_CURRENT" and .privacy_data_rights == "APPROVED_CURRENT" and .head_match == true and .manifest_match == true and .signatures_human == true and .expiry_within_evidence == true' \
  "$RESULT_DIR/current-authority/result.v0.1.json"

test ! -e "$KILL_SWITCH_PATH"
python scripts/rehearse_gate7_o01_controls.py preflight \
  --signal-path "$KILL_SWITCH_PATH" \
  --checkpoint "$RESULT_DIR/pre-campaign-boundary.v0.2.json" \
  --output "$RESULT_DIR/operational-controls-preflight.v0.2.json" \
  | tee "$RESULT_DIR/operational-controls-preflight-console.json"
test ! -e "$KILL_SWITCH_PATH"
jq -e \
  '.status == "PASS" and .kill_switch.pass == true and .kill_switch.requests_after_activation == 0 and .external_network_requests == 0' \
  "$RESULT_DIR/operational-controls-preflight.v0.2.json"

test ! -e "$RAW_TMP_DIR"
python scripts/run_gate7_o01_quality_coverage_lag_campaign_v0_2.py \
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
  -cf - -C "$RAW_TMP_DIR" . | gzip -n > /tmp/o01-v0-2-raw.tar.gz
plaintext_sha="sha256:$(sha256sum /tmp/o01-v0-2-raw.tar.gz | awk '{print $1}')"
openssl cms -encrypt -binary -aes256 \
  -in /tmp/o01-v0-2-raw.tar.gz -outform DER \
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
FINGERPRINT="$fingerprint" python - <<'PY'
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
}
(result_dir / "raw-retention.v0.1.json").write_text(
    json.dumps(payload, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
PY
rm -rf "$RAW_TMP_DIR" /tmp/o01-v0-2-raw.tar.gz
test ! -e "$RAW_TMP_DIR"

python scripts/rehearse_gate7_o01_controls.py finalise \
  --preflight "$RESULT_DIR/operational-controls-preflight.v0.2.json" \
  --checkpoint "$RESULT_DIR/pre-campaign-boundary.v0.2.json" \
  --preliminary "$RESULT_DIR/preliminary-result.v0.1.json" \
  --notification-ledger "$RESULT_DIR/notification-ledger.v0.1.jsonl" \
  --raw-retention "$RESULT_DIR/raw-retention.v0.1.json" \
  --output "$RESULT_DIR/operational-controls.v0.1.json"
python scripts/verify_gate7_o01_quality_coverage_lag_contract_v0_2.py \
  --plan "$PLAN_PATH" --result-dir "$RESULT_DIR" \
  | tee "$RESULT_DIR/final-result.json"
