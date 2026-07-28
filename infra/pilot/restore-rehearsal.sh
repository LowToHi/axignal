#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="${AXIGNAL_PILOT_COMPOSE_FILE:-infra/pilot/compose.yaml}"
COMPOSE_EDGE_FILE="${AXIGNAL_PILOT_COMPOSE_EDGE_FILE:-}"
ENV_FILE="${AXIGNAL_PILOT_ENV_FILE:?AXIGNAL_PILOT_ENV_FILE is required}"
POSTGRES_USER="${AXIGNAL_POSTGRES_USER:-axignal}"
POSTGRES_DB="${AXIGNAL_POSTGRES_DB:-axignal}"
RESTORE_DB="axignal_pilot_restore_check"
WORKDIR="$(mktemp -d)"
BACKUP="$WORKDIR/pilot.dump"
trap 'rm -rf "$WORKDIR"' EXIT
compose=(docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE")
[[ -n "$COMPOSE_EDGE_FILE" ]] && compose+=(-f "$COMPOSE_EDGE_FILE")

AXIGNAL_PILOT_ENV_FILE="$ENV_FILE" \
AXIGNAL_PILOT_COMPOSE_FILE="$COMPOSE_FILE" \
AXIGNAL_PILOT_COMPOSE_EDGE_FILE="$COMPOSE_EDGE_FILE" \
  bash infra/pilot/backup.sh "$BACKUP" >/dev/null

"${compose[@]}" exec -T postgres \
  dropdb --username "$POSTGRES_USER" --if-exists "$RESTORE_DB"
"${compose[@]}" exec -T postgres \
  createdb --username "$POSTGRES_USER" "$RESTORE_DB"
"${compose[@]}" exec -T postgres \
  pg_restore --username "$POSTGRES_USER" --dbname "$RESTORE_DB" \
  --no-owner --no-privileges < "$BACKUP"

SCHEMA_COUNT="$("${compose[@]}" exec -T postgres \
  psql --username "$POSTGRES_USER" --dbname "$RESTORE_DB" --tuples-only --no-align \
  --command "SELECT count(*) FROM pg_namespace WHERE nspname IN ('tenant_private','evaluation');" \
  | tr -d '[:space:]')"

test "$SCHEMA_COUNT" = "2"
"${compose[@]}" exec -T postgres \
  dropdb --username "$POSTGRES_USER" "$RESTORE_DB"

printf '{"backup_nonempty":true,"restored_schemas":%s,"restore_rehearsal":"PASS"}\n' "$SCHEMA_COUNT"
