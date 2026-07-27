#!/usr/bin/env bash
set -euo pipefail

expected_user="axignal-runner"
expected_home="/home/${expected_user}"
expected_work_prefix="${expected_home}/actions-runner/_work/"

if [[ "$(id -un)" != "${expected_user}" ]] || [[ "$(id -u)" == "0" ]]; then
  echo "Runner must execute as ${expected_user}, never root." >&2
  exit 1
fi

case "${GITHUB_WORKSPACE}/" in
  "${expected_work_prefix}"*) ;;
  *)
    echo "GITHUB_WORKSPACE is outside the dedicated runner work directory." >&2
    exit 1
    ;;
esac

case "${RUNNER_TEMP}/" in
  "${expected_work_prefix}"*) ;;
  *)
    echo "RUNNER_TEMP is outside the dedicated runner work directory." >&2
    exit 1
    ;;
esac

if [[ -r /var/run/docker.sock ]] || [[ -w /var/run/docker.sock ]]; then
  echo "The runner can access the rootful Docker socket." >&2
  exit 1
fi

if ! docker info --format '{{json .SecurityOptions}}' | grep -q '"name=rootless"'; then
  echo "Docker is not operating in rootless mode." >&2
  exit 1
fi

for forbidden_name in \
  DATABASE_URL \
  OPENAI_API_KEY \
  SSH_PRIVATE_KEY \
  STRIPE_SECRET_KEY \
  AWS_SECRET_ACCESS_KEY \
  AXIGNAL_PRODUCTION_DATABASE_URL; do
  if [[ -n "${!forbidden_name:-}" ]]; then
    echo "Forbidden production-capable environment variable is present: ${forbidden_name}" >&2
    exit 1
  fi
done

for forbidden_path in \
  "${expected_home}/.ssh/id_rsa" \
  "${expected_home}/.ssh/id_ed25519" \
  "${expected_home}/.env" \
  "${expected_home}/.env.production"; do
  if [[ -e "${forbidden_path}" ]]; then
    echo "Forbidden credential path is present: ${forbidden_path}" >&2
    exit 1
  fi
done

echo "PASS non-root identity, rootless Docker, workspace boundary and secret denylist"
