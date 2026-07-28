#!/usr/bin/env bash
set -euo pipefail

command="${1:-}"
metrics_dir="${RUNNER_TEMP:?RUNNER_TEMP is required}/axignal-runner-metrics"
metrics_file="${metrics_dir}/samples.tsv"
pid_file="${metrics_dir}/sampler.pid"
start_file="${metrics_dir}/started-at"

sample_forever() {
  local runner_uid workspace_kib cpu_percent rss_kib disk_used_kib
  runner_uid="$(id -u)"
  while true; do
    cpu_percent="$(
      ps -u "${runner_uid}" -o %cpu= |
        awk '{ total += $1 } END { printf "%.1f", total + 0 }'
    )"
    rss_kib="$(
      ps -u "${runner_uid}" -o rss= |
        awk '{ total += $1 } END { printf "%d", total + 0 }'
    )"
    workspace_kib="$(du -sk "${GITHUB_WORKSPACE}" 2>/dev/null | awk '{ print $1 + 0 }')"
    disk_used_kib="$(df -Pk "${GITHUB_WORKSPACE}" | awk 'NR == 2 { print $3 + 0 }')"
    printf '%s\t%s\t%s\t%s\t%s\n' \
      "$(date +%s)" "${cpu_percent}" "${rss_kib}" "${workspace_kib}" "${disk_used_kib}" \
      >> "${metrics_file}"
    sleep 5
  done
}

case "${command}" in
  start)
    mkdir -p "${metrics_dir}"
    : > "${metrics_file}"
    date +%s > "${start_file}"
    nohup "$0" sample >/dev/null 2>&1 &
    echo "$!" > "${pid_file}"
    ;;
  sample)
    sample_forever
    ;;
  stop)
    if [[ -f "${pid_file}" ]]; then
      sampler_pid="$(cat "${pid_file}")"
      kill "${sampler_pid}" 2>/dev/null || true
      wait "${sampler_pid}" 2>/dev/null || true
    fi
    [[ -s "${metrics_file}" ]] || {
      echo "No runner resource samples were recorded." >&2
      exit 1
    }
    duration_seconds="$(( $(date +%s) - $(cat "${start_file}") ))"
    read -r peak_cpu peak_rss peak_workspace disk_growth < <(
      awk -F '\t' '
        NR == 1 { first_disk = $5 }
        {
          if ($2 > peak_cpu) peak_cpu = $2
          if ($3 > peak_rss) peak_rss = $3
          if ($4 > peak_workspace) peak_workspace = $4
          last_disk = $5
        }
        END {
          printf "%.1f %d %d %d\n",
            peak_cpu + 0, peak_rss + 0, peak_workspace + 0, last_disk - first_disk
        }
      ' "${metrics_file}"
    )
    {
      echo "### Bounded resource evidence"
      echo
      echo "- Duration: \`${duration_seconds}s\`"
      echo "- Peak runner-user CPU: \`${peak_cpu}%\`"
      echo "- Peak runner-user RSS: \`${peak_rss} KiB\`"
      echo "- Peak workspace size: \`${peak_workspace} KiB\`"
      echo "- Host disk delta during sampling: \`${disk_growth} KiB\`"
    } >> "${GITHUB_STEP_SUMMARY:?GITHUB_STEP_SUMMARY is required}"
    ;;
  *)
    echo "Usage: $0 start|sample|stop" >&2
    exit 2
    ;;
esac
