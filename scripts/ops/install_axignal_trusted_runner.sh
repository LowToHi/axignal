#!/usr/bin/env bash
set -Eeuo pipefail

# Prepare an isolated AXIGNAL self-hosted runner. Registration is disabled by
# default because AXIGNAL is public. Set REGISTER_RUNNER=true only after trusted
# workflows use the labels self-hosted,linux,x64,axignal,trusted and exclude PRs.

REPOSITORY_URL="${REPOSITORY_URL:-https://github.com/LowToHi/axignal}"
RUNNER_VERSION="${RUNNER_VERSION:-2.336.0}"
RUNNER_SHA256="${RUNNER_SHA256:-04cf0be1aff4c3ec3554466c39124ca250e3effd8873bb7e8d68535aa9505d5d}"
RUNNER_NAME="${RUNNER_NAME:-axignal-trusted-01}"
RUNNER_USER="${RUNNER_USER:-runner-axignal}"
INSTALL_ROOT="${INSTALL_ROOT:-/opt/actions-runner-axignal}"
STATE_ROOT="${STATE_ROOT:-/var/lib/axignal-runner}"
WORK_ROOT="${WORK_ROOT:-${STATE_ROOT}/work}"
CACHE_ROOT="${CACHE_ROOT:-/var/cache/axignal}"
LOG_ROOT="${LOG_ROOT:-/var/log/axignal-runner}"
CACHE_BUDGET_GIB="${CACHE_BUDGET_GIB:-25}"
REGISTER_RUNNER="${REGISTER_RUNNER:-false}"
ALLOW_DOCKER="${ALLOW_DOCKER:-false}"

if [[ "${EUID}" -ne 0 ]]; then
  echo "ERROR: run as root" >&2
  exit 1
fi

case "${REGISTER_RUNNER}" in true|false) ;; *) echo "ERROR: REGISTER_RUNNER must be true or false" >&2; exit 1 ;; esac
case "${ALLOW_DOCKER}" in true|false) ;; *) echo "ERROR: ALLOW_DOCKER must be true or false" >&2; exit 1 ;; esac

export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y --no-install-recommends ca-certificates curl tar gzip jq findutils coreutils util-linux

if ! id "${RUNNER_USER}" >/dev/null 2>&1; then
  useradd --create-home --home-dir "${STATE_ROOT}" --shell /bin/bash "${RUNNER_USER}"
fi

install -d -m 0750 -o "${RUNNER_USER}" -g "${RUNNER_USER}" \
  "${INSTALL_ROOT}" "${STATE_ROOT}" "${WORK_ROOT}" "${CACHE_ROOT}" "${LOG_ROOT}"
for cache in npm pnpm pip playwright buildkit; do
  install -d -m 0750 -o "${RUNNER_USER}" -g "${RUNNER_USER}" "${CACHE_ROOT}/${cache}"
done

archive="/tmp/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz"
url="https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz"
curl --fail --location --retry 5 --retry-all-errors --connect-timeout 20 --max-time 600 \
  "${url}" --output "${archive}"
echo "${RUNNER_SHA256}  ${archive}" | sha256sum --check --status || {
  echo "ERROR: runner archive checksum mismatch" >&2
  rm -f "${archive}"
  exit 1
}

if [[ ! -x "${INSTALL_ROOT}/config.sh" ]]; then
  tar -xzf "${archive}" -C "${INSTALL_ROOT}"
fi
rm -f "${archive}"
chown -R "${RUNNER_USER}:${RUNNER_USER}" "${INSTALL_ROOT}" "${STATE_ROOT}" "${CACHE_ROOT}" "${LOG_ROOT}"

cat > "${INSTALL_ROOT}/.env" <<EOF
npm_config_cache=${CACHE_ROOT}/npm
pnpm_config_store_dir=${CACHE_ROOT}/pnpm
PIP_CACHE_DIR=${CACHE_ROOT}/pip
PLAYWRIGHT_BROWSERS_PATH=${CACHE_ROOT}/playwright
AXIGNAL_BUILDKIT_CACHE=${CACHE_ROOT}/buildkit
ACTIONS_RUNNER_HOOK_JOB_STARTED=/usr/local/sbin/axignal-runner-pre-job
ACTIONS_RUNNER_HOOK_JOB_COMPLETED=/usr/local/sbin/axignal-runner-post-job
EOF
chown "${RUNNER_USER}:${RUNNER_USER}" "${INSTALL_ROOT}/.env"
chmod 0640 "${INSTALL_ROOT}/.env"

cat > /etc/axignal-runner.conf <<EOF
RUNNER_USER=${RUNNER_USER}
INSTALL_ROOT=${INSTALL_ROOT}
STATE_ROOT=${STATE_ROOT}
WORK_ROOT=${WORK_ROOT}
CACHE_ROOT=${CACHE_ROOT}
LOG_ROOT=${LOG_ROOT}
CACHE_BUDGET_GIB=${CACHE_BUDGET_GIB}
EOF
chmod 0644 /etc/axignal-runner.conf

cat > /usr/local/sbin/axignal-runner-cache-guard <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail
source /etc/axignal-runner.conf
budget_bytes=$((CACHE_BUDGET_GIB * 1024 * 1024 * 1024))
used_bytes="$(du -sx --block-size=1 "${CACHE_ROOT}" | awk '{print $1}')"
percent=$((used_bytes * 100 / budget_bytes))
log="${LOG_ROOT}/cache-guard.log"
mkdir -p "${LOG_ROOT}"
printf '%s used_bytes=%s budget_bytes=%s percent=%s\n' "$(date -u +%FT%TZ)" "${used_bytes}" "${budget_bytes}" "${percent}" >> "${log}"
if (( percent >= 70 )); then
  find "${CACHE_ROOT}" -xdev -type f -atime +14 -delete || true
  find "${CACHE_ROOT}" -xdev -type d -empty -delete || true
