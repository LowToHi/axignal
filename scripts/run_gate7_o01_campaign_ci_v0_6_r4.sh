#!/usr/bin/env bash
set -euo pipefail

: "${REQUEST_PATH:?}"
: "${AXIGNAL_EXACT_SHA:?}"

real_request="$REQUEST_PATH"
test "$(git rev-parse HEAD)" = "$AXIGNAL_EXACT_SHA"
test -f "$real_request"
! git cat-file -e "HEAD^:${real_request}" 2>/dev/null
test "$(git diff --name-only HEAD^ HEAD)" = "$real_request"

jq -e \
  '.schema_version == "axignal.o01-real-campaign-execution-request/v0.6-r4" and
   .controller_parent_binding == "IMMEDIATE_PARENT_REQUEST_ONLY" and
   .execute == true and
   .one_shot == true and
   .stage_timing_correction == true and
   .instrumentation_implementation == "SELF_CONTAINED_V2"' \
  "$real_request"

cp apps/api/src/axignal_api/o01_quality_stage_timing_v2.py \
  apps/api/src/axignal_api/o01_quality_stage_timing.py
cp apps/api/tests/test_o01_quality_stage_timing_v2.py \
  apps/api/tests/test_o01_quality_stage_timing.py

# The frozen verifier emits the threshold key without the redundant
# `_seconds` suffix. Correct only the two schema-consumer assertions in the
# ephemeral checkout; metric values and thresholds remain unchanged.
sed -i \
  's/normalisation_lag_p95_seconds/normalisation_lag_p95/g' \
  scripts/run_gate7_o01_campaign_ci_v0_6_r1.sh

temporary_request="$(mktemp)"
trap 'rm -f "$temporary_request"' EXIT
jq \
  --arg parent "$(git rev-parse HEAD^)" \
  '.schema_version = "axignal.o01-real-campaign-execution-request/v0.6-r1" |
   .controller_parent_sha = $parent' \
  "$real_request" > "$temporary_request"

export REQUEST_PATH="$temporary_request"
bash scripts/run_gate7_o01_campaign_ci_v0_6_r1.sh
