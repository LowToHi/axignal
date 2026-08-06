#!/usr/bin/env bash
set -euo pipefail

: "${REQUEST_PATH:?}"
: "${AXIGNAL_EXACT_SHA:?}"

real_request="$REQUEST_PATH"
test "$(git rev-parse HEAD)" = "$AXIGNAL_EXACT_SHA"
test -f "$real_request"
! git cat-file -e "HEAD^:${real_request}" 2>/dev/null
changed="$(git diff --name-only HEAD^ HEAD)"
test "$changed" = "$real_request"

jq -e \
  '.schema_version == "axignal.o01-real-campaign-execution-request/v0.6-r2" and
   .controller_parent_binding == "IMMEDIATE_PARENT_REQUEST_ONLY" and
   .execute == true and
   .one_shot == true and
   .stage_timing_correction == true' \
  "$real_request"

temporary_request="$(mktemp)"
trap 'rm -f "$temporary_request"' EXIT
parent_sha="$(git rev-parse HEAD^)"
jq \
  --arg parent "$parent_sha" \
  '.schema_version = "axignal.o01-real-campaign-execution-request/v0.6-r1" |
   .controller_parent_sha = $parent' \
  "$real_request" > "$temporary_request"

export REQUEST_PATH="$temporary_request"
bash scripts/run_gate7_o01_campaign_ci_v0_6_r1.sh