fi
used_bytes="$(du -sx --block-size=1 "${CACHE_ROOT}" | awk '{print $1}')"
percent=$((used_bytes * 100 / budget_bytes))
if (( percent >= 85 )); then
  find "${CACHE_ROOT}" -xdev -type f -atime +3 -delete || true
  find "${CACHE_ROOT}" -xdev -type d -empty -delete || true
fi
used_bytes="$(du -sx --block-size=1 "${CACHE_ROOT}" | awk '{print $1}')"
percent=$((used_bytes * 100 / budget_bytes))
if (( percent >= 92 )); then
  touch "${STATE_ROOT}/BLOCKED_STORAGE"
else
  rm -f "${STATE_ROOT}/BLOCKED_STORAGE"
fi
chown -R "${RUNNER_USER}:${RUNNER_USER}" "${CACHE_ROOT}" "${STATE_ROOT}" "${LOG_ROOT}"
EOF
chmod 0755 /usr/local/sbin/axignal-runner-cache-guard

cat > /usr/local/sbin/axignal-runner-pre-job <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail
source /etc/axignal-runner.conf
/usr/local/sbin/axignal-runner-cache-guard
if [[ -e "${STATE_ROOT}/BLOCKED_STORAGE" ]]; then
  echo "AXIGNAL_RUNNER_STORAGE_GUARD=BLOCKED" >&2
  exit 75
fi
if [[ "${GITHUB_REPOSITORY:-}" != "LowToHi/axignal" ]]; then
  echo "AXIGNAL_RUNNER_REPOSITORY_GUARD=BLOCKED" >&2
  exit 76
fi
case "${GITHUB_EVENT_NAME:-}" in
  pull_request|pull_request_target)
    echo "AXIGNAL_RUNNER_PUBLIC_PR_GUARD=BLOCKED" >&2
    exit 77
    ;;
esac
echo "AXIGNAL_RUNNER_PRE_JOB=PASS"
EOF
chmod 0755 /usr/local/sbin/axignal-runner-pre-job

cat > /usr/local/sbin/axignal-runner-post-job <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail
/usr/local/sbin/axignal-runner-cache-guard
echo "AXIGNAL_RUNNER_POST_JOB=PASS"
EOF
chmod 0755 /usr/local/sbin/axignal-runner-post-job

cat > /etc/systemd/system/axignal-runner-cache-guard.service <<'EOF'
[Unit]
Description=AXIGNAL runner cache guard
After=local-fs.target

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/axignal-runner-cache-guard
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=/var/cache/axignal /var/lib/axignal-runner /var/log/axignal-runner
EOF

cat > /etc/systemd/system/axignal-runner-cache-guard.timer <<'EOF'
[Unit]
Description=Run AXIGNAL runner cache guard hourly

[Timer]
OnBootSec=5min
OnUnitActiveSec=1h
Persistent=true
RandomizedDelaySec=5min

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl enable --now axignal-runner-cache-guard.timer
/usr/local/sbin/axignal-runner-cache-guard

if [[ "${ALLOW_DOCKER}" == "true" ]]; then
  if getent group docker >/dev/null; then
    usermod -aG docker "${RUNNER_USER}"
  else
    echo "ERROR: ALLOW_DOCKER=true but docker group is absent" >&2
    exit 1
  fi
fi

if [[ "${REGISTER_RUNNER}" == "true" ]]; then
  if [[ -z "${RUNNER_REGISTRATION_TOKEN:-}" ]]; then
    read -rsp "GitHub runner registration token: " RUNNER_REGISTRATION_TOKEN
    echo
  fi
  if [[ -z "${RUNNER_REGISTRATION_TOKEN}" ]]; then
    echo "ERROR: runner registration token is required" >&2
    exit 1
  fi
  if [[ -f "${INSTALL_ROOT}/.runner" ]]; then
    echo "ERROR: runner already configured; refusing implicit replacement" >&2
    exit 1
  fi
  runuser -u "${RUNNER_USER}" -- bash -lc "cd '${INSTALL_ROOT}' && ./config.sh --unattended --url '${REPOSITORY_URL}' --token '${RUNNER_REGISTRATION_TOKEN}' --name '${RUNNER_NAME}' --labels 'axignal,trusted' --work '${WORK_ROOT}'"
  unset RUNNER_REGISTRATION_TOKEN
  cd "${INSTALL_ROOT}"
  ./svc.sh install "${RUNNER_USER}"
  ./svc.sh start
  ./svc.sh status
  echo "AXIGNAL_TRUSTED_RUNNER_REGISTERED=PASS"
else
  echo "AXIGNAL_TRUSTED_RUNNER_PREPARED=PASS"
  echo "AXIGNAL_TRUSTED_RUNNER_REGISTERED=NO"
fi

echo "RUNNER_VERSION=${RUNNER_VERSION}"
echo "RUNNER_SHA256=${RUNNER_SHA256}"
echo "RUNNER_ROOT=${INSTALL_ROOT}"
echo "RUNNER_WORK_ROOT=${WORK_ROOT}"
echo "RUNNER_CACHE_ROOT=${CACHE_ROOT}"
echo "RUNNER_CACHE_BUDGET_GIB=${CACHE_BUDGET_GIB}"
