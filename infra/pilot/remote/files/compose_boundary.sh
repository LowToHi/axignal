#!/usr/bin/env bash

axignal_compose_args() {
  local release="${1:?release path is required}"
  local env_file="${2:?environment file is required}"
  local base_file="$release/infra/pilot/compose.yaml"

  [[ -f "$base_file" ]] || {
    echo "missing pilot Compose file: $base_file" >&2
    return 2
  }
  [[ -f "$env_file" ]] || {
    echo "missing private environment file: $env_file" >&2
    return 2
  }

  set -a
  # shellcheck disable=SC1090
  source "$env_file"
  set +a

  local edge_mode="${AXIGNAL_PILOT_EDGE_MODE:-standalone}"
  local edge_file="$release/infra/pilot/remote/compose.$edge_mode.yaml"
  case "$edge_mode" in
    standalone | shared-traefik) ;;
    *)
      echo "unsupported AXIGNAL pilot edge mode: $edge_mode" >&2
      return 2
      ;;
  esac

  if [[ -f "$edge_file" ]]; then
    AXIGNAL_COMPOSE=(
      docker compose
      --env-file "$env_file"
      -f "$base_file"
      -f "$edge_file"
    )
    return 0
  fi

  if [[ "$edge_mode" == "standalone" ]] && grep -q '^[[:space:]]*ports:' "$base_file"; then
    AXIGNAL_COMPOSE=(docker compose --env-file "$env_file" -f "$base_file")
    return 0
  fi

  echo "release does not support required edge mode: $edge_mode" >&2
  return 2
}
