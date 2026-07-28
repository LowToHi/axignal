#!/usr/bin/env bash
set -euo pipefail

runner_root="/home/axignal-runner/actions-runner"
work_dir="${runner_root}/_work"

resolved_runner_root="$(realpath -e "${runner_root}")"
resolved_work_dir="$(realpath -e "${work_dir}")"

if [[ "${resolved_runner_root}" != "/home/axignal-runner/actions-runner" ]] ||
   [[ "${resolved_work_dir}" != "${resolved_runner_root}/_work" ]]; then
  echo "Refusing cleanup outside the AXIGNAL runner work directory." >&2
  exit 1
fi

for pattern in \
  'next-server' \
  'playwright.*node' \
  'uvicorn.*axignal' \
  'python.*pytest'; do
  pkill -u "$(id -u axignal-runner)" -f "${pattern}" 2>/dev/null || true
done

for cleanup_target in \
  "${resolved_work_dir}/axignal" \
  "${resolved_work_dir}/_temp" \
  "${resolved_work_dir}/_actions" \
  "${resolved_work_dir}/_tool"; do
  case "${cleanup_target}" in
    "${resolved_work_dir}/axignal" | \
    "${resolved_work_dir}/_temp" | \
    "${resolved_work_dir}/_actions" | \
    "${resolved_work_dir}/_tool")
      rm -rf -- "${cleanup_target}"
      ;;
    *)
      echo "Refusing unexpected cleanup target: ${cleanup_target}" >&2
      exit 1
      ;;
  esac
done

mkdir -p "${resolved_work_dir}"
chmod 700 "${resolved_work_dir}"

echo "PASS shared build runner workspace cleanup"
