#!/usr/bin/env bash
set -Eeuo pipefail

INSTALL_DIR="/opt/axignal-github-storage-reclaimer"
CONFIG_DIR="/root/.config/axignal"
TOKEN_FILE="${CONFIG_DIR}/github-storage.env"
REPORT_DIR="/var/log/axignal-github-storage-reclaimer"
PINNED_COMMIT="bb81e0d5a9356e4506920be9cd0071d5476c6d8d"
PINNED_BLOB_SHA="b4dc69c80f4b40e18beb38db15c68ac98ec07040"
RAW_URL="https://raw.githubusercontent.com/LowToHi/axignal/${PINNED_COMMIT}/scripts/ops/reclaim_github_actions_storage.py"
TARGET_FREE_MIB="${TARGET_FREE_MIB:-300}"
PRESERVE_RECENT_HOURS="${PRESERVE_RECENT_HOURS:-24}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
INSTALL_LOG="${REPORT_DIR}/install-${STAMP}.log"
DRY_REPORT="${REPORT_DIR}/dry-run-${STAMP}.json"
EXEC_REPORT="${REPORT_DIR}/execution-${STAMP}.json"
LOCK_FILE="/run/lock/axignal-github-storage-reclaimer.lock"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "This installer must run as root." >&2
  exit 10
fi

mkdir -p "$INSTALL_DIR" "$CONFIG_DIR" "$REPORT_DIR" "$(dirname "$LOCK_FILE")"
chmod 700 "$INSTALL_DIR" "$CONFIG_DIR" "$REPORT_DIR"
exec > >(tee -a "$INSTALL_LOG") 2>&1

printf 'AXIGNAL_ACTIONS_STORAGE_INSTALL_START=%s\n' "$(date -u --iso-8601=seconds)"
printf 'PINNED_COMMIT=%s\n' "$PINNED_COMMIT"
printf 'PINNED_BLOB_SHA=%s\n' "$PINNED_BLOB_SHA"

for command in curl python3 flock; do
  command -v "$command" >/dev/null 2>&1 || {
    echo "Missing required command: $command" >&2
    exit 11
  }
done

if [[ ! -f "$TOKEN_FILE" ]]; then
  cat >&2 <<EOF
Missing ${TOKEN_FILE}.
Create it with exactly:
  GH_TOKEN=<fine-grained token with Actions read/write and Contents read for LowToHi/axignal>
Then run this installer again.
EOF
  exit 12
fi

chmod 600 "$TOKEN_FILE"
# shellcheck disable=SC1090
source "$TOKEN_FILE"
: "${GH_TOKEN:?GH_TOKEN is missing from ${TOKEN_FILE}}"
export GH_TOKEN
export GITHUB_TOKEN="$GH_TOKEN"
export GITHUB_REPOSITORY="LowToHi/axignal"

TMP_SCRIPT="$(mktemp)"
trap 'rm -f "$TMP_SCRIPT"' EXIT

curl \
  --fail \
  --location \
  --retry 5 \
  --retry-all-errors \
  --connect-timeout 20 \
  --max-time 180 \
  "$RAW_URL" \
  --output "$TMP_SCRIPT"

python3 - "$TMP_SCRIPT" "$PINNED_BLOB_SHA" <<'PY'
from __future__ import annotations

import hashlib
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
expected = sys.argv[2]
data = path.read_bytes()
actual = hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()
if actual != expected:
    raise SystemExit(f"Git blob verification failed: expected={expected} actual={actual}")
print(f"RECLAIMER_GIT_BLOB_SHA={actual}")
PY

install -o root -g root -m 0700 "$TMP_SCRIPT" "$INSTALL_DIR/reclaim.py"
python3 -m py_compile "$INSTALL_DIR/reclaim.py"

cat >"/usr/local/sbin/axignal-actions-storage-reclaim" <<'WRAPPER'
#!/usr/bin/env bash
set -Eeuo pipefail

