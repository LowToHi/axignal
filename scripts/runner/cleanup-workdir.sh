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

for cleanup_target in "${resolved_work_dir}/axignal" "${resolved_work_dir}/_temp"; do
  case "${cleanup_target}" in
    "${resolved_runner_root}/_work/axignal" | "${resolved_runner_root}/_work/_temp")
      rm -rf -- "${cleanup_target}"
      ;;
    *)
      echo "Refusing unexpected cleanup target: ${cleanup_target}" >&2
      exit 1
      ;;
  esac
done

while IFS= read -r container_id; do
  project="$(
    docker inspect \
      --format '{{ index .Config.Labels "com.docker.compose.project" }}' \
      "${container_id}"
  )"
  case "${project}" in
    axignal-acceptance-*) docker rm --force "${container_id}" ;;
  esac
done < <(docker ps -aq --filter "label=com.docker.compose.project")

while IFS= read -r volume_name; do
  project="$(
    docker volume inspect \
      --format '{{ index .Labels "com.docker.compose.project" }}' \
      "${volume_name}"
  )"
  case "${project}" in
    axignal-acceptance-*) docker volume rm "${volume_name}" ;;
  esac
done < <(docker volume ls -q --filter "label=com.docker.compose.project")
