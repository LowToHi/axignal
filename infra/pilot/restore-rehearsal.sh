#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="${AXIGNAL_PILOT_COMPOSE_FILE:-infra/pilot/compose.yaml}"
ENV_FILE="${AXIGNAL_PILOT_ENV_FILE:?AXIGNAL_PILOT_ENV_FILE is required}"
POSTGRES_USER="${AXIGNAL_POSTGRES_USER:-axignal}"
POSTGRES_DB="${AXIGNAL_POSTGRES_DB:-axignal}"
RESTORE_DB="axignal_pilot_restore_check"
WORKDIR="$(mktemp -d)"
BACKUP="$WORKDIR/pilot.dump"
trap 'rm -rf "$WORKDIR"' EXIT

AXIGNAL_PILOT_ENV_FILE="$ENV_FILE" \
AXIGNAL_PILOT_COMPOSE_FILE="$COMPOSE_FILE" \
  bash infra/pilot/backup.sh "$BACKUP" >/dev/null

docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T postgres \
  dropdb --username "$POSTGRES_USER" --if-exists "$RESTORE_DB"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T postgres \
  createdb --username "$POSTGRES_USER" "$RESTORE_DB"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T postgres \
  pg_restore --username "$POSTGRES_USER" --dbname "$RESTORE_DB" \
  --no-owner --no-privileges < "$BACKUP"

SCHEMA_COUNT="$(docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T postgres \
  psql --username "$POSTGRES_USER" --dbname "$RESTORE_DB" --tuples-only --no-align \
  --command "SELECT count(*) FROM pg_namespace WHERE nspname IN ('tenant_private','evaluation');" \
  | tr -d '[:space:]')"

test "$SCHEMA_COUNT" = "2"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T postgres \
  dropdb --username "$POSTGRES_USER" "$RESTORE_DB"

printf '{"backup_nonempty":true,"restored_schemas":%s,"restore_rehearsal":"PASS"}\n' "$SCHEMA_COUNT"