TOKEN_FILE="/root/.config/axignal/github-storage.env"
REPORT_DIR="/var/log/axignal-github-storage-reclaimer"
LOCK_FILE="/run/lock/axignal-github-storage-reclaimer.lock"
TARGET_FREE_MIB="${TARGET_FREE_MIB:-300}"
PRESERVE_RECENT_HOURS="${PRESERVE_RECENT_HOURS:-24}"
DRY_RUN="${DRY_RUN:-true}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
REPORT_PATH="${REPORT_PATH:-${REPORT_DIR}/manual-${STAMP}.json}"

mkdir -p "$REPORT_DIR" "$(dirname "$LOCK_FILE")"
chmod 700 "$REPORT_DIR"
chmod 600 "$TOKEN_FILE"
# shellcheck disable=SC1090
source "$TOKEN_FILE"
: "${GH_TOKEN:?GH_TOKEN is missing from ${TOKEN_FILE}}"

export GH_TOKEN
export GITHUB_TOKEN="$GH_TOKEN"
export GITHUB_REPOSITORY="LowToHi/axignal"
export TARGET_FREE_MIB PRESERVE_RECENT_HOURS DRY_RUN REPORT_PATH

exec flock -n "$LOCK_FILE" python3 /opt/axignal-github-storage-reclaimer/reclaim.py
WRAPPER
chmod 700 /usr/local/sbin/axignal-actions-storage-reclaim

printf '\n### DRY RUN\n'
DRY_RUN=true \
TARGET_FREE_MIB="$TARGET_FREE_MIB" \
PRESERVE_RECENT_HOURS="$PRESERVE_RECENT_HOURS" \
REPORT_PATH="$DRY_REPORT" \
/usr/local/sbin/axignal-actions-storage-reclaim

python3 - "$DRY_REPORT" <<'PY'
from __future__ import annotations

import json
import pathlib
import sys

report = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
if not report.get("target_reached"):
    raise SystemExit(
        f"Dry-run cannot safely recover the target: planned={report.get('planned_free_mib')} MiB"
    )
if report.get("failures"):
    raise SystemExit(f"Dry-run contains failures: {report['failures']}")
print(f"DRY_RUN_PLANNED_FREE_MIB={report['planned_free_mib']}")
print(f"DRY_RUN_PLANNED_RUN_COUNT={report['planned_run_count']}")
PY

printf '\n### EXECUTION\n'
DRY_RUN=false \
TARGET_FREE_MIB="$TARGET_FREE_MIB" \
PRESERVE_RECENT_HOURS="$PRESERVE_RECENT_HOURS" \
REPORT_PATH="$EXEC_REPORT" \
/usr/local/sbin/axignal-actions-storage-reclaim

python3 - "$EXEC_REPORT" <<'PY'
from __future__ import annotations

import json
import pathlib
import sys

report = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
if report.get("failures"):
    raise SystemExit(f"Execution contains failures: {report['failures']}")
if not report.get("target_reached"):
    raise SystemExit(
        f"Execution did not reach target: freed={report.get('freed_mib')} MiB"
    )
if report.get("deleted_runs") != report.get("verified_404_runs"):
    raise SystemExit("Deleted runs and verified-404 runs differ")
print(f"AXIGNAL_ACTIONS_STORAGE_RECLAIMED_MIB={report['freed_mib']}")
print(f"AXIGNAL_ACTIONS_STORAGE_ESTIMATED_AFTER_MIB={report['estimated_mib_after']}")
print(f"AXIGNAL_ACTIONS_STORAGE_DELETED_RUNS={len(report['deleted_runs'])}")
print("AXIGNAL_ACTIONS_STORAGE_RECLAMATION=PASS")
PY

printf 'DRY_REPORT=%s\n' "$DRY_REPORT"
printf 'EXEC_REPORT=%s\n' "$EXEC_REPORT"
printf 'INSTALL_LOG=%s\n' "$INSTALL_LOG"
printf 'AXIGNAL_ACTIONS_STORAGE_INSTALL_END=%s\n' "$(date -u --iso-8601=seconds)"
