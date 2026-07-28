#!/usr/bin/env bash
set -uo pipefail

status=0

record_failure() {
  echo "$1" >&2
  status=1
}

if ! bash scripts/runner/sample-metrics.sh stop; then
  record_failure "Runner metrics could not be finalised."
fi

if ! docker compose down --volumes --remove-orphans; then
  record_failure "Disposable Compose services could not be destroyed."
fi

if [[ -n "$(docker ps -aq --filter "label=com.docker.compose.project=${COMPOSE_PROJECT_NAME}")" ]]; then
  record_failure "Acceptance containers remain after cleanup."
fi

if [[ -n "$(docker volume ls -q --filter "label=com.docker.compose.project=${COMPOSE_PROJECT_NAME}")" ]]; then
  record_failure "Acceptance volumes remain after cleanup."
fi

for port in 3000 3001 5432 6379 8000; do
  if ss -H -ltn "sport = :${port}" | grep -q .; then
    record_failure "TCP port ${port} remains open after cleanup."
  fi
done

if pgrep -u "$(id -u)" -f \
  'next-server|playwright.*node|postgres.*axignal|valkey-server.*axignal' >/dev/null; then
  record_failure "A job-related process remains after cleanup."
fi

exit "${status}"
