#!/usr/bin/env bash
set -euo pipefail

expected_user="axignal-runner"
expected_runner_name="axignal-build-01"
expected_home="/home/${expected_user}"
expected_work_prefix="${expected_home}/actions-runner/_work/"

fail() {
  echo "FAIL shared build runner boundary: $*" >&2
  exit 1
}

[[ "$(id -un)" == "${expected_user}" ]] || fail "effective user must be ${expected_user}"
[[ "$(id -u)" != "0" ]] || fail "runner must never execute as root"
[[ "${RUNNER_NAME:-}" == "${expected_runner_name}" ]] || fail "runner name must be ${expected_runner_name}"
[[ "${RUNNER_OS:-}" == "Linux" ]] || fail "runner OS must be Linux"
[[ "${RUNNER_ARCH:-}" == "X64" ]] || fail "runner architecture must be X64"
[[ "${HOME}" == "${expected_home}" ]] || fail "HOME must be ${expected_home}"

case "${GITHUB_WORKSPACE}/" in
  "${expected_work_prefix}"*) ;;
  *) fail "workspace is outside the dedicated runner work directory" ;;
esac

case "${RUNNER_TEMP}/" in
  "${expected_work_prefix}"*) ;;
  *) fail "runner temp is outside the dedicated runner work directory" ;;
esac

for forbidden_group in sudo docker; do
  if id -nG | tr ' ' '\n' | grep -qx "${forbidden_group}"; then
    fail "runner belongs to forbidden group ${forbidden_group}"
  fi
done

if [[ -r /var/run/docker.sock || -w /var/run/docker.sock ]]; then
  fail "rootful Docker socket is accessible"
fi

if [[ -n "${DOCKER_HOST:-}" ]]; then
  fail "DOCKER_HOST must not be present on the shared build runner"
fi

for forbidden_name in \
  DATABASE_URL \
  OPENAI_API_KEY \
  SSH_PRIVATE_KEY \
  STRIPE_SECRET_KEY \
  AWS_SECRET_ACCESS_KEY \
  AXIGNAL_PRODUCTION_DATABASE_URL \
  LOWTOHI_DATABASE_URL \
  IAMANCHA_DATABASE_URL \
  BIOCULTOR_DATABASE_URL; do
  if [[ -n "${!forbidden_name:-}" ]]; then
    fail "forbidden environment variable is present: ${forbidden_name}"
  fi
done

for forbidden_path in \
  "${expected_home}/.ssh/id_rsa" \
  "${expected_home}/.ssh/id_ed25519" \
  "${expected_home}/.env" \
  "${expected_home}/.env.production" \
  "/var/run/docker.sock" \
  "/var/lib/docker" \
  "/etc/traefik"; do
  if [[ -e "${forbidden_path}" && -r "${forbidden_path}" ]]; then
    fail "forbidden host path is readable: ${forbidden_path}"
  fi
done

if find "${GITHUB_WORKSPACE}" -xdev -type f \
  \( -name '.env' -o -name '.env.production' -o -name 'id_rsa' -o -name 'id_ed25519' \
     -o -name '*.pem' -o -name '*.key' \) -print -quit | grep -q .; then
  fail "credential-shaped file exists in the checkout"
fi

if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
  fail "shared build runner must not have a usable Docker daemon"
fi

if [[ -f /proc/self/mountinfo ]] && grep -Eq '/var/lib/docker|/var/run/docker\.sock|/etc/traefik' /proc/self/mountinfo; then
  fail "forbidden host mount is visible inside the runner boundary"
fi

printf 'PASS shared build runner identity, workspace, privilege, Docker and secret boundaries\n'
