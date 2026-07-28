#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="${AXIGNAL_PILOT_COMPOSE_FILE:-infra/pilot/compose.yaml}"
COMPOSE_EDGE_FILE="${AXIGNAL_PILOT_COMPOSE_EDGE_FILE:-}"
ENV_FILE="${AXIGNAL_PILOT_ENV_FILE:?AXIGNAL_PILOT_ENV_FILE is required}"
OUTPUT="${1:-runs/pilot-backups/axignal-$(date -u +%Y%m%dT%H%M%SZ).dump}"
POSTGRES_USER="${AXIGNAL_POSTGRES_USER:-axignal}"
POSTGRES_DB="${AXIGNAL_POSTGRES_DB:-axignal}"

mkdir -p "$(dirname "$OUTPUT")"
compose=(docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE")
[[ -n "$COMPOSE_EDGE_FILE" ]] && compose+=(-f "$COMPOSE_EDGE_FILE")
"${compose[@]}" exec -T postgres \
  pg_dump --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" --format custom \
  > "$OUTPUT"

test -s "$OUTPUT"
sha256sum "$OUTPUT" > "$OUTPUT.sha256"
printf '{"backup":"%s","sha256_file":"%s.sha256","status":"PASS"}\n' "$OUTPUT" "$OUTPUT"
