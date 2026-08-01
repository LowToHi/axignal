#!/usr/bin/env bash
set -euo pipefail

: "${AXIGNAL_EXACT_SHA:?required}"
: "${AXIGNAL_G7_PROFILE:?required}"
: "${AXIGNAL_G7_OUTPUT_DIR:?required}"
: "${AXIGNAL_G7_HEALTH_REQUESTS:?required}"
: "${AXIGNAL_G7_RESEARCH_RUNS:?required}"
: "${AXIGNAL_G7_SOAK_SECONDS:?required}"

project="${AXIGNAL_G7_COMPOSE_PROJECT:-axignal-g7}"
port="${AXIGNAL_G7_API_PORT:-18081}"
workers="${AXIGNAL_G7_WORKERS:-2}"
health_concurrency="${AXIGNAL_G7_HEALTH_CONCURRENCY:-20}"
research_concurrency="${AXIGNAL_G7_RESEARCH_CONCURRENCY:-6}"
soak_rps="${AXIGNAL_G7_SOAK_RPS:-2}"
output_dir="$(mkdir -p "$AXIGNAL_G7_OUTPUT_DIR" && cd "$AXIGNAL_G7_OUTPUT_DIR" && pwd)"
env_file="$output_dir/g7.env"
compose_files=(
  -f infra/pilot/compose.yaml
  -f infra/performance/compose.g7.yaml
)

cat > "$env_file" <<ENV
AXIGNAL_BUILD_SHA=$AXIGNAL_EXACT_SHA
AXIGNAL_G7_API_PORT=$port
AXIGNAL_POSTGRES_DB=axignal
AXIGNAL_POSTGRES_USER=axignal
AXIGNAL_POSTGRES_PASSWORD=ci-admin-password-not-for-deployment
AXIGNAL_PROPOSAL_DB_PASSWORD=ci-proposal-password-not-for-deployment
AXIGNAL_ADMISSION_DB_PASSWORD=ci-admission-password-not-for-deployment
AXIGNAL_HUMAN_REVIEW_DB_PASSWORD=ci-review-password-not-for-deployment
AXIGNAL_VALIDATION_DB_PASSWORD=ci-validation-password-not-for-deployment
AXIGNAL_VALIDATION_ANALYST_DB_PASSWORD=ci-analyst-password-not-for-deployment
AXIGNAL_SCHEDULER_DB_PASSWORD=ci-scheduler-password-not-for-deployment
AXIGNAL_AUTH_EMAIL=g7@example.test
AXIGNAL_AUTH_SUBJECT=usr_g7_capacity
AXIGNAL_AUTH_TENANT_ID=11111111-1111-4111-8111-111111111111
AXIGNAL_AUTH_PASSWORD_SCRYPT=scrypt\$00112233445566778899aabbccddeeff\$c90f8bf5f5c77a981b682204633909aba0e58fe328cb71c9c357399c5ca92ea4a088a494b462b96f17efb7360ac400648f893f36fa31d4ec996236784dcbee94
AXIGNAL_SESSION_SECRET=ci-session-secret-with-at-least-32-bytes
AXIGNAL_IDENTITY_ASSERTION_SECRET=ci-identity-secret-with-at-least-32-bytes
AXIGNAL_VALIDATION_PARTICIPANT_SALT=ci-participant-salt-with-at-least-32-bytes
AXIGNAL_OTEL_ENABLED=false
AXIGNAL_LIVE_SOURCES_ENABLED=false
AXIGNAL_TED_LIVE_SOURCES_ENABLED=false
ENV

compose() {
  docker compose \
    --project-name "$project" \
    --env-file "$env_file" \
    "${compose_files[@]}" \
    "$@"
}

capture() {
  compose ps --all > "$output_dir/compose-ps.txt" 2>&1 || true
  compose logs --no-color > "$output_dir/compose.log" 2>&1 || true
  docker ps \
    --filter "label=com.docker.compose.project=$project" \
    --format '{{json .}}' > "$output_dir/docker-ps.jsonl" 2>&1 || true
}

cleanup() {
  local exit_code=$?
  capture
  compose down --volumes --remove-orphans > "$output_dir/cleanup.log" 2>&1 || true
  return "$exit_code"
}
trap cleanup EXIT

compose config > "$output_dir/compose-rendered.yaml"
compose up --build --detach --wait api
compose --profile workers up \
  --build \
  --detach \
  --wait \
  --scale "research-worker=$workers" \
  research-worker

curl --fail --silent --show-error \
  "http://127.0.0.1:$port/readyz" \
  > "$output_dir/readiness.json"

python scripts/run_g7_performance_campaign.py \
  --profile "$AXIGNAL_G7_PROFILE" \
  --base-url "http://127.0.0.1:$port" \
  --identity-secret ci-identity-secret-with-at-least-32-bytes \
  --compose-project "$project" \
  --expected-sha "$AXIGNAL_EXACT_SHA" \
  --output "$output_dir/campaign.json" \
  --health-requests "$AXIGNAL_G7_HEALTH_REQUESTS" \
  --health-concurrency "$health_concurrency" \
  --research-runs "$AXIGNAL_G7_RESEARCH_RUNS" \
  --research-concurrency "$research_concurrency" \
  --soak-seconds "$AXIGNAL_G7_SOAK_SECONDS" \
  --soak-rps "$soak_rps" \
  | tee "$output_dir/campaign.stdout.json"

python - "$output_dir/campaign.json" <<'PY'
import json
import sys
from pathlib import Path

campaign = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert campaign["status"] == "PASS", campaign["findings"]
assert campaign["gate_decision"] == "IN_PROGRESS"
assert campaign["closure_authorised"] is False
assert campaign["human_capacity_acceptance_required"] is True
assert campaign["public_launch_authorised"] is False
PY
